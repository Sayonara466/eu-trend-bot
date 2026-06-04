#!/bin/bash
cd "$(dirname "$0")"
while true; do
  echo "$(date '+%Y-%m-%d %H:%M:%S') Bot starting..." >> bot.log
  node src/index.js >> bot.log 2>&1
  EXIT_CODE=$?
  echo "$(date '+%Y-%m-%d %H:%M:%S') Bot exited (code=$EXIT_CODE), restarting in 3s..." >> bot.log
  sleep 3
done
