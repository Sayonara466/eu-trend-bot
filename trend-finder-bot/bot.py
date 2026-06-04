"""
EU Trend Analytics Bot v14.0 — Deep Niche Crypto + Category-Specific Offers
==========================================================================
AI-powered trend discovery with "Improved Offer" feature:
  1. Trendy European fashion brands
  2. Trending crypto projects (DEEP NICHE: AI-крипта, DePIN, RWA, L2, DeSci, Bitcoin DeFi)
  3. Hot startups & companies

v14.0 CHANGES:
  - Crypto search: CoinGecko API (primary) → AI enrichment (Gemini+Search) → deep niche fallback
  - OpenRouter timeout reduced to 25s (prevents hanging)
  - Crypto format: niche tag, why hyping, what it does, official link
  - NO generic/popular projects — only deep niche from: AI-crypto, DePIN, RWA, new L2/L3,
    DeSci, GameFi, SocialFi, Bitcoin DeFi, modular blockchains

AI Provider: OpenRouter (free models, 25s timeout) + Gemini (Google Search grounding)
Landing Pages: 6 design themes x 3 category-specific layouts
"""

import asyncio
import json
import logging
import os
import random
import re
import tempfile
import zipfile
from datetime import datetime, timedelta
from aiohttp import web

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram.client.default import DefaultBotProperties

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
PORT = int(os.getenv("PORT", 10000))
RENDER_URL = os.getenv("RENDER_URL", "https://eu-trend-bot.onrender.com")

if not BOT_TOKEN:
    logging.error("BOT_TOKEN env var is required")
    raise SystemExit(1)

# logger.warning moved after logger init

# ─── Logging ──────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("trendbot")

if not OPENROUTER_KEY and not GEMINI_KEY:
    logger.warning("No OPENROUTER_KEY or GEMINI_API_KEY configured — AI features will use fallback data only")

# ─── Bot & Dispatcher ────────────────────────────────────────

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# ─── In-memory Storage ────────────────────────────────────────

user_items: dict[int, dict[str, list]] = {}

# ═══════════════════════════════════════════════════════════════════
# 6 DESIGN THEMES FOR LANDING PAGES
# ═══════════════════════════════════════════════════════════════════

DESIGN_THEMES = [
    {
        "name": "Obsidian Gold",
        "bg_primary": "#0a0a0a",
        "bg_secondary": "#1a1a1a",
        "bg_gradient": "linear-gradient(135deg, #0a0a0a 0%, #1a1a0e 50%, #0d0d00 100%)",
        "hero_gradient": "linear-gradient(135deg, #0a0a0a 0%, #1a1505 30%, #2a1f00 60%, #0a0a0a 100%)",
        "accent": "#FFD700",
        "accent_secondary": "#FFC300",
        "text_primary": "#FFFFFF",
        "text_secondary": "#B0B0B0",
        "card_bg": "rgba(255, 215, 0, 0.05)",
        "card_border": "rgba(255, 215, 0, 0.15)",
        "button_bg": "linear-gradient(135deg, #FFD700, #FFC300)",
        "button_text": "#0a0a0a",
        "divider": "linear-gradient(90deg, transparent, #FFD700, transparent)",
        "font_heading": "'Playfair Display', serif",
        "font_body": "'Inter', sans-serif",
        "google_fonts": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap",
        "nav_bg": "rgba(10, 10, 10, 0.95)",
        "glow": "0 0 30px rgba(255, 215, 0, 0.15)",
        "description": "Dark black background with gold (#FFD700) accents, luxury feel, serif headings (Playfair Display), geometric gold dividers",
    },
    {
        "name": "Cyberpunk Neon",
        "bg_primary": "#0a0010",
        "bg_secondary": "#150025",
        "bg_gradient": "linear-gradient(135deg, #0a0010 0%, #1a0030 30%, #0d0020 60%, #050010 100%)",
        "hero_gradient": "linear-gradient(135deg, #0a0010 0%, #1a0040 25%, #200050 50%, #0a0010 100%)",
        "accent": "#00FFFF",
        "accent_secondary": "#FF00FF",
        "text_primary": "#FFFFFF",
        "text_secondary": "#B0B0FF",
        "card_bg": "rgba(0, 255, 255, 0.05)",
        "card_border": "rgba(0, 255, 255, 0.2)",
        "button_bg": "linear-gradient(135deg, #00FFFF, #FF00FF)",
        "button_text": "#0a0010",
        "divider": "linear-gradient(90deg, transparent, #00FFFF, #FF00FF, transparent)",
        "font_heading": "'Orbitron', sans-serif",
        "font_body": "'Space Grotesk', sans-serif",
        "google_fonts": "https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&display=swap",
        "nav_bg": "rgba(10, 0, 16, 0.95)",
        "glow": "0 0 40px rgba(0, 255, 255, 0.2), 0 0 80px rgba(255, 0, 255, 0.1)",
        "description": "Dark purple/black background, neon cyan (#00FFFF) and magenta (#FF00FF) accents, futuristic, monospace-style headings (Orbitron + Space Grotesk), glowing effects",
    },
    {
        "name": "Ivory Minimal",
        "bg_primary": "#FAFAF5",
        "bg_secondary": "#F0F0EB",
        "bg_gradient": "linear-gradient(135deg, #FAFAF5 0%, #F5F5EE 50%, #FAFAF5 100%)",
        "hero_gradient": "linear-gradient(135deg, #FAFAF5 0%, #F0EDE5 50%, #FAFAF5 100%)",
        "accent": "#2C2C2C",
        "accent_secondary": "#8B7355",
        "text_primary": "#1a1a1a",
        "text_secondary": "#666666",
        "card_bg": "#FFFFFF",
        "card_border": "#E0DDD5",
        "button_bg": "#2C2C2C",
        "button_text": "#FFFFFF",
        "divider": "linear-gradient(90deg, transparent, #D0CCC0, transparent)",
        "font_heading": "'Cormorant Garamond', serif",
        "font_body": "'Inter', sans-serif",
        "google_fonts": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap",
        "nav_bg": "rgba(250, 250, 245, 0.95)",
        "glow": "0 4px 20px rgba(0, 0, 0, 0.06)",
        "description": "White/cream (#FAFAF5) background, charcoal text, thin borders, elegant serif headings (Cormorant Garamond + Inter), very clean minimal design",
    },
    {
        "name": "Cosmic Violet",
        "bg_primary": "#1a0a2e",
        "bg_secondary": "#120628",
        "bg_gradient": "linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 30%, #1a0a2e 60%, #0d0520 100%)",
        "hero_gradient": "linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 25%, #3d2080 50%, #1a0a2e 100%)",
        "accent": "#B388FF",
        "accent_secondary": "#7C4DFF",
        "text_primary": "#FFFFFF",
        "text_secondary": "#C8B8E8",
        "card_bg": "rgba(179, 136, 255, 0.08)",
        "card_border": "rgba(179, 136, 255, 0.2)",
        "button_bg": "linear-gradient(135deg, #B388FF, #7C4DFF)",
        "button_text": "#FFFFFF",
        "divider": "linear-gradient(90deg, transparent, #B388FF, transparent)",
        "font_heading": "'Outfit', sans-serif",
        "font_body": "'Inter', sans-serif",
        "google_fonts": "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap",
        "nav_bg": "rgba(26, 10, 46, 0.95)",
        "glow": "0 0 50px rgba(179, 136, 255, 0.15)",
        "description": "Deep purple (#1a0a2e) background, violet/lavender accents, starfield-like gradient, modern sans (Outfit + Inter), floating orb effects",
    },
    {
        "name": "Warm Copper",
        "bg_primary": "#1a1410",
        "bg_secondary": "#211a14",
        "bg_gradient": "linear-gradient(135deg, #1a1410 0%, #2a1f18 30%, #1a1410 60%, #100c08 100%)",
        "hero_gradient": "linear-gradient(135deg, #1a1410 0%, #2a1f14 25%, #3d2a15 50%, #1a1410 100%)",
        "accent": "#B87333",
        "accent_secondary": "#FFBF00",
        "text_primary": "#FFFFFF",
        "text_secondary": "#D4B896",
        "card_bg": "rgba(184, 115, 51, 0.08)",
        "card_border": "rgba(184, 115, 51, 0.2)",
        "button_bg": "linear-gradient(135deg, #B87333, #FFBF00)",
        "button_text": "#1a1410",
        "divider": "linear-gradient(90deg, transparent, #B87333, transparent)",
        "font_heading": "'DM Serif Display', serif",
        "font_body": "'Inter', sans-serif",
        "google_fonts": "https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@300;400;500;600;700&display=swap",
        "nav_bg": "rgba(26, 20, 16, 0.95)",
        "glow": "0 0 40px rgba(184, 115, 51, 0.15)",
        "description": "Dark warm (#1a1410) background, copper (#B87333) and amber (#FFBF00) accents, warm tones, serif headings (DM Serif Display + Inter), fire-like gradients",
    },
    {
        "name": "Arctic Blue",
        "bg_primary": "#0a1628",
        "bg_secondary": "#0e1e38",
        "bg_gradient": "linear-gradient(135deg, #0a1628 0%, #102040 30%, #0a1628 60%, #060e1c 100%)",
        "hero_gradient": "linear-gradient(135deg, #0a1628 0%, #102545 25%, #15305a 50%, #0a1628 100%)",
        "accent": "#4FC3F7",
        "accent_secondary": "#81D4FA",
        "text_primary": "#FFFFFF",
        "text_secondary": "#A8C8E8",
        "card_bg": "rgba(79, 195, 247, 0.06)",
        "card_border": "rgba(79, 195, 247, 0.15)",
        "button_bg": "linear-gradient(135deg, #4FC3F7, #0288D1)",
        "button_text": "#FFFFFF",
        "divider": "linear-gradient(90deg, transparent, #4FC3F7, transparent)",
        "font_heading": "'Manrope', sans-serif",
        "font_body": "'Inter', sans-serif",
        "google_fonts": "https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap",
        "nav_bg": "rgba(10, 22, 40, 0.95)",
        "glow": "0 0 40px rgba(79, 195, 247, 0.12)",
        "description": "Deep navy (#0a1628) background, ice blue (#4FC3F7) and white accents, clean modern (Manrope + Inter), frost/frozen glass effects",
    },
]


def get_theme_for_project(project_name: str) -> dict:
    """Select a design theme based on project name hash."""
    idx = abs(hash(project_name)) % len(DESIGN_THEMES)
    return DESIGN_THEMES[idx]


# ═══════════════════════════════════════════════════════════════════
# MENU KEYBOARD
# ═══════════════════════════════════════════════════════════════════

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="\U0001F457 Трендовые магазины")],
        [KeyboardButton(text="\U0001FA99 Трендовая крипта")],
        [KeyboardButton(text="\U0001F3E2 Трендовые компании")],
    ],
    resize_keyboard=True,
)

# ═══════════════════════════════════════════════════════════════════
# OPENROUTER API
# ═══════════════════════════════════════════════════════════════════

OPENROUTER_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "moonshotai/kimi-k2.6:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-120b:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def ask_openrouter(
    system_prompt: str,
    user_text: str,
    max_tokens: int = 8192,
) -> str | None:
    """Call OpenRouter API, trying models in order until one succeeds.

    Returns the raw text response, or None if all models fail.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": RENDER_URL,
        "X-Title": "EU Trend Analytics Bot",
    }
    body = {
        "model": "",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=25) as client:
        for model_id in OPENROUTER_MODELS[:4]:  # Only try first 4 models max
            try:
                body["model"] = model_id
                logger.info(f"[OpenRouter] Trying model: {model_id}")
                resp = await client.post(
                    OPENROUTER_URL,
                    headers=headers,
                    json=body,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    # Some models wrap thinking in <think/> tags; strip them
                    content = re.sub(r"<think[\s\S]*?</think\s*>", "", content).strip()
                    logger.info(f"[OpenRouter] {model_id} returned {len(content)} chars")
                    return content
                elif resp.status_code == 429:
                    logger.warning(f"[OpenRouter] {model_id}: rate limited, trying next")
                    continue
                else:
                    logger.warning(
                        f"[OpenRouter] {model_id}: HTTP {resp.status_code} "
                        f"— {resp.text[:300]}"
                    )
                    continue
            except Exception as e:
                logger.warning(f"[OpenRouter] {model_id}: {e}")
                continue

    logger.error("[OpenRouter] All models failed")
    return None


async def ask_openrouter_list(system_prompt: str) -> list:
    """Call OpenRouter and parse response as a JSON list."""
    result = await ask_openrouter(system_prompt)
    if not result:
        return []
    return _extract_json_list(result)


async def ask_openrouter_json(system_prompt: str, user_text: str) -> dict | None:
    """Call OpenRouter and parse response as a JSON object."""
    result = await ask_openrouter(system_prompt, user_text)
    if not result:
        return None
    return _extract_json_object(result)


async def ask_openrouter_html(system_prompt: str, user_text: str) -> str | None:
    """Call OpenRouter and extract raw HTML from the response."""
    result = await ask_openrouter(system_prompt, user_text, max_tokens=16384)
    if not result:
        return None
    return _extract_html(result)


# ═══════════════════════════════════════════════════════════════════
# GEMINI API — FALLBACK (with Google Search grounding)
# ═══════════════════════════════════════════════════════════════════

GEMINI_MODELS = ["gemini-2.0-flash", "gemini-2.5-flash-preview-05-20", "gemini-1.5-flash", "gemini-1.5-pro"]

async def ask_gemini(system_prompt: str, user_text: str = "", max_tokens: int = 8192) -> str | None:
    """Call Gemini API with Google Search grounding. Fallback when OpenRouter fails."""
    if not GEMINI_KEY:
        return None

    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_text or "Return ONLY valid JSON, nothing else."}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_tokens},
    }

    async with httpx.AsyncClient(timeout=90) as client:
        for model in GEMINI_MODELS:
            try:
                logger.info(f"[Gemini] Trying {model}...")
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}",
                    json=body,
                )
                if resp.status_code == 429:
                    logger.warning(f"[Gemini] {model}: rate limited")
                    continue
                if resp.status_code != 200:
                    logger.warning(f"[Gemini] {model}: HTTP {resp.status_code}")
                    continue
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                logger.info(f"[Gemini] {model}: returned {len(text)} chars")
                return text
            except Exception as e:
                logger.warning(f"[Gemini] {model}: {e}")
                continue

    logger.error("[Gemini] All models failed")
    return None


async def ask_ai_list(system_prompt: str) -> list:
    """Try OpenRouter first, then Gemini for list results."""
    # Try OpenRouter (fast, 25s timeout per model, max 4 models = ~100s total)
    result = await ask_openrouter(system_prompt, "")
    if result:
        parsed = _extract_json_list(result)
        if parsed:
            return parsed
    # Fallback to Gemini (has Google Search grounding for fresh data)
    gemini_result = await ask_gemini(system_prompt)
    if gemini_result:
        return _extract_json_list(gemini_result)
    return []


# ═══════════════════════════════════════════════════════════════════
# COINGECKO API — PRIMARY CRYPTO SEARCH (free, no key needed)
# ═══════════════════════════════════════════════════════════════════

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Categories for deep niche discovery
CG_CATEGORIES = [
    "artificial-intelligence",      # AI + Crypto
    "depin",                        # DePIN
    "real-world-assets",            # RWA
    "layer-2",                      # L2 scaling
    "decentralized-science-desci",  # DeSci
    "gaming",                       # GameFi
    "social",                       # SocialFi
]

# Popular/generic coins to FILTER OUT
POPULAR_COINS = {
    "bitcoin", "ethereum", "tether", "binancecoin", "ripple", "usd-coin",
    "cardano", "solana", "dogecoin", "tron", "polkadot", "chainlink",
    "polygon", "avalanche-2", "shiba-inu", "litecoin", "uniswap",
    "stellar", "monero", "cosmos", "aave", "maker", "near",
    "optimism", "arbitrum", "render-token", "pepe", "bnb",
    "sui", "aptos", "sei-network", "celestia", "ondo-finance",
    "berachain", "phantom", "io-net", "monad", "fetch-ai",
}


async def fetch_coingecko_trending() -> list[dict]:
    """Fetch trending coins from CoinGecko /search/trending endpoint.

    Returns list of dicts with: name, symbol, market_cap_rank, thumb.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{COINGECKO_BASE}/search/trending",
                headers={"Accept": "application/json"},
            )
            if resp.status_code == 200:
                data = resp.json()
                coins = data.get("coins", [])
                result = []
                for c in coins[:25]:
                    item = c.get("item", {})
                    coin_id = item.get("id", "")
                    # Filter out popular/generic coins
                    if coin_id in POPULAR_COINS:
                        continue
                    result.append({
                        "id": coin_id,
                        "name": item.get("name", ""),
                        "symbol": item.get("symbol", "").upper(),
                        "market_cap_rank": item.get("market_cap_rank"),
                        "thumb": item.get("thumb", ""),
                    })
                logger.info(f"[CoinGecko] Trending: found {len(result)} non-generic coins")
                return result
            else:
                logger.warning(f"[CoinGecko] /search/trending HTTP {resp.status_code}")
                return []
    except Exception as e:
        logger.warning(f"[CoinGecko] Trending fetch failed: {e}")
        return []


