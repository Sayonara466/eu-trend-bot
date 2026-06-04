/**
 * EU Trend Analyzer
 * Ищет набирающие популярность товары и услуги в Европе
 */

import ZAI from 'z-ai-web-dev-sdk';

const EXCLUDE_CATEGORIES = [
  'food delivery', 'groceries', 'restaurant', 'alcohol', 'pharmacy', 'medicine',
  'flowers', 'clothing', 'fashion', 'shoes', 'electronics', 'phones', 'laptops',
  'beauty products', 'makeup', 'skincare'
];

const SEARCH_QUERIES = [
  'fastest growing e-commerce categories Europe 2025 2026',
  'trending products European consumers buying 2026',
  'growing online shopping categories EU market',
  'new popular products Europe trending demand',
  'European consumer trends 2026 non-obvious',
  'best selling new products online Europe growth',
  'innovative products gaining popularity Europe',
  'European market trending niches 2025 2026',
];

class TrendAnalyzer {
  constructor() {
    this.zai = null;
    this.isAnalyzing = false;
  }

  async init() {
    this.zai = await ZAI.create();
    console.log('[Analyzer] Z-AI SDK initialized');
  }

  async searchWeb(query, retries = 2) {
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const result = await this.zai.functions.invoke('web_search', {
          query,
          num: 10
        });
        return result || [];
      } catch (err) {
        if (err.message?.includes('429') && attempt < retries) {
          console.log(`[Analyzer] Rate limited, waiting 5s before retry (${attempt + 1}/${retries})...`);
          await new Promise(r => setTimeout(r, 5000));
          continue;
        }
        console.error(`[Analyzer] Search error for "${query}":`, err.message);
        return [];
      }
    }
    return [];
  }

  async runFullAnalysis() {
    if (this.isAnalyzing) {
      throw new Error('Анализ уже запущен');
    }
    this.isAnalyzing = true;

    console.log('[Analyzer] Starting full trend analysis...');

    try {
      const allResults = [];

      // Последовательные запросы с задержкой — чтобы не словить rate limit
      for (let i = 0; i < SEARCH_QUERIES.length; i++) {
        console.log(`[Analyzer] Searching (${i + 1}/${SEARCH_QUERIES.length}): ${SEARCH_QUERIES[i]}`);
        const results = await this.searchWeb(SEARCH_QUERIES[i]);
        if (Array.isArray(results)) {
          allResults.push(...results);
        }
        // Задержка 2 сек между запросами
        if (i < SEARCH_QUERIES.length - 1) {
          await new Promise(r => setTimeout(r, 2000));
        }
      }

      console.log(`[Analyzer] Total raw results: ${allResults.length}`);

      // Группируем по домену и сортируем по релевантности
      const domainMap = new Map();
      for (const item of allResults) {
        const domain = item.host_name || item.url;
        if (!domain) continue;

        // Пропускаем примитивы
        const text = (item.name + ' ' + item.snippet).toLowerCase();
        if (EXCLUDE_CATEGORIES.some(cat => text.includes(cat))) continue;

        if (!domainMap.has(domain)) {
          domainMap.set(domain, {
            domain,
            name: item.name || '',
            snippet: item.snippet || '',
            url: item.url || '',
            rank: 0,
            mentions: 0,
            favicon: item.favicon || '',
          });
        }
        const entry = domainMap.get(domain);
        entry.mentions++;
        entry.rank = Math.max(entry.rank, item.rank || 0);
        if (item.rank && item.rank < entry.rank) entry.rank = item.rank;
      }

      // Сортируем по количеству упоминаний и рангу
      const sorted = [...domainMap.values()]
        .sort((a, b) => b.mentions - a.mentions || a.rank - b.rank);

      // Берём топ 30 уникальных доменов для глубокого анализа
      const topDomains = sorted.slice(0, 30);

      // Формируем финальные тренды
      const trends = [];
      for (const item of topDomains) {
        trends.push({
          name: this.cleanName(item.name),
          domain: item.domain,
          url: item.url,
          snippet: this.cleanSnippet(item.snippet),
          mentions: item.mentions,
        });
      }

      console.log(`[Analyzer] Final trends found: ${trends.length}`);

      const analysisResult = {
        date: new Date().toISOString(),
        timestamp: Date.now(),
        totalRawResults: allResults.length,
        trends,
      };

      return analysisResult;

    } finally {
      this.isAnalyzing = false;
    }
  }

  cleanName(name) {
    if (!name) return 'N/A';
    return name
      .replace(/\s*[-|–—].*$/, '')
      .replace(/\s*\|.*/, '')
      .trim()
      .substring(0, 100);
  }

  cleanSnippet(snippet) {
    if (!snippet) return '';
    return snippet.replace(/<[^>]*>/g, '').trim().substring(0, 200);
  }
}

export default TrendAnalyzer;
