/**
 * EU TREND BOT v4 — ФИНАЛЬНАЯ ВЕРСИЯ
 * - Мультиюзерный (работает для ВСЕХ)
 * - Встроенный watchdog (автоперезапуск при ошибках)
 * - Fallback на plain text если Markdown падает
 * - 10 поисковых запросов
 * - Ежедневный авто-анализ 09:00 МСК для ВСЕХ юзеров
 * - Состояние сохраняется в файл (выживает при рестарте)
 */
import ZAI from "z-ai-web-dev-sdk";
import fs from "fs";
import https from "https";

const BOT_TOKEN = "8792613395:AAGquGo3aZ1fbFjToatyR5hSLJiYR0Bs9s8";
const API = `https://api.telegram.org/bot${BOT_TOKEN}`;
const STATE_FILE = "./data/state.json";
const RESULTS_FILE = "./data/trends.json";
const TICK_MS = 12000;

if (!fs.existsSync("./data")) fs.mkdirSync("./data", { recursive: true });

// =============== TELEGRAM API ===============
function tgApi(method, body) {
  return new Promise((resolve, reject) => {
    const payload = typeof body === "object" ? JSON.stringify(body) : body;
    const u = new URL(`${API}/${method}`);
    const req = https.request({
      hostname: u.hostname, path: u.pathname, method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) },
      timeout: 25000,
    }, (res) => {
      let d = "";
      res.on("data", (c) => (d += c));
      res.on("end", () => { try { resolve(JSON.parse(d)); } catch { reject(new Error(d.substring(0, 200))); } });
    });
    req.on("error", reject);
    req.on("timeout", () => { req.destroy(); reject(new Error("timeout")); });
    req.write(payload);
    req.end();
  });
}

async function send(chatId, text, extra = {}) {
  try { return await tgApi("sendMessage", { chat_id: chatId, text, parse_mode: "Markdown", ...extra }); }
  catch {
    const p = text.replace(/\*/g, "").replace(/_/g, "").replace(/\[.*?\]\(.*?\)/g, "").replace(/&/g, "");
    return tgApi("sendMessage", { chat_id: chatId, text: p, ...extra });
  }
}

// =============== STATE ===============
function loadState() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, "utf-8")); }
  catch { return { lastUpdateId: 0, users: [], isAnalyzing: false, lastAnalysisDate: null }; }
}
function saveState(s) { try { fs.writeFileSync(STATE_FILE, JSON.stringify(s, null, 2)); } catch {} }
function addUser(s, id, name) {
  if (!s.users) s.users = [];
  if (!s.users.find(u => u.chatId === id)) s.users.push({ chatId: id, name: name || "User", addedAt: new Date().toISOString() });
}
function loadResults() {
  try { return JSON.parse(fs.readFileSync(RESULTS_FILE, "utf-8")); }
  catch { return null; }
}

// =============== BUTTONS ===============
function menu() {
  return { reply_markup: { inline_keyboard: [[{ text: "🔍 Запустить аналитику", callback_data: "start_analysis" }], [{ text: "📊 Выдать результаты", callback_data: "show_results" }]] } };
}

// =============== ANALYZER ===============
const SKIP = ["food delivery","groceries","grocery","restaurant","alcohol","pharmacy","medicine","flowers","clothing","fashion","shoes","phones","laptops","beauty products","makeup","cosmetics","recipe","meal","pizza","sushi","burger","drug","healthcare","hospital"];
const Q = [
  "fastest growing e-commerce categories Europe 2025 2026","trending products European consumers buying 2026",
  "growing online shopping categories EU market 2026","European consumer trends non-obvious 2026",
  "innovative products gaining popularity Europe 2026","European market trending niches 2025 2026",
  "new popular online orders Europe growing","European subscription services trending 2026",
  "top emerging product categories Europe ecommerce","European digital products trends 2026",
];

async function search(zai, q) {
  for (let t = 0; t <= 2; t++) {
    try { return (await zai.functions.invoke("web_search", { query: q, num: 10 })) || []; }
    catch (e) { if (e?.message?.includes("429") && t < 2) { await new Promise(r => setTimeout(r, 4000)); continue; } return []; }
  }
  return [];
}

