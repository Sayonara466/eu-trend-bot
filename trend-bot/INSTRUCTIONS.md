# EU Trend Analyzer Bot — ЗАПУСК ЗА 1 МИНУТУ

## Способ 1: С компьютера (любой ОС)

### Шаг 1. Установи Node.js (если нет)
Скачай с https://nodejs.org (версия 18+) и установи.

### Шаг 2. Скачай файл бота
Скопируй файл `bot.js` в любую папку.

### Шаг 3. Установи зависимости
Открой терминал в папке с `bot.js` и выполни:
```
npm install node-telegram-bot-api node-cron z-ai-web-dev-sdk
```

### Шаг 4. Запусти!
```
node bot.js
```

### Шаг 5. Открой Telegram
Найди бота **@analliitiikk_bot** → START → нажми кнопки!

---

## Способ 2: С ТЕЛЕФОНА через Replit.com (без компьютера!)

1. Открой **https://replit.com** в браузере телефона
2. Зарегистрируйся (бесплатно)
3. Нажми **"Create Repl"**
4. Выбери **Node.js**
5. В файл `index.js` вставь код из `bot.js`
6. Нажми **"Run"** (▶)
7. Бот запустится! Открой Telegram и работай!

---

## Способ 3: VPS для работы 24/7

Любой дешёвый VPS (Timeweb, Reg.ru, DigitalOcean от $3/мес):

```bash
# Установка Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt install -y nodejs

# Загрузи бота
mkdir trend-bot && cd trend-bot
# Помести bot.js сюда

# Зависимости
npm init -y
npm install node-telegram-bot-api node-cron z-ai-web-dev-sdk

# Запуск через pm2 (авторестарт)
npm install -g pm2
pm2 start bot.js --name trend-bot
pm2 save
pm2 startup
```

---

## Что делает бот:
- 🔍 **"Запустить аналитику"** → ищет тренды EU → "Аналитика завершена"
- 📊 **"Выдать результаты"** → ТОП-25 трендов с ссылками
- ⏰ **Автозапуск каждый день в 09:00 MSK**
