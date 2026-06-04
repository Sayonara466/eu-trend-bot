#!/bin/bash
cd /home/z/my-project/trend-bot
echo "=== EU TREND BOT LOOP STARTED $(date) ==="
while true; do
  node bot-cron.js 2>&1
  sleep 10
done
