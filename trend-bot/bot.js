/**
 * ╔══════════════════════════════════════════════════════╗
 * ║  EU TREND ANALYZER BOT — ВЕСЬ КОД В ОДНОМ ФАЙЛЕ      ║
 * ╠══════════════════════════════════════════════════════╣
 * ║  ЗАПУСК:                                              ║
 * ║  1. npm init -y                                       ║
 * ║  2. npm i node-telegram-bot-api node-cron z-ai-web-dev-sdk ║
 * ║  3. node bot.js                                       ║
 * ╚══════════════════════════════════════════════════════╝
 */

import TelegramBot from "node-telegram-bot-api";
import cron from "node-cron";
import fs from "fs";
import ZAI from "z-ai-web-dev-sdk";

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || "8792613395:AAGquGo3aZ1fbFjToatyR5hSLJiYR0Bs9s8";
const RESULTS_FILE = "./data/trends.json";

const EXCLUDE = [
  "food delivery", "groceries", "restaurant", "alcohol", "pharmacy", "medicine",
  "flowers", "clothing", "fashion", "shoes", "phones", "laptops", "beauty products", "makeup",
];

const QUERIES = [
  "fastest growing e-commerce categories Europe 2025 2026",
  "trending products European consumers buying 2026",
  "growing online shopping categories EU market 2026",
  "European consumer trends non-obvious 2026",
  "innovative products gaining popularity Europe",
  "European market trending niches 2025 2026",
  "new popular online orders Europe growing",
  "European subscription services trending 2026",
];

const EMOJIS = ["🔥","⚡","🚀","💎","🌟","🎯","📈","💡","🏆","⭐","💪","🎪","🎲","🧩","🔧","🧠","🌍","🎨","🔬","📦","🤖","🏗","🔋","💻","🎛"];

// State
let adminChatId = "";
let isAnalyzing = false;
let latestResult = null;

if (!fs.existsSync("./data")) fs.mkdirSync("./data");
try { if (fs.existsSync(RESULTS_FILE)) latestResult = JSON.parse(fs.readFileSync(RESULTS_FILE, "utf-8")); } catch (e) {}

const bot = new TelegramBot(BOT_TOKEN, { polling: true, request: { timeout: 30 } });

function getMenu() {
  return {
    reply_markup: {
      inline_keyboard: [
        [{ text: "🔍 Запустить аналитику", callback_data: "start_analysis" }],
        [{ text: "📊 Выдать результаты", callback_data: "show_results" }],
      ],
    },
  };
}

// ===== ANALYZER =====
async function searchOnce(zai, query) {
  for (let attempt = 0; attempt <= 3; attempt++) {
    try {
      const r = await zai.functions.invoke("web_search", { query, num: 10 });
      return r || [];
    } catch (err) {
      if (err?.message?.includes("429") && attempt < 3) {
        await new Promise((r) => setTimeout(r, 5000));
        continue;
      }
      return [];
    }
  }
  return [];
}

async function runAnalysis() {
  const zai = await ZAI.create();
  const allResults = [];
  for (let i = 0; i < QUERIES.length; i++) {
    console.log(`  [${i + 1}/${QUERIES.length}] ${QUERIES[i]}`);
    const r = await searchOnce(zai, QUERIES[i]);
    allResults.push(...r);
    if (i < QUERIES.length - 1) await new Promise((res) => setTimeout(res, 2500));
  }
  console.log(`  Raw: ${allResults.length} results`);

  const map = new Map();
  for (const item of allResults) {
    const domain = item.host_name || item.url;
    if (!domain) continue;
    const text = ((item.name || "") + " " + (item.snippet || "")).toLowerCase();
    if (EXCLUDE.some((c) => text.includes(c))) continue;
    if (!map.has(domain)) map.set(domain, { domain, name: item.name || "", snippet: item.snippet || "", url: item.url || "", mentions: 0 });
    const e = map.get(domain);
    e.mentions++;
    if (item.name && item.name.length > e.name.length) e.name = item.name;
    if (item.snippet && item.snippet.length > e.snippet.length) e.snippet = item.snippet;
  }

  const trends = [...map.values()]
    .sort((a, b) => b.mentions - a.mentions)
    .slice(0, 25)
    .map((t) => ({
      name: (t.name || "N/A").replace(/\s*[-|–—].*$/, "").trim().substring(0, 80),
      domain: t.domain,
      url: t.url,
      snippet: (t.snippet || "").replace(/<[^>]*>/g, "").substring(0, 180),
      mentions: t.mentions,
    }));

  latestResult = { date: new Date().toISOString(), totalRawResults: allResults.length, trends };
  fs.writeFileSync(RESULTS_FILE, JSON.stringify(latestResult, null, 2));
  return latestResult;
}

