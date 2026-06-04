/**
 * EU Trend Analyzer Telegram Bot v2 — STABLE
 * Используем polling=false + короткие запросы + auto-restart
 */

import TelegramBot from 'node-telegram-bot-api';
import cron from 'node-cron';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import TrendAnalyzer from './analyzer.js';
import { formatTrendResults } from './formatter.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(__dirname, '..', 'data');
const RESULTS_FILE = path.join(DATA_DIR, 'latest_results.json');

if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

// ===== CONFIG =====
const BOT_TOKEN = '8792613395:AAGquGo3aZ1fbFjToatyR5hSLJiYR0Bs9s8';
let ADMIN_CHAT_ID = '';
let latestResult = null;
let isAnalyzing = false;
let lastUpdateId = 0;
const EXPIRED_CB_IDS = new Set();

// Загружаем предыдущие результаты
if (fs.existsSync(RESULTS_FILE)) {
  try { latestResult = JSON.parse(fs.readFileSync(RESULTS_FILE, 'utf-8')); } catch(e) {}
}

const analyzer = new TrendAnalyzer();
const bot = new TelegramBot(BOT_TOKEN, { polling: false });

// ===== HELPERS =====
function getMainMenu() {
  return {
    reply_markup: {
      inline_keyboard: [
        [{ text: '🔍 Запустить аналитику', callback_data: 'start_analysis' }],
        [{ text: '📊 Выдать результаты', callback_data: 'show_results' }],
      ],
    },
  };
}

// Отправка сообщения с фоллбэком на Markdown ошибки
async function safeSend(chatId, text, extra = {}) {
  try {
    return await bot.sendMessage(chatId, text, { parse_mode: 'MarkdownV2', ...extra });
  } catch (mdErr) {
    // Если MarkdownV2 не прошёл — отправляем без форматирования
    console.log('[Bot] Markdown error, sending plain text');
    const plainExtra = { ...extra };
    delete plainExtra.parse_mode;
    return await bot.sendMessage(chatId, text, plainExtra);
  }
}