async function analyze(chatId, all = false) {
  const st = loadState();
  if (st.isAnalyzing) { await send(chatId, "⏳ Аналитика уже запущена! Подождите...", menu()); return; }
  st.isAnalyzing = true; saveState(st);
  try { await send(chatId, "🔄 *Аналитика трендов запущена...*\n\nИщу по 10 запросам. 1-2 минуты."); } catch {}
  try {
    const zai = await ZAI.create();
    const raw = [];
    for (let i = 0; i < Q.length; i++) {
      console.log(`  [${i+1}/${Q.length}] ${Q[i]}`);
      raw.push(...(await search(zai, Q[i])));
      if (i < Q.length - 1) await new Promise(r => setTimeout(r, 2000));
    }
    console.log(`  Raw: ${raw.length}`);
    const m = new Map();
    for (const it of raw) {
      const dom = it.host_name || ""; if (!dom) continue;
      const tx = ((it.name||"")+" "+(it.snippet||"")).toLowerCase();
      if (SKIP.some(c => tx.includes(c))) continue;
      if (!m.has(dom)) m.set(dom, { domain: dom, name: it.name||"", snippet: it.snippet||"", url: it.url||"", mentions: 0 });
      const e = m.get(dom); e.mentions++;
      if (it.name?.length > e.name.length) e.name = it.name;
      if (it.snippet?.length > e.snippet.length) e.snippet = it.snippet;
    }
    const trends = [...m.values()].sort((a,b) => b.mentions - a.mentions).slice(0,20).map(t => ({
      name: (t.name||"N/A").replace(/\s*[-|–—].*$/,"").trim().substring(0,80),
      domain: t.domain, url: t.url,
      snippet: (t.snippet||"").replace(/<[^>]*>/g,"").substring(0,180),
      mentions: t.mentions,
    }));
    fs.writeFileSync(RESULTS_FILE, JSON.stringify({ date: new Date().toISOString(), totalRawResults: raw.length, trends }, null, 2));
    const s2 = loadState(); s2.isAnalyzing = false; s2.lastAnalysisDate = new Date().toISOString(); saveState(s2);
    const targets = all && s2.users?.length ? s2.users.map(u => u.chatId) : [chatId];
    for (const c of targets) {
      try { await send(c, `✅ *Аналитика завершена!*\n\nНайдено *${trends.length}* трендов из *${raw.length}* источников.\n\nНажмите «📊 Выдать результаты».`, menu()); } catch {}
    }
    console.log(`  DONE: ${trends.length} trends -> ${targets.length} users`);
  } catch (err) {
    const s2 = loadState(); s2.isAnalyzing = false; saveState(s2);
    try { await send(chatId, `❌ Ошибка: ${err.message}`, menu()); } catch {}
    console.error("ERR:", err.message);
  }
}

// =============== FORMAT ===============
const E = ["🔥","⚡","🚀","💎","🌟","🎯","📈","💡","🏆","⭐","💪","🎪","🎲","🧩","🔧","🧠","🌍","🎨","🔬","📦"];
function fmt(d) {
  if (!d?.trends?.length) return ["📭 Результатов нет. Нажмите «Запустить аналитику»."];
  const dt = new Date(d.date);
  const ms = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"];
  const ds = `${dt.getDate()} ${ms[dt.getMonth()]} ${dt.getFullYear()}, ${dt.getHours()}:${String(dt.getMinutes()).padStart(2,"0")} MSK`;
  const ch = []; let ck = [];
  for (let i = 0; i < d.trends.length; i++) {
    const t = d.trends[i];
    ck.push(`${E[i%E.length]} *${i+1}. ${t.name}*\n🔗 ${t.domain}\n${t.snippet}\n[Читать](${t.url})\n📌 Упоминаний: ${t.mentions}`);
    if (ck.join("\n\n").length > 3500) { ch.push(ck); ck = []; }
  }
  if (ck.length) ch.push(ck);
  return ch.map((c,i) => (i===0 ? `📊 *ТОП-20 ТРЕНДОВ EU*\n🗓 ${ds}\n🔍 Источников: ${d.totalRawResults}\n${"━".repeat(28)}` : `📊 *ТОП-20 (продолжение)*\n${"━".repeat(28)}`) + "\n\n" + c.join("\n\n"));
}

