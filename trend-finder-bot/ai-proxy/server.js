import express from 'express';
import ZAI from 'z-ai-web-dev-sdk';

const app = express();
app.use(express.json({ limit: '1mb' }));

// ─── Config ──────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
const API_KEY = process.env.API_KEY || 'trend-bot-secret-2025';

let zai = null;

async function init() {
  try {
    zai = await ZAI.create();
    console.log('✅ z-ai-web-dev-sdk initialized');
  } catch (e) {
    console.error('❌ Failed to initialize SDK:', e.message);
    process.exit(1);
  }
}

// ─── Auth middleware ─────────────────────────────────────
function auth(req, res, next) {
  const key = req.headers['x-api-key'];
  if (key !== API_KEY) {
    return res.status(401).json({ error: 'Invalid API key' });
  }
  next();
}

// ─── Health ──────────────────────────────────────────────
app.get('/health', (req, res) => {
  res.json({ status: 'ok', sdk: zai ? 'ready' : 'not initialized' });
});

app.get('/', (req, res) => {
  res.json({ status: 'AI Proxy v1.0 for EU Trend Bot' });
});

// ─── IMPROVE OFFER ────────────────────────────────────────
app.post('/improve', auth, async (req, res) => {
  const { name, description, link, category } = req.body;

  if (!name) {
    return res.status(400).json({ error: 'name is required' });
  }

  const categoryLabel = {
    stores: 'fashion/e-commerce',
    crypto: 'crypto/Web3/DeFi',
    companies: 'technology/startup'
  }[category] || 'technology';

  const systemPrompt = `You are a legendary startup founder and product visionary. Someone brings you a trending project and asks you to reimagine it 10x better — like Elon Musk meets Steve Jobs.

The project is in the ${categoryLabel} category.

IMPORTANT RULES:
1. You must create a COMPLETELY NEW improved concept
2. The improved name must be CREATIVE and UNIQUE — use prefixes/suffixes appropriate for the category
3. For fashion: use elegant, premium-sounding names (French, Italian, Scandinavian vibes)
4. For crypto: use techy, futuristic names (.io, .xyz, .fi domains)
5. For tech: use modern, clean names (.ai, .app domains)
6. The offer must be SPECIFIC to the original project — explain exactly what's improved
7. Business model must have REAL prices ($X/mo, % commission)
8. GEO targets must be RELEVANT to the category (crypto → crypto-friendly countries, fashion → fashion capitals)
9. Keywords must be relevant for Google Ads and SEO
10. ALL text must be in RUSSIAN (except the improved_name and website URL which should be in English)

Return a JSON object with EXACTLY these 10 fields:
1. "improved_name" — Creative new name in English (.ai, .io, .xyz, .co, .app domain style)
2. "offer" — What's improved and why it's 10x better. 2-3 specific sentences in RUSSIAN.
3. "ai_core" — Core technology explanation in RUSSIAN. 1-2 sentences.
4. "killer_feature" — THE ONE killer feature in RUSSIAN. 1 sharp sentence.
5. "website" — Realistic URL in English (e.g. aura-studio.ai, nexvault.io)
6. "site_structure" — Full website description in RUSSIAN. What sections, what user sees/does. 3-4 sentences.
7. "business_model" — How it makes money with REAL numbers in RUSSIAN. 1-2 sentences.
8. "breakthrough" — Why this becomes a unicorn in RUSSIAN. 1 sentence.
9. "geo_targets" — Array of 5-6 objects: {"country":"Country Name","cities":"City1, City2","reason":"1 sentence reason in RUSSIAN"}
10. "keywords" — Array of 12-15 keywords/phrases in English for Google Ads/SEO

Return ONLY the JSON object. No markdown, no code blocks, just raw JSON.`;

  const userPrompt = `Create an improved 10x version of this project:

Name: ${name}
Description: ${description || 'No description available'}
Website: ${link || 'N/A'}
Category: ${categoryLabel}

Return the JSON object with the improved concept.`;

  try {
    console.log(`[Improve] Processing: ${name} (${category})`);

    const completion = await zai.chat.completions.create({
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ],
      temperature: 0.85,
      max_tokens: 4096,
    });

    let content = completion.choices[0]?.message?.content || '';
    console.log(`[Improve] Raw response length: ${content.length}`);

    // Clean markdown fences if present
    content = content.replace(/```json\s*/gi, '').replace(/```\s*/gi, '').trim();

    // Extract JSON
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      console.error(`[Improve] No JSON found in response for ${name}`);
      return res.status(500).json({ error: 'Failed to parse AI response', raw: content.substring(0, 500) });
    }

    const result = JSON.parse(jsonMatch[0]);

    // Validate required fields
    const required = ['improved_name', 'offer', 'ai_core', 'killer_feature', 'website', 'site_structure', 'business_model', 'breakthrough', 'geo_targets', 'keywords'];
    const missing = required.filter(f => !result[f]);
    if (missing.length > 0) {
      console.warn(`[Improve] Missing fields: ${missing.join(', ')} for ${name}`);
    }

    console.log(`[Improve] SUCCESS: ${result.improved_name}`);
    res.json(result);

  } catch (e) {
    console.error(`[Improve] ERROR for ${name}: ${e.message}`);
    res.status(500).json({ error: e.message });
  }
});

// ─── START ───────────────────────────────────────────────
async function start() {
  await init();
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 AI Proxy running on port ${PORT}`);
  });
}

start();
