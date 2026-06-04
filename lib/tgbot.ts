/**
 * Telegram Bot — EU Trend Analyzer v5 AI Expert
 * Runs as background process inside Next.js server
 */
import TelegramBot from "node-telegram-bot-api";
import cron from "node-cron";
import fs from "fs";
import path from "path";

const BOT_TOKEN = "8792613395:AAGquGo3aZ1fbFjToatyR5hSLJiYR0Bs9s8";
const DATA_DIR = path.join(process.cwd(), "trend-bot", "data");
const RESULTS_FILE = path.join(DATA_DIR, "trends.json");
const STATE_FILE = path.join(DATA_DIR, "state.json");
const EXCLUDE = [
  "food delivery","groceries","restaurant","alcohol","pharmacy","medicine",
  "flowers","clothing","fashion","shoes","phones","laptops","beauty products","makeup",
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
  "best selling new products online Europe growth statistics",
  "Google Trends rising products Europe 2026",
];
const EMOJIS = ["🔥","⚡","🚀","💎","🌟","🎯","📈","💡","🏆","⭐","💪","🎪","🎲","🧩","🔧","🧠","🌍","🎨","🔬","📦","🤖","🏗","🔋","💻","🎛"];

let state: any = { users: [], lastUpdateId: 0, isAnalyzing: false, analysisStartedAt: null };
let latestResult: any = null;
let bot: TelegramBot | null = null;

function loadData() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
  try { state = JSON.parse(fs.readFileSync(STATE_FILE, "utf-8")); } catch(e) {}
  try { latestResult = JSON.parse(fs.readFileSync(RESULTS_FILE, "utf-8")); } catch(e) {}
}

function saveState() { try { fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2)); } catch(e) {} }

function getMenu() {
  return { reply_markup: { inline_keyboard: [
    [{ text: "🔍 Запустить аналитику", callback_data: "start_analysis" }],
    [{ text: "📊 Выдать результаты", callback_data: "show_results" }],
  ]}};
}

function saveUser(chatId: number, name: string) {
  if (!state.users) state.users = [];
  if (!state.users.find((u: any) => u.chatId === chatId)) {
    state.users.push({ chatId, name: name || "User", addedAt: new Date().toISOString() });
    saveState();
  }
}

async function searchOnce(zai: any, query: string) {
  for (let a = 0; a <= 2; a++) {
    try { return (await zai.functions.invoke("web_search", { query, num: 10 })) || []; }
    catch(e: any) { if (e?.message?.includes("429") && a < 2) { await new Promise(r=>setTimeout(r,5000)); continue; } return []; }
  }
  return [];
}

async function aiExpertAnalysis(rawContext: string) {
  const { default: ZAI } = await import("z-ai-web-dev-sdk");
  const zai = await ZAI.create();
  const sys = `You are a senior European E-Commerce Market analyst.
Categories: Smart Home, Health & Wellness Tech, Pet Tech, Eco/Sustainable, EdTech, FinTech, AI Tools, SaaS, Subscription Boxes, Hobby & DIY, Home Office, Outdoor & Garden, Baby & Kids Tech, Smart Kitchen, Gaming Accessories, Wearable Tech, Auto Accessories, Security, Fitness Equipment, Solar/Energy, Niche Handmade, Digital Products.
Rules: NON-OBVIOUS growing niches, growth %, market size $, demand level (Low/Medium/High/Very High), WHY trending, target audience, e-commerce opportunity. Exclude: food, alcohol, medicine, flowers, clothing, shoes, cosmetics.
Return ONLY JSON array of 20 trends:
[{"name":"product","category":"Cat","growth_rate":"+35% YoY","market_size":"$2.4B","demand_level":"High","target_audience":"who","why_trending":"why","opportunity":"chance","sources_count":5,"top_sources":["url"]}]`;
  const c = await zai.chat.completions.create({
    messages: [{ role: "system", content: sys }, { role: "user", content: `Analyze EU e-commerce trends:\n${rawContext}\nReturn ONLY JSON.` }],
    temperature: 0.3,
  });
  let txt = (c.choices[0]?.message?.content||"").replace(/```json\s*/gi,"").replace(/```\s*/g,"").trim();
  const m = txt.match(/\[[\s\S]*\]/);
  if (m) { try { return JSON.parse(m[0]); } catch(e: any) {} }
  return null;
}