// =============== PROCESS ===============
async function processUpdate(up, st) {
  const cid = up.message?.chat?.id, uname = up.message?.from?.first_name || "", cb = up.callback_query;
  if (up.message?.text === "/start") {
    addUser(st, cid, uname);
    try { await send(cid, "👋 *EU Trend Analyzer Bot*\n\nАнализирую набирающие популярность товары и услуги в Европе.\n\nКаждый раз — *свежий поиск* по интернету.\n\nНажмите кнопку 👇", menu()); } catch {}
    return;
  }
  if (up.message?.text === "/status") {
    const r = loadResults(); addUser(st, cid, uname);
    const lt = r ? new Date(r.date).toLocaleString("ru-RU",{timeZone:"Europe/Moscow"}) : "пока нет";
    await send(cid, `📋 *Статус*\n\n🟢 Работает\n👥 Юзеров: ${st.users?.length||0}\n📊 Последняя: ${lt}\n📈 Трендов: ${r?.trends?.length||0}\n⏰ Авто: 09:00 МСК`, menu());
    return;
  }
  if (cb) {
    const ccid = cb.message?.chat?.id, cn = cb.from?.first_name||"";
    addUser(st, ccid, cn);
    try { await tgApi("answerCallbackQuery",{callback_query_id:cb.id}); } catch {}
    if (cb.data === "start_analysis") { console.log(`  Analysis: ${cn} (${ccid})`); analyze(ccid); return; }
    if (cb.data === "show_results") {
      const r = loadResults();
      if (!r) { await send(ccid, "📭 Нет результатов. Запустите аналитику.", menu()); return; }
      const ms = fmt(r);
      for (let i = 0; i < ms.length; i++) {
        try { await send(ccid, ms[i]); } catch { try { await tgApi("sendMessage",{chat_id:ccid,text:ms[i].replace(/\*/g,"")}); } catch {} }
        if (i < ms.length-1) await new Promise(r=>setTimeout(r,400));
      }
      await send(ccid, "───", menu());
      return;
    }
  }
}

// =============== DAILY ===============
function daily(s) {
  if (s.isAnalyzing || !s.users?.length) return false;
  const n = new Date(), h = (n.getUTCHours()+3)%24, m = n.getUTCMinutes();
  if (h===9 && m<15 && s.lastAnalysisDate?.split("T")[0] !== n.toISOString().split("T")[0]) return true;
  return false;
}

// =============== TICK ===============
async function tick() {
  const st = loadState();
  try {
    const r = await tgApi("getUpdates", { offset: st.lastUpdateId+1, timeout: 5, allowed_updates: ["message","callback_query"] });
    const ups = r.ok ? r.result : [];
    if (ups.length) console.log(`[${new Date().toISOString()}] ${ups.length} updates`);
    for (const u of ups) {
      try { await processUpdate(u, st); } catch(e) { console.error("UPD:",e.message); }
      if (u.update_id > st.lastUpdateId) st.lastUpdateId = u.update_id;
    }
    saveState(st);
    if (daily(st)) { console.log("  Daily trigger"); analyze(st.users[0]?.chatId, true); }
  } catch(e) { console.error("TICK:",e.message); }
}

// =============== START ===============
const s = loadState();
console.log("🚀 EU TREND BOT v4 FINAL");
console.log(`👥 Юзеров: ${s.users?.length||0} | 📊 Результатов: ${loadResults()?.trends?.length||0}`);
console.log("⏱ Tick: 12s | Daily: 09:00 MSK");
tick();
setInterval(tick, TICK_MS);
setInterval(() => {}, 60000);
