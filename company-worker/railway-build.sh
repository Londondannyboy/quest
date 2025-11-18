#!/bin/bash
# Railway build script to install Playwright browsers

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🎭 Installing Playwright browsers..."
playwright install chromium

echo "✅ Build complete!"
