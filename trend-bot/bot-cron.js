/**
 * ╔════════════════════════════════════════════════════════════╗
 * ║  EU TREND BOT — CRON MODE (без long polling!)            ║
 * ║  Запускается по расписанию, обрабатывает сообщения и       ║
 * ║  завершается. Никаких зависших процессов.                 ║
 * ╚════════════════════════════════════════════════════════════╝
 */

import ZAI from "z-ai-web-dev-sdk";
import fs from "fs";
import https from "https";

const BOT_TOKEN = "8792613395:AAGquGo3aZ1fbFjToatyR5hSLJiYR0Bs9s8";
const API = `https://api.telegram.org/bot${BOT_TOKEN}`;
const STATE_FILE = "./data/state.json";
const RESULTS_FILE = "./data/trends.json";

if (!fs.existsSync("./data")) fs.mkdirSync("./data", { recursive: true });

// ===================== TELEGRAM API =====================
function tgApi(method, body) {
  return new Promise((resolve, reject) => {
    const payload = typeof body === "object" ? JSON.stringify(body) : body;
    const url = new URL(`${API}/${method}`);
    const options = {
      hostname: url.hostname,
      path: url.pathname,
      method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) },
      timeout: 30000,
    };
    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => {
        try { resolve(JSON.parse(data)); } catch { reject(new Error("JSON parse error: " + data.substring(0, 200))); }
      });
    });
    req.on("error", reject);
    req.on("timeout", () => { req.destroy(); reject(new Error("timeout")); });
    req.write(payload);
    req.end();
  });
}

async function sendMessage(chatId, text, extra = {}) {
  return tgApi("sendMessage", { chat_id: chatId, text, parse_mode: "Markdown", ...extra });
}

// ===================== STATE =====================
function loadState() {
  try {
    if (fs.existsSync(STATE_FILE)) return JSON.parse(fs.readFileSync(STATE_FILE, "utf-8"));
  } catch {}
  return { lastUpdateId: 0, adminChatId: null, isAnalyzing: false, lastAnalysisDate: null };
}

function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function loadResults() {
  try {
    if (fs.existsSync(RESULTS_FILE)) return JSON.parse(fs.readFileSync(RESULTS_FILE, "utf-8"));
  } catch {}
  return null;
}

// ===================== BUTTONS =====================
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

// ===================== ANALYZER =====================
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

async function runAnalysis(chatId) {
  const state = loadState();
  state.isAnalyzing = true;
  saveState(state);

  await sendMessage(chatId, "🔄 *Аналитика трендов запущена...*\n\nИщу тренды Европы. Это займёт 1-2 минуты.");

  try {
    const zai = await ZAI.create();
    const allResults = [];

    for (let i = 0; i < QUERIES.length; i++) {
      console.log(`  [${i + 1}/${QUERIES.length}] ${QUERIES[i]}`);
      const r = await searchOnce(zai, QUERIES[i]);
      allResults.push(...r);
      if (i < QUERIES.length - 1) await new Promise((res) => setTimeout(res, 2500));
    }
    console.log(`  Raw results: ${allResults.length}`);

    // Deduplicate by domain, filter primitives
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
      .slice(0, 20)
      .map((t) => ({
        name: (t.name || "N/A").replace(/\s*[-|–—].*$/, "").trim().substring(0, 80),
        domain: t.domain,
        url: t.url,
        snippet: (t.snippet || "").replace(/<[^>]*>/g, "").substring(0, 180),
        mentions: t.mentions,
      }));

    const result = { date: new Date().toISOString(), totalRawResults: allResults.length, trends };
    fs.writeFileSync(RESULTS_FILE, JSON.stringify(result, null, 2));

    state.isAnalyzing = false;
    state.lastAnalysisDate = new Date().toISOString();
    saveState(state);

    await sendMessage(chatId, "✅ *Аналитика завершена!*\n\nНажмите «📊 Выдать результаты» чтобы посмотреть.", getMenu());
    console.log(`  DONE: ${trends.length} trends saved`);
    return true;
  } catch (err) {
    state.isAnalyzing = false;
    saveState(state);
    await sendMessage(chatId, `❌ Ошибка аналитики: ${err.message}`, getMenu());
    console.error("Analysis error:", err.message);
    return false;
  }
}

// ===================== FORMAT RESULTS =====================
const EMOJIS = ["🔥","⚡","🚀","💎","🌟","🎯","📈","💡","🏆","⭐","💪","🎪","🎲","🧩","🔧","🧠","🌍","🎨","🔬","📦"];

