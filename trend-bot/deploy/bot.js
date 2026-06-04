/**
 * ╔════════════════════════════════════════════════════════════╗
 * ║  EU TREND BOT — ПОЛНАЯ ВЕРСИЯ ДЛЯ DEPLOY               ║
 * ║  Деплой: Replit.com / Render.com / Railway.app / VPS       ║
 * ║  Запуск:  npm install && node bot.js                       ║
 * ║                                                            ║
 * ║  Работает БЕСЕОПЕЧНОЕК для любого кол-ва юзеров          ║
 * ║  Поиск через DuckDuckGo (не нужен API ключ!)              ║
 * ║  Авто-анализ каждый день в 09:00 МСК                      ║
 * ╚════════════════════════════════════════════════════════════╝
 */

import TelegramBot from "node-telegram-bot-api";
import cron from "node-cron";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const BOT_TOKEN = "8792613395:AAGquGo3aZ1fbFjToatyR5hSLJiYR0Bs9s8";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(__dirname, "data");
const TRENDS_FILE = path.join(DATA_DIR, "trends.json");
const STATE_FILE = path.join(DATA_DIR, "state.json");

if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

// =============== FILTERS ===============
const SKIP = [
  "food delivery","groceries","grocery","restaurant","alcohol","pharmacy","medicine",
  "flowers","flower","clothing","fashion","shoes","phones","laptops","beauty products",
  "makeup","cosmetics","recipe","meal","meals","pizza","sushi","burger","drug",
  "healthcare","hospital","workout","gym","yoga","pet food","baby food",
];

const QUERIES = [
  "fastest growing e-commerce categories Europe 2025 2026",
  "trending products European consumers buying 2026",
  "growing online shopping categories EU market 2026",
  "European consumer trends non-obvious 2026",
  "innovative products gaining popularity Europe 2026",
  "European market trending niches 2025 2026",
  "new popular online orders Europe growing",
  "European subscription services trending 2026",
  "top emerging product categories Europe ecommerce",
  "European digital products trends 2026",
];

// =============== STATE ===============
function loadState() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, "utf-8")); }
  catch { return { users: [], isAnalyzing: false, lastAnalysisDate: null }; }
}
function saveState(s) { try { fs.writeFileSync(STATE_FILE, JSON.stringify(s, null, 2)); } catch {} }
function addUser(s, id, name) {
  if (!s.users) s.users = [];
  if (!s.users.find(u => u.chatId === id)) s.users.push({ chatId: id, name: name || "User" });
}
function loadTrends() {
  try { return JSON.parse(fs.readFileSync(TRENDS_FILE, "utf-8")); }
  catch { return null; }
}
function saveTrends(t) { try { fs.writeFileSync(TRENDS_FILE, JSON.stringify(t, null, 2)); } catch {} }

// =============== DUCKDUCKGO SEARCH (NO API KEY!) ===============
function stripHtml(h) {
  return h.replace(/<[^>]*>/g, "").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').trim();
}

async function searchDDG(query) {
  try {
    const resp = await fetch(`https://lite.duckduckgo.com/lite/?q=${encodeURIComponent(query)}`, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html",
      },
      redirect: "follow",
    });
    if (!resp.ok) return [];
    const html = await resp.text();
    const results = [];

    // Parse DuckDuckGo Lite HTML
    const linkRx = /<a[^>]+class="result-link"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
    const snipRx = /<td[^>]+class="result-snippet"[^>]*>([\s\S]*?)<\/td>/gi;
    const urlRx = /<td[^>]+class="result-url"[^>]*>([\s\S]*?)<\/td>/gi;

    const links = [], snips = [], urls = [];
    let m;
    while ((m = linkRx.exec(html)) !== null) links.push({ url: m[1], title: stripHtml(m[2]) });
    while ((m = snipRx.exec(html)) !== null) snips.push(stripHtml(m[1]));
    while ((m = urlRx.exec(html)) !== null) urls.push(stripHtml(m[1]));

    for (let i = 0; i < links.length; i++) {
      try {
        let rawUrl = links[i].url;
        if (rawUrl.includes("uddg=")) {
          const p = new URL(rawUrl).searchParams;
          if (p.get("uddg")) rawUrl = decodeURIComponent(p.get("uddg"));
        }
        if (!rawUrl.startsWith("http")) rawUrl = "https://" + rawUrl;
        const domain = new URL(rawUrl).hostname.replace(/^www\./, "");
        results.push({ name: links[i].title, url: rawUrl, domain, snippet: snips[i] || "", host_name: domain });
      } catch {}
    }
    return results;
  } catch (e) {
    console.error("Search err:", e.message);
    return [];
  }
}