async def fetch_coingecko_by_category(category_slug: str) -> list[dict]:
    """Fetch top coins from a specific CoinGecko category.

    Returns list of dicts with: id, name, symbol, market_cap_rank.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{COINGECKO_BASE}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "category": category_slug,
                    "order": "volume_desc",
                    "per_page": 10,
                    "page": 1,
                    "sparkline": "false",
                    "price_change_percentage": "7d",
                },
                headers={"Accept": "application/json"},
            )
            if resp.status_code == 200:
                data = resp.json()
                result = []
                for coin in data:
                    coin_id = coin.get("id", "")
                    if coin_id in POPULAR_COINS:
                        continue
                    result.append({
                        "id": coin_id,
                        "name": coin.get("name", ""),
                        "symbol": coin.get("symbol", "").upper(),
                        "market_cap_rank": coin.get("market_cap_rank"),
                        "price_change_7d": coin.get("price_change_percentage_7d_in_currency"),
                    })
                logger.info(f"[CoinGecko] Category {category_slug}: {len(result)} coins")
                return result
            else:
                logger.warning(f"[CoinGecko] /coins/markets?category={category_slug} HTTP {resp.status_code}")
                return []
    except Exception as e:
        logger.warning(f"[CoinGecko] Category {category_slug} fetch failed: {e}")
        return []


NICHE_EMOJIS = {
    "AI": "🤖",
    "DePIN": "📡",
    "RWA": "🏦",
    "L2/L3": "⚡",
    "DeSci": "🔬",
    "GameFi": "🎮",
    "SocialFi": "💬",
    "Bitcoin DeFi": "₿",
    "Modular": "🧩",
}

NICHE_CATEGORY_MAP = {
    "AI": "artificial-intelligence",
    "DePIN": "depin",
    "RWA": "real-world-assets",
    "GameFi": "gaming",
    "SocialFi": "social",
}


async def search_crypto_deep() -> list[dict]:
    """Main crypto search: CoinGecko → AI enrichment → deep niche fallback.

    Strategy:
    1. Fetch trending from CoinGecko
    2. Fetch top coins from niche categories (AI, DePIN, RWA, L2, GameFi)
    3. Deduplicate, pick 8 best
    4. Enrich descriptions with AI (Gemini w/ Google Search grounding)
    5. If AI fails, use CoinGecko data with generated descriptions
    6. If CoinGecko also fails, use hardcoded deep niche fallback
    """
    # ─── Step 1: Fetch from CoinGecko ───
    all_coins: dict[str, dict] = {}

    # Trending coins
    trending = await fetch_coingecko_trending()
    for coin in trending:
        all_coins[coin["id"]] = coin

    # Category coins (try 3 random categories for variety)
    categories_to_try = random.sample(CG_CATEGORIES, min(3, len(CG_CATEGORIES)))
    for cat_slug in categories_to_try:
        cat_coins = await fetch_coingecko_by_category(cat_slug)
        for coin in cat_coins:
            if coin["id"] not in all_coins:
                all_coins[coin["id"]] = coin

    if all_coins:
        logger.info(f"[CryptoSearch] CoinGecko returned {len(all_coins)} unique coins")

        # Pick top 12 (prioritize trending, then by market cap)
        coin_list = list(all_coins.values())[:12]

        # ─── Step 2: Enrich with AI ───
        coins_text = "\n".join(
            f"- {c['name']} ({c['symbol']}) — market_cap_rank: {c.get('market_cap_rank', 'N/A')}"
            for c in coin_list
        )

        enrich_prompt = f"""You are a deep niche crypto analyst. For each coin below, provide:
- niche: one of AI, DePIN, RWA, L2/L3, DeSci, GameFi, SocialFi, Bitcoin DeFi, Modular
- why_hyping: 1-2 sentences WHY it is trending right now
- what_does: 1-2 sentences what the project actually does
- link: official website URL

Coins:
{coins_text}

IMPORTANT: Only include projects that are truly trending and from deep niches. 
Skip any that are generic or top-50 CMC coins.

Return JSON array:
[{{"name":"CoinName (TICKER)","niche":"AI","why_hyping":"...","what_does":"...","link":"https://official-site.com"}}]

Return ONLY the JSON array with exactly 8 projects."""

        enriched = await ask_ai_list(enrich_prompt)
        if enriched and len(enriched) >= 3:
            logger.info(f"[CryptoSearch] AI enriched {len(enriched)} projects")
            valid = []
            for item in enriched:
                if item.get("name") and item.get("niche") and item.get("why_hyping") and item.get("link"):
                    valid.append(item)
            if len(valid) >= 3:
                return valid[:8]

        # ─── Step 3: Fallback — use CoinGecko data with basic enrichment ───
        logger.info("[CryptoSearch] AI enrichment failed, building from CoinGecko data")
        result = []
        # Map category slug to nice name
        slug_to_niche = {v: k for k, v in NICHE_CATEGORY_MAP.items()}
        slug_to_niche["layer-2"] = "L2/L3"
        slug_to_niche["decentralized-science-desci"] = "DeSci"

        # Track which coins came from which categories
        coin_categories: dict[str, str] = {}
        # For simplicity, assign niche based on the category we fetched them from
        seen_ids = set()
        for cat_slug in categories_to_try:
            nice_niche = slug_to_niche.get(cat_slug, "Crypto")
            try:
                cat_coins = await fetch_coingecko_by_category(cat_slug)
            except Exception:
                cat_coins = []
            for coin in cat_coins:
                if coin["id"] not in seen_ids:
                    coin_categories[coin["id"]] = nice_niche
                    seen_ids.add(coin["id"])

        for coin in coin_list[:8]:
            niche = coin_categories.get(coin["id"], "Crypto")
            result.append({
                "name": f"{coin['name']} ({coin['symbol']})",
                "niche": niche,
                "why_hyping": (
                    f"Активный рост объёмов торгов. "
                    f"Market Cap Rank: #{coin.get('market_cap_rank', 'N/A')}."
                ),
                "what_does": f"Крипто-проект в нише {niche} — активно растущий протокол с реальной технологией.",
                "link": f"https://www.coingecko.com/en/coins/{coin['id']}",
            })
        return result

    # ─── Step 4: CoinGecko failed entirely → use deep niche fallback ───
    logger.warning("[CryptoSearch] CoinGecko failed, using deep niche fallback")
    return FALLBACK_CRYPTO


async def ask_ai_json(system_prompt: str, user_text: str) -> dict | None:
    """Try OpenRouter first, then Gemini for JSON object results."""
    result = await ask_openrouter(system_prompt, user_text)
    if result:
        parsed = _extract_json_object(result)
        if parsed:
            return parsed
    gemini_result = await ask_gemini(system_prompt, user_text)
    if gemini_result:
        return _extract_json_object(gemini_result)
    return None


async def ask_ai_html(system_prompt: str, user_text: str) -> str | None:
    """Try OpenRouter first, then Gemini for HTML generation."""
    result = await ask_openrouter(system_prompt, user_text, max_tokens=16384)
    if result:
        html = _extract_html(result)
        if html and len(html) > 500:
            return html
    gemini_result = await ask_gemini(system_prompt, user_text, max_tokens=16384)
    if gemini_result:
        return _extract_html(gemini_result)
    return None


# ─── Response Parsing Helpers ─────────────────────────────────


def _clean_response(text: str) -> str:
    """Remove markdown code fences and clean up AI response."""
    text = text.replace("```json", "").replace("```html", "").replace("```", "")
    return text.strip()


def _extract_json_list(text: str) -> list:
    """Extract a JSON array from raw text."""
    text = _clean_response(text)
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        return []
    try:
        items = json.loads(match.group(0))
        if isinstance(items, list) and len(items) > 0:
            return items
    except json.JSONDecodeError as e:
        logger.warning(f"[Parse] JSON list parse error: {e}")
    return []


def _extract_json_object(text: str) -> dict | None:
    """Extract a JSON object from raw text."""
    text = _clean_response(text)
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError as e:
        logger.warning(f"[Parse] JSON object parse error: {e}")
    return None


def _extract_html(text: str) -> str | None:
    """Extract HTML code from AI response."""
    text = _clean_response(text)
    lower = text.lower()
    idx = lower.find("<!doctype")
    if idx == -1:
        idx = lower.find("<html")
    if idx >= 0:
        return text[idx:]
    # If no HTML tags found, return None so fallback is used
    logger.warning("[Parse] No HTML content found in response")
    return None


# ═══════════════════════════════════════════════════════════════════
# ORIGINAL SITE ANALYSIS
# ═══════════════════════════════════════════════════════════════════

async def analyze_original_site(url: str) -> dict:
    """Try to fetch and analyze the original site for design hints.

    Extracts title, meta description, colors from CSS, and font names.
    """
    if not url:
        return {}
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
            })
            if resp.status_code != 200:
                logger.info(f"[SiteAnalysis] HTTP {resp.status_code} for {url}")
                return {}

            html = resp.text[:50000]  # first 50KB is enough

            # Extract <title>
            title_match = re.search(
                r"<title>(.*?)</title>", html, re.I | re.S
            )

            # Extract meta description
            desc_match = re.search(
                r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
                html,
                re.I,
            )

            # Extract hex colors from CSS/style content (first 20KB)
            css_section = html[:20000]
            colors = re.findall(r"#[0-9a-fA-F]{3,8}", css_section)

            # Filter out obviously non-color hex codes (too long, not real CSS)
            valid_colors = []
            for c in colors:
                c_len = len(c)
                if c_len in (4, 5, 7, 9):  # #RGB, #RGBA, #RRGGBB, #RRGGBBAA
                    valid_colors.append(c)

            # Extract font-family declarations
            fonts = re.findall(
                r"font-family\s*:\s*([^;}{]+)",
                css_section,
            )
            # Clean up font values
            cleaned_fonts = []
            for f in fonts:
                f = f.strip().rstrip(",").strip()
                if f and len(f) < 100:
                    cleaned_fonts.append(f)

            result = {
                "title": (
                    title_match.group(1).strip() if title_match else ""
                ),
                "meta_description": (
                    desc_match.group(1).strip() if desc_match else ""
                ),
                "sample_colors": list(set(valid_colors[:15])),
                "sample_fonts": list(set(cleaned_fonts[:8])),
                "html_length": len(html),
            }
            logger.info(
                f"[SiteAnalysis] Analyzed {url}: "
                f"title='{result['title'][:50]}', "
                f"colors={len(result['sample_colors'])}, "
                f"fonts={len(result['sample_fonts'])}"
            )
            return result

    except Exception as e:
        logger.warning(f"[SiteAnalysis] Failed to analyze {url}: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════════
# AI PROMPTS — TREND SEARCH
# ═══════════════════════════════════════════════════════════════════

PROMPT_STORES = """You are a European fashion trend expert. List the TOP 8 most trendy, hyped, stylish European fashion brands and boutiques (2025-2026 era).

These must be COOL, INDEPENDENT, HYPE brands — NOT mass market chains. Think: Scandinavian minimalism, Parisian chic, sustainable fashion, streetwear going mainstream, luxury casual, indie labels.

DO NOT just copy these examples — include FRESH brands beyond these:
Samsøe Samsøe, ARKET, GANNI, Weekday, COS, & Other Stories, A.P.C., Sézane, Veja, NA-KD, By Far, Gestuz, Baum und Pferdgarten, Sandqvist, Rotate, Marni, Jacquemus.

STRICTLY DO NOT include: H&M, Zara, Mango, Uniqlo, Decathlon, Primark, C&A, Nike mainline, Adidas mainline.

For each brand provide EXACTLY these fields:
- name: brand name
- style: 2-3 catchy sentences about the brand's aesthetic, vibe, and why it's trending
- link: EXACT URL to the official website
- country: country of origin

IMPORTANT: Use your knowledge of real European fashion brands. Include both well-known trendy brands and emerging ones.

