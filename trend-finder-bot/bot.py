"""
EU Trend Analytics Bot v15.1 — Deep Niche All Categories
==========================================================================
AI-powered trend discovery with "Improved Offer" feature:
  1. Trendy DTC stores (young, hyped, viral products across ALL categories)
  2. Trending crypto projects (DEEP NICHE: AI, DePIN, RWA, L2/L3, DeSci, Bitcoin DeFi)
  3. Hot startups & companies (Series A-C, pre-IPO — NOT Fortune 500)

v15.1 CHANGES:
  - Stores search: aggressive retry loop (5 rounds) with OpenRouter + Gemini in parallel
  - Stores search: minimum 6 verified stores before sending (was 3)
  - Stores search: 150s timeout (was 40s) to allow thorough search
  - Stores search: validates ALL 3 fallback pools (was 2)
  - Stores search: 3rd fallback pool added (24 total candidates)
  - AI prompts: request 20 stores per call (was 12) for larger validation buffer
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

from site_generator import generate_premium_site

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


async def _fetch_coingecko_fast() -> list[dict]:
    """Concurrent CoinGecko fetch: trending + 3 random categories in parallel.
    Total timeout: 12 seconds for ALL calls combined.
    """
    categories_to_try = random.sample(CG_CATEGORIES, min(3, len(CG_CATEGORIES)))

    tasks = [asyncio.create_task(fetch_coingecko_trending())]
    for slug in categories_to_try:
        tasks.append(asyncio.create_task(fetch_coingecko_by_category(slug)))

    done, pending = await asyncio.wait(tasks, timeout=12)
    for p in pending:
        p.cancel()

    all_coins: dict[str, dict] = {}
    for t in done:
        try:
            coins = t.result()
            for coin in coins:
                all_coins[coin["id"]] = coin
        except Exception:
            pass

    return list(all_coins.values())[:15]


CRYPTO_REQUIRED_NICHES = [
    "AI", "DePIN", "RWA", "Bitcoin DeFi", "GameFi", "SocialFi", "L2/L3",
]

NICHE_ALIASES: dict[str, str] = {
    # normalize AI model niche labels to canonical names
    "ai agents": "AI", "ai": "AI", "artificial intelligence": "AI",
    "ai-agents": "AI", "ai agents": "AI",
    "depin": "DePIN", "de-pin": "DePIN", "decentralized infrastructure": "DePIN",
    "rwa": "RWA", "real world assets": "RWA", "real-world assets": "RWA", "tokenization": "RWA",
    "bitcoin defi": "Bitcoin DeFi", "btc defi": "Bitcoin DeFi", "btc l2": "Bitcoin DeFi", "bitcoin l2": "Bitcoin DeFi",
    "gamefi": "GameFi", "gaming": "GameFi", "game": "GameFi", "blockchain gaming": "GameFi",
    "socialfi": "SocialFi", "social": "SocialFi", "decentralized social": "SocialFi", "social network": "SocialFi",
    "l2": "L2/L3", "l3": "L2/L3", "l2/l3": "L2/L3", "layer 2": "L2/L3", "layer 3": "L2/L3",
    "desci": "DeSci", "decentralized science": "DeSci",
    "modular": "L2/L3", "modular blockchain": "L2/L3",
}


def _normalize_niche(raw: str) -> str:
    """Normalize a niche label to one of CRYPTO_REQUIRED_NICHES."""
    if not raw:
        return ""
    low = raw.strip().lower()
    if low in NICHE_ALIASES:
        return NICHE_ALIASES[low]
    # brute-force substring match
    for key, canonical in NICHE_ALIASES.items():
        if key in low or low in key:
            return canonical
    return raw.strip()  # return as-is if unknown


def _dedup_by_niche(items: list[dict], max_per_niche: int = 1) -> list[dict]:
    """Keep at most *max_per_niche* items per niche (first seen wins)."""
    seen: dict[str, int] = {}
    result = []
    for item in items:
        niche = _normalize_niche(item.get("niche", ""))
        if not niche:
            continue
        if seen.get(niche, 0) >= max_per_niche:
            continue
        seen[niche] = seen.get(niche, 0) + 1
        result.append(item)
    return result


async def search_crypto_deep() -> list[dict]:
    """Main crypto search: CoinGecko (fast, 12s) → AI enrichment (20s) → fallback.

    Strategy:
    1. Concurrent CoinGecko fetch: trending + 3 random categories (12s timeout)
    2. Enrich with Gemini (has Google Search grounding for real-time data)
    3. If AI fails, use CoinGecko data with basic enrichment
    4. If CoinGecko fails, use deep niche fallback (rotated pool)

    CRITICAL: All returned items are deduplicated — at most 1 project per niche.
    """
    # ─── Step 1: Fast concurrent CoinGecko fetch ───
    all_coins = await _fetch_coingecko_fast()

    if all_coins:
        logger.info(f"[CryptoSearch] CoinGecko returned {len(all_coins)} unique coins")

        # ─── Step 2: Enrich with AI (20s timeout) ───
        coins_text = "\n".join(
            f"- {c['name']} ({c['symbol']}) — rank: {c.get('market_cap_rank', 'N/A')}"
            for c in all_coins[:12]
        )

        enrich_prompt = f"""You are a deep niche crypto analyst. I need exactly 6 crypto projects, each from a DIFFERENT niche. The niches MUST be:
1. AI (AI agents, AI trading, on-chain AI)
2. DePIN (decentralized physical infrastructure)
3. RWA (tokenization of real-world assets, T-Bills, real estate on-chain)
4. Bitcoin DeFi / BTC L2 (staking, restaking, L2 on Bitcoin)
5. GameFi (blockchain gaming with real economy)
6. SocialFi (decentralized social networks, tokenized social)
Optional 7th: L2/L3 with hype (new rollups, modular blockchains)

For each project provide:
- name: Project Name (TICKER)
- niche: exact string from the list above (AI / DePIN / RWA / Bitcoin DeFi / GameFi / SocialFi / L2/L3)
- what_does: 1 sentence what the project does
- why_hyping: 1 sentence WHY it's trending NOW (specific: TVL growth %, listing, mainnet, partnership)
- link: official website URL

Available coins from CoinGecko:
{coins_text}

STRICT RULES:
- Each niche must appear AT MOST ONCE. No duplicates.
- Skip generic top-50 CMC coins like ETH, SOL, BNB.
- Prefer deep niche / emerging projects.
- If you can't find a project for a niche, skip that niche — do NOT reuse a niche.

