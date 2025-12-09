#!/usr/bin/env python3
"""Test Apify API integration without Temporal."""

import asyncio
import os
import sys
import httpx
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings


async def test_apify_api():
    """Test basic Apify API connectivity and actor run."""

    # Load environment
    load_dotenv(Path(__file__).parent.parent / ".env")

    settings = get_settings()

    if not settings.apify_api_key:
        print("❌ APIFY_API_KEY not set in .env")
        return False

    api_key = settings.apify_api_key
    actor_id = settings.apify_actor_id
    base_url = settings.apify_base_url

    print("\n" + "=" * 70)
    print("Testing Apify API Integration")
    print("=" * 70)
    print(f"Actor ID: {actor_id}")
    print(f"Base URL: {base_url}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Check API connectivity
        print("\n1️⃣  Testing API connectivity...")
        try:
            response = await client.get(
                f"{base_url}/acts/{actor_id}",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            actor_info = response.json()
            print(f"✅ Actor found: {actor_info['data']['name']}")
            print(f"   Title: {actor_info['data'].get('title', 'N/A')}")
        except Exception as e:
            print(f"❌ API connectivity failed: {e}")
            return False

        # Test 2: Start a small test run
        print("\n2️⃣  Starting test run (50 results, UK only)...")
        try:
            run_input = {
                "location": "United Kingdom",
                "searchKeywords": "fractional",
                "maxResults": 50,
                "scrapeJobDetails": False,  # Faster for testing
            }

            response = await client.post(
                f"{base_url}/acts/{actor_id}/runs",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=run_input,
            )
            response.raise_for_status()
            run_data = response.json()
            run_id = run_data["data"]["id"]
            print(f"✅ Run started: {run_id}")
            print(f"   Status: {run_data['data']['status']}")
            print(f"   View: https://console.apify.com/actors/runs/{run_id}")

        except Exception as e:
            print(f"❌ Failed to start run: {e}")
            return False

        # Test 3: Check run status
        print("\n3️⃣  Checking run status...")
        try:
            response = await client.get(
                f"{base_url}/actor-runs/{run_id}",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            status_data = response.json()
            status = status_data["data"]["status"]
            print(f"✅ Run status: {status}")
            if status == "RUNNING":
                print("   (Run is still executing - this is normal for first test)")

        except Exception as e:
            print(f"❌ Failed to check status: {e}")
            return False

    print("\n" + "=" * 70)
    print("✅ Apify API integration working!")
    print("   You can now start the worker with:")
    print("   python -m src.worker")
    print("=" * 70 + "\n")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_apify_api())
    sys.exit(0 if success else 1)
