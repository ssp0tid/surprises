#!/bin/bash
cd "$(dirname "$0")"

echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "✅ Uptime Monitor starting up..."
echo "🌐 Web UI available at: http://localhost:8000"
echo "🔍 Checks run automatically every 1 minute"
echo "⏹️  Press Ctrl+C to stop"
echo ""

python3 main.py