// ===== UPDATE HANDLER =====
async function handleUpdate(update) {
  try {
    // --- MESSAGE ---
    if (update.message) {
      const chatId = update.message.chat.id;
      const text = update.message.text || '';
      ADMIN_CHAT_ID = String(chatId);

      if (text === '/start') {
        await safeSend(chatId,
          '👋 *EU Trend Analyzer Bot*\n\nАнализирую набирающие популярность товары и услуги в Европе.\n\nНажмите кнопку ниже для начала:',
          getMainMenu()
        );
        console.log(`[Bot] /start from chat ${chatId}`);
      } else if (text === '/status') {
        const s = latestResult
          ? `📊 Последняя аналитика: ${latestResult.date}\n📈 Трендов: ${latestResult.trends?.length || 0}\n🔍 Источников: ${latestResult.totalRawResults || 0}`
          : '📭 Результатов пока нет';
        await bot.sendMessage(chatId, s, getMainMenu());
      }
      return;
    }

    // --- CALLBACK QUERY ---
    if (update.callback_query) {
      const cq = update.callback_query;
      const chatId = cq.message?.chat?.id;
      const data = cq.data;
      ADMIN_CHAT_ID = String(chatId);

      // Пропускаем старые callback query
      if (EXPIRED_CB_IDS.has(cq.id)) {
        console.log(`[Bot] Skipping expired callback ${cq.id}`);
        return;
      }

      // Пытаемся ответить, игнорируем ошибку таймаута
      try {
        await bot.answerCallbackQuery(cq.id);
      } catch (e) {
        // Не критично — кнопка просто останется "нажатой"
        EXPIRED_CB_IDS.add(cq.id);
        console.log(`[Bot] Callback ${cq.id} expired, skipping`);
        return;
      }

      // --- START ANALYSIS ---
      if (data === 'start_analysis') {
        if (isAnalyzing) {
          await bot.sendMessage(chatId, '⏳ Анализ уже запущен! Подождите...', getMainMenu());
          return;
        }

        await bot.sendMessage(chatId, '🔄 *Аналитика трендов запущена...*\n\nИщу набирающие популярность товары и услуги в Европе.\nЭто займет 1-2 минуты.', {
          parse_mode: 'MarkdownV2',
        });
        console.log(`[Bot] Analysis STARTED for chat ${chatId}`);

        isAnalyzing = true;

        // Запускаем анализ в фоне, чтобы не блокировать pollLoop
        (async () => {
          try {
            await analyzer.init();
            const result = await analyzer.runFullAnalysis();
            latestResult = result;
            fs.writeFileSync(RESULTS_FILE, JSON.stringify(result, null, 2));
            console.log(`[Bot] Analysis DONE: ${result.trends.length} trends`);
            await safeSend(chatId,
              '✅ *Аналитика завершена!*\n\nНажмите «Выдать результаты» чтобы увидеть ТОП трендов.',
              getMainMenu()
            );
          } catch (err) {
            console.error('[Bot] Analysis FAILED:', err.message);
            await bot.sendMessage(chatId, `❌ Ошибка при анализе:\n${err.message}\n\nПопробуйте ещё раз.`, getMainMenu());
          } finally {
            isAnalyzing = false;
          }
        })();
        return;
      }

      // --- SHOW RESULTS ---
      if (data === 'show_results') {
        if (!latestResult) {
          await bot.sendMessage(chatId, '📭 Результатов пока нет.\n\nНажмите «Запустить аналитику» чтобы начать.', getMainMenu());
          return;
        }
        console.log(`[Bot] Sending results for chat ${chatId}`);
        const messages = formatTrendResults(latestResult);
        for (const m of messages) {
          await safeSend(chatId, m);
          await new Promise(r => setTimeout(r, 500));
        }
        await bot.sendMessage(chatId, '───\nДля новой аналитики нажмите кнопку:', getMainMenu());
      }
    }
  } catch (err) {
    console.error('[Bot] handleUpdate error:', err.message?.substring(0, 200));
  }
}

// ===== POLL LOOP =====
async function pollLoop() {
  while (true) {
    try {
      const updates = await bot.getUpdates({
        offset: lastUpdateId + 1,
        timeout: 10,
      });

      if (updates && updates.length > 0) {
        for (const u of updates) {
          lastUpdateId = u.update_id;
          // Не await — обрабатываем fire-and-forget для скорости
          handleUpdate(u);
        }
        console.log(`[Bot] Got ${updates.length} update(s)`);
      }
    } catch (err) {
      if (err.code === 'ETIMEDOUT' || err.code === 'ECONNRESET' || err.code === 'EPIPE') {
        // Network glitch — норм, просто повторяем
      } else {
        console.error('[Bot] Poll error:', err.code, err.message?.substring(0, 100));
      }
    }
    await new Promise(r => setTimeout(r, 1000));
  }
}

// ===== CRON =====
cron.schedule('0 9 * * *', async () => {
  if (isAnalyzing || !ADMIN_CHAT_ID) return;
  isAnalyzing = true;
  try {
    await analyzer.init();
    const result = await analyzer.runFullAnalysis();
    latestResult = result;
    fs.writeFileSync(RESULTS_FILE, JSON.stringify(result, null, 2));
    await safeSend(ADMIN_CHAT_ID,
      '🔄 *Ежедневная аналитика завершена!* Результаты готовы к выдаче.',
      getMainMenu()
    );
  } catch (err) {
    console.error('[Cron] Error:', err.message);
  } finally {
    isAnalyzing = false;
  }
}, { timezone: 'Europe/Moscow' });

// ===== START =====
console.log('========================================');
console.log('  EU TREND ANALYZER BOT v2');
console.log('========================================');
console.log('  Cron: 09:00 MSK daily');
console.log('  Status: RUNNING');
console.log('========================================');

pollLoop();