Return JSON array:
[{{"name":"...","niche":"AI","what_does":"...","why_hyping":"...","link":"https://..."}}]
Return ONLY JSON."""

        try:
            enriched = await asyncio.wait_for(ask_ai_list(enrich_prompt), timeout=20)
            if enriched and len(enriched) >= 3:
                valid = [item for item in enriched if all(item.get(k) for k in ("name", "niche", "what_does", "why_hyping", "link"))]
                # Normalize niche names
                for item in valid:
                    item["niche"] = _normalize_niche(item["niche"])
                deduped = _dedup_by_niche(valid, max_per_niche=1)
                if len(deduped) >= 3:
                    logger.info(f"[CryptoSearch] AI enriched {len(deduped)} unique-niche projects (from {len(valid)} raw)")
                    return deduped[:7]
        except asyncio.TimeoutError:
            logger.warning("[CryptoSearch] AI enrichment timed out")

        # ─── Step 3: CoinGecko data with basic enrichment ───
        logger.info("[CryptoSearch] AI failed, building from CoinGecko data")
        slug_to_niche = {v: k for k, v in NICHE_CATEGORY_MAP.items()}
        slug_to_niche["layer-2"] = "L2/L3"
        slug_to_niche["decentralized-science-desci"] = "DeSci"

        result = []
        for coin in all_coins[:12]:
            change = coin.get("price_change_7d")
            niche = slug_to_niche.get(coin.get("category", ""), "")
            if not niche:
                continue
            result.append({
                "name": f"{coin['name']} ({coin['symbol']})",
                "niche": niche,
                "what_does": f"Протокол в нише {niche} — развивающаяся DeFi-инфраструктура с реальным продуктом.",
                "why_hyping": f"Рост объёмов торгов. 7d: {change:+.1f}%" if change else "Активный рост объёмов на DEX.",
                "link": f"https://www.coingecko.com/en/coins/{coin['id']}",
            })
        deduped = _dedup_by_niche(result, max_per_niche=1)
        if deduped:
            logger.info(f"[CryptoSearch] CoinGecko basic: {len(deduped)} unique-niche projects (from {len(result)} raw)")
            return deduped[:7]

    # ─── Step 4: CoinGecko failed → rotated deep niche fallback ───
    logger.warning("[CryptoSearch] CoinGecko failed, using rotated fallback")
    pool = random.choice(FALLBACK_CRYPTO_POOLS)
    deduped = _dedup_by_niche(pool, max_per_niche=1)
    if len(deduped) < 4:
        # If this pool has duplicates, try other pools and merge
        all_unique = dict()  # niche -> item
        for p in FALLBACK_CRYPTO_POOLS:
            for item in p:
                niche = _normalize_niche(item.get("niche", ""))
                if niche and niche not in all_unique:
                    all_unique[niche] = item
        deduped = list(all_unique.values())[:7]
    return deduped


async def validate_store_site(url: str) -> dict:
    """STRICT check: store must return 200 OK with ACTUAL products via JSON endpoint.

    Returns dict:
      {"accessible": bool, "platform": str, "product_count": int, "url": str}

    HARD RULES — a store is ONLY accessible if:
      - Shopify: /products.json returns 200 with non-empty "products" array
      - WooCommerce: /wp-json/wc/v3/products returns 200 with array of products
    Everything else (HTML detection, collections page, unknown platform) = NOT accessible.
    """
    if not url:
        return {"accessible": False, "platform": "unknown", "product_count": 0, "url": url}

    base = url.rstrip("/")

    # Normalize URL
    if not base.startswith("http"):
        base = "https://" + base

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }

            # ── Test 1: Shopify /products.json — MUST return JSON with products ──
            try:
                resp = await client.get(f"{base}/products.json", headers=headers)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        products = data.get("products", [])
                        count = len(products)
                        if count >= 15:
                            logger.info(f"[Validate] {url}: SHOPIFY ✅ ({count} products in JSON)")
                            return {
                                "accessible": True,
                                "platform": "Shopify",
                                "product_count": count,
                                "url": base,
                            }
                        elif count > 0:
                            logger.info(f"[Validate] {url}: SHOPIFY ⚠️ only {count} products (need 15+)")
                    except Exception:
                        logger.info(f"[Validate] {url}: /products.json 200 but not valid JSON")
            except Exception:
                pass

            # ── Test 2: WooCommerce /wp-json/wc/v3/products — MUST return JSON ──
            try:
                resp = await client.get(f"{base}/wp-json/wc/v3/products", headers=headers)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if isinstance(data, list) and len(data) >= 15:
                            logger.info(f"[Validate] {url}: WOOCOMMERCE ✅ ({len(data)} products)")
                            return {
                                "accessible": True,
                                "platform": "WooCommerce",
                                "product_count": len(data),
                                "url": base,
                            }
                    except Exception:
                        pass
            except Exception:
                pass

            # ── ALL OTHER CHECKS REMOVED ──
            # No HTML-based detection, no collections page, no "other" platform.
            # If the site doesn't give us JSON with products, it's NOT accessible.

            logger.info(f"[Validate] {url}: ❌ NO JSON products endpoint found")
            return {"accessible": False, "platform": "blocked", "product_count": 0, "url": base}

    except Exception as e:
        logger.warning(f"[Validate] {url}: Error: {e}")
        return {"accessible": False, "platform": "error", "product_count": 0, "url": url}


async def _validate_batch(items: list[dict], checked_urls: set[str]) -> list[dict]:
    """Validate a batch of store candidates. Returns newly verified items."""
    fresh = [i for i in items if i.get("name") and i.get("link", "").strip() not in checked_urls]
    if not fresh:
        return []

    tasks = [validate_store_site(i.get("link", "").strip()) for i in fresh]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    verified = []
    for item, result in zip(fresh, results):
        if isinstance(result, Exception):
            logger.info(f"[StoresSearch] ❌ SKIP {item.get('name')}: validation error")
            continue
        accessible = result.get("accessible", False)
        pcount = result.get("product_count", 0)
        if accessible and pcount > 0:
            item["platform_detected"] = result.get("platform", "unknown")
            item["product_count"] = pcount
            item["parse_status"] = f"✅ Каталог доступен ({pcount} товаров)"
            verified.append(item)
            checked_urls.add(item.get("link", "").strip())
            logger.info(f"[StoresSearch] ✅ VERIFIED {item.get('name')}: {result.get('platform')} ({pcount})")
        else:
            logger.info(f"[StoresSearch] ❌ SKIP {item.get('name')}: no JSON products")
    return verified


async def search_stores_deep() -> list[dict]:
    """Search for young, parseable Shopify/WooCommerce DTC stores in PREMIUM niches.

    HARD RULE: Only stores with VERIFIED JSON product access are shown to user.
    MINIMUM: Do NOT return fewer than 6 verified stores unless all options exhausted.

    Flow:
    1. Ask AI for 20 young European DTC stores (30s timeout)
    2. VALIDATE each: check /products.json or /wp-json/wc/v3/products
    3. KEEP ONLY stores with 200 OK + actual products in JSON
    4. If <6 verified → retry AI up to 5 more times (each with 20 new stores)
    5. Each retry uses BOTH OpenRouter and Gemini in parallel
    6. If still <6 → validate ALL fallback pools until we have 6+
    7. Only return whatever we have if ALL options truly exhausted
    """
    MIN_STORES = 6
    MAX_STORES = 10
    MAX_RETRIES = 5
    verified_items: list[dict] = []
    checked_urls: set[str] = set()

    # ═══════════════════════════════════════════════════════
    # ROUND 1: Initial AI call (20 stores)
    # ═══════════════════════════════════════════════════════
    try:
        items = await asyncio.wait_for(ask_ai_list(PROMPT_STORES), timeout=35)
        if items:
            valid = [i for i in items if i.get("name") and i.get("link")]
            if valid:
                logger.info(f"[StoresSearch] ROUND 1: AI returned {len(valid)} stores, validating...")
                verified_items.extend(await _validate_batch(valid, checked_urls))
    except asyncio.TimeoutError:
        logger.warning("[StoresSearch] ROUND 1: AI timed out")
    except Exception as e:
        logger.warning(f"[StoresSearch] ROUND 1: AI error: {e}")

    if len(verified_items) >= MIN_STORES:
        logger.info(f"[StoresSearch] ROUND 1 done: {len(verified_items)} verified ✅")
        return verified_items[:MAX_STORES]

    # ═══════════════════════════════════════════════════════
    # ROUNDS 2-6: Aggressive retries — OpenRouter + Gemini in parallel
    # ═══════════════════════════════════════════════════════
    for attempt in range(MAX_RETRIES):
        if len(verified_items) >= MIN_STORES:
            break

        logger.info(
            f"[StoresSearch] RETRY {attempt+1}/{MAX_RETRIES}: "
            f"{len(verified_items)}/{MIN_STORES} verified, trying OpenRouter + Gemini..."
        )

        # Run OpenRouter AND Gemini in parallel for different stores
        async def _fetch_or() -> list:
            try:
                return await asyncio.wait_for(ask_ai_list(PROMPT_STORES_RETRY), timeout=30)
            except Exception:
                return []

        async def _fetch_gem() -> list:
            try:
                result = await asyncio.wait_for(ask_gemini(PROMPT_STORES_RETRY), timeout=40)
                if result:
                    return _extract_json_list(result)
            except Exception:
                pass
            return []

        or_items, gem_items = await asyncio.gather(_fetch_or(), _fetch_gem())
        combined = or_items + gem_items

        if combined:
            logger.info(f"[StoresSearch] RETRY {attempt+1}: got {len(or_items)} OR + {len(gem_items)} Gemini stores")
            new_verified = await _validate_batch(combined, checked_urls)
            verified_items.extend(new_verified)
        else:
            logger.info(f"[StoresSearch] RETRY {attempt+1}: AI returned nothing")

        if len(verified_items) >= MIN_STORES:
            break

    if len(verified_items) >= MIN_STORES:
        logger.info(f"[StoresSearch] After {MAX_RETRIES} retries: {len(verified_items)} verified ✅")
        return verified_items[:MAX_STORES]

    # ═══════════════════════════════════════════════════════
    # FINAL: Validate ALL fallback pools until we hit 6+
    # ═══════════════════════════════════════════════════════
    logger.warning(
        f"[StoresSearch] AI gave only {len(verified_items)} verified, "
        f"validating ALL fallback pools..."
    )
    fallback_verified = await _get_validated_fallback_stores()
    # Merge, dedup by URL
    fallback_urls = {i.get("link", "").strip() for i in verified_items}
    for item in fallback_verified:
        if item.get("link", "").strip() not in fallback_urls:
            verified_items.append(item)
            fallback_urls.add(item.get("link", "").strip())

    logger.info(f"[StoresSearch] FINAL: {len(verified_items)} verified (AI + fallback)")
    return verified_items[:MAX_STORES]


async def _get_validated_fallback_stores() -> list[dict]:
    """Validate ALL stores from ALL fallback pools.
    Only return stores with VERIFIED product JSON access.
    Checks every pool to maximize verified count.
    """
    verified = []
    checked = set()

    for pool_idx, pool in enumerate(FALLBACK_STORES_POOLS):
        if not pool:
            continue
        # Filter out already-checked URLs
        fresh_items = [
            item for item in pool
            if item.get("link", "").strip() not in checked
        ]
        if not fresh_items:
            continue

        tasks = [validate_store_site(item.get("link", "").strip()) for item in fresh_items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for item, result in zip(fresh_items, results):
            checked.add(item.get("link", "").strip())
            if isinstance(result, Exception):
                logger.info(f"[FallbackStores] ❌ SKIP {item.get('name')}: error")
                continue
            accessible = result.get("accessible", False)
            pcount = result.get("product_count", 0)
            platform = result.get("platform", "unknown")
            item["platform_detected"] = platform
            item["product_count"] = pcount
            if accessible and pcount > 0:
                item["parse_status"] = f"✅ Каталог доступен ({pcount} товаров)"
                verified.append(item)
                logger.info(f"[FallbackStores] ✅ POOL{pool_idx+1} VERIFIED {item.get('name')}: {platform} ({pcount})")
            else:
                logger.info(f"[FallbackStores] ❌ POOL{pool_idx+1} SKIP {item.get('name')}: no JSON")

        if len(verified) >= 10:
            break

    logger.info(f"[FallbackStores] Total: {len(verified)} verified across {len(FALLBACK_STORES_POOLS)} pools")
    return verified[:10]


async def search_companies_deep() -> list[dict]:
    """Search for trending niche startups/companies.

    Strategy:
    1. Ask AI with strict niche prompt (25s timeout)
    2. If AI fails, use rotated fallback pools
    """
    try:
        items = await asyncio.wait_for(ask_ai_list(PROMPT_COMPANIES), timeout=25)
        if items and len(items) >= 3:
            valid = [item for item in items if all(item.get(k) for k in ("name", "description", "link"))]
            if len(valid) >= 3:
                logger.info(f"[CompaniesSearch] AI returned {len(valid)} companies")
                return valid[:8]
    except asyncio.TimeoutError:
        logger.warning("[CompaniesSearch] AI timed out")
    except Exception as e:
        logger.warning(f"[CompaniesSearch] AI error: {e}")

    logger.warning("[CompaniesSearch] Using rotated fallback")
    return random.choice(FALLBACK_COMPANIES_POOLS)


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


async def parse_store_products(url: str, desc: str = "", name: str = "") -> list[dict]:
    """Scrape product data from an online store.

    PRIORITY ORDER (matches validate_store_site exactly):
      1. Shopify /products.json — SAME endpoint validator confirmed works
      2. WooCommerce /wp-json/wc/v3/products — SAME endpoint validator confirmed works
      3. HTML fallback: JSON-LD, CSS selectors, product links (only if JSON fails)
    """
    if not url:
        return []

    try:
        import json as _json
        from urllib.parse import urljoin, urlparse
        from bs4 import BeautifulSoup

        BROWSER_HEADERS = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        }
        JSON_HEADERS = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        }

        products: list[dict] = []
        base = url.rstrip("/")

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:

            # ═══════════════════════════════════════════════════════════
            # PRIORITY 1: Shopify /products.json — SAME as validator
            # ═══════════════════════════════════════════════════════════
            try:
                resp = await client.get(f"{base}/products.json", headers=JSON_HEADERS)
                if resp.status_code == 200:
                    data = resp.json()
                    shopify_products = data.get("products", [])
                    if shopify_products:
                        for sp in shopify_products:
                            pname = sp.get("title", "")
                            pimages = sp.get("images", [])
                            img = pimages[0].get("src", "") if pimages else ""
                            if not img:
                                # Try featured_image in variants
                                variants = sp.get("variants", [])
                                if variants:
                                    img = variants[0].get("featured_image", {}).get("src", "")
                            pprice = ""
                            variants = sp.get("variants", [])
                            if variants:
                                pprice = variants[0].get("price", "")
                                currency = sp.get("vendor", "")
                            # Normalize image URL
                            if img and img.startswith("//"):
                                img = "https:" + img
                            elif img and img.startswith("/"):
                                parsed = urlparse(url)
                                img = f"{parsed.scheme}://{parsed.netloc}{img}"

                            if pname:
                                products.append({
                                    "name": pname[:120],
                                    "image": img[:500] if img else "",
                                    "price": pprice[:60] if pprice else "",
                                })
                        if products:
                            logger.info(
                                f"[ParseProducts] ✅ Shopify /products.json: "
                                f"{len(products)} products from {url}"
                            )
            except Exception as e:
                logger.debug(f"[ParseProducts] /products.json failed: {e}")

            # ═══════════════════════════════════════════════════════════
            # PRIORITY 2: WooCommerce /wp-json/wc/v3/products
            # ═══════════════════════════════════════════════════════════
            if not products:
                try:
                    resp = await client.get(
                        f"{base}/wp-json/wc/v3/products",
                        headers=JSON_HEADERS,
                    )
                    if resp.status_code == 200:
                        wc_products = resp.json()
                        if isinstance(wc_products, list) and wc_products:
                            for wp in wc_products:
                                pname = wp.get("name", "")
                                img = ""
                                images = wp.get("images", [])
                                if images:
                                    img = images[0].get("src", "")
                                pprice = wp.get("price", "")
                                if img and img.startswith("//"):
                                    img = "https:" + img
                                if pname:
                                    products.append({
                                        "name": pname[:120],
                                        "image": img[:500] if img else "",
                                        "price": pprice[:60] if pprice else "",
                                    })
                            if products:
                                logger.info(
                                    f"[ParseProducts] ✅ WooCommerce JSON: "
                                    f"{len(products)} products from {url}"
                                )
                except Exception as e:
                    logger.debug(f"[ParseProducts] /wp-json/wc/v3/products failed: {e}")

            # ═══════════════════════════════════════════════════════════
            # PRIORITY 3: HTML fallback (only if JSON gave nothing)
            # ═══════════════════════════════════════════════════════════
            if not products:
                paths_to_try = [
                    base + "/shop",
                    base + "/collections/all",
                    base + "/en/shop",
                    base + "/en/collections/all",
                    base + "/shop-all",
                    base + "/category/all",
                    base + "/new",
                    base + "/en/new",
                    base + "/products",
                ]
                urls_to_try = [base] + paths_to_try

                for try_url in urls_to_try:
                    try:
                        resp = await client.get(try_url, headers=BROWSER_HEADERS)
                        if resp.status_code != 200:
                            continue
                        html = resp.text[:300000]
                        soup = BeautifulSoup(html, "lxml")

                        # ── Strategy A: JSON-LD Product / ItemList ──
                        for script_tag in soup.find_all("script", type="application/ld+json"):
                            try:
                                data = _json.loads(script_tag.string)
                                items = []
                                if isinstance(data, dict):
                                    if data.get("@type") == "ItemList":
                                        items = data.get("itemListElement", [])
                                    elif data.get("@graph"):
                                        items = data.get("@graph", [])
                                    elif data.get("@type") == "Product":
                                        items = [data]
                                if isinstance(data, list):
                                    items = data

                                for item in items:
                                    p_type = item.get("@type", "")
                                    if p_type in ("Product", "ListItem"):
                                        prod = item.get("item", item)
                                        if prod.get("@type") != "Product":
                                            continue
                                        pname = prod.get("name", "")
                                        pimg = ""
                                        offers = prod.get("offers", {})
                                        if isinstance(offers, dict):
                                            pimg = offers.get("image", "") or prod.get("image", "")
                                            price = offers.get("price", "")
                                            currency = offers.get("priceCurrency", "")
                                            if price and currency:
                                                price = f"{currency}{price}"
                                        elif isinstance(offers, list) and offers:
                                            pimg = offers[0].get("image", "") or prod.get("image", "")
                                            price = offers[0].get("price", "")
                                            currency = offers[0].get("priceCurrency", "")
                                            if price and currency:
                                                price = f"{currency}{price}"
                                        else:
                                            pimg = prod.get("image", "")
                                            price = ""

                                        if not pimg and isinstance(pimg, list):
                                            pimg = pimg[0] if pimg else ""
                                        if isinstance(pimg, dict):
                                            pimg = pimg.get("url", "")

                                        if pname and pimg:
                                            if pimg.startswith("//"):
                                                pimg = "https:" + pimg
                                            elif pimg.startswith("/"):
                                                pimg = f"https://{urlparse(url).netloc}{pimg}"
                                            products.append({
                                                "name": pname[:120],
                                                "image": pimg[:500],
                                                "price": str(price)[:60] if price else "",
                                            })
                            except Exception:
                                continue

                        if len(products) >= 4:
                            logger.info(f"[ParseProducts] JSON-LD: {len(products)} from {try_url}")
                            break

                        # ── Strategy B: CSS product card selectors ──
                        selectors = [
                            "div.product-card", "div.product-item", "div.product",
                            "li.product", "article.product",
                            "div[class*='product-card']", "div[class*='productCard']",
                            "div[class*='product_item']", "div[class*='item-card']",
                            "div[class*='collection-item']", "a[class*='product']",
                            "div[class*='card-product']",
                        ]
                        cards = []
                        for sel in selectors:
                            found = soup.select(sel)
                            if len(found) >= 2:
                                cards = found
                                break

                        # ── Strategy C: Product links with images ──
                        if len(cards) < 2:
                            for a_tag in soup.select("a[href]"):
                                href = a_tag.get("href", "")
                                if "/products/" in href or "/product/" in href:
                                    parent = a_tag.parent
                                    if parent and parent.find("img"):
                                        cards.append(parent)
                            cards = cards[:24]

                        # ── Extract from cards ──
                        for card in cards[:24]:
                            try:
                                img_tag = card.find("img")
                                if not img_tag:
                                    continue
                                img_src = (
                                    img_tag.get("src") or
                                    img_tag.get("data-src") or
                                    img_tag.get("data-lazy-src") or ""
                                )
                                if not img_src:
                                    srcset = img_tag.get("data-srcset") or img_tag.get("srcset") or ""
                                    if srcset:
                                        first_src = srcset.split(",")[0].strip().split()[0]
                                        if first_src:
                                            img_src = first_src
                                if not img_src or "data:" in img_src:
                                    continue
                                if img_src.startswith("//"):
                                    img_src = "https:" + img_src
                                elif img_src.startswith("/"):
                                    parsed_base = urlparse(url)
                                    img_src = f"{parsed_base.scheme}://{parsed_base.netloc}{img_src}"

                                pname = ""
                                h_tag = card.find(["h3", "h2", "h4", "h5"])
                                if h_tag:
                                    pname = h_tag.get_text(strip=True)
                                if not pname:
                                    a_tag = card.find("a")
                                    if a_tag:
                                        pname = (a_tag.get("title", "") or
                                                 a_tag.get("aria-label", "") or
                                                 a_tag.get_text(strip=True))

                                price = ""
                                price_tag = card.find(string=re.compile(r"[€$£₽]?\s*\d+[.,]\d{2}"))
                                if price_tag:
                                    price = price_tag.strip()
                                if not price:
                                    for cls_pat in ["price", "amount", "cost", "product-price", "money"]:
                                        pt = card.find(class_=re.compile(cls_pat, re.I))
                                        if pt:
                                            price = pt.get_text(strip=True)
                                            break

                                if pname and img_src:
                                    products.append({
                                        "name": pname[:120],
                                        "image": img_src[:500],
                                        "price": price[:60] if price else "",
                                    })
                            except Exception:
                                continue

                        if len(products) >= 4:
                            logger.info(f"[ParseProducts] Cards: {len(products)} from {try_url}")
                            break

                    except Exception as e:
                        logger.debug(f"[ParseProducts] {try_url} failed: {e}")
                        continue

            # Deduplicate by product name (NOT image — many products share empty images)
            seen: set[str] = set()
            unique: list[dict] = []
            for p in products:
                key = p.get("name", "").strip().lower()
                if key and key not in seen:
                    seen.add(key)
                    unique.append(p)

            # Mark every product with source URL for verification
            for p in unique:
                p["source_url"] = url

            logger.info(
                f"[ParseProducts] Total {len(unique)} products from {url} "
                f"(method: {'Shopify JSON' if unique else 'HTML'})"
            )

            return unique[:60]

    except ImportError:
        logger.warning("[ParseProducts] Required lib not installed")
        return []
    except Exception as e:
        logger.warning(f"[ParseProducts] Failed for {url}: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
# AI PROMPTS — TREND SEARCH
# ═══════════════════════════════════════════════════════════════════

PROMPT_STORES = """You are a European tech/electronics DTC analyst. You ONLY find online stores that sell PHYSICAL ELECTRONICS and TECH DEVICES.

