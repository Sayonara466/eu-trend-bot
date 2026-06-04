import { NextRequest, NextResponse } from "next/server";

const BOT_TOKEN = "8792613395:AAGquGo3aZ1fbFjToatyR5hSLJiYR0Bs9s8";

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const webhookUrl = url.searchParams.get("url");

  if (!webhookUrl) {
    return NextResponse.json({ error: "Pass ?url= parameter" }, { status: 400 });
  }

  // Delete existing webhook first
  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook?drop_pending_updates=true`);

  // Set new webhook
  const res = await fetch(
    `https://api.telegram.org/bot${BOT_TOKEN}/setWebhook?url=${encodeURIComponent(webhookUrl)}`
  );
  const data = await res.json();

  return NextResponse.json(data);
}