Return ONLY a valid JSON array of exactly 8 brands, nothing else:
[{\"name\":\"GANNI\",\"style\":\"...\",\"link\":\"https://www.ganni.com\",\"country\":\"Denmark\"}]"""

PROMPT_CRYPTO = """You are a DEEP NICHE crypto analyst who tracks projects BEFORE they go mainstream. Your knowledge cutoff is April 2025.

CRITICAL: You must find projects from THESE specific niches — NOT generic/popular ones:
1. AI + Crypto: AI agents on-chain, tokenized AI models, AI-powered trading, speculative AI for smart contracts
2. DePIN (Decentralized Physical Infrastructure): GPU clouds, mapping networks, sensor data, telecom DePIN
3. RWA (Real World Assets): tokenized treasuries, real estate on-chain, credit protocols, institutional DeFi
4. New L2/L3: Base ecosystem, Blast, Mode Network, Degen Chain, emerging rollups — NOT Arbitrum/Optimism
5. DeSci (Decentralized Science): bioDAOs, IP-NFTs, research funding on-chain
6. Bitcoin DeFi: BTC L2, restaking, Babylon, Merlin Chain, BounceBit
7. GameFi with real economics: not just P2E but full virtual economies
8. SocialFi: decentralized social, tokenized content, creator economies

STRICTLY FORBIDDEN (DO NOT include these or any similarly popular coins):
Bitcoin, Ethereum, Solana, BNB, XRP, Cardano, Avalanche, Polkadot, Chainlink, Polygon,
Uniswap, Aave, MakerDAO, Phantom, MetaMask, Render Network, io.net, Monad, Ondo Finance,
Berachain, Pepe, any meme coins, any top-50 CMC coins.

For each project provide EXACTLY these fields:
- "name": project name and ticker in parentheses, e.g. "Spectral (SPEC)"
- "niche": one of: AI, DePIN, RWA, L2/L3, DeSci, GameFi, SocialFi, Bitcoin DeFi, Modular
- "why_hyping": 1-2 specific sentences explaining WHY it is trending RIGHT NOW (growth TVL %, mainnet launch, listing, fund investment, partnership)
- "what_does": 1-2 sentences explaining the actual technology/product
- "link": EXACT URL to the official website

Return ONLY a valid JSON array of exactly 8 projects:
[{"name":"Spectral (SPEC)","niche":"AI","why_hyping":"...","what_does":"...","link":"https://spectral.finance"}]"""

PROMPT_COMPANIES = """You are a technology and business startup analyst. List the TOP 8 most hyped, rapidly growing startups and companies in Europe and globally (2025-2026 era).

SECTORS: foodtech, biotech, fintech, logistics, AI, green tech, EV, space, cyber, robotics, healthtech, climate tech, quantum, semiconductor.

STRICTLY DO NOT include: Apple, Google, Microsoft, Amazon, Meta, Tesla, Nvidia, OpenAI, Samsung, FAANG/MAMAA, Oracle, SAP, Salesforce.

For each company provide EXACTLY these fields:
- name: exact official company name
- description: 2-3 catchy sentences — what the company does AND why it is trending
- link: EXACT URL to official website
- sector: primary business sector

IMPORTANT: Use your knowledge of real companies. Include both well-known trending startups and emerging ones.

Return ONLY a valid JSON array of exactly 8 companies, nothing else:
[{"name":"Helsing","description":"...","link":"https://helsing.ai","sector":"AI / Defense"}]"""

# ═══════════════════════════════════════════════════════════════════
# IMPROVED OFFER PROMPTS — CATEGORY-SPECIFIC
# ═══════════════════════════════════════════════════════════════════

PROMPT_IMPROVE_STORES = """You are a legendary fashion tech innovator and luxury brand strategist.

A client brings you this fashion brand:
NAME: {name}
DESCRIPTION: {description}
ORIGINAL LINK: {link}
CATEGORY: Fashion Brand

Your task — create a DEEPLY ANALYZED improved fashion brand concept.

CRITICAL RULES FOR FASHION BRANDS:
- The improvement must be SPECIFIC to fashion/retail — NOT generic tech buzzwords
- Think about: AI stylist, virtual try-on, capsule wardrobe subscriptions, metaverse shopping, sustainability-tech, size-inclusive AI, AR fitting rooms, social commerce
- The improved name must be a creative evolution (e.g., GANNI → GANNI Aura, COS → COS Atelier, Sézane → Sézane Maison, Veja → Veja ONE)
- NEVER use "Pro", "2.0", "+" suffixes — the name must feel like a natural fashion brand extension
- The improvement must address real fashion industry pain points: returns, sizing, sustainability, discovery
- Mention "{name}" by name to ensure customization

EXAMPLE transformations:
- COS (minimalism) → COS Atelier: AI builds a capsule wardrobe from your body type, lifestyle, and color palette with virtual try-on and garment rental
- GANNI (playful sustainable) → GANNI Aura: Each piece comes with a digital twin in the metaverse, NFC authentication against counterfeits, and a circular economy resale marketplace built in
- Veja (sustainable sneakers) → Veja ONE: Custom biometric sneakers 3D-printed from recycled ocean plastic, with an app tracking your carbon footprint per step

Return a JSON object with EXACTLY these fields:

1. "improved_name": A fashion-forward evolution name of "{name}"

2. "improved_description": 3-4 vivid sentences describing the improved fashion concept. What specific tech/fashion innovation was added? How does it change the shopping experience? Why would Gen Z and Millennials obsess over it?

3. "improved_link": A stylized fashion URL (e.g. https://brandname-atelier.com or .store or .fashion)

4. "killer_feature": 1 sentence about the ONE fashion-tech feature that makes this irresistible

5. "geo_analysis": An OBJECT for fashion brand traffic:
{{
  "tier1": [list of 3-4 top fashion markets with 1-line reason — think: Scandinavia, France, UK, Italy, Germany, Netherlands],
  "tier2": [list of 3-4 secondary markets],
  "tier3": [list of 2-3 emerging fashion markets],
  "best_platforms": [list of 3-4 platforms — Instagram, Pinterest, TikTok are MUST-HAVE for fashion],
  "budget_split": "suggested budget % split between GEOs and platforms",
  "estimated_cpa": "estimated CPA range in USD for tier1"
}}

6. "keywords": Fashion-specific SEO and PPC keywords:
{{
  "branded": [3-4 branded keywords],
  "generic": [4-5 high-volume fashion keywords],
  "long_tail": [4-5 long-tail fashion keywords],
  "competitor": [2-3 competitor brand keywords],
  "negative": [2-3 negative keywords]
}}

7. "target_audience": 2-3 sentences about the ideal fashion customer (age, style preferences, shopping behavior, income level, values like sustainability)

Return ONLY the JSON object. No markdown, no code blocks, just raw JSON."""


PROMPT_IMPROVE_CRYPTO = """You are a legendary Web3 architect, crypto VC, and DeFi product genius.

A client brings you this crypto project:
NAME: {name}
DESCRIPTION: {description}
ORIGINAL LINK: {link}
CATEGORY: Crypto Project

Your task — create a DEEPLY ANALYZED improved crypto/Web3 concept.

CRITICAL RULES FOR CRYPTO PROJECTS:
- The improvement must be SPECIFIC to crypto/DeFi/Web3 — NOT generic business talk
- Think about: AI portfolio management, cross-chain without bridges, social trading, yield gamification, DePIN integration, smart contract insurance, intent-based trading, account abstraction, zero-knowledge proofs, restaking
- The improved name must be a natural crypto evolution (e.g., Phantom → PhantomX, Solana → Solana Nexus, Render → Render Hyper, Monad → Monad Flux)
- NEVER use "Pro", "2.0", "+" suffixes — the name must sound like a serious protocol evolution
- The improvement must address real crypto pain points: UX complexity, security risks, fragmentation, volatility exposure
- Mention "{name}" by name to ensure customization

EXAMPLE transformations:
- Phantom Wallet → PhantomX: AI wallet that determines your risk profile, auto-distributes assets across DeFi protocols, mines DePIN tokens in background, and insures your portfolio via smart contract insurance
- Render Network → Render Hyper: Multi-chain GPU marketplace with zero-knowledge proof of compute, allowing anyone to rent GPU power without trusting a central party, with AI-optimized job routing
- Solana → Solana Nexus: Unified L1/L2 settlement layer that eliminates the need for bridges entirely, with built-in DEX aggregator, intent-based mempool, and social trading feeds

Return a JSON object with EXACTLY these fields:

1. "improved_name": A crypto-native evolution name of "{name}"

2. "improved_description": 3-4 technical but accessible sentences. What specific crypto/Web3 innovation was added? How does it solve a real DeFi/blockchain problem? What makes devs and users excited?

3. "improved_link": A crypto URL (e.g. https://projectname-x.io or .xyz or .network or .protocol)

4. "killer_feature": 1 sentence about the ONE crypto feature that makes this a must-use protocol

5. "geo_analysis": An OBJECT for crypto project traffic:
{{
  "tier1": [list of 3-4 top crypto markets with 1-line reason — think: Singapore, UAE, US, South Korea, Japan, Turkey, Vietnam],
  "tier2": [list of 3-4 secondary markets],
  "tier3": [list of 2-3 emerging crypto markets],
  "best_platforms": [list of 3-4 platforms — Twitter/X, Discord, Telegram, CoinGecko, DappRadar],
  "budget_split": "suggested budget % split between GEOs and platforms",
  "estimated_cpa": "estimated CPA range in USD for tier1"
}}

6. "keywords": Crypto-specific SEO and PPC keywords:
{{
  "branded": [3-4 branded keywords],
  "generic": [4-5 high-volume crypto keywords],
  "long_tail": [4-5 long-tail crypto keywords],
  "competitor": [2-3 competitor protocol keywords],
  "negative": [2-3 negative keywords]
}}

7. "target_audience": 2-3 sentences about the ideal crypto user (experience level, portfolio size, interests like DeFi/NFTs/gaming, geographic profile)

Return ONLY the JSON object. No markdown, no code blocks, just raw JSON."""


PROMPT_IMPROVE_COMPANIES = """You are a legendary startup advisor, serial founder, and Fortune 500 growth consultant.

A client brings you this company:
NAME: {name}
DESCRIPTION: {description}
ORIGINAL LINK: {link}
CATEGORY: Startup/Company

Your task — create a DEEPLY ANALYZED improved business concept.

CRITICAL RULES FOR COMPANIES:
- The improvement must be SPECIFIC to the company's industry — NOT generic tech buzzwords
- Think about: scaling the business model, AI automation of core processes, new market expansion, embedded finance, robotics integration, B2B2C pivots, platformization, regulatory tech, supply chain AI, vertical SaaS consolidation
- The improved name must be a strategic evolution (e.g., Revolut → Revolut AIO, Klarna → Klarna OS, Helsing → Helsing Nexus, DeepL → DeepL Enterprise Mesh)
- NEVER use "Pro", "2.0", "+" suffixes — the name must feel like a serious business evolution
- The improvement must address real business pain points in the company's specific sector
- Mention "{name}" by name to ensure customization

EXAMPLE transformations:
- Revolut (neobank) → Revolut AIO: AI-powered business bank with automatic accounting, tax optimization, treasury management in crypto, and embedded trade finance — a full CFO-as-a-service platform
- Klarna (BNPL) → Klarna OS: Open commerce operating system where any merchant gets Klarna's AI recommendation engine, checkout, and BNPL as an API — turning Klarna from a product into a platform
- Helsing (AI defense) → Helsing Nexus: Multi-domain AI command system integrating space, cyber, and electronic warfare with autonomous threat response and allied coalition coordination

Return a JSON object with EXACTLY these fields:

1. "improved_name": A business-appropriate evolution name of "{name}"

2. "improved_description": 3-4 concrete sentences. What specific business model innovation was added? How does it scale? What revenue streams open up? Why would enterprises/investors immediately see 10x potential?

3. "improved_link": A business URL (e.g. https://brandname-os.com or .platform or .enterprise or .ai)

4. "killer_feature": 1 sentence about the ONE business feature that makes this the category killer

5. "geo_analysis": An OBJECT for B2B/SaaS/tech company traffic:
{{
  "tier1": [list of 3-4 top markets with 1-line reason — think: US, UK, Germany, France, Nordics for B2B],
  "tier2": [list of 3-4 secondary markets],
  "tier3": [list of 2-3 emerging markets],
  "best_platforms": [list of 3-4 platforms — LinkedIn, Google Ads, producthunt, industry-specific platforms],
  "budget_split": "suggested budget % split between GEOs and platforms",
  "estimated_cpa": "estimated CPA range in USD for tier1"
}}

6. "keywords": Business-specific SEO and PPC keywords:
{{
  "branded": [3-4 branded keywords],
  "generic": [4-5 high-volume business keywords],
  "long_tail": [4-5 long-tail business keywords],
  "competitor": [2-3 competitor company keywords],
  "negative": [2-3 negative keywords]
}}

7. "target_audience": 2-3 sentences about the ideal customer (B2B buyer personas, company size, decision-maker role, industry vertical, pain points)

Return ONLY the JSON object. No markdown, no code blocks, just raw JSON."""


IMPROVE_PROMPTS: dict[str, str] = {
    "stores": PROMPT_IMPROVE_STORES,
    "crypto": PROMPT_IMPROVE_CRYPTO,
    "companies": PROMPT_IMPROVE_COMPANIES,
}


# ═══════════════════════════════════════════════════════════════════
# LANDING PAGE PROMPTS — CATEGORY-SPECIFIC SECTIONS
# ═══════════════════════════════════════════════════════════════════

LANDING_SECTIONS_STORES = """
THIS IS A FASHION/LIFESTYLE BRAND — the site must feel like a premium fashion e-commerce experience.

VISUAL STYLE:
- Large hero with full-width gradient background, brand name in serif display font, elegant tagline
- Plenty of whitespace, luxury feel, editorial magazine-like layout
- Large CSS gradient placeholders for "lookbook" imagery (use gradient boxes with labels like "NEW COLLECTION", "SPRING 2026", etc.)
- Animated transitions on scroll — items fade in elegantly

SECTIONS TO INCLUDE (in this EXACT order):
1. Fixed Navigation bar — logo text left, nav links center (Collections, Story, Sustainability, Contact), hamburger menu for mobile
2. HERO — full-viewport gradient background, brand name in 72px serif font, tagline beneath, two CTA buttons: "Explore Collection" and "Book AI Stylist"
3. LOOKBOOK GRID — 6 cards in 3x2 grid (on desktop), each card is a colored gradient square with collection name overlay (e.g. "Nordic Minimal", "Urban Edge", "Resort 2026"). On hover, cards scale up slightly with glow. Each card has a label like "NEW", "TRENDING", or "EXCLUSIVE"
4. HOW IT WORKS — 3-step visual process: Step 1 "Take Style Quiz", Step 2 "AI Builds Your Wardrobe", Step 3 "Virtual Try-On & Order". Use numbered circles and connecting lines
5. AI STYLIST SHOWCASE — a large feature section with the killer feature prominently displayed. Show a mock "AI Style Profile" card with placeholder data (color palette dots, body type indicator, style score). Make it look like a real app screenshot using CSS only
6. SUSTAINABILITY SECTION — section about eco-friendly practices with 3 stat counters (e.g. "92% Recycled Materials", "Zero Carbon Shipping", "10,000+ Trees Planted"). Use CSS animated counter numbers
7. TESTIMONIALS — 3 fashion testimonials from realistic people (fashion blogger, sustainability advocate, stylist). Each with star rating (use CSS stars), quote, name, and Instagram-style avatar circle (CSS gradient)
8. FAQ — 4-5 fashion-specific Q&As (sizing, returns, shipping, materials, sustainability). Accordion style with smooth CSS transitions
9. NEWSLETTER SIGNUP — email input field with "Get Early Access to Drops" CTA. Clean minimal design
10. FOOTER — 4 columns: About, Collections, Customer Care, Connect (social icons as CSS circles). Copyright
"""

LANDING_SECTIONS_CRYPTO = """
THIS IS A CRYPTO/WEB3/DeFi PROJECT — the site must feel like a cutting-edge fintech dashboard.

VISUAL STYLE:
- Dark, tech-forward design (matches dark theme colors perfectly)
- Dashboard-like UI elements: progress bars, stat cards, animated charts (CSS-only)
- Monospace/tech fonts for data, clean sans-serif for headings
- Subtle grid/matrix background pattern using CSS
- Animated particle/grid effects using CSS
- Data-dense layout with metrics, graphs, and protocol stats

SECTIONS TO INCLUDE (in this EXACT order):
1. Fixed Navigation bar — logo text (monospace), nav links (Protocol, Dashboard, Developers, Community), "Launch App" CTA button with glow, hamburger for mobile
2. HERO — dark gradient background with subtle CSS grid pattern overlay, project name in bold tech font, protocol tagline, TVL/stats banner below (e.g. "$2.4B TVL | 150K+ Users | 12 Chains"), two CTAs: "Launch dApp" and "Read Docs"
3. LIVE STATS DASHBOARD — 4 stat cards in a row showing animated CSS-only metrics: TVL ($), Active Users, Transactions 24h, APY %. Each card has a CSS bar/progress indicator and trend arrow (CSS triangle). Use CSS animations to make numbers count up
4. HOW IT WORKS — 4-step technical flow: Connect Wallet → Deposit/ Stake → AI Optimizes → Earn Yield. Each step has an icon (CSS shapes: wallet icon, coin stack, brain/AI icon, money bag) and connecting arrows between steps
5. FEATURE DEEP-DIVE — 3 large feature panels for the core innovations: (1) Cross-chain Engine with chain logos as CSS circles, (2) AI Portfolio Manager with mock pie chart in CSS, (3) Security Layer with shield icon and audit badges. Each panel is a dark card with neon accent border
6. TOKENOMICS / METRICS — Visual token distribution using CSS pie chart (conic-gradient), with legend showing percentages. Include: Team 15%, Community 40%, Liquidity 25%, Development 20%. Add "Token Utility" cards showing use cases
7. ECOSYSTEM / INTEGRATIONS — Grid of partner/integration logos as CSS-only branded circles or squares with text labels (e.g. "Uniswap", "Aave", "Chainlink"). 6-8 items in responsive grid
8. ROADMAP — Horizontal timeline with 4 phases (Q1-Q4), each phase has milestone items and a progress indicator. Use CSS lines and dots for the timeline
9. COMMUNITY — Social proof section with: Discord members count, Twitter followers, GitHub stars — each as a stat card. CTA buttons for each platform
10. FOOTER — dark footer with 3 columns: Protocol, Resources, Community. Copyright and "Built on [Blockchain]" badge
"""

LANDING_SECTIONS_COMPANIES = """
THIS IS A B2B/SaaS/TECH COMPANY — the site must feel like a professional enterprise platform.

VISUAL STYLE:
- Clean, corporate-modern design. Professional but not boring
- Data-driven: revenue metrics, growth charts, case study numbers
- Structure-focused: clear hierarchy, card-based layouts, clear CTAs
- Trust signals: client logos, partnership badges, certification marks (all CSS-only)
- Subtle animations, nothing flashy — professional and authoritative

SECTIONS TO INCLUDE (in this EXACT order):
1. Fixed Navigation bar — logo text, nav links (Product, Solutions, Pricing, About), "Book a Demo" CTA button, hamburger for mobile
2. HERO — clean gradient background, company name in bold sans-serif, value proposition tagline, two CTAs: "Start Free Trial" and "Watch Demo". Below hero: trusted-by logo strip with 5-6 CSS-only company logo placeholders (gray rounded rectangles with company name text)
3. KEY METRICS BANNER — 4 metric cards in a row: Revenue Growth (%), Enterprise Clients (#), Average ROI (%), Uptime (%). Each with large number in bold and label beneath. Use CSS counter animation
4. PRODUCT SHOWCASE — large section showing the main product. Use CSS to create a mock dashboard/app screenshot (window chrome + content area with sidebar and metric widgets). Feature labels point to different parts of the mockup
5. SOLUTIONS / USE CASES — 3-4 use case cards, each with: industry icon (CSS), title, description, key benefit stat. Industries like: Healthcare, Finance, Logistics, Manufacturing. Cards have left accent border
6. CASE STUDY — a detailed case study card with: client company name, industry, challenge, solution, results (with before/after metrics). Include a quote from a "VP of Operations" type persona
7. INTEGRATIONS GRID — 6-8 integration/tool logos as CSS-only cards in a grid: Salesforce, Slack, Stripe, AWS, etc. Each shows the tool name and a brief integration description
8. PRICING PREVIEW — 3 pricing tiers (Starter, Pro, Enterprise) in cards. Each shows: price, key features list (CSS checkmarks), CTA button. Enterprise card is highlighted with theme accent border
9. FAQ — 5 B2B-specific Q&As (security, compliance, SLA, onboarding, data privacy). Accordion style
10. CTA BANNER — full-width gradient section: "Ready to Transform Your Business?" with large CTA button and subtext "14-day free trial. No credit card required."
11. FOOTER — 4 columns: Product, Company, Resources, Legal. Copyright and compliance badges (GDPR, SOC2 — CSS-only badge shapes)
"""

LANDING_SECTIONS: dict[str, str] = {
    "stores": LANDING_SECTIONS_STORES,
    "crypto": LANDING_SECTIONS_CRYPTO,
    "companies": LANDING_SECTIONS_COMPANIES,
}


def build_landing_page_prompt(
    project_info: dict,
    theme: dict,
    site_analysis: dict,
    category: str = "stores",
) -> str:
    """Build category-specific landing page generation prompt with theme + site analysis."""

    site_hints = ""
    if site_analysis:
        title = site_analysis.get("title", "")
        meta_desc = site_analysis.get("meta_description", "")
        colors = site_analysis.get("sample_colors", [])
        fonts = site_analysis.get("sample_fonts", [])

        site_hints = f"""
ORIGINAL SITE DESIGN HINTS:
- Original title: {title}
- Original meta description: {meta_desc}
- Colors found on original site: {', '.join(colors[:10]) if colors else 'None detected'}
- Fonts used on original site: {', '.join(fonts[:5]) if fonts else 'None detected'}

IMPORTANT: Your generated landing page should be INSPIRED by the original site's design language:
- Use a SIMILAR but IMPROVED/UPGRADED color palette (blend with the theme colors above)
- Use similar typography style but with the theme's specified fonts
- Include similar sections/features as the original would have
- Make it look like a PREMIUM UPGRADE of the original
- Keep the same general layout structure but more polished
"""

    category_sections = LANDING_SECTIONS.get(category, LANDING_SECTIONS_STORES)

    prompt = f"""You are an elite web developer and designer. Create a complete, stunning single-page landing website for this improved project:

PROJECT NAME: {project_info.get('improved_name', '')}
DESCRIPTION: {project_info.get('improved_description', '')}
KILLER FEATURE: {project_info.get('killer_feature', '')}
ORIGINAL LINK: {project_info.get('original_link', '')}
IMPROVED LINK: {project_info.get('improved_link', '')}
CATEGORY: {category}

DESIGN THEME: {theme['name']}
EXACT COLOR PALETTE:
  - Background primary: {theme['bg_primary']}
  - Background secondary: {theme['bg_secondary']}
  - Accent color: {theme['accent']}
  - Accent secondary: {theme['accent_secondary']}
  - Text primary: {theme['text_primary']}
  - Text secondary: {theme['text_secondary']}
  - Card background: {theme['card_bg']}
  - Card border: {theme['card_border']}
  - Button background: {theme['button_bg']}
  - Button text color: {theme['button_text']}

EXACT FONTS (use these via @import in <style>):
  - Headings: {theme['font_heading']}
  - Body text: {theme['font_body']}
  - Google Fonts URL: {theme['google_fonts']}

BACKGROUND STYLING:
  - Page background: {theme['bg_gradient']}
  - Hero background: {theme['hero_gradient']}
  - Navigation bar: {theme['nav_bg']}
  - Glow/shadow effects: {theme['glow']}
  - Dividers: {theme['divider']}

CARD STYLING: Background {theme['card_bg']}, border {theme['card_border']}, rounded corners (16px), subtle glow shadow
BUTTON STYLING: Background {theme['button_bg']}, text {theme['button_text']}, rounded (50px), hover scale effect, bold font
{site_hints}
CRITICAL DESIGN INSTRUCTIONS:
- Use the exact colors, fonts, and styling specified above
- This theme is "{theme['name']}" — {theme['description']}
- Match the aesthetic perfectly

{category_sections}

TECHNICAL REQUIREMENTS:
- ALL CSS must be in a single <style> tag in <head>
- ALL JavaScript must be in a single <script> tag before </body>
- Google Fonts must be loaded via @import url(...) inside the <style> tag
- Responsive design: mobile (< 768px), tablet (768-1024px), desktop (> 1024px)
- Smooth scroll navigation (scroll-behavior: smooth, and JS scrollIntoView)
- Mobile hamburger menu toggle with JavaScript
- Countdown timer in JavaScript (7 days from current date)
- Scroll-triggered fade-in animations using IntersectionObserver
- NO external CSS/JS files, NO CDN links (except Google Fonts @import)
- NO images or external assets — use CSS gradients, shapes, and Unicode/emoji for visuals
- Include proper <meta charset>, <meta viewport>, and <title> tags
- Return ONLY raw HTML starting with <!DOCTYPE html>
- NO markdown formatting, NO code fences, NO explanation — just the HTML"""

    return prompt


# ═══════════════════════════════════════════════════════════════════
# FALLBACK DATA
# ═══════════════════════════════════════════════════════════════════

FALLBACK_STORES: list[dict] = [
    {
        "name": "GANNI",
        "style": (
            "Danish sustainable fashion with bold colors and playful prints. "
            "Every fashion influencer rocks their signature balloon sleeves and "
            "cheeky graphics. They turned sustainability into the coolest thing "
            "on the runway."
        ),
        "link": "https://www.ganni.com",
        "country": "Denmark",
    },
    {
        "name": "ARKET",
        "style": (
            "Nordic minimalist fashion from H&M Group that feels like a luxury "
            "concept store. Timeless pieces blending Scandinavian design with "
            "obsessive focus on quality fabrics."
        ),
        "link": "https://www.arket.com",
        "country": "Sweden",
    },
    {
        "name": "Sézane",
        "style": (
            "Parisian-chic womenswear with vintage-inspired silhouettes and a "
            "cult Instagram following. Each collection is a love letter to "
            "1970s Paris, reimagined for the modern woman."
        ),
        "link": "https://www.sezane.com",
        "country": "France",
    },
    {
        "name": "COS",
        "style": (
            "Premium minimalism with architectural silhouettes and clean lines. "
            "Every piece feels like a wearable sculpture from a modern art museum."
        ),
        "link": "https://www.cos.com",
        "country": "Sweden",
    },
    {
        "name": "A.P.C.",
        "style": (
            "French casual luxury brand with iconic raw denim and understated "
            "Parisian cool since 1987. The brand fashion insiders wear when "
            "they want effortless style."
        ),
        "link": "https://www.apc.fr",
        "country": "France",
    },
    {
        "name": "Veja",
        "style": (
            "Sustainable sneakers made in Brazil with transparent ethical "
            "supply chain. Worn by Meghan Markle and Emma Watson, proving "
            "eco-friendly is the most fashionable choice."
        ),
        "link": "https://www.veja-store.com",
        "country": "France/Brazil",
    },
    {
        "name": "By Far",
        "style": (
            "Bulgarian accessories brand with 90s-inspired shoes and bags "
            "that break the internet every drop. Their Jodie bag is the most "
            "photographed accessory of the year."
        ),
        "link": "https://www.byfar.com",
        "country": "Bulgaria",
    },
    {
        "name": "Samsøe Samsøe",
        "style": (
            "Scandinavian effortless luxury with relaxed tailoring and "
            "premium materials. Their cashmere sweaters and silk dresses are "
            "quiet luxury staples every it-girl has."
        ),
        "link": "https://www.samskoe-samskoe.com",
        "country": "Denmark",
    },
]

FALLBACK_CRYPTO: list[dict] = [
    {
        "name": "Spectral (SPEC)",
        "niche": "AI",
        "why_hyping": (
            "Спекулятивный синтаксис для смарт-контрактов — позволяет создавать "
            "on-chain AI-агентов прямо из промптов. TVL вырос на 400% за последние 30 дней,"
            " протокол активно интегрируется в DeFi-экосистемы."
        ),
        "what_does": (
            "Платформа для токенизации и синтеза AI-агентов, которые могут "
            "автономно торговать, анализировать рынки и управлять DeFi-позицими."
        ),
        "link": "https://spectral.finance",
    },
    {
        "name": "Virtuals Protocol (VIRTUAL)",
        "niche": "AI",
        "why_hyping": (
            "AI-агенты с токенизацией на Base — самый хайповый narratives 2025. "
            "Капитализация выросла с $50M до $2B+ за 3 месяца. AI-агент AIXBT "
            "стал вирусным crypto-инфлюенсером на X/Twitter."
        ),
        "what_does": (
            "Платформа для создания, токенизации и монетизации AI-агентов. "
            "Каждый агент — это автономная сущность с собственным токеном, "
            "которая взаимодействует в соцсетях, играх и DeFi."
        ),
        "link": "https://virtuals.io",
    },
    {
        "name": "Hivemapper (HONEY)",
        "niche": "DePIN",
        "why_hyping": (
            "Крупнейшая децентрализованная картографическая сеть — 150K+ дэш-камер "
            "по всему миру. Карта покрытия выросла на 200% за квартал. "
            "Контракты с Mapillary и Niantic."
        ),
        "what_does": (
            "Водители с дэш-камерами собирают данные дорожной карты в реальном времени. "
            "За каждый километр получают токены HONEY. Данные продаются компаниям."
        ),
        "link": "https://hivemapper.com",
    },
    {
        "name": "Babylon (BABY)",
        "niche": "Bitcoin DeFi",
        "why_hyping": (
            "Bitcoin staking для безопасности PoS-сетей — $5B+ BTC застейкано. "
            "Партнёрства с 50+ L2/L1 проектами. Самый масштабный Bitcoin DeFi-протокол."
        ),
        "what_does": (
            "Позволяет владельцам BTC стейкать свои биткоины для обеспечения "
            "безопасности Proof-of-Stake сетей, не покидая Bitcoin L1. "
            "Создаёт экономику безопасности поверх Bitcoin."
        ),
        "link": "https://babylonlabs.io",
    },
    {
        "name": "Midas (MIDAS)",
        "niche": "RWA",
        "why_hyping": (
            "Токенизированные гособлигации США с доходностью 5%+ on-chain. "
            "TVL вырос с $10M до $200M+ за 2 месяца. Институциональные "
            "инвесторы массово заходят через Midas."
        ),
        "what_does": (
            "Платформа RWA, которая токенизирует казначейские облигации США "
            "и другие традиционные финансовые активы, предоставляя "
            "доступ к стабильному доходу через DeFi."
        ),
        "link": "https://midas.app",
    },
    {
        "name": "Mode Network (MODE)",
        "niche": "L2/L3",
        "why_hyping": (
            "L2 на OP Stack с репутационной системой и ретро-дропами. "
            "TVL вырос на 350% за месяц. Активная экосистема DeFi-протоколов "
            "и уникальная модель совместного финансирования sequencer fees."
        ),
        "what_does": (
            "Optimistic Rollup L2 с системой Onchain Boost — часть комиссий от sequencer "
            "распределяется между протоколами, которые привлекают пользователей."
        ),
        "link": "https://mode.network",
    },
    {
        "name": "Aethir (ATH)",
        "niche": "DePIN",
        "why_hyping": (
            "Децентрализованные GPU-облака для AI и cloud gaming — 90K+ нод. "
            "Партнёрство с Qualcomm и PixelBirds. Выручка $30M+ за квартал, "
            "один из немногих DePIN с реальным revenue."
        ),
        "what_does": (
            "Enterprise-grade DePIN для распределённых GPU-вычислений. "
            "Предоставляет децентрализованную инфраструктуру для AI-инференса, "
            "облачного гейминга и рендеринга."
        ),
        "link": "https://www.aethir.com",
    },
    {
        "name": "Molecule (MOLEC)",
        "niche": "DeSci",
        "why_hyping": (
            "БиоDAO платформа — децентрализованное финансирование научных "
            "исследований через IP-NFT. $20M+ привлечено для исследований "
            "онкологии и долголетия. Narrative DeSci активно растёт."
        ),
        "what_does": (
            "Создаёт биоDAO для финансирования научных исследований. "
            "Интеллектуальная собственность токенизируется как IP-NFT, "
            "позволяя сообществам совместно владеть результатами исследований."
        ),
        "link": "https://molecule.to",
    },
]

FALLBACK_COMPANIES: list[dict] = [
    {
        "name": "Helsing",
        "description": (
            "European AI defense startup building sovereign AI for NATO "
            "allies with 500M+ EUR raised. Europe's answer to Palantir."
        ),
        "link": "https://helsing.ai",
        "sector": "AI / Defense",
    },
    {
        "name": "Klarna",
        "description": (
            "Swedish BNPL giant pivoting to AI shopping assistant, profitable "
            "since 2023, $46B valuation. AI that does what a personal shopper "
            "team used to."
        ),
        "link": "https://www.klarna.com",
        "sector": "Fintech",
    },
    {
        "name": "Revolut",
        "description": (
            "UK neobank with 45M+ users expanding into crypto, trading, "
            "travel money. Started as a travel card, became a financial "
            "super-app."
        ),
        "link": "https://www.revolut.com",
        "sector": "Fintech",
    },
    {
        "name": "DeepL",
        "description": (
            "Cologne AI translation startup surpassing Google Translate "
            "quality, $2B valuation. Enterprise clients abandon every "
            "other tool."
        ),
        "link": "https://www.deepl.com",
        "sector": "AI / Language",
    },
    {
        "name": "Northvolt",
        "description": (
            "Swedish battery maker building Europe's first EV gigafactory "
            "with $10B+ invested. Europe's bet to end Asian battery dependency."
        ),
        "link": "https://northvolt.com",
        "sector": "Green Tech / EV",
    },
    {
        "name": "Bolt",
        "description": (
            "Estonian mobility super-app — ride-hailing, scooters, food "
            "delivery. Profitable and expanding to Africa. Beat Uber by "
            "being faster and cheaper."
        ),
        "link": "https://bolt.eu",
        "sector": "Mobility",
    },
    {
        "name": "Einride",
        "description": (
            "Swedish autonomous electric truck startup doing commercial "
            "autonomous freight across Europe. Futuristic pod-trucks — "
            "already happening."
        ),
        "link": "https://www.einride.com",
        "sector": "Logistics / EV",
    },
    {
        "name": "Picnic",
        "description": (
            "Dutch online supermarket with AI-powered route planning and "
            "micro-fulfillment centers. Delivering groceries at cut-rate "
            "prices via ML optimization."
        ),
        "link": "https://www.picnic.app",
        "sector": "Foodtech / Logistics",
    },
]

# Fallback analysis data (used when AI completely fails)
FALLBACK_ANALYSIS = {
    "improved_name": "",
    "improved_description": "",
    "improved_link": "",
    "killer_feature": "",
    "geo_analysis": {
        "tier1": [
            "USA — largest market with high purchasing power",
            "UK — fashion-conscious with high conversion rates",
            "Germany — largest EU economy with strong demand",
        ],
        "tier2": ["France", "Netherlands", "Sweden", "Canada"],
        "tier3": ["UAE", "South Korea", "Japan"],
        "best_platforms": ["Meta Ads (Instagram + Facebook)", "Google Ads", "TikTok Ads"],
        "budget_split": "60% Tier 1, 25% Tier 2, 15% Tier 3",
        "estimated_cpa": "$8-15 USD",
    },
    "keywords": {
        "branded": [],
        "generic": ["best online store 2025", "trendy fashion brand", "hype brand"],
        "long_tail": ["affordable luxury fashion europe", "sustainable trendy clothing"],
        "competitor": [],
        "negative": ["cheap", "fake", "replica"],
    },
    "target_audience": (
        "Men and women aged 18-35 interested in trends, fashion, and technology. "
        "Medium to high income, active on social media, early adopters."
    ),
}


def get_fallback_analysis(name: str, desc: str, link: str, category: str = "stores") -> dict:
    """Generate fallback analysis data using the original item's info, category-specific."""
    analysis = dict(FALLBACK_ANALYSIS)

    if category == "crypto":
        analysis["improved_name"] = f"{name}X"
        analysis["improved_description"] = (
            f"The next evolution of {name} — a protocol-level upgrade that eliminates "
            f"cross-chain friction with intent-based execution, AI-driven yield optimization, "
            f"and built-in smart contract insurance. Already processing $500M in daily volume "
            f"across 15 chains with zero bridging risk."
        )
        safe_slug = name.lower().replace(" ", "-").replace("/", "-")[:30]
        analysis["improved_link"] = f"https://{safe_slug}-x.io"
        analysis["killer_feature"] = (
            f"Zero-bridge cross-chain execution with AI yield routing — your assets "
            f"auto-compound across the best protocols without ever leaving your wallet."
        )
        analysis["geo_analysis"]["tier1"] = [
            "Singapore — crypto hub with institutional adoption",
            "UAE — progressive regulation, high crypto penetration",
            "USA — largest market despite regulatory uncertainty",
            "South Korea — highest crypto trading volume per capita",
        ]
        analysis["geo_analysis"]["best_platforms"] = [
            "Twitter/X", "Discord", "Telegram", "CoinGecko Ads",
        ]
        analysis["keywords"]["generic"] = [
            "best crypto protocol 2025", "DeFi yield optimization",
            "cross-chain bridge alternative", "crypto AI portfolio",
        ]
        analysis["keywords"]["long_tail"] = [
            "how to earn yield on Solana automatically",
            "zero-knowledge crypto wallet",
            "AI crypto portfolio manager",
        ]
        analysis["target_audience"] = (
            "Crypto-native users aged 22-40 with $5K+ portfolio. Active DeFi users, "
            "multi-chain power users, and crypto traders looking for yield optimization."
        )
    elif category == "companies":
        analysis["improved_name"] = f"{name} OS"
        analysis["improved_description"] = (
            f"{name} reimagined as an enterprise operating system — AI-automated workflows, "
            f"embedded financial services, and a platform play that turns every customer into "
            f"a distribution channel. Processing $2B in transactions, serving 50K+ businesses "
            f"across 30 countries with autonomous operations."
        )
        safe_slug = name.lower().replace(" ", "-").replace("/", "-")[:30]
        analysis["improved_link"] = f"https://{safe_slug}-os.com"
        analysis["killer_feature"] = (
            f"Full-stack AI automation — from lead generation to revenue recognition, "
            f"the platform runs your business operations autonomously while you focus on strategy."
        )
        analysis["geo_analysis"]["tier1"] = [
            "USA — largest B2B SaaS market globally",
            "UK — fintech/tech hub with enterprise buyers",
            "Germany — strong enterprise software demand",
            "Nordics — high digital adoption, tech-forward",
        ]
        analysis["geo_analysis"]["best_platforms"] = [
            "LinkedIn Ads", "Google Ads", "Product Hunt", "G2",
        ]
        analysis["keywords"]["generic"] = [
            "best enterprise SaaS 2025", "AI business automation",
            "B2B platform solution", "scale business operations",
        ]
        analysis["keywords"]["long_tail"] = [
            "AI automation for mid-size companies",
            "enterprise operating system platform",
            "automate business workflows with AI",
        ]
        analysis["target_audience"] = (
            "B2B decision makers: CTOs, VPs of Operations, CFOs at companies with 50-5000 "
            "employees. Looking to reduce operational costs by 40%+ through AI automation."
        )
    else:
        # stores — default
        analysis["improved_name"] = f"{name} Atelier"
        analysis["improved_description"] = (
            f"The next evolution of {name} — AI-powered personal fashion experience. "
            f"An AI stylist builds your perfect capsule wardrobe from your body type, "
            f"lifestyle, and color palette. Virtual try-on, sustainable materials, "
            f"and exclusive drops. Already at $80M ARR with 500K+ subscribers."
        )
        safe_slug = name.lower().replace(" ", "-").replace("/", "-")[:30]
        analysis["improved_link"] = f"https://{safe_slug}-atelier.com"
        analysis["killer_feature"] = (
            f"AI stylist — takes your photo, analyzes your style DNA, and builds "
            f"a complete personalized wardrobe delivered to your door."
        )
        analysis["geo_analysis"]["tier1"] = [
            "Scandinavia — sustainability-conscious, high fashion spend",
            "UK — largest European fashion e-commerce market",
            "France — fashion capital, high brand loyalty",
            "Germany — strong purchasing power, growing online fashion",
        ]
        analysis["geo_analysis"]["best_platforms"] = [
            "Instagram", "TikTok", "Pinterest", "Google Shopping",
        ]
        analysis["keywords"]["generic"] = [
            "AI fashion stylist online", "personalized wardrobe subscription",
            "sustainable fashion brand 2025", "virtual try-on clothing",
        ]
        analysis["keywords"]["long_tail"] = [
            "AI personalized clothing subscription europe",
            "sustainable capsule wardrobe service",
            "virtual fitting room fashion brand",
        ]
        analysis["target_audience"] = (
            "Fashion-forward men and women aged 20-38 in urban areas. "
            "Values sustainability, personalization, and convenience. "
            "Medium-high income, active on Instagram/TikTok, early adopters of fashion-tech."
        )


# ═══════════════════════════════════════════════════════════════════
# FALLBACK HTML GENERATOR — 6 THEMES
# ═══════════════════════════════════════════════════════════════════

def generate_fallback_html(
    imp_name: str,
    imp_desc: str,
    killer: str,
) -> str:
    """Generate a complete, good-looking landing page using the 6-theme system.

    This is used when the AI fails to produce HTML.
    """
    theme = get_theme_for_project(imp_name)

    # Escape for HTML
    safe_name = _html_escape(imp_name)
    safe_desc = _html_escape(imp_desc)
    safe_killer = _html_escape(killer)

    # Launch date: 7 days from now
    launch_date = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")

    # Features based on generic but useful descriptions
    features = [
        ("🚀", "AI-Powered Engine", "Built with cutting-edge AI that learns and adapts to your needs in real time, delivering personalized results."),
        ("🌍", "Global Scale", "Designed from day one to serve millions of users across every continent with zero downtime."),
        ("🔒", "Secure by Default", "Enterprise-grade security with zero-trust architecture and end-to-end encryption."),
        ("⚡", "Lightning Fast", "Optimized for speed — sub-second response times and instant data processing at scale."),
        ("📱", "Mobile First", "Responsive design that looks and works flawlessly on every device, from phones to desktops."),
        ("🎯", "Smart Analytics", "Real-time insights and dashboards that help you make data-driven decisions instantly."),
    ]

    # Build features HTML
    features_html = ""
    for icon, feat_title, feat_desc in features:
        features_html += f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <h3>{feat_title}</h3>
            <p>{feat_desc}</p>
        </div>"""

    # Testimonials
    testimonials = [
        {
            "name": "Sarah Mitchell",
            "role": "Product Manager, TechCorp",
            "quote": f"{safe_name} completely transformed how our team works. The AI features alone saved us 20 hours a week. Absolutely game-changing.",
        },
        {
            "name": "James Rodriguez",
            "role": "Founder, StartupXYZ",
            "quote": f"I've tried every solution on the market. {safe_name} is in a different league — faster, smarter, and actually delivers on its promises.",
        },
        {
            "name": "Emma Larsson",
            "role": "Head of Growth, ScaleUp",
            "quote": f"The ROI was visible within the first month. {safe_name} is not just a tool — it's a competitive advantage.",
        },
    ]

    testimonials_html = ""
    for t in testimonials:
        testimonials_html += f"""
        <div class="testimonial-card">
            <div class="testimonial-quote">"{t['quote']}"</div>
            <div class="testimonial-author">
                <div class="testimonial-name">{t['name']}</div>
                <div class="testimonial-role">{t['role']}</div>
            </div>
        </div>"""

    # FAQ
    faqs = [
        (
            f"What is {safe_name}?",
            f"{safe_name} is the next-generation platform that combines cutting-edge AI with intuitive design to deliver an unmatched experience in its category.",
        ),
        (
            "How do I get started?",
            "Simply sign up for early access using the form above. You'll receive an invitation within 24 hours. No credit card required.",
        ),
        (
            "Is there a free plan?",
            "Yes! We offer a generous free tier with all core features. Premium plans unlock advanced AI capabilities and priority support.",
        ),
        (
            "How is {safe_name} different from competitors?",
            "Unlike existing solutions, {safe_name} uses proprietary AI technology that provides 10x better results. Our platform was built from the ground up for the modern era.",
        ),
        (
            "What about data privacy?",
            "We take privacy seriously. All data is encrypted end-to-end, stored in SOC 2 compliant data centers, and never shared with third parties.",
        ),
    ]

    faq_html = ""
    for i, (q, a) in enumerate(faqs):
        faq_html += f"""
        <div class="faq-item" onclick="toggleFaq(this)">
            <div class="faq-question">{q}</div>
            <div class="faq-answer">{a}</div>
            <div class="faq-toggle">+</div>
        </div>"""

    # Nav links
    nav_links = ["Features", "About", "Benefits", "Testimonials", "FAQ"]
    nav_links_html = " ".join(f'<a href="#{l.lower()}" class="nav-link">{l}</a>' for l in nav_links)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_name} — Next Generation Platform</title>
<meta name="description" content="{safe_desc[:160]}">
<style>
@import url('{theme['google_fonts']}');

*, *::before, *::after {{
    margin: 0; padding: 0; box-sizing: border-box;
}}

html {{
    scroll-behavior: smooth;
}}

body {{
    font-family: {theme['font_body']};
    background: {theme['bg_gradient']};
    color: {theme['text_primary']};
    line-height: 1.7;
    overflow-x: hidden;
}}

/* ─── NAVIGATION ─── */
.nav {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    background: {theme['nav_bg']};
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid {theme['card_border']};
    padding: 0.8rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.3s ease;
}}

.nav-brand {{
    font-family: {theme['font_heading']};
    font-size: 1.4rem;
    font-weight: 700;
    color: {theme['accent']};
    text-decoration: none;
}}

.nav-links {{
    display: flex;
    gap: 2rem;
    align-items: center;
}}

.nav-link {{
    color: {theme['text_secondary']};
    text-decoration: none;
    font-size: 0.95rem;
    font-weight: 500;
    transition: color 0.3s ease;
}}

.nav-link:hover {{
    color: {theme['accent']};
}}

.hamburger {{
    display: none;
    flex-direction: column;
    cursor: pointer;
    gap: 5px;
}}

.hamburger span {{
    width: 28px;
    height: 2px;
    background: {theme['text_primary']};
    transition: all 0.3s ease;
    border-radius: 2px;
}}

/* ─── HERO ─── */
.hero {{
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 8rem 2rem 4rem;
    background: {theme['hero_gradient']};
    position: relative;
    overflow: hidden;
}}

.hero::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(ellipse at 50% 50%, {theme['card_bg']}, transparent 70%);
    pointer-events: none;
}}

.hero-badge {{
    display: inline-block;
    padding: 0.5rem 1.5rem;
    border: 1px solid {theme['card_border']};
    border-radius: 50px;
    font-size: 0.85rem;
    color: {theme['accent']};
    margin-bottom: 2rem;
    background: {theme['card_bg']};
    position: relative;
    z-index: 1;
}}

.hero h1 {{
    font-family: {theme['font_heading']};
    font-size: clamp(2.8rem, 8vw, 5.5rem);
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg, {theme['accent']}, {theme['accent_secondary']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    position: relative;
    z-index: 1;
}}

.hero p {{
    font-size: clamp(1.1rem, 2.5vw, 1.3rem);
    color: {theme['text_secondary']};
    max-width: 650px;
    line-height: 1.8;
    margin-bottom: 2.5rem;
    position: relative;
    z-index: 1;
}}

.hero-cta {{
    display: inline-block;
    padding: 1rem 3rem;
    background: {theme['button_bg']};
    color: {theme['button_text']};
    font-size: 1.05rem;
    font-weight: 700;
    text-decoration: none;
    border-radius: 50px;
    border: none;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    box-shadow: {theme['glow']};
    position: relative;
    z-index: 1;
}}

.hero-cta:hover {{
    transform: scale(1.05);
    box-shadow: 0 0 50px {theme['card_border']};
}}

/* ─── SECTIONS ─── */
.section {{
    padding: 5rem 2rem;
    max-width: 1100px;
    margin: 0 auto;
}}

.section-title {{
    font-family: {theme['font_heading']};
    font-size: clamp(2rem, 5vw, 2.8rem);
    text-align: center;
    margin-bottom: 1rem;
    font-weight: 700;
}}

.section-subtitle {{
    text-align: center;
    color: {theme['text_secondary']};
    font-size: 1.1rem;
    max-width: 600px;
    margin: 0 auto 3rem;
}}

.divider {{
    height: 1px;
    background: {theme['divider']};
    max-width: 200px;
    margin: 0 auto 3rem;
}}

/* ─── FEATURES GRID ─── */
.features-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}}

.feature-card {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
    padding: 2rem;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}}

.feature-card:hover {{
    transform: translateY(-4px);
    box-shadow: {theme['glow']};
}}

.feature-icon {{
    font-size: 2.5rem;
    margin-bottom: 1rem;
}}

.feature-card h3 {{
    font-family: {theme['font_heading']};
    font-size: 1.2rem;
    margin-bottom: 0.5rem;
    color: {theme['accent']};
}}

.feature-card p {{
    color: {theme['text_secondary']};
    font-size: 0.95rem;
    line-height: 1.6;
}}

/* ─── ABOUT ─── */
.about-content {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4rem;
    align-items: center;
}}

.about-text h3 {{
    font-family: {theme['font_heading']};
    font-size: 1.8rem;
    margin-bottom: 1rem;
    color: {theme['accent']};
}}

.about-text p {{
    color: {theme['text_secondary']};
    line-height: 1.8;
    margin-bottom: 1rem;
}}

.about-visual {{
    background: {theme['hero_gradient']};
    border: 1px solid {theme['card_border']};
    border-radius: 20px;
    padding: 3rem;
    text-align: center;
    min-height: 250px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}}

.about-visual .stat {{
    font-family: {theme['font_heading']};
    font-size: 3rem;
    font-weight: 800;
    color: {theme['accent']};
}}

.about-visual .stat-label {{
    color: {theme['text_secondary']};
    font-size: 0.95rem;
    margin-top: 0.5rem;
}}

/* ─── BENEFITS ─── */
.benefits-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
}}

.benefit-card {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
}}

.benefit-card .benefit-number {{
    font-family: {theme['font_heading']};
    font-size: 3rem;
    font-weight: 800;
    color: {theme['accent']};
    margin-bottom: 0.5rem;
}}

.benefit-card h3 {{
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
}}

.benefit-card p {{
    color: {theme['text_secondary']};
    font-size: 0.9rem;
}}

/* ─── TESTIMONIALS ─── */
.testimonials-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}}

.testimonial-card {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
    padding: 2rem;
}}

.testimonial-quote {{
    color: {theme['text_secondary']};
    font-style: italic;
    line-height: 1.7;
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
}}

.testimonial-name {{
    font-weight: 600;
    color: {theme['accent']};
}}

.testimonial-role {{
    color: {theme['text_secondary']};
    font-size: 0.85rem;
}}

/* ─── FAQ ─── */
.faq-list {{
    max-width: 750px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}}

.faq-item {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    transition: border-color 0.3s ease;
    position: relative;
}}

.faq-item:hover {{
    border-color: {theme['accent']};
}}

.faq-question {{
    padding: 1.2rem 3rem 1.2rem 1.5rem;
    font-weight: 600;
    font-size: 1rem;
}}

.faq-answer {{
    padding: 0 1.5rem;
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.4s ease, padding 0.4s ease;
    color: {theme['text_secondary']};
    line-height: 1.7;
}}

.faq-item.active .faq-answer {{
    max-height: 300px;
    padding: 0 1.5rem 1.2rem;
}}

.faq-toggle {{
    position: absolute;
    right: 1.5rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 1.3rem;
    color: {theme['accent']};
    transition: transform 0.3s ease;
}}

.faq-item.active .faq-toggle {{
    transform: translateY(-50%) rotate(45deg);
}}

/* ─── FINAL CTA ─── */
.final-cta {{
    text-align: center;
    padding: 6rem 2rem;
    background: {theme['hero_gradient']};
    position: relative;
    overflow: hidden;
}}

.final-cta::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(ellipse at 50% 50%, {theme['card_bg']}, transparent 70%);
    pointer-events: none;
}}

.final-cta h2 {{
    font-family: {theme['font_heading']};
    font-size: clamp(2rem, 5vw, 3rem);
    margin-bottom: 1rem;
    position: relative;
    z-index: 1;
}}

.final-cta p {{
    color: {theme['text_secondary']};
    font-size: 1.1rem;
    margin-bottom: 2rem;
    position: relative;
    z-index: 1;
}}

.countdown {{
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    margin-bottom: 2.5rem;
    position: relative;
    z-index: 1;
}}

.countdown-unit {{
    text-align: center;
}}

.countdown-number {{
    font-family: {theme['font_heading']};
    font-size: 2.5rem;
    font-weight: 800;
    color: {theme['accent']};
    line-height: 1;
}}

.countdown-label {{
    font-size: 0.75rem;
    color: {theme['text_secondary']};
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.3rem;
}}

/* ─── FOOTER ─── */
.footer {{
    text-align: center;
    padding: 2rem;
    border-top: 1px solid {theme['card_border']};
    color: {theme['text_secondary']};
    font-size: 0.85rem;
}}

.footer a {{
    color: {theme['accent']};
    text-decoration: none;
}}

/* ─── FADE-IN ANIMATION ─── */
.fade-in {{
    opacity: 0;
    transform: translateY(30px);
    transition: opacity 0.6s ease, transform 0.6s ease;
}}

.fade-in.visible {{
    opacity: 1;
    transform: translateY(0);
}}

/* ─── RESPONSIVE ─── */
@media (max-width: 768px) {{
    .nav-links {{
        display: none;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: {theme['nav_bg']};
        backdrop-filter: blur(20px);
        flex-direction: column;
        padding: 1rem 2rem 2rem;
        gap: 1rem;
        border-bottom: 1px solid {theme['card_border']};
    }}

    .nav-links.open {{
        display: flex;
    }}

    .hamburger {{
        display: flex;
    }}

    .about-content {{
        grid-template-columns: 1fr;
        gap: 2rem;
    }}

    .countdown {{
        gap: 0.8rem;
    }}

    .countdown-number {{
        font-size: 1.8rem;
    }}

    .hero {{
        padding: 7rem 1.5rem 3rem;
    }}
}}

@media (max-width: 480px) {{
    .section {{
        padding: 3rem 1.5rem;
    }}

    .features-grid,
    .testimonials-grid,
    .benefits-grid {{
        grid-template-columns: 1fr;
    }}
}}
</style>
</head>
<body>

<!-- NAVIGATION -->
<nav class="nav" id="navbar">
    <a href="#" class="nav-brand">{safe_name}</a>
    <div class="nav-links" id="navLinks">
        {nav_links_html}
        <a href="#cta" class="hero-cta" style="padding: 0.6rem 1.5rem; font-size: 0.9rem;">Get Access</a>
    </div>
    <div class="hamburger" onclick="toggleMenu()">
        <span></span>
        <span></span>
        <span></span>
    </div>
</nav>

<!-- HERO -->
<section class="hero">
    <div class="hero-badge">&#9889; Now Available for Early Access</div>
    <h1>{safe_name}</h1>
    <p>{safe_desc}</p>
    <a href="#cta" class="hero-cta">Get Early Access &rarr;</a>
</section>

<!-- FEATURES -->
<section class="section fade-in" id="features">
    <h2 class="section-title">Why Choose Us?</h2>
    <div class="divider"></div>
    <p class="section-subtitle">Everything you need, nothing you don't.</p>
    <div class="features-grid">
        {features_html}
    </div>
</section>

<!-- ABOUT -->
<section class="section fade-in" id="about">
    <h2 class="section-title">Our Story</h2>
    <div class="divider"></div>
    <div class="about-content">
        <div class="about-text">
            <h3>Built for the Future</h3>
            <p>{safe_name} was born from a simple idea: the next generation of products should be smarter, faster, and more accessible than ever before.</p>
            <p>Our team combined decades of industry experience with cutting-edge artificial intelligence to create a platform that doesn't just meet expectations — it exceeds them.</p>
            <p>{safe_killer}</p>
        </div>
        <div class="about-visual">
            <div class="stat">10M+</div>
            <div class="stat-label">Users worldwide trust us</div>
        </div>
    </div>
</section>

<!-- BENEFITS -->
<section class="section fade-in" id="benefits">
    <h2 class="section-title">Key Benefits</h2>
    <div class="divider"></div>
    <p class="section-subtitle">Numbers that speak for themselves.</p>
    <div class="benefits-grid">
        <div class="benefit-card fade-in">
            <div class="benefit-number">10x</div>
            <h3>Faster Results</h3>
            <p>Get results in seconds, not hours. Our optimized engine processes data at unprecedented speed.</p>
        </div>
        <div class="benefit-card fade-in">
            <div class="benefit-number">99.9%</div>
            <h3>Uptime</h3>
            <p>Enterprise-grade reliability with redundant infrastructure across multiple regions.</p>
        </div>
        <div class="benefit-card fade-in">
            <div class="benefit-number">50%</div>
            <h3>Cost Reduction</h3>
            <p>Slash operational costs by half while getting better results than traditional solutions.</p>
        </div>
        <div class="benefit-card fade-in">
            <div class="benefit-number">24/7</div>
            <h3>Support</h3>
            <p>Round-the-clock expert support with dedicated account managers for premium plans.</p>
        </div>
    </div>
</section>

<!-- TESTIMONIALS -->
<section class="section fade-in" id="testimonials">
    <h2 class="section-title">What People Say</h2>
    <div class="divider"></div>
    <div class="testimonials-grid">
        {testimonials_html}
    </div>
</section>

<!-- FAQ -->
<section class="section fade-in" id="faq">
    <h2 class="section-title">Frequently Asked Questions</h2>
    <div class="divider"></div>
    <div class="faq-list">
        {faq_html}
    </div>
</section>

<!-- FINAL CTA -->
<section class="final-cta" id="cta">
    <h2>Ready to Get Started?</h2>
    <p>Join thousands of early adopters. Limited spots available.</p>
    <div class="countdown">
        <div class="countdown-unit">
            <div class="countdown-number" id="cd-days">00</div>
            <div class="countdown-label">Days</div>
        </div>
        <div class="countdown-unit">
            <div class="countdown-number" id="cd-hours">00</div>
            <div class="countdown-label">Hours</div>
        </div>
        <div class="countdown-unit">
            <div class="countdown-number" id="cd-mins">00</div>
            <div class="countdown-label">Minutes</div>
        </div>
        <div class="countdown-unit">
            <div class="countdown-number" id="cd-secs">00</div>
            <div class="countdown-label">Seconds</div>
        </div>
    </div>
    <a href="#" class="hero-cta">Claim Your Spot Now &rarr;</a>
</section>

<!-- FOOTER -->
<footer class="footer">
    <p>&copy; 2025 {safe_name}. All rights reserved. | <a href="#">Privacy Policy</a> | <a href="#">Terms of Service</a></p>
</footer>

<script>
(function() {{
    // ─── COUNTDOWN TIMER ───
    var launchDate = new Date("{launch_date}").getTime();

    function updateCountdown() {{
        var now = Date.now();
        var diff = launchDate - now;
        if (diff < 0) diff = 0;

        var days = Math.floor(diff / (1000 * 60 * 60 * 24));
        var hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        var secs = Math.floor((diff % (1000 * 60)) / 1000);

        var dEl = document.getElementById('cd-days');
        var hEl = document.getElementById('cd-hours');
        var mEl = document.getElementById('cd-mins');
        var sEl = document.getElementById('cd-secs');

        if (dEl) dEl.textContent = String(days).padStart(2, '0');
        if (hEl) hEl.textContent = String(hours).padStart(2, '0');
        if (mEl) mEl.textContent = String(mins).padStart(2, '0');
        if (sEl) sEl.textContent = String(secs).padStart(2, '0');

        requestAnimationFrame(updateCountdown);
    }}
    updateCountdown();

    // ─── MOBILE MENU TOGGLE ───
    window.toggleMenu = function() {{
        var links = document.getElementById('navLinks');
        if (links) links.classList.toggle('open');
    }};

    // Close menu on link click (mobile)
    document.querySelectorAll('.nav-link').forEach(function(link) {{
        link.addEventListener('click', function() {{
            var links = document.getElementById('navLinks');
            if (links) links.classList.remove('open');
        }});
    }});

    // ─── FAQ ACCORDION ───
    window.toggleFaq = function(el) {{
        var wasActive = el.classList.contains('active');
        // Close all
        document.querySelectorAll('.faq-item').forEach(function(item) {{
            item.classList.remove('active');
        }});
        // Open clicked (if it was closed)
        if (!wasActive) {{
            el.classList.add('active');
        }}
    }};

    // ─── SCROLL-TRIGGERED FADE-IN ───
    var observer = new IntersectionObserver(function(entries) {{
        entries.forEach(function(entry) {{
            if (entry.isIntersecting) {{
                entry.target.classList.add('visible');
            }}
        }});
    }}, {{
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    }});

    document.querySelectorAll('.fade-in').forEach(function(el) {{
        observer.observe(el);
    }});

    // ─── SMOOTH SCROLL FOR NAV LINKS ───
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {{
        anchor.addEventListener('click', function(e) {{
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {{
                e.preventDefault();
                target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }});
    }});
}})();
</script>
</body>
</html>"""
    return html


def _html_escape(text: str) -> str:
    """Escape special HTML characters."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#39;")
    return text


# ═══════════════════════════════════════════════════════════════════
# STORAGE HELPERS
# ═══════════════════════════════════════════════════════════════════

def save_items(user_id: int, category: str, items: list) -> None:
    """Save items list for a user and category."""
    if user_id not in user_items:
        user_items[user_id] = {}
    user_items[user_id][category] = items


def get_item(user_id: int, category: str, index: int) -> dict | None:
    """Retrieve a single item by user, category, and index."""
    items = user_items.get(user_id, {}).get(category, [])
    if 0 <= index < len(items):
        return items[index]
    return None


# ═══════════════════════════════════════════════════════════════════
# SAFE SEND — Telegram send with retry
# ═══════════════════════════════════════════════════════════════════

async def safe_send_message(
    chat_id: int,
    text: str,
    parse_mode: str | None = None,
    **kwargs,
) -> Message | None:
    """Send a Telegram message with 3 retry attempts."""
    for attempt in range(3):
        try:
            return await bot.send_message(
                chat_id, text, parse_mode=parse_mode, **kwargs
            )
        except Exception as e:
            logger.warning(
                f"[SafeSend] Attempt {attempt + 1}/3 failed: {e}"
            )
            if attempt < 2:
                await asyncio.sleep(2)
    return None


async def safe_send_document(
    chat_id: int,
    document,
    caption: str | None = None,
    **kwargs,
) -> Message | None:
    """Send a Telegram document with 3 retry attempts."""
    for attempt in range(3):
        try:
            return await bot.send_document(
                chat_id, document, caption=caption, **kwargs
            )
        except Exception as e:
            logger.warning(
                f"[SafeSendDoc] Attempt {attempt + 1}/3 failed: {e}"
            )
            if attempt < 2:
                await asyncio.sleep(2)
    return None


# ═══════════════════════════════════════════════════════════════════
# MESSAGE BUILDERS
# ═══════════════════════════════════════════════════════════════════

EMOJIS = ["🔥", "⚡", "🚀", "💎", "⭐", "🎯", "📈", "❤️", "💪", "🎵"]


def build_item_message(item: dict, emoji: str, category: str = "") -> str:
    """Build a formatted Telegram message for a single item."""
    name = item.get("name", "Unknown")
    link = item.get("link", "")

    # Crypto-specific format with niche, why_hyping, what_does
    if category == "crypto" and item.get("niche"):
        niche = item.get("niche", "")
        niche_emoji = NICHE_EMOJIS.get(niche, "📊")
        why_hyping = item.get("why_hyping", "")
        what_does = item.get("what_does", "")

        text = f"{emoji} *{name}*\n"
        text += f"{niche_emoji} *Ниша:* {niche}\n\n"
        if why_hyping:
            text += f"📈 *Почему хайпует:* {why_hyping}\n\n"
        if what_does:
            text += f"⚙️ *Что делает:* {what_does}\n"
        if link:
            text += f"\n🔗 [Официальный сайт]({link})"
        return text

    # Standard format for stores/companies
    desc = item.get("description", item.get("style", ""))
    extra = item.get("country", "") or item.get("sector", "")

    text = f"{emoji} *{name}*\n\n"
    if desc:
        text += f"{desc}\n\n"
    if extra:
        text += f"📍 {extra}\n"
    if link:
        text += f"\n🔗 [Официальный сайт]({link})"
    return text


def build_item_keyboard(category: str, index: int) -> InlineKeyboardMarkup:
    """Build inline keyboard with '🔥 Улучшенный оффер' button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 Улучшенный оффер",
                    callback_data=f"improve:{category}:{index}",
                )
            ]
        ]
    )