ALLOWED PRODUCT CATEGORIES (STRICTLY these 6 — nothing else):
  1. Robot vacuums & smart home: robot vacuum cleaners, smart sensors, smart bulbs, smart plugs/outlets, smart locks, smart thermostats, home automation hubs
  2. IP cameras & security: wireless security cameras, video doorbells, alarm systems, smart intercoms, baby monitors
  3. Kitchen electronics: smart blenders, air fryers, smart coffee makers, sous vide cookers, smart kitchen scales, electric kettles
  4. Sports & fitness electronics: smart watches, smart rings (Oura-style), fitness trackers, heart rate monitors, GPS sport watches, smart jump ropes with counters
  5. Networking equipment: gaming routers, mesh WiFi systems, network switches, WiFi extenders, powerline adapters, SFP modules
  6. Portable electronics: portable projectors, Bluetooth speakers, power banks, portable SSDs, e-readers, dash cams, action cameras

ABSOLUTELY FORBIDDEN (stores selling ANY of these will be REJECTED):
  - Clothing, shoes, fashion, accessories, bags, jewelry, watches (non-smart)
  - Home decor: candles, vases, planters, wallpaper, lamps (non-smart), furniture, art
  - Cosmetics, skincare, beauty products, fragrances
  - Food, drinks, beverages, supplements, matcha, coffee beans, tea
  - Pet supplies, toys, stationery, books
  - Phone cases, screen protectors (too cheap/low-ticket)
  - Yoga mats (non-smart), meditation cushions, basic fitness gear without electronics