async function runAnalysis() {
  const { default: ZAI } = await import("z-ai-web-dev-sdk");
  const zai = await ZAI.create();
  const all: any[] = [];
  for (let i = 0; i < QUERIES.length; i++) {
    console.log(`[TG-BOT] Search ${i+1}/${QUERIES.length}`);
    all.push(...(await searchOnce(zai, QUERIES[i])));
    if (i < QUERIES.length-1) await new Promise(r=>setTimeout(r,2000));
  }
  const seen = new Set(), filtered: any[] = [];
  for (const it of all) {
    const k = (it.url||it.host_name||"").replace(/\/$/,"");
    if (!k||seen.has(k)) continue; seen.add(k);
    const t = ((it.name||"")+" "+(it.snippet||"")).toLowerCase();
    if (EXCLUDE.some(c=>t.includes(c))) continue;
    filtered.push({ name:it.name||"", snippet:it.snippet||"", url:it.url||"", host:it.host_name||"" });
  }

  let aiTrends: any = null;
  try {
    console.log("[TG-BOT] AI analysis...");
    const ctx = filtered.slice(0,50).map((it: any,i: number)=>`[${i+1}] ${it.name}\n    ${it.snippet}\n    URL: ${it.url}`).join("\n\n");
    aiTrends = await aiExpertAnalysis(ctx);
    console.log(`[TG-BOT] AI returned ${aiTrends?.length||0} trends`);
  } catch(e: any) { console.log("[TG-BOT] AI failed:", e.message?.substring(0,100)); }

  let trends: any[];
  if (aiTrends?.length) {
    trends = aiTrends.slice(0,20).map((t: any,i: number)=>({
      rank:i+1, name:t.name||`#${i+1}`, category:t.category||"General",
      growth_rate:t.growth_rate||"N/A", market_size:t.market_size||"N/A",
      demand_level:t.demand_level||"Medium", target_audience:t.target_audience||"",
      why_trending:t.why_trending||"", opportunity:t.opportunity||"",
      sources_count:t.sources_count||0, top_sources:t.top_sources||[],
    }));
  } else {
    const map = new Map();
    for (const it of filtered) {
      const d = it.host||it.url;
      if (!map.has(d)) map.set(d,{d,name:it.name,snippet:it.snippet,url:it.url,m:1});
      else { const e=map.get(d) as any; e.m++; if(it.snippet?.length>e.snippet.length) e.snippet=it.snippet; }
    }
    trends = [...map.values()].sort((a: any,b: any)=>b.m-a.m).slice(0,20).map((t: any,i: number)=>({
      rank:i+1, name:(t.name||"N/A").replace(/\s*[-|–—].*$/,"").trim().substring(0,80),
      category:"Search", growth_rate:"N/A", market_size:"N/A",
      demand_level:t.m>=4?"High":t.m>=2?"Medium":"Low", target_audience:"",
      why_trending:t.snippet.replace(/<[^>]*>/g,"").substring(0,200), opportunity:"",
      sources_count:t.m, top_sources:[t.url],
    }));
  }

  latestResult = { date:new Date().toISOString(), totalRawResults:all.length, filteredResults:filtered.length, analysisType:aiTrends?"AI Expert":"Web Search", trends };
  fs.writeFileSync(RESULTS_FILE, JSON.stringify(latestResult, null, 2));
  return latestResult;
}

