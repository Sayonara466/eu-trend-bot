#!/usr/bin/env python3
"""
Генерация графиков для EU Trend Analytics
Создаёт 2 картинки: bar chart + pie chart и сохраняет в PNG
"""
import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Подключаем шрифты для русского текста
fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/SarasaMonoSC-Regular.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/SarasaMonoSC-Bold.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
plt.rcParams['font.sans-serif'] = ['SarasaMonoSC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = sys.argv[1] if len(sys.argv) > 1 else '/home/z/my-project/trend-bot/data/trends.json'
OUTPUT_BAR = '/home/z/my-project/trend-bot/data/chart_bar.png'
OUTPUT_PIE = '/home/z/my-project/trend-bot/data/chart_pie.png'

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

trends = data.get('trends', [])
if not trends:
    print("NO_TRENDS")
    sys.exit(0)

# Подготовка данных
names = []
mentions = []
domains = []
for t in trends:
    name = t.get('name', 'N/A')
    # Обрезаем длинные имена
    if len(name) > 35:
        name = name[:32] + '...'
    names.append(name)
    mentions.append(t.get('mentions', 1))
    domains.append(t.get('domain', ''))

# Цветовая палитра
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
          '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
          '#F8C471', '#82E0AA', '#F1948A', '#AED6F1', '#D2B4DE',
          '#A3E4D7', '#FAD7A0', '#A9CCE3', '#D5F5E3', '#FADBD8']

# ===== BAR CHART =====
fig, ax = plt.subplots(figsize=(12, 8))
fig.patch.set_facecolor('#1a1a2e')
ax.set_facecolor('#16213e')

bars = ax.barh(range(len(names)), mentions, color=colors[:len(names)], edgecolor='white', linewidth=0.5, height=0.7)

# Добавляем значения на столбцы
for i, (bar, val) in enumerate(zip(bars, mentions)):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
            f' {val}', va='center', ha='left', color='white', fontsize=10, fontweight='bold')

ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=8, color='white')
ax.invert_yaxis()
ax.set_xlabel('Упоминаний', color='white', fontsize=12, fontweight='bold')
ax.set_title('TOP-20 TRENDOV EU E-COMMERCE', color='white', fontsize=16, fontweight='bold', pad=15)
ax.tick_params(axis='x', colors='white')
ax.spines['bottom'].set_color('#4a4a6a')
ax.spines['left'].set_color('#4a4a6a')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='x', color='#2a2a4a', alpha=0.5, linestyle='--')

plt.tight_layout()
plt.savefig(OUTPUT_BAR, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
plt.close()
print(f"BAR: {OUTPUT_BAR}")

# ===== PIE CHART - категории доменов =====
fig, ax = plt.subplots(figsize=(10, 8))
fig.patch.set_facecolor('#1a1a2e')

# Группируем по домену
domain_mentions = {}
for t in trends:
    d = t.get('domain', 'other')
    domain_mentions[d] = domain_mentions.get(d, 0) + t.get('mentions', 1)

# Топ-10 доменов, остальные = "Прочие"
sorted_domains = sorted(domain_mentions.items(), key=lambda x: x[1], reverse=True)
top_domains = sorted_domains[:10]
other_count = sum(v for _, v in sorted_domains[10:])
if other_count > 0:
    top_domains.append(('Прочие', other_count))

pie_labels = [d[0] for d in top_domains]
pie_values = [d[1] for d in top_domains]

wedges, texts, autotexts = ax.pie(
    pie_values, labels=None, autopct='%1.1f%%',
    colors=colors[:len(pie_values)],
    startangle=140, pctdistance=0.8,
    wedgeprops=dict(width=0.5, edgecolor='#1a1a2e', linewidth=2)
)
for at in autotexts:
    at.set_color('white')
    at.set_fontsize(9)
    at.set_fontweight('bold')

# Легенда
legend_labels = [f'{l} ({v})' for l, v in zip(pie_labels, pie_values)]
ax.legend(wedges, legend_labels, title="Домены", loc="center left",
          bbox_to_anchor=(1, 0, 0.5, 1), fontsize=8, title_fontsize=10,
          facecolor='#16213e', edgecolor='#4a4a6a', labelcolor='white')
ax.set_title('RASPREDelenie TRENDOV PO DOMENAM', color='white', fontsize=14, fontweight='bold', pad=15)

plt.tight_layout()
plt.savefig(OUTPUT_PIE, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
plt.close()
print(f"PIE: {OUTPUT_PIE}")

print(f"TOTAL_TRENDS: {len(trends)}")
print(f"TOTAL_RAW: {data.get('totalRawResults', 0)}")