// =============== ANALYZER ===============
async function runAnalysis(notifyChatId, notifyAll = false) {
  const state = loadState();
  if (state.isAnalyzing) {
    if (notifyChatId) bot.sendMessage(notifyChatId, "⏳ Аналитика уже запущена! Подождите...", getKeyboard()).catch(() => {});
    return;
  }
  state.isAnalyzing = true;
  saveState(state);

  const statusMsg = notifyChatId ? await bot.sendMessage(notifyChatId, "🔄 *Аналитика трендов запущена...*", getKeyboard()).catch(() => null) : null;

  try {
    const allResults = [];
    for (let i = 0; i < QUERIES.length; i++) {
      console.log(`  [${i + 1}/${QUERIES.length}] ${QUERIES[i]}`);
      const results = await searchDDG(QUERIES[i]);
      allResults.push(...results);
      console.log(`    -> ${results.length} results`);

      if (statusMsg && i % 2 === 0) {
        try { await bot.editMessageText(`🔄 Аналитика... Запросов: ${i + 1}/${QUERIES.length}, Найдено: ${allResults.length}`, { chat_id: notifyChatId, message_id: statusMsg.message_id }); } catch {}
      }
      await sleep(1500 + Math.random() * 1000);
    }

    // Deduplicate by domain, filter, sort
    const map = new Map();
    for (const item of allResults) {
      const domain = item.domain || item.host_name || "";
      if (!domain) continue;
      const text = ((item.name || "") + " " + (item.snippet || "")).toLowerCase();
      if (SKIP.some(c => text.includes(c))) continue;
      if (!map.has(domain)) map.set(domain, { domain, name: item.name || "", snippet: item.snippet || "", url: item.url || "", mentions: 0 });
      const e = map.get(domain);
      e.mentions++;
      if ((item.name || "").length > e.name.length) e.name = item.name;
      if ((item.snippet || "").length > e.snippet.length) e.snippet = item.snippet;
    }

    const trends = [...map.values()]
      .sort((a, b) => b.mentions - a.mentions)
      .slice(0, 20)
      .map(t => ({
        name: (t.name || "N/A").replace(/\s*[-|–—].*$/, "").trim().substring(0, 80),
        domain: t.domain,
        url: t.url,
        snippet: (t.snippet || "").substring(0, 180),
        mentions: t.mentions,
      }));

    saveTrends({ date: new Date().toISOString(), totalRawResults: allResults.length, trends });
    state.isAnalyzing = false;
    state.lastAnalysisDate = new Date().toISOString();
    saveState(state);

    console.log(`  DONE: ${trends.length} trends`);

    // Notify
    const targets = notifyAll && state.users?.length ? state.users.map(u => u.chatId) : (notifyChatId ? [notifyChatId] : []);
    for (const cid of targets) {
      try {
        await bot.sendMessage(cid, `✅ *Аналитика завершена!*\n\nНайдено *${trends.length}* трендов.\nНажмите «📊 Выдать результаты» чтобы посмотреть.`, getKeyboard());
      } catch {}
    }
  } catch (err) {
    state.isAnalyzing = false;
    saveState(state);
    console.error("Analysis err:", err.message);
    if (notifyChatId) bot.sendMessage(notifyChatId, `❌ Ошибка: ${err.message}`, getKeyboard()).catch(() => {});
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// =============== FORMAT RESULTS ===============
const EMOJIS = ["🔥","⚡","🚀","💎","🌟","🎯","📈","💡","🏆","⭐","💪","🎪","🎲","🧩","🔧","🧠","🌍","🎨","🔬","📦"];

function escapeMd(t) { return t.replace(/([_*\[\]()~`>#+\-=|{}.!])/g, "\\$1"); }

async function sendResults(chatId) {
  const data = loadTrends();
  if (!data?.trends?.length) {
    await bot.sendMessage(chatId, "📭 Результатов нет. Сначала запустите аналитику.", getKeyboard());
    return;
  }
  const d = new Date(data.date);
  const ms = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"];
  const ds = `${d.getDate()} ${ms[d.getMonth()]} ${d.getFullYear()}`;

  const chunks = [];
  let chunk = [];
  for (let i = 0; i < data.trends.length; i++) {
    const t = data.trends[i];
    const e = EMOJIS[i % EMOJIS.length];
    const title = t.name.length > 70 ? t.name.substring(0, 67) + "..." : t.name;
    const snip = t.snippet.length > 120 ? t.snippet.substring(0, 117) + "..." : t.snippet;
    chunk.push(`${e} *${i+1}\\. ${escapeMd(title)}*\n🔗 ${escapeMd(t.domain)}\n${snip ? "_"+escapeMd(snip)+"_" : ""}\n📊 Упоминаний: ${t.mentions}`);
    if (chunk.join("\n\n").length > 3500) { chunks.push(chunk); chunk = []; }
  }
  if (chunk.length) chunks.push(chunk);

  for (let i = 0; i < chunks.length; i++) {
    const header = i === 0
      ? `📊 *ТОП-20 ТРЕНДОВ EU*\n🗓 ${ds}\n🔍 Источников: ${data.totalRawResults}\n${"━".repeat(28)}`
      : `📊 *ТОП-20 (продолжение)*\n${"━".repeat(28)}`;
    const text = header + "\n\n" + chunks[i].join("\n\n");
    try { await bot.sendMessage(chatId, text, { parse_mode: "MarkdownV2" }); }
    catch { try { await bot.sendMessage(chatId, text.replace(/\\\*/g, "").replace(/_/g, ""), { disable_web_page_preview: true }); } catch {} }
    await sleep(400);
  }
  await bot.sendMessage(chatId, "───", getKeyboard());
}

// =============== BOT ===============
const bot = new TelegramBot(BOT_TOKEN, { polling: true, request: { timeout: 30 } });

function getKeyboard() {
  return {
    reply_markup: {
      inline_keyboard: [
        [{ text: "🔍 Запустить аналитику", callback_data: "run_analysis" }],
        [{ text: "📊 Выдать результаты", callback_data: "show_results" }],
      ],
    },
  };
}

// /start
bot.onText(/\/start/, async (msg) => {
  const st = loadState();
  addUser(st, msg.chat.id, msg.from?.first_name);
  saveState(st);
  try {
    await bot.sendMessage(msg.chat.id,
      "👋 *EU Trend Analyzer Bot*\n\nАнализирую набирающие популярность товары и услуги в Европе.\n\nКаждый раз — *свежий поиск* по 10 запросам.\n\nВыберите действие 👇",
      { parse_mode: "Markdown", ...getKeyboard() }
    );
  } catch {
    await bot.sendMessage(msg.chat.id, "👋 EU Trend Analyzer Bot\n\nАнализирую набирающие популярность товары и услуги в Европе.\n\nВыберите действие 👇", getKeyboard());
  }
  console.log(`  /start from ${msg.from?.first_name} (${msg.chat.id})`);
});

// /status
bot.onText(/\/status/, async (msg) => {
  const st = loadState();
  addUser(st, msg.chat.id, msg.from?.first_name);
  saveState(st);
  const trends = loadTrends();
  const lt = trends ? new Date(trends.date).toLocaleString("ru-RU", { timeZone: "Europe/Moscow" }) : "пока нет";
  await bot.sendMessage(msg.chat.id,
    `📋 *Статус*\n\n🟢 Бот работает\n👥 Юзеров: ${st.users?.length || 0}\n📊 Последняя: ${lt}\n📈 Трендов: ${trends?.trends?.length || 0}\n⏰ Авто: 09:00 МСК`,
    getKeyboard()
  );
});

// Buttons
bot.on("callback_query", async (cq) => {
  const chatId = cq.message.chat.id;
  const name = cq.from?.first_name || "";
  const st = loadState();
  addUser(st, chatId, name);
  saveState(st);
  await bot.answerCallbackQuery(cq.id).catch(() => {});

  if (cq.data === "run_analysis") {
    console.log(`  Analysis: ${name} (${chatId})`);
    runAnalysis(chatId);
  } else if (cq.data === "show_results") {
    console.log(`  Results: ${name} (${chatId})`);
    await sendResults(chatId);
  }
});

// Errors
bot.on("polling_error", (e) => {
  console.error("Poll:", e.message);
  if (e.code === "ETELEGRAM" || e.code === "ENOTFOUND") {
    setTimeout(() => { bot.stopPolling().then(() => bot.startPolling()); }, 5000);
  }
});

// Daily auto-analysis at 09:00 MSK (06:00 UTC)
cron.schedule("0 6 * * *", async () => {
  console.log("  Daily auto-analysis triggered");
  const st = loadState();
  if (st.users?.length && !st.isAnalyzing) {
    await runAnalysis(st.users[0].chatId, true);
  }
}, { timezone: "Europe/Moscow", scheduled: true });

// Start
console.log("══════════════════════════════════════");
console.log("🚀 EU TREND BOT — DEPLOY VERSION");
console.log("══════════════════════════════════════");
const initState = loadState();
console.log(`👥 Юзеров: ${initState.users?.length || 0}`);
console.log(`📊 Трендов: ${loadTrends()?.trends?.length || 0}`);
console.log("⏰ Daily: 09:00 MSK");
console.log("══════════════════════════════════════");
