/**
 * ╔════════════════════════════════════════════════════════════╗
 * ║  EU TREND BOT — Cloudflare Workers Version                ║
 * ║  FREE deployment: 100K requests/day, cron triggers, KV     ║
 * ║                                                            ║
 * ║  Webhook mode (no polling) + KV storage (no filesystem)   ║
 * ║  Cron trigger for daily 09:00 MSK analysis                 ║
 * ╚════════════════════════════════════════════════════════════╝
 */

// =============== CONFIG ===============
const BOT_TOKEN = "8792613395:AAGquGo3aZ1fbFjToatyR5hSLJiYR0Bs9s8";
const API_BASE = `https://api.telegram.org/bot${BOT_TOKEN}`;

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

const EMOJIS = ["🔥","⚡","🚀","💎","🌟","🎯","📈","💡","🏆","⭐","💪","🎪","🎲","🧩","🔧","🧠","🌍","🎨","🔬","📦"];

// =============== HELPERS ===============
function escapeMd(t) {
  return t.replace(/([_*\[\]()~`>#+\-=|{}.!])/g, "\\$1");
}

function stripHtml(h) {
  return h.replace(/<[^>]*>/g, "").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').trim();
}

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

// =============== TELEGRAM API (direct HTTP, no library) ===============
async function tg(method, body) {
  const res = await fetch(`${API_BASE}/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

async function sendMessage(chatId, text, extra = {}) {
  try { return await tg("sendMessage", { chat_id: chatId, text, ...extra }); }
  catch (e) { console.error("sendMsg err:", e.message); }
}

async function editMessage(chatId, messageId, text) {
  try { return await tg("editMessageText", { chat_id: chatId, message_id: messageId, text }); }
  catch (e) { console.error("editMsg err:", e.message); }
}

async function answerCallback(callbackQueryId) {
  try { return await tg("answerCallbackQuery", { callback_query_id: callbackQueryId }); }
  catch {}
}

// =============== KV STORAGE (replaces filesystem) ===============
async function loadState(env) {
  try {
    const raw = await env.KV.get("state");
    return raw ? JSON.parse(raw) : { users: [], isAnalyzing: false, lastAnalysisDate: null };
  } catch {
    return { users: [], isAnalyzing: false, lastAnalysisDate: null };
  }
}

async function saveState(env, state) {
  await env.KV.put("state", JSON.stringify(state));
}

async function loadTrends(env) {
  try {
    const raw = await env.KV.get("trends");
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

async function saveTrends(env, trends) {
  await env.KV.put("trends", JSON.stringify(trends));
}

function addUser(state, id, name) {
  if (!state.users) state.users = [];
  if (!state.users.find(u => u.chatId === id)) state.users.push({ chatId: id, name: name || "User" });
}

// =============== DUCKDUCKGO SEARCH ===============
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

    const linkRx = /<a[^>]+class="result-link"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
    const snipRx = /<td[^>]+class="result-snippet"[^>]*>([\s\S]*?)<\/td>/gi;

    const links = [], snips = [];
    let m;
    while ((m = linkRx.exec(html)) !== null) links.push({ url: m[1], title: stripHtml(m[2]) });
    while ((m = snipRx.exec(html)) !== null) snips.push(stripHtml(m[1]));

    for (let i = 0; i < links.length; i++) {
      try {
        let rawUrl = links[i].url;
        if (rawUrl.includes("uddg=")) {
          const p = new URL(rawUrl).searchParams;
          if (p.get("uddg")) rawUrl = decodeURIComponent(p.get("uddg"));
        }
        if (!rawUrl.startsWith("http")) rawUrl = "https://" + rawUrl;
        const domain = new URL(rawUrl).hostname.replace(/^www\./, "");
        results.push({ name: links[i].title, url: rawUrl, domain, snippet: snips[i] || "" });
      } catch {}
    }
    return results;
  } catch (e) {
    console.error("Search err:", e.message);
    return [];
  }
}

// =============== ANALYZER ===============
async function runAnalysis(env, ctx, notifyChatId, notifyAll = false) {
  const state = await loadState(env);
  if (state.isAnalyzing) {
    if (notifyChatId) sendMessage(notifyChatId, "⏳ Аналитика уже запущена! Подождите...", getKeyboard());
    return;
  }
  state.isAnalyzing = true;
  await saveState(env, state);

  const statusMsg = notifyChatId
    ? await sendMessage(notifyChatId, "🔄 *Аналитика трендов запущена...*", getKeyboard())
    : null;
  const statusMsgId = statusMsg?.ok ? statusMsg.result?.message_id : null;

  try {
    const allResults = [];
    for (let i = 0; i < QUERIES.length; i++) {
      console.log(`[${i + 1}/${QUERIES.length}] ${QUERIES[i]}`);
      const results = await searchDDG(QUERIES[i]);
      allResults.push(...results);

      if (statusMsgId && i % 3 === 0) {
        editMessage(notifyChatId, statusMsgId,
          `🔄 Аналитика... Запросов: ${i + 1}/${QUERIES.length}, Найдено: ${allResults.length}`);
      }
    }

    // Deduplicate, filter, sort
    const map = new Map();
    for (const item of allResults) {
      const domain = item.domain || "";
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

    await saveTrends(env, { date: new Date().toISOString(), totalRawResults: allResults.length, trends });
    state.isAnalyzing = false;
    state.lastAnalysisDate = new Date().toISOString();
    await saveState(env, state);

    console.log(`DONE: ${trends.length} trends`);

    // Notify
    const targets = notifyAll && state.users?.length ? state.users.map(u => u.chatId) : (notifyChatId ? [notifyChatId] : []);
    for (const cid of targets) {
      sendMessage(cid,
        `✅ *Аналитика завершена!*\n\nНайдено *${trends.length}* трендов.\nНажмите «📊 Выдать результаты» чтобы посмотреть.`,
        getKeyboard());
    }
  } catch (err) {
    state.isAnalyzing = false;
    await saveState(env, state);
    console.error("Analysis err:", err.message);
    if (notifyChatId) sendMessage(notifyChatId, `❌ Ошибка: ${err.message}`, getKeyboard());
  }
}

// =============== FORMAT RESULTS ===============
async function sendResults(chatId, env) {
  const data = await loadTrends(env);
  if (!data?.trends?.length) {
    await sendMessage(chatId, "📭 Результатов нет. Сначала запустите аналитику.", getKeyboard());
    return;
  }
  const d = new Date(data.date);
  const months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"];
  const ds = `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;

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
    try {
      await sendMessage(chatId, text, { parse_mode: "MarkdownV2" });
    } catch {
      try {
        await sendMessage(chatId, text.replace(/\\\*/g, "").replace(/_/g, ""), { disable_web_page_preview: true });
      } catch {}
    }
  }
  await sendMessage(chatId, "───", getKeyboard());
}

// =============== WEBHOOK HANDLER ===============
async function handleUpdate(update, env, ctx) {
  // /start
  if (update.message?.text?.startsWith("/start")) {
    const msg = update.message;
    const state = await loadState(env);
    addUser(state, msg.chat.id, msg.from?.first_name);
    await saveState(env, state);
    await sendMessage(msg.chat.id,
      "👋 *EU Trend Analyzer Bot*\n\nАнализирую набирающие популярность товары и услуги в Европе.\n\nКаждый раз — *свежий поиск* по 10 запросам.\n\nВыберите действие 👇",
      { parse_mode: "Markdown", ...getKeyboard() });
    return;
  }

  // /status
  if (update.message?.text?.startsWith("/status")) {
    const msg = update.message;
    const state = await loadState(env);
    addUser(state, msg.chat.id, msg.from?.first_name);
    await saveState(env, state);
    const trends = await loadTrends(env);
    const lt = trends ? new Date(trends.date).toLocaleString("ru-RU", { timeZone: "Europe/Moscow" }) : "пока нет";
    await sendMessage(msg.chat.id,
      `📋 *Статус*\n\n🟢 Бот работает (CF Workers)\n👥 Юзеров: ${state.users?.length || 0}\n📊 Последняя: ${lt}\n📈 Трендов: ${trends?.trends?.length || 0}\n⏰ Авто: 09:00 МСК`,
      getKeyboard());
    return;
  }

  // Callback queries (inline button presses)
  if (update.callback_query) {
    const cq = update.callback_query;
    const chatId = cq.message?.chat?.id;
    const name = cq.from?.first_name || "";
    const state = await loadState(env);
    addUser(state, chatId, name);
    await saveState(env, state);
    await answerCallback(cq.id);

    if (cq.data === "run_analysis") {
      console.log(`Analysis: ${name} (${chatId})`);
      // Use waitUntil to avoid the 30s CPU timeout on free tier
      ctx.waitUntil(runAnalysis(env, ctx, chatId));
    } else if (cq.data === "show_results") {
      console.log(`Results: ${name} (${chatId})`);
      await sendResults(chatId, env);
    }
    return;
  }
}

// =============== WORKER ENTRY POINTS ===============
export default {
  // HTTP handler — receives Telegram webhook POSTs
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // GET: health check
    if (request.method === "GET" && url.pathname === "/") {
      const state = await loadState(env);
      return new Response(JSON.stringify({
        status: "ok",
        service: "EU Trend Bot (Cloudflare Workers)",
        users: state.users?.length || 0,
      }), { headers: { "Content-Type": "application/json" } });
    }

    // GET /set-webhook: register this worker as Telegram webhook
    if (url.pathname === "/set-webhook" && request.method === "GET") {
      const webhookUrl = `${url.origin}`;
      const result = await tg("setWebhook", {
        url: webhookUrl,
        allowed_updates: ["message", "callback_query"],
      });
      return new Response(JSON.stringify({ webhookUrl, telegram: result }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    // POST: Telegram webhook
    if (request.method === "POST") {
      try {
        const update = await request.json();
        await handleUpdate(update, env, ctx);
        return new Response(JSON.stringify({ ok: true }), {
          headers: { "Content-Type": "application/json" },
        });
      } catch (e) {
        console.error("Webhook error:", e.message);
        return new Response(JSON.stringify({ error: e.message }), { status: 500 });
      }
    }

    return new Response("EU Trend Bot — POST for webhooks, GET /set-webhook to configure", { status: 404 });
  },

  // Cron trigger — daily at 06:00 UTC = 09:00 MSK
  async scheduled(event, env, ctx) {
    console.log("Daily cron triggered at", new Date().toISOString());
    const state = await loadState(env);
    if (state.users?.length && !state.isAnalyzing) {
      ctx.waitUntil(runAnalysis(env, ctx, state.users[0].chatId, true));
    }
  },
};
