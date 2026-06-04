/**
 * Форматирование результатов аналитики для Telegram
 */

function escapeMarkdown(text) {
  return text.replace(/[_*[\]()~`>#+\-=|{}.!]/g, '\\$&');
}

function formatDate(isoString) {
  const d = new Date(isoString);
  const months = [
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
  ];
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
}

export function formatTrendResults(data) {
  if (!data || !data.trends || data.trends.length === 0) {
    return 'Результаты пока пусты. Запустите аналитику.';
  }

  const dateStr = formatDate(data.date);
  let text = '';

  const trendEmojis = [
    '🔥', '⚡', '🚀', '💎', '🌟', '🎯', '📈', '💡', '🏆', '⭐',
    '💪', '🎪', '🎲', '🧩', '🔧', '🧠', '🌍', '🎨', '🔬', '📦'
  ];

  // Разбиваем на сообщения по 10 трендов (лимит Telegram ~4096 символов)
  const chunks = [];
  let chunk = [];

  for (let i = 0; i < data.trends.length; i++) {
    const t = data.trends[i];
    const num = i + 1;
    const emoji = trendEmojis[i % trendEmojis.length];

    const entry = [
      `${emoji} *${num}\\. ${escapeMarkdown(t.name)}*`,
      `   ${escapeMarkdown(t.domain)}`,
      `   _${escapeMarkdown(t.snippet)}_`,
      `   ${escapeMarkdown(t.url)}`,
      `   Упоминаний: ${t.mentions}`,
    ].join('\n');

    chunk.push(entry);

    // Если чанк становится слишком большим — сохраняем и начинаем новый
    if (chunk.join('\n\n').length > 3500) {
      chunks.push(chunk);
      chunk = [];
    }
  }
  if (chunk.length > 0) chunks.push(chunk);

  // Формируем финальные сообщения
  const messages = chunks.map((ch, idx) => {
    const header = idx === 0
      ? `📊 *АНАЛИТИКА ТРЕНДОВ EU*\\n🗓 Дата: ${dateStr}\\n🔍 Источников обработано: ${data.totalRawResults}\\n${'━'.repeat(30)}`
      : `📊 *АНАЛИТИКА ТРЕНДОВ EU \\(продолжение\\)*\\n${'━'.repeat(30)}`;

    return header + '\n\n' + ch.join('\n\n') + '\n';
  });

  return messages;
}

export function formatStatusMessage(analyzing) {
  if (analyzing) {
    return '⏳ Анализ в процессе... Пожалуйста, подождите.';
  }
  return '✅ Бот готов к работе.';
}
