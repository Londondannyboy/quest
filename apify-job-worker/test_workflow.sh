#!/bin/bash
# Test the Apify LinkedIn Scraper Workflow

cd /Users/dankeegan/worker/apify-job-worker

echo "🚀 Testing Apify LinkedIn Scraper Workflow"
echo "========================================"
echo ""
echo "Make sure the worker is running in another terminal:"
echo "  cd /Users/dankeegan/worker/apify-job-worker"
echo "  source .venv/bin/activate"
echo "  python3 -m src.worker"
echo ""
echo "Starting workflow test in 3 seconds..."
sleep 3

source .venv/bin/activate
python3 scripts/trigger_scrape.py