function formatResults(data) {
  if (!data?.trends?.length) return ["📭 Результатов пока нет."];
  const d = new Date(data.date);
  const months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"];
  const dateStr = `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;

  const chunks = [];
  let chunk = [];
  for (let i = 0; i < data.trends.length; i++) {
    const t = data.trends[i];
    const e = EMOJIS[i % EMOJIS.length];
    chunk.push(`${e} *${i + 1}. ${t.name}*\n🔗 ${t.domain}\n${t.snippet}\n[Читать далее](${t.url})\n📌 Упоминаний: ${t.mentions}`);
    if (chunk.join("\n\n").length > 3500) { chunks.push(chunk); chunk = []; }
  }
  if (chunk.length) chunks.push(chunk);

  return chunks.map((ch, idx) => {
    const h = idx === 0
      ? `📊 *АНАЛИТИКА ТРЕНДОВ EU — ТОП-20*\n🗓 ${dateStr}\n🔍 Источников проанализировано: ${data.totalRawResults}\n${"━".repeat(28)}`
      : `📊 *АНАЛИТИКА ТРЕНДОВ EU (продолжение)*\n${"━".repeat(28)}`;
    return h + "\n\n" + ch.join("\n\n");
  });
}

// ===================== PROCESS UPDATES =====================
async function processUpdate(update, state) {
  const chatId = update.message?.chat?.id;
  const callbackQuery = update.callback_query;

  // Handle /start command
  if (update.message?.text === "/start") {
    state.adminChatId = chatId;
    await sendMessage(chatId, "👋 *EU Trend Analyzer Bot*\n\nАнализирую набирающие популярность товары и услуги в Европе.\n\nНажмите кнопку ниже 👇", getMenu());
    return;
  }

  // Handle /status command
  if (update.message?.text === "/status") {
    const results = loadResults();
    if (results) {
      const d = new Date(results.date);
      await sendMessage(chatId, `📊 Последняя аналитика: ${d.toLocaleString("ru-RU")}\n📈 Трендов найдено: ${results.trends?.length}\n🔍 Источников: ${results.totalRawResults}`, getMenu());
    } else {
      await sendMessage(chatId, "📭 Результатов пока нет. Нажмите «Запустить аналитику».", getMenu());
    }
    return;
  }

  // Handle callback buttons
  if (callbackQuery) {
    const cbChatId = callbackQuery.message?.chat?.id;
    state.adminChatId = cbChatId;

    // Acknowledge callback
    await tgApi("answerCallbackQuery", { callback_query_id: callbackQuery.id });

    if (callbackQuery.data === "start_analysis") {
      if (state.isAnalyzing) {
        await sendMessage(cbChatId, "⏳ Аналитика уже запущена! Подождите завершения...", getMenu());
        return;
      }
      // Start analysis (this will take a while)
      saveState(state);
      await runAnalysis(cbChatId);
      return;
    }

    if (callbackQuery.data === "show_results") {
      const results = loadResults();
      if (!results) {
        await sendMessage(cbChatId, "📭 Результатов пока нет. Сначала запустите аналитику.", getMenu());
        return;
      }
      const msgs = formatResults(results);
      for (let i = 0; i < msgs.length; i++) {
        try {
          await sendMessage(cbChatId, msgs[i]);
        } catch {
          // Retry without markdown if formatting fails
          await tgApi("sendMessage", { chat_id: cbChatId, text: msgs[i].replace(/\*/g, "") });
        }
        if (i < msgs.length - 1) await new Promise((r) => setTimeout(r, 500));
      }
      await sendMessage(cbChatId, "───", getMenu());
      return;
    }
  }
}

// ===================== MAIN =====================
async function main() {
  console.log(`[${new Date().toISOString()}] Bot cron tick started`);

  const state = loadState();

  // 1. Fetch pending updates
  let updates = [];
  try {
    const resp = await tgApi("getUpdates", { offset: state.lastUpdateId + 1, timeout: 5, allowed_updates: ["message", "callback_query"] });
    updates = resp.ok ? resp.result : [];
    console.log(`  Fetched ${updates.length} updates`);
  } catch (err) {
    console.error("  getUpdates error:", err.message);
    return;
  }

  // 2. Process each update
  for (const update of updates) {
    try {
      await processUpdate(update, state);
    } catch (err) {
      console.error("  Update processing error:", err.message);
    }
    if (update.update_id > state.lastUpdateId) {
      state.lastUpdateId = update.update_id;
    }
  }

  // 3. Save state
  saveState(state);

  // 4. Confirm processed updates
  if (updates.length > 0) {
    try {
      await tgApi("getUpdates", { offset: state.lastUpdateId + 1, timeout: 0 });
    } catch {}
  }

  console.log(`[${new Date().toISOString()}] Bot cron tick completed`);
}

main().catch((err) => {
  console.error("Fatal:", err.message);
  process.exit(1);
});
