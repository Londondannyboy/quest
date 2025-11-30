#!/usr/bin/env python3
"""
Test script to trigger Country Guide workflow via Gateway API.

Usage:
    python test_country_guide.py [country_name] [country_code]

Examples:
    python test_country_guide.py Portugal PT
    python test_country_guide.py Cyprus CY
    python test_country_guide.py "United Kingdom" GB
"""

import requests
import sys
import os

# Gateway URL - change this to your Railway gateway URL
GATEWAY_URL = os.environ.get("GATEWAY_URL", "https://gateway-production-b744.up.railway.app")

def trigger_country_guide(country_name: str, country_code: str, video_quality: str = "medium"):
    """Trigger a country guide workflow via the gateway API."""

    endpoint = f"{GATEWAY_URL}/v1/workflows/country-guide"

    payload = {
        "country_name": country_name,
        "country_code": country_code,
        "app": "relocation",
        "video_quality": video_quality,
        "target_word_count": 4000,
        "use_cluster_architecture": True  # ALWAYS use cluster mode for full workflow
    }

    print(f"🌍 Triggering Country Guide workflow for {country_name} ({country_code})")
    print(f"📡 Endpoint: {endpoint}")
    print(f"📦 Payload: {payload}")
    print()

    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        print("✅ Workflow triggered successfully!")
        print(f"📋 Workflow ID: {result.get('workflow_id', 'N/A')}")
        print(f"🔗 Run ID: {result.get('run_id', 'N/A')}")
        print()
        print("Track progress in Temporal UI:")
        print(f"   https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows/{result.get('workflow_id', '')}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to trigger workflow: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text[:500]}")
        return None

def main():
    # Default to Cyprus (smaller for testing)
    country_name = sys.argv[1] if len(sys.argv) > 1 else "Cyprus"
    country_code = sys.argv[2] if len(sys.argv) > 2 else "CY"
    video_quality = sys.argv[3] if len(sys.argv) > 3 else "medium"

    print("=" * 60)
    print("🧪 Country Guide Workflow Test")
    print("=" * 60)
    print()

    result = trigger_country_guide(country_name, country_code, video_quality)

    if result:
        print()
        print("=" * 60)
        print("✅ Test initiated successfully!")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("❌ Test failed - check gateway logs")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