CRITICAL REQUIREMENTS — EVERY store must meet ALL:
1. European: EU + UK, Switzerland, Norway
2. Sells REAL tech/electronics devices (not accessories or lifestyle products)
3. On SHOPIFY with open /products.json that returns 200 with products array
4. Store MUST have 15+ products in /products.json
5. NOT a marketplace (NOT Amazon, eBay, Currys, MediaMarkt, Fnac, Darty, El Corte Ingles, Boulanger, Expert, Coolblue)
6. NOT a major brand (NOT Apple, Samsung, Dyson, iRobot, Roborock, Xiaomi, TP-Link direct)

Think of DTC tech brands that built their own Shopify stores:
- Robot vacuum startups (like Neato competitors, new brands)
- Smart home gadget startups
- Fitness tracker/smart ring startups
- Gaming peripheral brands
- Portable tech brands
- Niche audio/speaker brands

Return 20 stores as JSON:
[{"name":"...","category":"robot vacuums & smart home","why_hyping":"...","link":"https://...","country":"Germany","platform":"Shopify"}]"""

PROMPT_STORES_RETRY = """URGENT RETRY. I need European Shopify stores selling ONLY electronics/tech devices.

STRICT PRODUCT RULES — stores must sell products from these categories:
- Robot vacuums, smart home sensors/bulbs/plugs/locks/thermostats
- IP cameras, video doorbells, security systems
- Smart kitchen appliances: blenders, air fryers, coffee makers
- Smart watches, smart rings, fitness trackers, GPS watches
- Gaming routers, mesh WiFi systems, networking gear
- Portable projectors, Bluetooth speakers, power banks, dash cams

FORBIDDEN (zero tolerance):
- Clothing, shoes, bags, jewelry, fashion
- Candles, decor, vases, furniture, art, wallpaper
- Cosmetics, skincare, beauty, fragrances
- Food, drinks, supplements, coffee, tea, matcha
- Phone cases, screen protectors
- Anything that is NOT electronics/tech

REQUIREMENTS:
1. Shopify store with /products.json returning 200 OK
2. 15+ products in the JSON
3. European (EU, UK, CH, NO)
4. NOT behind Cloudflare (403)
5. DIFFERENT stores than before

Return 20 stores: [{"name":"...","category":"...","why_hyping":"...","link":"https://...","country":"...","platform":"Shopify"}]"""

PROMPT_CRYPTO = """You are a DEEP NICHE crypto analyst who tracks projects BEFORE they go mainstream.

CRITICAL: Find projects from THESE specific niches ONLY:
1. AI + Crypto: AI agents on-chain, tokenized AI models, AI-powered trading
2. DePIN: GPU clouds, mapping networks, sensor data, telecom DePIN
3. RWA (Real World Assets): tokenized treasuries, real estate on-chain, credit protocols
4. New L2/L3: Base ecosystem, Blast, Mode Network, Degen Chain, emerging rollups
5. DeSci (Decentralized Science): bioDAOs, IP-NFTs, research funding on-chain
6. Bitcoin DeFi: BTC L2, restaking, Babylon, Merlin Chain, BounceBit
7. GameFi: full virtual economies with real economics
8. SocialFi: decentralized social, tokenized content, creator economies

STRICTLY FORBIDDEN (DO NOT include these or any similarly popular coins):
Bitcoin, Ethereum, Solana, BNB, XRP, Cardano, Avalanche, Polkadot, Chainlink, Polygon,
Uniswap, Aave, MakerDAO, Render Network, io.net, Monad, Ondo Finance,
Berachain, Pepe, any meme coins, any top-50 CMC coins.

For each project provide EXACTLY these fields:
- "name": project name and ticker in parentheses, e.g. "Spectral (SPEC)"
- "niche": one of: AI, DePIN, RWA, L2/L3, DeSci, GameFi, SocialFi, Bitcoin DeFi, Modular
- "why_hyping": 1-2 specific sentences WHY it is trending RIGHT NOW (TVL growth, mainnet launch, listing, funding, partnership)
- "what_does": 1-2 sentences about the actual technology/product
- "link": EXACT URL to the official website

Return ONLY a valid JSON array of exactly 8 projects:
[{"name":"Spectral (SPEC)","niche":"AI","why_hyping":"...","what_does":"...","link":"https://spectral.finance"}]"""

PROMPT_COMPANIES = """You are a technology and business startup analyst. List the TOP 8 most hyped, RAPIDLY GROWING startups and companies globally (2025-2026 era).

CRITICAL: Find REAL STARTUPS and fast-growing tech companies — NOT established giants.
Focus on: Series A-C startups, pre-IPO companies, recently IPO'd tech, companies with explosive growth.

SECTORS: AI, defense tech, biotech, fintech, logistics, green tech, EV, robotics,
healthtech, climate tech, photonics, quantum, semiconductor, space tech, developer tools.

STRICTLY FORBIDDEN (DO NOT include ANY of these):
Apple, Google, Microsoft, Amazon, Meta, Tesla, Nvidia, OpenAI, Samsung, Oracle, SAP,
Salesforce, IBM, Intel, AMD, Cisco, Uber, Airbnb, Spotify, Netflix, Stripe, PayPal,
Shopify, Adobe, ServiceNow, Atlassian, Palantir, Snowflake, Datadog, CrowdStrike.

Also AVOID: Revolut, Klarna, DeepL, Northvolt (too well-known, find FRESHER alternatives).

For each company provide EXACTLY these fields:
- name: exact official company name
- description: 2-3 catchy sentences — what the company does AND why it is trending RIGHT NOW (funding, growth, launch)
- link: EXACT URL to official website
- sector: primary business sector

Return ONLY a valid JSON array of exactly 8 companies, nothing else:
[{"name":"Mistral AI","description":"...","link":"https://mistral.ai","sector":"AI / LLM"}]"""

# ═══════════════════════════════════════════════════════════════════
# IMPROVED OFFER PROMPTS — CATEGORY-SPECIFIC
# ═══════════════════════════════════════════════════════════════════

PROMPT_IMPROVE_STORES = """You are a legendary e-commerce tech innovator and DTC brand strategist.

A client brings you this online store:
NAME: {name}
DESCRIPTION: {description}
ORIGINAL LINK: {link}
CATEGORY: Online Store

Your task — create a DEEPLY ANALYZED improved online store concept.

CRITICAL RULES FOR DTC STORES:
- The improvement must be SPECIFIC to the store's product category — NOT generic tech buzzwords
- Analyze what category this store is in (gadgets, home decor, skincare, fitness, pet supplies, coffee, kitchen, outdoor, etc.) and tailor the innovation accordingly
- Think about: AI-powered personalization, subscription models, AR product preview, community features, sustainability, smart packaging, loyalty/rewards, social commerce, influencer collab platform
- The improved name must be a creative evolution (e.g., BrewDog → BrewDog Craft Lab, Bower Collective → Bower Home, FiID → FiID Motion)
- NEVER use "Pro", "2.0", "+" suffixes — the name must feel like a natural brand extension
- The improvement must address real e-commerce pain points: discovery, trust, returns, personalization, repeat purchases
- Mention "{name}" by name to ensure customization

EXAMPLE transformations (adapt to the actual store category):
- Wild deodorant → Wild Collective: AI-powered personalized refill schedule based on usage patterns, community-driven new scent voting, carbon-neutral last-mile delivery
- Bower Collective → Bower Home: Smart home dispensers auto-order refills via IoT sensors, family usage analytics dashboard, gamified sustainability challenges with rewards
- Coffee Duck → Coffee Duck Roasters: AI-curated monthly coffee box based on taste profile quiz, live roasting sessions on TikTok Shop, NFC-enabled bags with farm-of-origin stories

Return a JSON object with EXACTLY these fields:

1. "improved_name": A creative evolution name of "{name}"

2. "improved_description": 3-4 vivid sentences describing the improved store concept. What specific tech/innovation was added? How does it change the shopping experience? Why would customers obsess over it?

