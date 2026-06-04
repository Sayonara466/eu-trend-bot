/**
 * instrumentation.ts — runs when Next.js starts
 * Launches Telegram bot polling in background
 */
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    // Dynamic import to avoid build issues
    const { startBot } = await import("./lib/tgbot");
    startBot().catch(e => console.error("[TG-BOT] Fatal:", e.message));
  }
}