function esc(t: string) { return t ? t.replace(/[_*[\]()~`>#+\-=|{}.!]/g, "\\$&") : ""; }

function formatResults(data: any) {
  if (!data?.trends?.length) return ["📭 Результатов нет."];
  const d = new Date(data.date);
  const ms = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"];
  const ds = `${d.getDate()} ${ms[d.getMonth()]} ${d.getFullYear()}`;
  const isAI = data.analysisType === "AI Expert";
  const catMap: Record<string,number> = {}, demMap: Record<string,number> = {"Very High":0,"High":0,"Medium":0,"Low":0};
  for (const t of data.trends) {
    catMap[t.category||"Other"]=(catMap[t.category||"Other"]||0)+1;
    const dl=(t.demand_level||"Medium").toLowerCase();
    if(dl.includes("very high"))demMap["Very High"]++;else if(dl.includes("high"))demMap["High"]++;else if(dl.includes("medium"))demMap["Medium"]++;else demMap["Low"]++;
  }
  const topCats=Object.entries(catMap).sort((a,b)=>b[1]-a[1]).slice(0,4).map(([c,n])=>`${esc(c)}: ${n}`).join(" | ");
  const demLine=Object.entries(demMap).filter(([,v])=>v>0).map(([l,v])=>`${l}: ${v}`).join(" | ");
  const chunks: string[][] = []; let chunk: string[] = [];
  for (let i=0;i<data.trends.length;i++) {
    const t=data.trends[i],e=EMOJIS[i%EMOJIS.length];
    let entry: string;
    if (isAI) {
      entry=[`${e} *${i+1}\\. ${esc(t.name)}*`,`   Категория: ${esc(t.category||"N/A")}  |  Спрос: ${esc(t.demand_level||"Medium")}`,`   Рост: ${esc(t.growth_rate||"N/A")}  |  Рынок: ${esc(t.market_size||"N/A")}`,t.target_audience?`   Аудитория: ${esc(t.target_audience)}`:"",t.why_trending?`   Тренд: ${esc(t.why_trending)}`:"",t.opportunity?`   Возможность: ${esc(t.opportunity)}`:"",t.top_sources?.length?`   Источник: ${esc(t.top_sources[0])}`:""].filter(Boolean).join("\n");
    } else {
      entry=[`${e} *${i+1}\\. ${esc(t.name)}*`,`   ${esc(t.why_trending?.substring(0,150)||"")}`,t.top_sources?.length?`   ${esc(t.top_sources[0])}`:"",`   Упоминаний: ${t.sources_count}`].filter(Boolean).join("\n");
    }
    chunk.push(entry);
    if (chunk.join("\n\n").length>3500){chunks.push(chunk);chunk=[];}
  }
  if(chunk.length)chunks.push(chunk);
  return chunks.map((ch,idx)=>{
    const h=idx===0?`📊 *АНАЛИТИКА ТРЕНДОВ EU*\n🤖 ${isAI?"AI экспертный анализ":"Веб\\-поиск"}\n🗓 ${ds}\n🔍 Источников: ${data.totalRawResults}\n${"━".repeat(25)}\n📌 Категории: ${topCats}\n🌡 Спрос: ${demLine}\n${"━".repeat(25)}`:`📊 *АНАЛИТИКА ТРЕНДОВ EU \\(продолжение\\)*\n${"━".repeat(25)}`;
    return h+"\n\n"+ch.join("\n\n");
  });
}

async function handleUpdate(u: any) {
  if (!bot) return;
  try {
    if (u.message) {
      const chatId = u.message.chat.id;
      const text = u.message.text || "";
      saveUser(chatId, u.message.from?.first_name || "User");
      if (text === "/start") {
        bot.sendMessage(chatId, "👋 *EU Trend Analyzer Bot \\— AI Expert*\n\nАнализирую набирающие популярность товары и услуги в Европе\\.\n\nНажмите кнопку:", { parse_mode: "Markdown", ...getMenu() });
        console.log(`[TG-BOT] /start from ${u.message.from?.first_name} (${chatId})`);
      } else if (text === "/status") {
        const s = latestResult
          ? `📊 Последняя: ${latestResult.date}\n📈 Трендов: ${latestResult.trends?.length}\n🔍 Источников: ${latestResult.totalRawResults}\n🤖 Тип: ${latestResult.analysisType||"N/A"}`
          : "📭 Нет результатов";
        bot.sendMessage(chatId, s, getMenu());
      }
      return;
    }
    if (u.callback_query) {
      const cq = u.callback_query;
      const chatId = cq.message?.chat?.id;
      bot.answerCallbackQuery(cq.id).catch(()=>{});
      if (cq.data === "start_analysis") {
        if (state.isAnalyzing) { bot.sendMessage(chatId, "⏳ Анализ уже запущен! Подождите...", getMenu()); return; }
        bot.sendMessage(chatId, "🔄 *Аналитика запущена...*\n\n🤖 ИИ собирает данные и проводит экспертный анализ\\.\nЗаймёт 2\\-3 минуты\\.", { parse_mode: "Markdown" });
        state.isAnalyzing = true;
        state.analysisStartedAt = Date.now();
        saveState();
        const targetChat = chatId;
        runAnalysis()
          .then(r => {
            console.log(`[TG-BOT] DONE: ${r.trends.length} trends (${r.analysisType})`);
            state.isAnalyzing = false;
            state.analysisStartedAt = null;
            saveState();
            for (const usr of (state.users||[])) {
              bot!.sendMessage(usr.chatId, `✅ *Анализ завершён!*\n\n🤖 ${r.analysisType}\n📊 ${r.trends.length} трендов\n🔍 ${r.totalRawResults} источников\n\nНажмите «Выдать результаты»\\.`, { parse_mode: "Markdown", ...getMenu() }).catch(()=>{});
            }
          })
          .catch(err => {
            console.error("[TG-BOT] Analysis error:", (err as Error).message?.substring(0,200));
            state.isAnalyzing = false;
            state.analysisStartedAt = null;
            saveState();
            bot!.sendMessage(targetChat, `❌ Ошибка: ${(err as Error).message}`, getMenu()).catch(()=>{});
          });
      }
      if (cq.data === "show_results") {
        if (!latestResult) { bot.sendMessage(chatId, "📭 Нет результатов. Сначала запустите аналитику.", getMenu()); return; }
        const msgs = formatResults(latestResult);
        for (let i = 0; i < msgs.length; i++) {
          await new Promise(res => setTimeout(res, 600));
          bot.sendMessage(chatId, msgs[i], { parse_mode: "Markdown" }).catch(() => bot!.sendMessage(chatId, msgs[i]));
        }
        setTimeout(() => bot.sendMessage(chatId, "───", getMenu()), 300);
      }
    }
  } catch(err: any) {
    console.error("[TG-BOT] handleUpdate:", err.message?.substring(0,100));
  }
}

async function pollLoop() {
  while (true) {
    try {
      const updates = await bot!.getUpdates({ offset: state.lastUpdateId + 1, timeout: 5 });
      if (updates?.length) {
        for (const u of updates) {
          state.lastUpdateId = u.update_id;
          handleUpdate(u);
        }
        saveState();
      }
    } catch(err: any) {
      if (err.code !== "ETIMEDOUT" && err.code !== "ECONNRESET" && err.code !== "EPIPE") {
        console.error("[TG-BOT] Poll:", err.code, err.message?.substring(0,100));
      }
    }
    await new Promise(r => setTimeout(r, 2000));
  }
}

export async function startBot() {
  console.log("[TG-BOT] Starting...");
  loadData();
  bot = new TelegramBot(BOT_TOKEN, { polling: false });

  // Daily cron
  cron.schedule("0 9 * * *", () => {
    const users = state.users || [];
    if (state.isAnalyzing || !users.length) return;
    state.isAnalyzing = true;
    state.analysisStartedAt = Date.now();
    saveState();
    runAnalysis()
      .then(() => {
        for (const u of users) {
          bot!.sendMessage(u.chatId, "🤖 *Ежедневный AI\\-отчёт готов!*\nНажмите «Выдать результаты»\\.", { parse_mode: "Markdown", ...getMenu() }).catch(()=>{});
        }
      })
      .catch((e: any) => console.error("[TG-BOT] Cron:", e))
      .finally(() => { state.isAnalyzing = false; state.analysisStartedAt = null; saveState(); });
  }, { timezone: "Europe/Moscow" });

  console.log(`[TG-BOT] ✅ Running, ${state.users?.length||0} users`);
  pollLoop();
}