3. "improved_link": A stylized URL (e.g. https://brandname-lab.com or .store or .co or .shop)

4. "killer_feature": 1 sentence about the ONE feature that makes this irresistible

5. "geo_analysis": An OBJECT for DTC store traffic:
{{
  "tier1": [list of 3-4 top markets with 1-line reason — think: UK, Germany, Netherlands, France, Scandinavia, Switzerland],
  "tier2": [list of 3-4 secondary markets],
  "tier3": [list of 2-3 emerging markets],
  "best_platforms": [list of 3-4 platforms — TikTok, Instagram, Pinterest, Google Shopping are MUST-HAVE for DTC],
  "budget_split": "suggested budget % split between GEOs and platforms",
  "estimated_cpa": "estimated CPA range in USD for tier1"
}}

6. "keywords": Category-specific SEO and PPC keywords:
{{
  "branded": [3-4 branded keywords],
  "generic": [4-5 high-volume category keywords],
  "long_tail": [4-5 long-tail category keywords],
  "competitor": [2-3 competitor keywords],
  "negative": [2-3 negative keywords]
}}

7. "target_audience": 2-3 sentences about the ideal customer (age, interests, shopping behavior, income level, values)

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

# Category labels for display
CATEGORY_LABELS: dict[str, str] = {
    "stores": "Магазин",
    "crypto": "Крипто-проект",
    "companies": "Компания / Стартап",
}


async def detect_category(name: str, desc: str, link: str) -> str:
    """Use AI to determine the category of a project.

    Returns one of: "stores", "crypto", "companies".
    Falls back to the button category if AI fails.
    """
    # ─── Heuristic fast check (no AI needed) ───
    desc_lower = desc.lower()
    link_lower = link.lower()
    name_lower = name.lower()

    # Crypto signals
    crypto_keywords = [
        "token", "defi", "blockchain", "web3", "nft", "crypto", "tvl",
        "smart contract", "dao", "staking", "yield", "liquidity",
        "depin", "rwa", "layer-2", "l2", "l3", "rollup", "consensus",
        "coin", "tokenomics", "dex", "ceex", "amm", "bridge",
    ]
    crypto_tlds = [".io", ".xyz", ".network", ".protocol", ".fi", ".finance", ".eth", ".sol", ".chain"]
    crypto_symbols = re.findall(r"\([A-Z]{2,6}\)", name)  # ticker like (SPEC), (VIRTUAL)

    # Store/brand signals (broad — any DTC e-commerce, not just fashion)
    store_keywords = [
        "fashion", "clothing", "brand", "boutique", "womenswear", "menswear",
        "streetwear", "sneakers", "accessories", "collection", "apparel",
        "sustainable fashion", "designer", "шоп", "одежда", "мода",
        "style", "luxury", "ready-to-wear", "rtw", "couture", "runway",
        "silhouette", "fabric", "sewing", "textile", "knitwear",
        # Non-fashion DTC signals
        "store", "shop", "магазин", "товары", "продукты", "buy", "order",
        "кастом", "handmade", "handcrafted", "organic", "eco-friendly",
        "skincare", "cosmetics", "косметика", "уход", "fragrance",
        "coffee", "matcha", "кофе", "спешелти", "gourmet", "food",
        "fitness", "gym", "workout", "yoga", "pilates",
        "pet", "собака", "кошка", "зоотовары", "pet supplies",
        "home", "decor", "декор", "interior", "kitchen", "кухня",
        "gadgets", "гаджеты", "smart", "wireless", "tech",
        "outdoor", "travel", "camping", "hiking",
        "stationery", "канцелярия", "craft", "hobby", "хобби",
        "beer", "craft beer", "wine", "кrafт",
    ]
    store_tlds = [".com", ".store", ".fashion", ".shop", ".co", ".fr", ".dk", ".se", ".de", ".nl", ".it", ".es"]

    # Score each category
    scores = {"crypto": 0, "stores": 0, "companies": 0}

    for kw in crypto_keywords:
        if kw in desc_lower:
            scores["crypto"] += 2
    for tld in crypto_tlds:
        if link_lower.endswith(tld) or f".{tld}" in link_lower:
            scores["crypto"] += 2
    if crypto_symbols:
        scores["crypto"] += 3
    # Ticker-like patterns in name
    if re.search(r"\([A-Z]{2,6}\)", name):
        scores["crypto"] += 3

    for kw in store_keywords:
        if kw in desc_lower:
            scores["stores"] += 2
    for tld in store_tlds:
        if link_lower.endswith(tld):
            scores["stores"] += 1

    # If heuristic gives clear signal (gap of 3+), use it
    max_score = max(scores.values())
    if max_score >= 4:
        best = max(scores, key=scores.get)
        if scores[best] - min(scores.values()) >= 2:
            logger.info(f"[DetectCat] Heuristic: {best} (scores: {scores})")
            return best

    # ─── AI fallback for ambiguous cases ───
    classify_prompt = f"""Classify this project into EXACTLY ONE category.

Project: {name}
Description: {desc[:300]}
Website: {link}

Categories:
- "stores" — DTC online stores, e-commerce brands, product shops (any category: gadgets, home, beauty, fitness, food, pet, etc.)
- "crypto" — Crypto projects, DeFi protocols, blockchain platforms, Web3 apps, token projects, DAOs
- "companies" — Tech startups, SaaS companies, biotech, defense tech, AI companies, enterprise software

Return ONLY ONE WORD: stores, crypto, or companies. Nothing else."""

    try:
        result = await asyncio.wait_for(ask_openrouter(classify_prompt, ""), timeout=15)
        if result:
            detected = result.strip().lower().strip('"').strip("'")
            if detected in ("stores", "crypto", "companies"):
                logger.info(f"[DetectCat] AI classified as: {detected}")
                return detected
    except Exception as e:
        logger.warning(f"[DetectCat] AI failed: {e}")

    # Fallback: return None (caller will use button category)
    return ""


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

FALLBACK_STORES: list[dict] = []  # Kept for compat; use FALLBACK_STORES_POOLS instead

FALLBACK_STORES_POOLS: list[list[dict]] = [
    # ── Pool 1: Smart Home & Robot Vacuums — Shopify tech stores ──
    [
        {
            "name": "Narwal",
            "category": "robot vacuums & smart home",
            "why_hyping": (
                "Робот-пылесос Narwal Freo с самоочисткой — TikTok обзоры 10M+ просмотров. "
                "LiDAR-навигация, вибрация mop. Продажи +300% за год."
            ),
            "link": "https://narwal.com",
            "country": "China/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "SwitchBot",
            "category": "robot vacuums & smart home",
            "why_hyping": (
                "Умный дом — curtains, bulbs, hubs, sensors. TikTok 5M+ просмотров. "
                "Микро-роботы для автоматизации. 50K+ юнитов/мес."
            ),
            "link": "https://switch-bot.com",
            "country": "China/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Aqara",
            "category": "robot vacuums & smart home",
            "why_hyping": (
                "Умный дом — датчики, розетки, моторы для штор, камеры. "
                "YouTube/TikTok обзоры. Ecosystem с Zigbee/Matter. 20K+ заказов/мес."
            ),
            "link": "https://aqara.eu",
            "country": "Germany",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Eufy (Anker)",
            "category": "robot vacuums & smart home",
            "why_hyping": (
                "Роботы-пылесосы и смарт-камеры Anker. Viral unboxing на TikTok. "
                "Бесшумные роботы с самоочисткой. 100K+ продаж/мес."
            ),
            "link": "https://eufy.com",
            "country": "Germany",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Tapo by TP-Link",
            "category": "robot vacuums & smart home",
            "why_hyping": (
                "Датчики, лампочки, камеры, розетки TP-Link Tapo. "
                "Бюджетный умный дом с TikTok-хайпом. 30K+ юнитов/мес."
            ),
            "link": "https://tp-link.com/eu",
            "country": "Netherlands",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Roborock EU",
            "category": "robot vacuums & smart home",
            "why_hyping": (
                "Премиум роботы-пылесосы с LiDAR. TikTok 8M+ обзоров. "
                "Моппинг, самоочистка, 3D mapping. Продажи +500%."
            ),
            "link": "https://roborock.com/eu",
            "country": "China/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Reolink",
            "category": "IP cameras & security",
            "why_hyping": (
                "WiFi камеры и системы безопасности. TikTok unboxing 2M+. "
                "5MP/8MP, colour night vision, person detection. 15K+ продаж/мес."
            ),
            "link": "https://reolink.com",
            "country": "China/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Ezviz",
            "category": "IP cameras & security",
            "why_hyping": (
                "Умные камеры и видеодомофоны. TikTok security reviews 1M+. "
                "Hikvision subsidiary, доступные цены. 25K+ продаж/мес."
            ),
            "link": "https://ezviz.com/eu",
            "country": "China/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
    ],
    # ── Pool 2: Kitchen Electronics & Fitness Tech — Shopify tech stores ──
    [
        {
            "name": "Ninja Kitchen EU",
            "category": "kitchen electronics",
            "why_hyping": (
                "Электроника для кухни — блендеры, фритюрницы, грили. "
                "TikTok cooking videos 20M+. Viral air fryer reviews. 200K+ продаж/мес."
            ),
            "link": "https://ninjakitchen.eu",
            "country": "UK",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Sage Appliances",
            "category": "kitchen electronics",
            "why_hyping": (
                "Умные кофемашины, тостеры, блендеры. TikTok 3M+ обзоров. "
                "Premium kitchen tech. 50K+ продаж/мес в EU."
            ),
            "link": "https://sageappliances.com",
            "country": "UK/Australia",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Oura Ring",
            "category": "sports & fitness electronics",
            "why_hyping": (
                "Умное кольцо Oura Ring Gen 3. TikTok 500M+ просмотров. "
                "Трекинг сна, HRV, температуры. Продажи +400%."
            ),
            "link": "https://ouraring.com",
            "country": "Finland/US",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Whoop",
            "category": "sports & fitness electronics",
            "why_hyping": (
                "Фитнес-трекер с подписочной моделью. Viral на TikTok среди атлетов. "
                "HRV, recovery, strain monitoring. 100K+ подписчиков."
            ),
            "link": "https://whoop.com",
            "country": "US/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Coros",
            "category": "sports & fitness electronics",
            "why_hyping": (
                "GPS sport watches для бегунов. TikTok running community 2M+. "
                "14 дней батареи, точный GPS. 15K+ продаж/мес."
            ),
            "link": "https://coros.com",
            "country": "China/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "ASUS ROG EU",
            "category": "networking equipment",
            "why_hyping": (
                "Игровые роутеры и mesh-системы. TikTok gaming setups 5M+. "
                "ROG Rapture GT-AX6000, AiMesh. 20K+ продаж/мес."
            ),
            "link": "https://rog.asus.com",
            "country": "Taiwan/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Deco by TP-Link",
            "category": "networking equipment",
            "why_hyping": (
                "Mesh WiFi системы Deco. TikTok smart home setups 3M+. "
                "WiFi 6/7, coverage 500m2. 30K+ юнитов/мес."
            ),
            "link": "https://tp-link.com/deco",
            "country": "Netherlands",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Synology",
            "category": "networking equipment",
            "why_hyping": (
                "NAS и сетевое хранение. YouTube/TikTok homelab 10M+. "
                "Media server, surveillance, backup. 15K+ продаж/мес."
            ),
            "link": "https://synology.com",
            "country": "Taiwan/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
    ],
    # ── Pool 3: Portable Electronics & Niche Tech — Shopify tech stores ──
    [
        {
            "name": "Anker EU",
            "category": "portable electronics",
            "why_hyping": (
                "Пауэрбанки, колонки, кабели, проекторы. TikTok tech reviews 50M+. "
                "Nebula проекторы, Soundcore колонки. 500K+ продаж/мес."
            ),
            "link": "https://anker.com",
            "country": "China/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Wemo",
            "category": "robot vacuums & smart home",
            "why_hyping": (
                "Умные розетки, диммеры, датчики движения Belkin. "
                "TikTok smart home tours 1M+. Matter/HomeKit совместимые."
            ),
            "link": "https://wemo.com",
            "country": "US/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Arlo EU",
            "category": "IP cameras & security",
            "why_hyping": (
                "Беспроводные камеры безопасности с аккумулятором. TikTok 3M+. "
                "AI person detection, colour night vision. 40K+ продаж/мес."
            ),
            "link": "https://arlo.com",
            "country": "US/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "MagSafe magnets EU",
            "category": "portable electronics",
            "why_hyping": (
                "Портативные колонки с MagSafe, зарядки, проекторы. "
                "TikTok unboxing 5M+. Компактные гаджеты для Apple. 20K+ продаж/мес."
            ),
            "link": "https://mag-safe.eu",
            "country": "Netherlands",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Garmin EU",
            "category": "sports & fitness electronics",
            "why_hyping": (
                "Спортивные часы и GPS-трекеры. TikTok fitness 8M+. "
                "Forerunner, Fenix, Venu. Мульти-спорт. 60K+ продаж/мес."
            ),
            "link": "https://garmin.com",
            "country": "Switzerland/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Xiaomi EU",
            "category": "robot vacuums & smart home",
            "why_hyping": (
                "Роботы-пылесосы, увлажнители,空气净化器, проекторы. "
                "TikTok tech 100M+. Бюджетные смарт-устройства. 300K+ продаж/мес."
            ),
            "link": "https://mi.com/eu",
            "country": "China/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Netatmo",
            "category": "robot vacuums & smart home",
            "why_hyping": (
                "Французский умный дом — камеры, термостаты, датчики погоды. "
                "TikTok smart home EU 2M+. Design-oriented. 10K+ продаж/мес."
            ),
            "link": "https://netatmo.com",
            "country": "France",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
        {
            "name": "Sonos EU",
            "category": "portable electronics",
            "why_hyping": (
                "WiFi колонки и home cinema. TikTok audio setups 5M+. "
                "Portability, multi-room, Dolby Atmos. 30K+ продаж/мес."
            ),
            "link": "https://sonos.com",
            "country": "US/EU",
            "platform_detected": "Shopify",
            "parse_status": "",
            "product_count": 0,
        },
    ],
]

FALLBACK_CRYPTO: list[dict] = []  # Kept for compat; use FALLBACK_CRYPTO_POOLS instead

FALLBACK_CRYPTO_POOLS: list[list[dict]] = [
    # ── Pool 1: all 7 niches unique ──
    [
        {
            "name": "Spectral (SPEC)",
            "niche": "AI",
            "why_hyping": (
                "On-chain AI-агенты из промптов — синтаксис для смарт-контрактов. "
                "TVL вырос на 400% за 30 дней. Активно интегрируется в DeFi."
            ),
            "what_does": (
                "Токенизация и синтез AI-агентов, которые автономно торгуют, "
                "анализируют рынки и управляют DeFi-позициями."
            ),
            "link": "https://spectral.finance",
        },
        {
            "name": "Hivemapper (HONEY)",
            "niche": "DePIN",
            "why_hyping": (
                "150K+ дэш-камер по всему миру. Покрытие выросло на 200% за квартал. "
                "Контракты с Mapillary и Niantic."
            ),
            "what_does": (
                "Водители с дэш-камерами собирают карту в реальном времени. "
                "Токены HONEY за каждый километр. Данные продаются компаниям."
            ),
            "link": "https://hivemapper.com",
        },
        {
            "name": "Midas (MIDAS)",
            "niche": "RWA",
            "why_hyping": (
                "Токенизированные гособлигации США с 5%+ on-chain. "
                "TVL: $10M → $200M+ за 2 месяца."
            ),
            "what_does": (
                "RWA-платформа токенизирует казначейские облигации США "
                "и другие активы для DeFi-доступа к стабильному доходу."
            ),
            "link": "https://midas.app",
        },
        {
            "name": "Babylon (BABY)",
            "niche": "Bitcoin DeFi",
            "why_hyping": (
                "Bitcoin staking для безопасности PoS-сетей — $5B+ BTC застейкано. "
                "Партнёрства с 50+ L2/L1 проектами."
            ),
            "what_does": (
                "Владельцы BTC стейкают биткоины для обеспечения безопасности "
                "PoS-сетей, не покидая Bitcoin L1."
            ),
            "link": "https://babylonlabs.io",
        },
        {
            "name": "Illuvium (ILV)",
            "niche": "GameFi",
            "why_hyping": (
                "AAA-качество auto-battler RPG на Immutable X. "
                "$100M+ привлечено. Первый реальный GameFi с графикой уровня AAA."
            ),
            "what_does": (
                "Blockchain RPG с auto-battler механикой и collectible NFT-персонажами. "
                "Полная игровая экономика с land, crafting, PVP."
            ),
            "link": "https://illuvium.io",
        },
        {
            "name": "Friend.tech (FRIEND)",
            "niche": "SocialFi",
            "why_hyping": (
                "Возрождение на Base — токенизированные соцсети. "
                "Перенос на Base привлек 500K+ юзеров. Новый сезон с улучшенной экономикой."
            ),
            "what_does": (
                "Децентрализованная соцсеть: profile-bound токены для создателей. "
                "Чаты, tipping, exclusive content — всё on-chain."
            ),
            "link": "https://www.friend.tech",
        },
        {
            "name": "Mode Network (MODE)",
            "niche": "L2/L3",
            "why_hyping": (
                "L2 на OP Stack с ретро-дропами. TVL +350% за месяц. "
                "Onchain Boost — часть комиссий sequencer идёт протоколам."
            ),
            "what_does": (
                "Optimistic Rollup L2 с уникальной моделью: комиссии от sequencer "
                "распределяются между протоколами, привлекающими пользователей."
            ),
            "link": "https://mode.network",
        },
    ],
    # ── Pool 2: all 7 niches unique (different projects) ──
    [
        {
            "name": "Virtuals Protocol (VIRTUAL)",
            "niche": "AI",
            "why_hyping": (
                "AI-агенты с токенизацией на Base — самый хайповый narrative 2025. "
                "Капитализация с $50M до $2B+ за 3 месяца. AIXBT — вирусный инфлюенсер."
            ),
            "what_does": (
                "Создание, токенизация и монетизация AI-агентов. Каждый агент — "
                "автономная сущность с токеном, взаимодействующая в соцсетях и DeFi."
            ),
            "link": "https://virtuals.io",
        },
        {
            "name": "Aethir (ATH)",
            "niche": "DePIN",
            "why_hyping": (
                "90K+ GPU-нод для AI и cloud gaming. Партнёрство с Qualcomm. "
                "Выручка $30M+ за квартал — один из немногих DePIN с реальным revenue."
            ),
            "what_does": (
                "Enterprise-grade DePIN для распределённых GPU-вычислений: "
                "AI-инференс, облачный гейминг, рендеринг."
            ),
            "link": "https://www.aethir.com",
        },
        {
            "name": "OpenEden (TBILL)",
            "niche": "RWA",
            "why_hyping": (
                "Токенизированные T-Bills с реальным доходом 5%+ APY. "
                "TVL вырос с $5M до $500M+. Аудит Big Four."
            ),
            "what_does": (
                "Институциональная RWA-платформа для токенизации казначейских "
                "векселей США на Ethereum и Mantle."
            ),
            "link": "https://www.openeden.com",
        },
        {
            "name": "BounceBit (BB)",
            "niche": "Bitcoin DeFi",
            "why_hyping": (
                "Bitcoin restaking на BRC-20 — уникальный bridge между BTC DeFi "
                "и EVM-экосистемой. TVL $500M+."
            ),
            "what_does": (
                "Позволяет стейкать BTC для заработка yield через DeFi-протоколы "
                "на EVM-совместимых сетях."
            ),
            "link": "https://bouncebit.io",
        },
        {
            "name": "Pixels (PIXEL)",
            "niche": "GameFi",
            "why_hyping": (
                "Farm-sim на Ronin Network — 1M+ DAU. Стал одним из самых "
                "играемых Web3-игр. Монетизация через премиум-предметы."
            ),
            "what_does": (
                "Блокчейн-игра в стиле Stardew Valley: farming, crafting, "
                "социальные механики. Встроенная NFT-экономика."
            ),
            "link": "https://pixels.xyz",
        },
        {
            "name": "Farcaster",
            "niche": "SocialFi",
            "why_hyping": (
                "Децентрализованный Twitter на Ethereum. 500K+ MAU. "
                "Frames — viral feature для встроенных mini-apps. Warps привлёк $150M."
            ),
            "what_does": (
                "Децентрализованная социальная сеть с open protocol. "
                "Frames позволяют создавать интерактивные мини-приложения в постах."
            ),
            "link": "https://farcaster.xyz",
        },
        {
            "name": "Blast (BLAST)",
            "niche": "L2/L3",
            "why_hyping": (
                "L2 с native yield на ETH и USDB. $2B+ TVL на аирдроп. "
                "Parrots — самый популярный DApp в экосистеме."
            ),
            "what_does": (
                "Optimistic Rollup на Ethereum с автоматическим yield для ETH и "
                "стейблкоинов. Аэрдроп $BLAST — один из крупнейших в 2024."
            ),
            "link": "https://blast.io",
        },
    ],
    # ── Pool 3: all 7 niches unique (more different projects) ──
    [
        {
            "name": "Sona (SONA)",
            "niche": "AI",
            "why_hyping": (
                "AI-протокол для генерации музыки. Партнёрство с Universal Music. "
                "Trending narrative: AI + Music. Токен вырос 500% на аирдроп."
            ),
            "what_does": (
                "Децентрализованная платформа для AI-генерации и лицензирования "
                "музыки. Решает проблемы copyright в AI-music."
            ),
            "link": "https://sona.xyz",
        },
        {
            "name": "Grass (GRASS)",
            "niche": "DePIN",
            "why_hyping": (
                "Браузерное DePIN — продаёт bandwidth данных для AI training. "
                "2M+ пользователей. Токен на Bybit и Binance."
            ),
            "what_does": (
                "Расширение браузера, которое собирает bandwidth для AI-компаний. "
                "Пользователи получают GRASS за расшаренный интернет."
            ),
            "link": "https://app.getgrass.io",
        },
        {
            "name": "Centrifuge (CFG)",
            "niche": "RWA",
            "why_hyping": (
                "Крупнейшая DeFi-платформа для реальных активов — $200M+ TVL. "
                "Токенизирует кредиты, недвижимость и инвойсы."
            ),
            "what_does": (
                "Liquidity pool для RWA: реальные активы (кредиты, недвижимость) "
                "становятся collateral в DeFi-протоколах."
            ),
            "link": "https://centrifuge.io",
        },
        {
            "name": "Lombard Staked BTC (LBTC)",
            "niche": "Bitcoin DeFi",
            "why_hyping": (
                "Liquid staking Bitcoin — LBTC используется как collateral в DeFi. "
                "TVL $1B+. Интеграция с Aave, Compound, Uniswap."
            ),
            "what_does": (
                "Протокол liquid staking для Bitcoin: стейкаешь BTC, получаешь LBTC, "
                "который можно использовать в DeFi-протоколах на Ethereum."
            ),
            "link": "https://lombard.finance",
        },
        {
            "name": "Shrapnel (SHRAP)",
            "niche": "GameFi",
            "why_hyping": (
                "AAA FPS на Avalanche — extraction shooter с NFT-лутом. "
                "$40M+ финансирование. Открытый бета-тест привлек 1M+ игроков."
            ),
            "what_does": (
                "Competitive FPS с реальной экономикой: NFT-оружие, карты, скины. "
                "Игроки создают контент и продают его на маркетплейсе."
            ),
            "link": "https://shrapnel.com",
        },
        {
            "name": "Lens Protocol",
            "niche": "SocialFi",
            "why_hyping": (
                "Social graph на Polygon — Aave-команда. 500K+ профилей. "
                "Open social graph для Web3: любой может строить соцсети поверх Lens."
            ),
            "what_does": (
                "Децентрализованный social graph: профиль, подписки, контент — всё NFT. "
                "Разработчики строят фронты поверх открытого протокола."
            ),
            "link": "https://lens.xyz",
        },
        {
            "name": "Mantle (MNT)",
            "niche": "L2/L3",
            "why_hyping": (
                "L2 на OP Stack с $1B+ TVL. Mantle Treasury управляет $3B+. "
                "mETH Protocol — liquid staking с интеграцией в DeFi."
            ),
            "what_does": (
                "Optimistic Rollup L2 с модульной архитектурой: DA-слой (EigenDA), "
                "execution, staking. Один из крупнейших L2 по TVL."
            ),
            "link": "https://mantle.xyz",
        },
    ],
]

FALLBACK_COMPANIES: list[dict] = []  # Kept for compat; use FALLBACK_COMPANIES_POOLS instead

FALLBACK_COMPANIES_POOLS: list[list[dict]] = [
    # ── Pool 1: European AI & Defense ──
    [
        {
            "name": "Helsing",
            "description": (
                "European AI defense startup — sovereign AI для НАТО. "
                "$500M+ привлечено. European answer to Palantir. "
                "Контракты с министерствами обороны Германии, Франции, Испании."
            ),
            "link": "https://helsing.ai",
            "sector": "AI / Defense",
        },
        {
            "name": "Mistral AI",
            "description": (
                "Французский AI-лаб — $600M+ раунд, конкурирует с OpenAI. "
                "Модели Mistral Large и Codestral. Самый быстрорастущий "
                "European AI-стартап. Open-source + enterprise."
            ),
            "link": "https://mistral.ai",
            "sector": "AI / LLM",
        },
        {
            "name": "Synthesia",
            "description": (
                "UK AI video generation — $90M funding, enterprise focus. "
                "Генерация профессиональных видео из текста за минуты. "
                "2,000+ enterprise клиентов, replacing traditional video production."
            ),
            "link": "https://www.synthesia.io",
            "sector": "AI / Video",
        },
        {
            "name": "DeepL",
            "description": (
                "Cologne AI-перевод, превосходящий Google Translate. "
                "$2B valuation. Enterprise-клиенты массово переходят "
                "с Google/DeepL. Pro-версия для команд."
            ),
            "link": "https://www.deepl.com",
            "sector": "AI / Language",
        },
        {
            "name": "Hugging Face",
            "description": (
                "French AI — GitHub для ML-моделей. $4.5B valuation. "
                "Главная платформа open-source AI. "
                "100B+ downloads моделей, every AI dev uses it."
            ),
            "link": "https://huggingface.co",
            "sector": "AI / Platform",
        },
        {
            "name": "Owkin",
            "description": (
                "French AI-биотех — $300M+ funding. AI для "
                "открытия лекарств и диагностики. Партнёрства с Pfizer и Sanofi."
            ),
            "link": "https://www.owkin.com",
            "sector": "Biotech / AI",
        },
        {
            "name": "Alan",
            "description": (
                "French healthtech insurtech — preventative healthcare. "
                "$600M+ valuation, 800K+ members. AI-ассистент для "
                "пользователей и автоматизированные выплаты."
            ),
            "link": "https://www.alan.com",
            "sector": "Healthtech / Insurtech",
        },
        {
            "name": "Meilisearch",
            "description": (
                "French open-source search engine — Rust-based, instant results. "
                "Альтернатива Algolia/Elasticsearch. Growing 200% YoY. "
                "80K+ GitHub stars, $25M+ funding."
            ),
            "link": "https://www.meilisearch.com",
            "sector": "DevTools / Search",
        },
    ],
    # ── Pool 2: Global hot startups ──
    [
        {
            "name": "Groq",
            "description": (
                "AI chip startup — ultra-fast LPU inference. "
                "В 10x быстрее GPU для LLM. $600M+ funding. "
                "Open-source model hosting. Конкурирует с NVIDIA."
            ),
            "link": "https://groq.com",
            "sector": "AI Chips / Infrastructure",
        },
        {
            "name": "ElevenLabs",
            "description": (
                "Polish AI voice cloning — $80M+ funding. Самый реалистичный "
                "AI-voice на рынке. dubbing для контента, audiobooks, gaming. "
                "1M+ users."
            ),
            "link": "https://elevenlabs.io",
            "sector": "AI / Audio",
        },
        {
            "name": "Figure AI",
            "description": (
                "US humanoid robotics — $675M+ funding. Роботы-гуманоиды "
                "для складов и мануфактуры. Partner with BMW and OpenAI. "
                "First commercial deployment in 2025."
            ),
            "link": "https://www.figure.ai",
            "sector": "Robotics / AI",
        },
        {
            "name": "Runway",
            "description": (
                "US AI video generation — Gen-3 Alpha модель. "
                "$240M+ funding, $4B valuation. Hollywood studios "
                "используют для VFX и storyboarding."
            ),
            "link": "https://runwayml.com",
            "sector": "AI / Creative",
        },
        {
            "name": "Anduril",
            "description": (
                "US defense tech — $2.4B+ funding. AI-powered autonomous "
                "defense systems, drone swarms, surveillance towers. "
                "Replacing legacy defense contractors."
            ),
            "link": "https://www.anduril.com",
            "sector": "Defense / AI",
        },
        {
            "name": "Harvey AI",
            "description": (
                "US legal AI — $80M+ funding. AI-ассистент для юристов. "
                "Клиенты: Allen & Overy, PwC, O'Melveny. Automates contract review."
            ),
            "link": "https://www.harvey.ai",
            "sector": "Legal Tech / AI",
        },
        {
            "name": "Glean",
            "description": (
                "US enterprise AI search — $200M+ funding. "
                "Поиск по всем рабочим инструментам (Slack, Drive, Confluence). "
                "AI-ответы на основе внутренних данных компании."
            ),
            "link": "https://www.glean.com",
            "sector": "Enterprise / AI",
        },
        {
            "name": "Hebbia",
            "description": (
                "US AI for analysts — $130M+ funding. Matrix AI для "
                "анализа 1000-page документов. Используют хедж-фонды "
                "и инвестиционные банки."
            ),
            "link": "https://www.hebbia.ai",
            "sector": "AI / Finance",
        },
    ],
    # ── Pool 3: Climate, logistics & emerging tech ──
    [
        {
            "name": "Northvolt",
            "description": (
                "Swedish battery maker — $10B+ invested. Первая европейская "
                "EV gigafactory. Ставка Европы на независимость "
                "от азиатских батарей. Контракт с BMW и VW."
            ),
            "link": "https://northvolt.com",
            "sector": "Green Tech / EV",
        },
        {
            "name": "Einride",
            "description": (
                "Swedish autonomous electric trucks — коммерческие "
                "автономные грузоперевозки по Европе. Pod-trucks будущего "
                "уже работают. $500M+ funding."
            ),
            "link": "https://www.einride.com",
            "sector": "Logistics / EV",
        },
        {
            "name": "Klarna",
            "description": (
                "Swedish BNPL → AI shopping assistant. Прибыльный с 2023, "
                "$46B valuation. AI replaced 700 customer service agents. "
                "Переход от BNPL к AI-powered commerce platform."
            ),
            "link": "https://www.klarna.com",
            "sector": "Fintech / AI",
        },
        {
            "name": "Lightmatter",
            "description": (
                "US photonic AI chips — использует свет для вычислений. "
                "В 100x эффективнее GPU для AI inference. $800M+ funding. "
                "Следующий этап chip-индустрии."
            ),
            "link": "https://lightmatter.com",
            "sector": "Photonics / AI Chips",
        },
        {
            "name": "Cognition (Devin)",
            "description": (
                "US autonomous AI software engineer — Devin. "
                "AI, который самостоятельно пишет, тестирует и деплоит код. "
                "$175M+ funding. Самый обсуждаемый AI-product 2025."
            ),
            "link": "https://cognition.ai",
            "sector": "AI / Developer Tools",
        },
        {
            "name": "Poolside AI",
            "description": (
                "French AI coding assistant — $126M seed round (largest ever). "
                "Конкурент GitHub Copilot с focus на enterprise. "
                "Founded by ex-Meta AI lead."
            ),
            "link": "https://poolside.ai",
            "sector": "AI / Developer Tools",
        },
        {
            "name": "Bolt",
            "description": (
                "Estonian mobility super-app — ride-hailing, scooters, food. "
                "Прибыльный и расширяется в Африку. $2B+ valuation. "
                "Побеждает Uber ценой и скоростью."
            ),
            "link": "https://bolt.eu",
            "sector": "Mobility / Super-app",
        },
        {
            "name": "Celonis",
            "description": (
                "German process mining — AI для оптимизации бизнес-процессов. "
                "$4B+ valuation. Клиенты: Siemens, Roche, Vodafone. "
                "Выявляет неэффективности в компаниях через data analysis."
            ),
            "link": "https://www.celonis.com",
            "sector": "Enterprise AI / Process Mining",
        },
    ],
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

    # Stores format — new DTC store layout with category, country, hype reason
    if category == "stores":
        cat = item.get("category", item.get("style", ""))
        why_hyping = item.get("why_hyping", item.get("description", item.get("style", "")))
        country = item.get("country", "")
        parse_status = item.get("parse_status", "")

        text = f"{emoji} *{name}*\n"
        if cat:
            text += f"📦 *Категория:* {cat}\n"
        if country:
            text += f"🌍 *Страна:* {country}\n"
        if why_hyping:
            text += f"🚀 *Почему хайпует:* {why_hyping}\n"
        if parse_status:
            text += f"✅ *Парсинг:* {parse_status}\n"
        if link:
            text += f"\n🔗 [Сайт магазина]({link})"
        return text

    # Standard format for companies
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

def create_site_zip(
    html_content: str,
    project_name: str,
    css_content: str = "",
    js_content: str = "",
) -> str:
    """Create a ZIP file on disk at /tmp/ and return the path.

    The ZIP contains a single self-contained index.html (CSS + JS inlined).
    The caller is responsible for deleting the temp file after use.
    """
    safe_name = project_name.lower().replace(" ", "-").replace("/", "-")[:50]
    tmp_path = os.path.join(tempfile.gettempdir(), f"{safe_name}-site.zip")

    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Always write a single self-contained index.html at the ZIP root
        # CSS and JS are now inlined inside the HTML (no external files)
        zf.writestr("index.html", html_content)
        zf.writestr(
            "README.txt",
            f"Premium Website: {project_name}\n"
            f"{'=' * 40}\n\n"
            f"1. Extract the ZIP and open index.html in any modern browser\n"
            f"2. Fully responsive — works on mobile and desktop\n"
            f"3. All interactions work: FAQ accordion, burger menu, smooth scroll, modal\n"
            f"4. Premium dark theme with glassmorphism effects\n",
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
    category: str = "",
) -> tuple[str, str]:
    """Build the full analysis text message.

    Returns (markdown_text, plain_text) — plain_text is used as fallback
    if Markdown parsing fails.
    """

    # ── Category tag as first line ──
    cat_label = CATEGORY_LABELS.get(category, "")
    cat_tag = f"🏷 *{cat_label}*\n\n" if cat_label else ""

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
        f"{cat_tag}"
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
            "👋 *EU Trend Analytics v15.0*\n\n"
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

        # ─── Route to dedicated deep search per category ───
        search_fns = {
            "crypto": search_crypto_deep,
            "stores": search_stores_deep,
            "companies": search_companies_deep,
        }
        search_fn = search_fns.get(matched_category)

        items = []
        if search_fn:
            # Stores need much more time (5 retries + Gemini parallel + fallback)
            timeout = 150 if matched_category == "stores" else 40
            try:
                items = await asyncio.wait_for(search_fn(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(f"[{matched_category}] Search timed out ({timeout}s), using fallback")
            except Exception as e:
                logger.warning(f"[{matched_category}] Search error: {e}")

        # ─── Fallback: rotated pools ───
        if not items:
            fallback_pools = {
                "crypto": FALLBACK_CRYPTO_POOLS,
                "stores": FALLBACK_STORES_POOLS,
                "companies": FALLBACK_COMPANIES_POOLS,
            }
            pools = fallback_pools.get(matched_category, [])
            items = random.choice(pools) if pools else []
            logger.info(f"[{matched_category}] Using fallback ({len(items)} items)")

        await send_items_batch(message, items, matched_category, CATEGORY_TITLES[matched_category])
        return True
    except Exception as e:
        logger.error(f"[handle_category] {e}", exc_info=True)
        _last_errors.append(f"category-{matched_category}: {e}")
        try:
            fallback_pools = {
                "crypto": FALLBACK_CRYPTO_POOLS,
                "stores": FALLBACK_STORES_POOLS,
                "companies": FALLBACK_COMPANIES_POOLS,
            }
            pools = fallback_pools.get(matched_category, [])
            fallback_items = random.choice(pools) if pools else []
            if fallback_items:
                await send_items_batch(message, fallback_items, matched_category, CATEGORY_TITLES[matched_category])
            else:
                await message.answer("❌ Ошибка при поиске трендов. Попробуй позже.")
        except Exception:
            pass
        return True


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
    "stores": FALLBACK_STORES_POOLS[0] if FALLBACK_STORES_POOLS else [],
    "crypto": FALLBACK_CRYPTO_POOLS[0] if FALLBACK_CRYPTO_POOLS else [],
    "companies": FALLBACK_COMPANIES_POOLS[0] if FALLBACK_COMPANIES_POOLS else [],
}

CATEGORY_TITLES: dict[str, str] = {
    "stores": "ТРЕНДОВЫЕ МАГАЗИНЫ ЕВРОПЫ",
    "crypto": "ТРЕНДОВАЯ КРИПТА",
    "companies": "ТРЕНДОВЫЕ КОМПАНИИ",
}

CATEGORY_NAMES: dict[str, str] = {
    "stores": "DTC Store",
    "crypto": "Crypto Project",
    "companies": "Startup/Company",
}

CATEGORY_SEARCH_MESSAGES: dict[str, str] = {
    "stores": "🔍 *Ищу молодые хайпующие магазины Европы...*",
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

    # ─── Step 1: Detect/confirm category ───
    detected = await detect_category(name, desc, link)
    if detected:
        if detected != category:
            logger.info(
                f"[Improve] Category overridden: button={category} → detected={detected}"
            )
        category = detected
    else:
        logger.info(f"[Improve] Category detection failed, using button: {category}")

    cat_label = CATEGORY_LABELS.get(category, "Проект")

    # ─── Step 2: Send "generating" status ───
    status_msg = await safe_send_message(
        chat_id,
        f"🏷 *{cat_label}* | 🔥 *{name}*\n\n"
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

    # ─── Step 2b: Parse products for stores — STRICT URL binding ───
    current_shop_url = link  # ← жёсткая привязка к магазину
    store_products: list[dict] = []
    if category == "stores" and current_shop_url:
        try:
            store_products = await parse_store_products(
                current_shop_url, desc=desc, name=name
            )
            # Verify: every product must have source_url == current_shop_url
            verified = [
                p for p in store_products
                if p.get("source_url") == current_shop_url
            ]
            logger.info(
                f"[Improve] PARSE RESULT: "
                f"source={current_shop_url} | "
                f"scraped={len(store_products)} | "
                f"verified={len(verified)}"
            )
            store_products = verified
        except Exception as e:
            logger.warning(f"[Improve] Product parsing failed: {e}")

    # ─── Step 2c: Report product parsing status to user ───
    if category == "stores":
        if len(store_products) == 0:
            await status_msg.edit_text(
                f"🏷 *{cat_label}* | 🔥 *{name}*\n\n"
                f"⚠️ Не удалось спарсить каталог {name}\n"
                f"Источник: {current_shop_url}\n\n"
                f"Сайт генерируется без товаров.\n"
                f"⏳ Шаг 2/4: AI-анализ концепции + GEO..."
            )
        else:
            await status_msg.edit_text(
                f"🏷 *{cat_label}* | 🔥 *{name}*\n\n"
                f"✅ Шаг 1/4: Анализ сайта\n"
                f"🛍 Спаршено товаров: *{len(store_products)}*\n"
                f"   Источник: {current_shop_url}\n"
                f"⏳ Шаг 2/4: AI-анализ концепции + GEO..."
            )
    else:
        # Non-store categories
        try:
            await status_msg.edit_text(
                f"🏷 *{cat_label}* | 🔥 *{name}*\n\n"
                f"{'✅' if site_analysis else '⏭️'} Шаг 1/4: "
                f"{'Анализ сайта — готов' if site_analysis else 'Анализ сайта — пропущен'}\n"
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
            f"🏷 *{cat_label}* | 🔥 *{name}*\n\n"
            f"✅ Шаг 1/4: Анализ сайта\n"
            f"✅ Шаг 2/4: AI-анализ готов\n"
            f"⏳ Шаг 3/4: Создаю премиальный сайт..."
        )
    except Exception:
        pass

    # ─── Step 6: Determine theme ───
    theme = get_theme_for_project(imp_name)
    logger.info(f"[Improve] Theme: {theme['name']} for {imp_name}")

    # ─── Step 7: Generate premium website ───
    project_info = {
        "improved_name": imp_name,
        "improved_description": imp_desc,
        "killer_feature": killer,
        "original_link": link,
        "improved_link": imp_link,
    }

    html_content, css_content, js_content = generate_premium_site(
        name=imp_name,
        description=imp_desc,
        killer_feature=killer,
        analysis=analysis,
        category=category,
        site_analysis=site_analysis,
        products=store_products,
    )
    logger.info(
        f"[Improve] Premium site generated: HTML={len(html_content)}, "
        f"CSS={len(css_content)}, JS={len(js_content)}"
    )

    # ─── Step 8: Create multi-file ZIP on disk ───
    tmp_path = create_site_zip(html_content, imp_name, css_content, js_content)

    # ─── Step 9: Update status ───
    try:
        await status_msg.edit_text(
            f"🏷 *{cat_label}* | 🔥 *{name}*\n\n"
            f"✅ Шаг 1/4: Анализ сайта\n"
            f"✅ Шаг 2/4: AI-анализ готов\n"
            f"✅ Шаг 3/4: Премиальный сайт создан\n"
            f"⏳ Шаг 4/4: Отправка файлов..."
        )
    except Exception:
        pass

    # ─── Step 10: Send analysis message ───
    md_text, plain_text = build_analysis_message(name, analysis, category=category)

    try:
        await safe_send_message(chat_id, md_text)
    except Exception:
        # Retry with plain text (no Markdown)
        await safe_send_message(chat_id, plain_text)

    # ─── Step 11: Send ZIP document ───
    safe_file_name = imp_name.lower().replace(" ", "-")[:50]
    try:
        document = FSInputFile(tmp_path, filename=f"{safe_file_name}-site.zip")
        product_info = ""
        if category == "stores" and store_products:
            product_info = f"\n🛍 Товаров в каталоге: {len(store_products)}"
        elif category == "stores" and not store_products:
            product_info = "\n⚠️ Каталог не спарсен (сайт блокирует парсинг)"
        sent = await safe_send_document(
            chat_id,
            document,
            caption=(
                f"📦 *{imp_name} — Готовый сайт*\n\n"
                f"🎨 Дизайн: {'светлый бутик' if category == 'stores' else 'тёмный Web3' if category == 'crypto' else 'корпоративный B2B'}"
                f"{product_info}\n"
                f"Разархивируй → открой index.html в браузере"
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
        product_line = ""
        if category == "stores":
            if store_products:
                product_line = f"🛍 Каталог: {len(store_products)} товаров из {current_shop_url}"
            else:
                product_line = f"⚠️ Каталог не спарсен (сайт блокирует парсинг)"
        await status_msg.edit_text(
            f"🏷 *{cat_label}* | ✅ *{imp_name} — готов!*\n\n"
            f"📊 Анализ + GEO + Ключевые слова — выше\n"
            f"{'📦 ' + product_line if product_line else ''}"
            f"{'📦 Готовый сайт (тёмный Web3)' if category == 'crypto' else ''}"
            f"{'📦 Готовый сайт (корпоративный B2B)' if category == 'companies' else ''}\n\n"
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
