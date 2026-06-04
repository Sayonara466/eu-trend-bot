import { NextRequest, NextResponse } from "next/server";

const BOT_TOKEN = "8792613395:AAGquGo3aZ1fbFjToatyR5hSLJiYR0Bs9s8";
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

// In-memory state
let adminChatId = "";
let isAnalyzing = false;
let latestResult: any = null;

// Load previous results
import fs from "fs";
const RESULTS_FILE = "/home/z/my-project/download/trend_results.json";
try {
  if (fs.existsSync(RESULTS_FILE)) {
    latestResult = JSON.parse(fs.readFileSync(RESULTS_FILE, "utf-8"));
  }
} catch (e) {}

function saveResults() {
  try {
    fs.writeFileSync(RESULTS_FILE, JSON.stringify(latestResult, null, 2));
  } catch (e) {}
}

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

async function sendTelegram(chatId: string, text: string, extra: any = {}) {
  try {
    const res = await fetch(
      `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId, text, ...extra }),
      }
    );
    return await res.json();
  } catch (e) {
    console.error("sendTelegram error:", e);
    return null;
  }
}

async function answerCallback(callbackQueryId: string) {
  try {
    await fetch(
      `https://api.telegram.org/bot${BOT_TOKEN}/answerCallbackQuery`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ callback_query_id: callbackQueryId }),
      }
    );
  } catch (e) {}
}

// ===== ANALYZER =====
async function searchWeb(query: string): Promise<any[]> {
  const ZAI = (await import("z-ai-web-dev-sdk")).default;
  const zai = await ZAI.create();

  for (let attempt = 0; attempt <= 2; attempt++) {
    try {
      const result = await zai.functions.invoke("web_search", { query, num: 10 });
      return result || [];
    } catch (err: any) {
      if (err?.message?.includes("429") && attempt < 2) {
        await new Promise((r) => setTimeout(r, 5000));
        continue;
      }
      console.error(`Search error: ${err?.message}`);
      return [];
    }
  }
  return [];
}

async function runAnalysis() {
  const allResults: any[] = [];

  for (let i = 0; i < QUERIES.length; i++) {
    console.log(`Query ${i + 1}/${QUERIES.length}: ${QUERIES[i]}`);
    const results = await searchWeb(QUERIES[i]);
    allResults.push(...results);
    if (i < QUERIES.length - 1) await new Promise((r) => setTimeout(r, 2000));
  }

  console.log(`Raw results: ${allResults.length}`);

  const domainMap = new Map<string, any>();
  for (const item of allResults) {
    const domain = item.host_name || item.url;
    if (!domain) continue;
    const text = ((item.name || "") + " " + (item.snippet || "")).toLowerCase();
    if (EXCLUDE.some((cat) => text.includes(cat))) continue;

    if (!domainMap.has(domain)) {
      domainMap.set(domain, { domain, name: item.name || "", snippet: item.snippet || "", url: item.url || "", mentions: 0 });
    }
    const entry = domainMap.get(domain)!;
    entry.mentions++;
    if (item.name && item.name.length > entry.name.length) entry.name = item.name;
    if (item.snippet && item.snippet.length > entry.snippet.length) entry.snippet = item.snippet;
  }

  const trends = [...domainMap.values()]
    .sort((a, b) => b.mentions - a.mentions)
    .slice(0, 25)
    .map((t) => ({
      name: (t.name || "N/A").replace(/\s*[-|–—].*$/, "").trim().substring(0, 80),
      domain: t.domain,
      url: t.url,
      snippet: (t.snippet || "").replace(/<[^>]*>/g, "").trim().substring(0, 180),
      mentions: t.mentions,
    }));

  latestResult = { date: new Date().toISOString(), totalRawResults: allResults.length, trends };
  saveResults();
  return latestResult;
}