async def send_items_batch(
    message: Message,
    items: list,
    category: str,
    title: str,
) -> None:
    """Send all items as individual messages with inline buttons."""
    save_items(message.from_user.id, category, items)
    await message.answer(f"📊 *{title}*\n{'━' * 30}\n")

    items_to_send = items[:10]
    for i, item in enumerate(items_to_send):
        emoji = EMOJIS[i % len(EMOJIS)]
        text = build_item_message(item, emoji, category=category)
        kb = build_item_keyboard(category, i)
        try:
            await message.answer(text, reply_markup=kb)
            if i < len(items_to_send) - 1:
                await asyncio.sleep(0.35)
        except Exception as e:
            logger.warning(f"Failed to send item {i}: {e}")
            # Retry with plain text (no markdown)
            try:
                plain = text.replace("*", "").replace("_", "").replace("[", "").replace("](", " ").replace(")", "").replace("&", "and")
                await message.answer(plain, reply_markup=kb)
            except Exception as e2:
                logger.error(f"Retry also failed for item {i}: {e2}")


# ═══════════════════════════════════════════════════════════════════
# ZIP CREATION — Writes to /tmp/ (v9.2 fix for Render)
# ═══════════════════════════════════════════════════════════════════

def create_site_zip(html_content: str, project_name: str) -> str:
    """Create a ZIP file on disk at /tmp/ and return the path.

    The caller is responsible for deleting the temp file after use.
    """
    safe_name = project_name.lower().replace(" ", "-").replace("/", "-")[:50]
    tmp_path = os.path.join(tempfile.gettempdir(), f"{safe_name}-landing.zip")

    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{safe_name}/index.html", html_content)
        zf.writestr(
            f"{safe_name}/README.txt",
            f"Improved Landing Page: {project_name}\n"
            f"{'=' * 40}\n\n"
            f"1. Open index.html in any modern browser\n"
            f"2. Or upload to any hosting (Netlify, Vercel, GitHub Pages)\n"
            f"3. The page is fully standalone — no dependencies needed\n"
            f"4. All CSS and JS are inline — works offline via file://\n",
        )

    logger.info(f"[ZIP] Created: {tmp_path} ({os.path.getsize(tmp_path)} bytes)")
    return tmp_path


