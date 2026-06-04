#!/bin/sh
set -e

echo "=========================================="
echo "Starting EU Trend Bot v6.1"
echo "=========================================="

# Start Node.js AI proxy in background on port 3000
echo "[1/2] Starting AI Proxy (Node.js, port 3000)..."
cd /app/ai-proxy && node server.js &
AI_PID=$!

# Give AI proxy time to initialize
sleep 3

echo "[2/2] Starting Telegram Bot (Python, port 10000)..."
cd /app && python bot.py &
BOT_PID=$!

# Wait for either process to exit
wait -n $AI_PID $BOT_PID
EXIT_CODE=$?

echo "Process exited with code $EXIT_CODE. Shutting down..."
kill $AI_PID $BOT_PID 2>/dev/null
exit $EXIT_CODE