// ===== FORMAT RESULTS =====
function formatResults(data: any): string[] {
  if (!data?.trends?.length) return ["📭 Результатов пока нет."];

  const d = new Date(data.date);
  const months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"];
  const dateStr = `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;

  const chunks: string[][] = [];
  let chunk: string[] = [];

  for (let i = 0; i < data.trends.length; i++) {
    const t = data.trends[i];
    const e = EMOJIS[i % EMOJIS.length];
    const entry = [
      `${e} *${i + 1}. ${t.name}*`,
      `${t.domain}`,
      `${t.snippet}`,
      `${t.url}`,
      `Упоминаний: ${t.mentions}`,
    ].join("\n");
    chunk.push(entry);
    if (chunk.join("\n\n").length > 3500) {
      chunks.push(chunk);
      chunk = [];
    }
  }
  if (chunk.length) chunks.push(chunk);

  return chunks.map((ch, idx) => {
    const header = idx === 0
      ? `📊 *АНАЛИТИКА ТРЕНДОВ EU*\n🗓 ${dateStr}\n🔍 Источников: ${data.totalRawResults}\n${"━".repeat(25)}`
      : `📊 *АНАЛИТИКА ТРЕНДОВ EU (продолжение)*\n${"━".repeat(25)}`;
    return header + "\n\n" + ch.join("\n\n");
  });
}

// ===== WEBHOOK HANDLER =====
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    console.log("Webhook received:", JSON.stringify(body).substring(0, 200));

    // --- MESSAGE ---
    if (body.message) {
      const chatId = body.message.chat.id;
      const text = body.message.text || "";
      adminChatId = String(chatId);

      if (text === "/start") {
        await sendTelegram(chatId,
          "👋 *EU Trend Analyzer Bot*\n\nАнализирую набирающие популярность товары и услуги в Европе.\n\nНажмите кнопку ниже:",
          { parse_mode: "Markdown", ...getMenu() }
        );
        return NextResponse.json({ ok: true });
      }

      if (text === "/status") {
        const s = latestResult
          ? `📊 Последняя: ${latestResult.date}\n📈 Трендов: ${latestResult.trends?.length || 0}\n🔍 Источников: ${latestResult.totalRawResults || 0}`
          : "📭 Нет результатов";
        await sendTelegram(chatId, s, getMenu());
        return NextResponse.json({ ok: true });
      }
    }

    // --- CALLBACK QUERY ---
    if (body.callback_query) {
      const cq = body.callback_query;
      const chatId = cq.message?.chat?.id;
      const data = cq.data;
      adminChatId = String(chatId);

      await answerCallback(cq.id);

      // START ANALYSIS
      if (data === "start_analysis") {
        if (isAnalyzing) {
          await sendTelegram(chatId, "⏳ Анализ уже запущен! Ждите...", getMenu());
          return NextResponse.json({ ok: true });
        }

        await sendTelegram(chatId,
          "🔄 *Аналитика трендов запущена...*\n\nИщу набирающие популярность товары и услуги в Европе.\nЭто займёт 1-2 минуты.",
          { parse_mode: "Markdown" }
        );
        console.log(`Analysis STARTED for ${chatId}`);

        isAnalyzing = true;
        // Fire analysis in background — respond immediately
        (async () => {
          try {
            const result = await runAnalysis();
            console.log(`Analysis DONE: ${result.trends.length} trends`);
            await sendTelegram(adminChatId,
              "✅ *Аналитика завершена!*\n\nНажмите «Выдать результаты» чтобы увидеть ТОП трендов.",
              { parse_mode: "Markdown", ...getMenu() }
            );
          } catch (err: any) {
            console.error("Analysis FAIL:", err?.message);
            await sendTelegram(adminChatId,
              `❌ Ошибка: ${err?.message}\nПопробуйте ещё раз.`,
              getMenu()
            );
          } finally {
            isAnalyzing = false;
          }
        })();

        return NextResponse.json({ ok: true });
      }

      // SHOW RESULTS
      if (data === "show_results") {
        if (!latestResult) {
          await sendTelegram(chatId, "📭 Нет результатов.\nСначала нажмите «Запустить аналитику».", getMenu());
          return NextResponse.json({ ok: true });
        }

        console.log(`Sending RESULTS to ${chatId}`);
        const msgs = formatResults(latestResult);
        for (const m of msgs) {
          await sendTelegram(chatId, m, { parse_mode: "Markdown" });
          await new Promise((r) => setTimeout(r, 400));
        }
        await sendTelegram(chatId, "───", getMenu());

        return NextResponse.json({ ok: true });
      }
    }

    return NextResponse.json({ ok: true });
  } catch (err: any) {
    console.error("Webhook error:", err?.message);
    return NextResponse.json({ ok: false, error: err?.message }, { status: 500 });
  }
}

export async function GET() {
  return NextResponse.json({
    status: "running",
    analyzing: isAnalyzing,
    hasResults: !!latestResult,
    resultDate: latestResult?.date || null,
    trendCount: latestResult?.trends?.length || 0,
  });
}