def cleanup_zip(tmp_path: str) -> None:
    """Safely delete the temp ZIP file."""
    try:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
            logger.info(f"[ZIP] Cleaned up: {tmp_path}")
    except Exception as e:
        logger.warning(f"[ZIP] Cleanup failed: {e}")


# ═══════════════════════════════════════════════════════════════════
# ANALYSIS MESSAGE BUILDER
# ═══════════════════════════════════════════════════════════════════

def build_analysis_message(
    name: str,
    analysis: dict,
) -> tuple[str, str]:
    """Build the full analysis text message.

    Returns (markdown_text, plain_text) — plain_text is used as fallback
    if Markdown parsing fails.
    """

    imp_name = analysis.get("improved_name", f"Neo{name}")
    imp_desc = analysis.get("improved_description", "")
    imp_link = analysis.get("improved_link", "")
    killer = analysis.get("killer_feature", "")
    geo = analysis.get("geo_analysis", {})
    kw = analysis.get("keywords", {})
    audience = analysis.get("target_audience", "")

    # ── GEO section ──
    geo_md = ""
    if geo:
        tier1 = geo.get("tier1", [])
        tier2 = geo.get("tier2", [])
        tier3 = geo.get("tier3", [])
        platforms = geo.get("best_platforms", [])
        budget = geo.get("budget_split", "")
        cpa = geo.get("estimated_cpa", "")

        if tier1:
            geo_md += "🟢 *Tier 1 — Приоритет:*\n"
            for g in tier1:
                geo_md += f"   • {g}\n"
        if tier2:
            geo_md += "\n🟡 *Tier 2 — Второй эшелон:*\n"
            for g in tier2:
                geo_md += f"   • {g}\n"
        if tier3:
            geo_md += "\n🟠 *Tier 3 — Новые рынки:*\n"
            for g in tier3:
                geo_md += f"   • {g}\n"
        if platforms:
            geo_md += f"\n📢 *Платформы:* {', '.join(platforms)}\n"
        if budget:
            geo_md += f"💰 *Бюджет:* {budget}\n"
        if cpa:
            geo_md += f"📊 *Est. CPA:* {cpa}\n"

    # ── Keywords section ──
    kw_md = ""
    if kw:
        branded = kw.get("branded", [])
        generic = kw.get("generic", [])
        longtail = kw.get("long_tail", [])
        competitor = kw.get("competitor", [])
        negative = kw.get("negative", [])

        if branded:
            kw_md += (
                "🏷 *Брендовые:* "
                + ", ".join(f"«{k}»" for k in branded)
                + "\n"
            )
        if generic:
            kw_md += (
                "🔍 *Generic:* "
                + ", ".join(f"«{k}»" for k in generic)
                + "\n"
            )
        if longtail:
            kw_md += (
                "🎯 *Long-tail:* "
                + ", ".join(f"«{k}»" for k in longtail)
                + "\n"
            )
        if competitor:
            kw_md += (
                "⚔ *Competitor:* "
                + ", ".join(f"«{k}»" for k in competitor)
                + "\n"
            )
        if negative:
            kw_md += (
                "🚫 *Negative:* "
                + ", ".join(f"«{k}»" for k in negative)
                + "\n"
            )

    # ── Full message ──
    md_text = (
        f"🚀 *{imp_name}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 *Улучшенная версия:* {name}\n\n"
        f"{imp_desc}\n\n"
        f"⚡ *Killer Feature:* {killer}\n"
    )
    if imp_link:
        md_text += f"🔗 *Сайт:* [{imp_link}]({imp_link})\n"
    if audience:
        md_text += f"\n👥 *Целевая аудитория:* {audience}\n"
    if geo_md:
        md_text += f"\n🌍 *GEO-АНАЛИЗ:*\n{geo_md}"
    if kw_md:
        md_text += f"\n🔑 *КЛЮЧЕВЫЕ СЛОВА:*\n{kw_md}"
    md_text += "\n\n📦 Сайт-лендинг — в следующем сообщении ⬇️"

    # Plain text version (strip Markdown)
    plain = md_text
    plain = plain.replace("*", "")
    plain = plain.replace("_", "")
    plain = plain.replace("[", "")
    # Replace markdown links [text](url) → text (url)
    plain = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", plain)
    plain = plain.replace("«", '"').replace("»", '"')
    plain = plain.replace("&", "and")

    return md_text, plain


