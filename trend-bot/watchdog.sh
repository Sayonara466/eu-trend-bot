#!/bin/bash
# EU TREND BOT — AUTO-RESTART WATCHDOG
# Если бот падает — автоматически перезапускает
# Запускать: bash watchdog.sh &
cd /home/z/my-project/trend-bot
while true; do
  echo "[$(date)] Bot starting..."
  node bot-loop.js 2>&1
  EXIT=$?
  echo "[$(date)] Bot exited (code=$EXIT), restarting in 3s..."
  sleep 3
done