// ===== FORMAT =====
function formatResults(data) {
  if (!data?.trends?.length) return ["📭 Результатов нет."];
  const d = new Date(data.date);
  const months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"];
  const dateStr = `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
  const chunks = [];
  let chunk = [];
  for (let i = 0; i < data.trends.length; i++) {
    const t = data.trends[i];
    const e = EMOJIS[i % EMOJIS.length];
    chunk.push([`${e} *${i + 1}. ${t.name}*`, t.domain, t.snippet, t.url, `Упоминаний: ${t.mentions}`].join("\n"));
    if (chunk.join("\n\n").length > 3500) { chunks.push(chunk); chunk = []; }
  }
  if (chunk.length) chunks.push(chunk);
  return chunks.map((ch, idx) => {
    const h = idx === 0
      ? `📊 *АНАЛИТИКА ТРЕНДОВ EU*\n🗓 ${dateStr}\n🔍 Источников: ${data.totalRawResults}\n${"━".repeat(25)}`
      : `📊 *АНАЛИТИКА ТРЕНДОВ EU (продолжение)*\n${"━".repeat(25)}`;
    return h + "\n\n" + ch.join("\n\n");
  });
}

// ===== HANDLERS =====
bot.onText(/\/start/, (msg) => {
  adminChatId = String(msg.chat.id);
  bot.sendMessage(msg.chat.id,
    "👋 *EU Trend Analyzer Bot*\n\nАнализирую набирающие популярность товары и услуги в Европе.\n\nНажмите кнопку:",
    { parse_mode: "Markdown", ...getMenu() }
  );
});

bot.onText(/\/status/, (msg) => {
  const s = latestResult
    ? `📊 Последняя: ${latestResult.date}\n📈 Трендов: ${latestResult.trends?.length}\n🔍 Источников: ${latestResult.totalRawResults}`
    : "📭 Нет результатов";
  bot.sendMessage(msg.chat.id, s, getMenu());
});

bot.on("callback_query", (cq) => {
  const chatId = cq.message?.chat?.id;
  adminChatId = String(chatId);
  bot.answerCallbackQuery(cq.id).catch(() => {});

  if (cq.data === "start_analysis") {
    if (isAnalyzing) { bot.sendMessage(chatId, "⏳ Уже запущено! Ждите...", getMenu()); return; }
    bot.sendMessage(chatId, "🔄 *Аналитика трендов запущена...*\n\nИщу тренды Европы. 1-2 минуты.", { parse_mode: "Markdown" });
    isAnalyzing = true;
    runAnalysis()
      .then((r) => {
        console.log(`DONE: ${r.trends.length} trends`);
        bot.sendMessage(adminChatId, "✅ *Аналитика завершена!*\n\nНажмите «Выдать результаты».", { parse_mode: "Markdown", ...getMenu() });
      })
      .catch((err) => {
        bot.sendMessage(adminChatId, `❌ Ошибка: ${err.message}`, getMenu());
      })
      .finally(() => { isAnalyzing = false; });
  }

  if (cq.data === "show_results") {
    if (!latestResult) { bot.sendMessage(chatId, "📭 Нет результатов. Сначала запустите аналитику.", getMenu()); return; }
    const msgs = formatResults(latestResult);
    msgs.forEach((m, i) => setTimeout(() => bot.sendMessage(chatId, m, { parse_mode: "Markdown" }).catch(() => bot.sendMessage(chatId, m)), i * 500));
    setTimeout(() => bot.sendMessage(chatId, "───", getMenu()), msgs.length * 500 + 300);
  }
});

// ===== CRON =====
cron.schedule("0 9 * * *", () => {
  if (isAnalyzing || !adminChatId) return;
  isAnalyzing = true;
  runAnalysis()
    .then(() => bot.sendMessage(adminChatId, "🔄 Ежедневная аналитика завершена!", getMenu()))
    .catch((e) => console.error("Cron:", e))
    .finally(() => { isAnalyzing = false; });
}, { timezone: "Europe/Moscow" });

// ===== START =====
process.on("uncaughtException", (e) => console.error("[FATAL]", e.message));
process.on("unhandledRejection", (e) => console.error("[REJ]", e));
bot.on("polling_error", (e) => { if (!e.message.includes("ETIMEDOUT") && !e.message.includes("ECONNRESET")) console.error("[Poll]", e.message); });

console.log("🚀 EU TREND ANALYZER BOT — RUNNING");
console.log("📋 Cron: 09:00 MSK daily");