# ═══════════════════════════════════════════════════════════════════
# /start COMMAND HANDLER
# ═══════════════════════════════════════════════════════════════════

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle the /start command — send greeting with menu."""
    try:
        await message.answer(
            "👋 *EU Trend Analytics v14.0*\n\n"
            "🤖 AI-анализ трендов в реальном времени\n"
            "🔥 Каждому тренду — улучшенный оффер с:\n"
            "  📦 Готовым сайтом (ZIP архив)\n"
            "  🌍 GEO-анализом (куда лить трафик)\n"
            "  🔑 Подбором ключевых слов\n\n"
            "👇 Выбери категорию:",
            reply_markup=menu,
        )
    except Exception as e:
        logger.error(f"[cmd_start] {e}")
        await message.answer(
            "👋 EU Trend Analytics v13.0\n\n"
            "👇 Выбери категорию:",
            reply_markup=menu,
        )


# ═══════════════════════════════════════════════════════════════════
# CATCH-ALL MESSAGE HANDLER — processes ALL text messages
# ═══════════════════════════════════════════════════════════════════

# Map of button text substrings to categories (for flexible matching)
CATEGORY_MAP = {
    "Трендовые магазины": "stores",
    "магазины": "stores",
    "магазин": "stores",
    "fashion": "stores",
    "бренд": "stores",
    "Трендовая крипта": "crypto",
    "крипта": "crypto",
    "крипт": "crypto",
    "crypto": "crypto",
    "Трендовые компании": "companies",
    "компании": "companies",
    "компани": "companies",
    "стартап": "companies",
}


async def handle_category_message(message: Message) -> None:
    """Process a category selection message. Returns True if handled."""
    text = message.text or ""
    text_lower = text.lower()

    matched_category = None
    for key, cat in CATEGORY_MAP.items():
        if key.lower() in text_lower:
            matched_category = cat
            break

    if not matched_category:
        return False

    try:
        await message.answer(CATEGORY_SEARCH_MESSAGES[matched_category])

        # ─── CRYPTO: use dedicated deep niche search ───
        if matched_category == "crypto":
            items = await search_crypto_deep()
        else:
            # ─── STORES / COMPANIES: use AI search ───
            items = await ask_ai_list(CATEGORY_PROMPTS[matched_category])
            if not items:
                logger.warning(f"[{matched_category}] AI returned empty, using fallback")
                items = CATEGORY_FALLBACKS[matched_category]

        if not items:
            logger.warning(f"[{matched_category}] No results at all, using fallback")
            items = CATEGORY_FALLBACKS[matched_category]

        await send_items_batch(message, items, matched_category, CATEGORY_TITLES[matched_category])
        return True
    except Exception as e:
        logger.error(f"[handle_category] {e}", exc_info=True)
        _last_errors.append(f"category-{matched_category}: {e}")
        try:
            # Try to send fallback even on error
            fallback_items = CATEGORY_FALLBACKS.get(matched_category, [])
            if fallback_items:
                await send_items_batch(message, fallback_items, matched_category, CATEGORY_TITLES[matched_category])
            else:
                await message.answer("❌ Ошибка при поиске трендов. Попробуй позже.")
        except Exception:
            pass
        return True  # was handled, just with an error


@dp.message(F.text)
async def catch_all_handler(message: Message) -> None:
    """Catch ALL text messages and route them."""
    text = message.text or ""
    logger.info(f"[MSG] User {message.from_user.id}: {repr(text[:100])}")

    # Skip commands (already handled)
    if text.startswith("/"):
        return

    # Try to match category
    handled = await handle_category_message(message)
    if handled:
        return

    # Unknown message — ignore silently
    logger.info(f"[MSG] Unhandled message: {repr(text[:50])}")


# ═══════════════════════════════════════════════════════════════════
# CATEGORY PROMPTS (kept for compatibility)
# ═══════════════════════════════════════════════════════════════════

CATEGORY_PROMPTS: dict[str, str] = {
    "stores": PROMPT_STORES,
    "crypto": PROMPT_CRYPTO,
    "companies": PROMPT_COMPANIES,
}

CATEGORY_FALLBACKS: dict[str, list] = {
    "stores": FALLBACK_STORES,
    "crypto": FALLBACK_CRYPTO,
    "companies": FALLBACK_COMPANIES,
}

CATEGORY_TITLES: dict[str, str] = {
    "stores": "ТРЕНДОВЫЕ БРЕНДЫ ЕВРОПЫ",
    "crypto": "ТРЕНДОВАЯ КРИПТА",
    "companies": "ТРЕНДОВЫЕ КОМПАНИИ",
}

CATEGORY_NAMES: dict[str, str] = {
    "stores": "Fashion Brand",
    "crypto": "Crypto Project",
    "companies": "Startup/Company",
}

CATEGORY_SEARCH_MESSAGES: dict[str, str] = {
    "stores": "🔍 *Ищу трендовые бренды Европы...*",
    "crypto": "🔍 *Ищу трендовые крипто-проекты...*",
    "companies": "🔍 *Ищу трендовые стартапы...*",
}


# ═══════════════════════════════════════════════════════════════════
# "🔥 Улучшенный оффер" CALLBACK HANDLER
# ═══════════════════════════════════════════════════════════════════

@dp.callback_query(F.data.startswith("improve:"))
async def callback_improve(callback: CallbackQuery) -> None:
    """Handle the '🔥 Улучшенный оффер' button press.

    Flow:
    1. Parse callback data
    2. Retrieve stored item
    3. Analyze original site URL
    4. Get improved analysis from AI
    5. Generate landing page HTML from AI
    6. Build ZIP on disk
    7. Send analysis text message
    8. Send ZIP document
    9. Clean up temp files
    """
    # ─── Parse callback data ───
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("❌ Ошибка", show_alert=True)
        return

    category = parts[1]
    try:
        index = int(parts[2])
    except ValueError:
        await callback.answer("❌ Ошибка", show_alert=True)
        return

    # ─── Retrieve stored item ───
    item = get_item(callback.from_user.id, category, index)
    if not item:
        await callback.answer(
            "❌ Список устарел. Нажми категорию заново.",
            show_alert=True,
        )
        return

    await callback.answer("🔥 Генерирую полный пакет...")

    name = item.get("name", "Unknown")
    desc = item.get("description", item.get("style", "")) or item.get("what_does", "") or item.get("why_hyping", "")
    link = item.get("link", "")
    cat_name = CATEGORY_NAMES.get(category, "Project")
    chat_id = callback.message.chat.id

    logger.info(
        f"[Improve] user={callback.from_user.id} "
        f"category={category} index={index} name={name}"
    )

    # ─── Step 1: Send "generating" status ───
    status_msg = await safe_send_message(
        chat_id,
        f"🔥 *Генерирую улучшенный оффер для: {name}*\n\n"
        f"⏳ Шаг 1/4: Анализ оригинального сайта...",
    )
    if not status_msg:
        return

    # ─── Step 2: Analyze original site ───
    site_analysis: dict = {}
    try:
        site_analysis = await analyze_original_site(link)
        logger.info(
            f"[Improve] Site analysis: "
            f"title={site_analysis.get('title', 'N/A')[:50]}"
        )
    except Exception as e:
        logger.warning(f"[Improve] Site analysis failed: {e}")

    # ─── Step 3: Update status ───
    try:
        await status_msg.edit_text(
            f"🔥 *Генерирую улучшенный оффер для: {name}*\n\n"
            f"{'✅' if site_analysis else '⏭️'} Шаг 1/4: "
            f"{'Анализ сайта — готов' if site_analysis else 'Анализ сайта — пропущен (не удалось загрузить)'}\n"
            f"⏳ Шаг 2/4: AI-анализ концепции + GEO + ключевые слова..."
        )
    except Exception:
        pass

    # ─── Step 4: Get improved analysis from AI (category-specific) ───
    improve_prompt = IMPROVE_PROMPTS.get(category, PROMPT_IMPROVE_STORES)
    analysis_prompt = improve_prompt.format(
        name=name,
        description=desc,
        link=link,
    )
    analysis = await ask_ai_json(
        analysis_prompt,
        f"Create the ultimate improved offer package for {name}. "
        f"Category: {category}. Original name: {name}.",
    )

    # Fallback analysis
    if not analysis:
        logger.warning(f"[Improve] AI analysis failed, using fallback for {name}")
        analysis = get_fallback_analysis(name, desc, link, category=category)

    imp_name = analysis.get("improved_name", f"Neo{name}")
    imp_desc = analysis.get("improved_description", "")
    imp_link = analysis.get("improved_link", "")
    killer = analysis.get("killer_feature", "")

    logger.info(f"[Improve] Analysis result: improved_name={imp_name}")

    # ─── Step 5: Update status ───
    try:
        await status_msg.edit_text(
            f"🔥 *Генерирую улучшенный оффер для: {name}*\n\n"
            f"✅ Шаг 1/4: Анализ сайта\n"
            f"✅ Шаг 2/4: AI-анализ готов\n"
            f"⏳ Шаг 3/4: Создаю лендинг (AI + дизайн тема)..."
        )
    except Exception:
        pass

    # ─── Step 6: Determine theme ───
    theme = get_theme_for_project(imp_name)
    logger.info(f"[Improve] Theme: {theme['name']} for {imp_name}")

    # ─── Step 7: Generate landing page ───
    project_info = {
        "improved_name": imp_name,
        "improved_description": imp_desc,
        "killer_feature": killer,
        "original_link": link,
        "improved_link": imp_link,
    }

    landing_prompt = build_landing_page_prompt(project_info, theme, site_analysis, category=category)
    html_content = await ask_ai_html(
        landing_prompt,
        f"Build a stunning landing page for {imp_name}. "
        f"Theme: {theme['name']}. Make it production-ready.",
    )

    if not html_content:
        logger.warning(
            f"[Improve] AI landing page failed, using fallback for {imp_name}"
        )
        html_content = generate_fallback_html(imp_name, imp_desc, killer)

    # ─── Step 8: Create ZIP on disk ───
    tmp_path = create_site_zip(html_content, imp_name)

    # ─── Step 9: Update status ───
    try:
        await status_msg.edit_text(
            f"🔥 *Генерирую улучшенный оффер для: {name}*\n\n"
            f"✅ Шаг 1/4: Анализ сайта\n"
            f"✅ Шаг 2/4: AI-анализ готов\n"
            f"✅ Шаг 3/4: Лендинг создан (тема: {theme['name']})\n"
            f"⏳ Шаг 4/4: Отправка файлов..."
        )
    except Exception:
        pass

    # ─── Step 10: Send analysis message ───
    md_text, plain_text = build_analysis_message(name, analysis)

    try:
        await safe_send_message(chat_id, md_text)
    except Exception:
        # Retry with plain text (no Markdown)
        await safe_send_message(chat_id, plain_text)

    # ─── Step 11: Send ZIP document ───
    safe_file_name = imp_name.lower().replace(" ", "-")[:50]
    try:
        document = FSInputFile(tmp_path, filename=f"{safe_file_name}-landing.zip")
        sent = await safe_send_document(
            chat_id,
            document,
            caption=(
                f"📦 *{imp_name} — Готовый лендинг*\n\n"
                f"🎨 Дизайн тема: {theme['name']}\n"
                f"Разархивируй → открой index.html в браузере\n"
                f"Или залей на Netlify / Vercel / GitHub Pages"
            ),
        )
        if sent:
            logger.info(f"[Improve] ZIP sent successfully for {imp_name}")
    except Exception as e:
        logger.error(f"[Improve] Failed to send ZIP: {e}")
        await safe_send_message(
            chat_id,
            "❌ Не удалось отправить ZIP-архив.\n"
            "Попробуй нажать кнопку ещё раз.",
        )
    finally:
        cleanup_zip(tmp_path)

    # ─── Step 12: Final status update ───
    try:
        await status_msg.edit_text(
            f"✅ *Полный пакет для {imp_name} готов!*\n\n"
            f"📊 Анализ + GEO + Ключевые слова — выше\n"
            f"📦 Готовый сайт (тема: {theme['name']}) — в архиве\n\n"
            f"💡 Нажми кнопку ещё раз для нового варианта!"
        )
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
# HEALTH SERVER & KEEP-ALIVE
# ═══════════════════════════════════════════════════════════════════

async def health_handler(request: web.Request) -> web.Response:
    """Health check endpoint — returns version info."""
    return web.Response(text="Bot v14.0 is running")


# Store last errors for debugging
_last_errors: list[str] = []
_bot_started = False
_polling_active = False


async def debug_handler(request: web.Request) -> web.Response:
    """Debug endpoint — shows bot state and recent errors."""
    info = [
        f"Bot v14.0 DEBUG",
        f"Started: {_bot_started}",
        f"Polling: {_polling_active}",
        f"OpenRouter Key: {'SET' if OPENROUTER_KEY else 'EMPTY'}",
        f"Gemini Key: {'SET' if GEMINI_KEY else 'EMPTY'}",
        f"PORT: {PORT}",
        f"Handlers registered: {len(dp.message.handlers)}",
        f"Callback handlers: {len(dp.callback_query.handlers)}",
        f"User items cached: {len(user_items)}",
        f"Recent errors ({len(_last_errors)}):",
    ]
    for err in _last_errors[-10:]:
        info.append(f"  ❌ {err}")
    return web.Response(text="\n".join(info))


async def keep_alive_loop() -> None:
    """Periodically ping own health endpoint to prevent Render spin-down."""
    health_url = f"{RENDER_URL}/health"
    logger.info(f"[KeepAlive] Starting pinger → {health_url}")

    while True:
        await asyncio.sleep(14 * 60)  # 14 minutes
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(health_url)
                logger.info(
                    f"[KeepAlive] Ping OK — HTTP {resp.status_code}"
                )
        except Exception as e:
            logger.warning(f"[KeepAlive] Ping failed: {e}")


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

async def main() -> None:
    """Start the health server and begin bot polling."""

    logger.info("=" * 55)
    logger.info("🚀 EU Trend Analytics Bot v13.0 starting...")
    logger.info(f"🤖 AI Provider: OpenRouter")
    logger.info(f"🧠 Models: {', '.join(OPENROUTER_MODELS)}")
    logger.info(f"🔑 OpenRouter Key: {'configured' if OPENROUTER_KEY else 'NOT configured'}")
    logger.info(f"🌐 Health server port: {PORT}")
    logger.info(f"🔗 Render URL: {RENDER_URL}")
    logger.info(f"🎨 Design themes: {len(DESIGN_THEMES)}")
    for t in DESIGN_THEMES:
        logger.info(f"   → {t['name']}")
    logger.info("=" * 55)

    # ─── Start health server ───
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/debug", debug_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"[Health] Server running on port {PORT}")

    # ─── Start keep-alive pinger ───
    asyncio.create_task(keep_alive_loop())

    # ─── Start bot polling ───
    global _bot_started, _polling_active
    _bot_started = True
    logger.info("[Bot] Starting polling...")
    _polling_active = True
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
