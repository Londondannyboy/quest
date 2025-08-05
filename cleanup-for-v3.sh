#!/bin/bash

# Quest V3 Cleanup Script
# This script removes all code except V3 documentation

echo "🧹 Quest V3 Cleanup Script"
echo "========================="
echo ""
echo "This will DELETE all files except:"
echo "- V3_*.md documentation files"
echo "- archive/ directory"
echo "- .git/ directory"
echo ""
read -p "Are you sure you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "📁 Creating temporary backup of V3 docs..."
mkdir -p temp-v3-docs
cp V3_*.md temp-v3-docs/ 2>/dev/null || echo "No V3 docs to backup"

echo ""
echo "🗑️  Removing all code and config files..."

# Remove all files except hidden directories and our exceptions
find . -maxdepth 1 -type f ! -name "V3_*.md" ! -name ".gitignore" -delete

# Remove specific directories
rm -rf app/
rm -rf components/
rm -rf lib/
rm -rf pages/
rm -rf prisma/
rm -rf public/
rm -rf scripts/
rm -rf styles/
rm -rf types/
rm -rf utils/
rm -rf node_modules/
rm -rf .next/
rm -rf out/
rm -rf build/
rm -rf coverage/
rm -rf docs/examples/

# Remove config files
rm -f next.config.js
rm -f package*.json
rm -f tsconfig.json
rm -f tailwind.config.js
rm -f postcss.config.*
rm -f .eslintrc.*
rm -f jest.config.*
rm -f server.js
rm -f *.js
rm -f *.ts
rm -f *.tsx
rm -f yarn.lock
rm -f pnpm-lock.yaml
rm -f .env*

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📋 Remaining files:"
ls -la

echo ""
echo "🚀 Ready for V3 restart! Follow V3_MBAD_CHECKLIST.md Sprint 0"