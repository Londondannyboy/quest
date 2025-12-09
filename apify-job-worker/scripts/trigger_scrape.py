#!/usr/bin/env python3
"""Manually trigger LinkedInApifyScraperWorkflow for testing."""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from temporalio.client import Client

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings


async def trigger_linkedin_scrape():
    """Manually trigger a LinkedIn scrape workflow."""

    # Load environment
    load_dotenv(Path(__file__).parent.parent / ".env")

    settings = get_settings()

    if not settings.temporal_api_key:
        print("❌ TEMPORAL_API_KEY not set in .env")
        return False

    print("\n" + "=" * 70)
    print("Triggering LinkedIn Apify Scraper Workflow")
    print("=" * 70)
    print(f"Temporal Host: {settings.temporal_host}")
    print(f"Namespace: {settings.temporal_namespace}")
    print(f"Task Queue: {settings.temporal_task_queue}")

    try:
        # Connect to Temporal
        print("\nConnecting to Temporal...")
        client = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
            api_key=settings.temporal_api_key,
            tls=settings.temporal_tls,
        )
        print("✅ Connected to Temporal")

        # Prepare workflow config - use smaller dataset for testing
        task_queue = settings.temporal_task_queue
        workflow_id = f"linkedin-apify-test-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        config = {
            "location": "United Kingdom",
            "keywords": "fractional OR part-time OR contract",
            "jobs_entries": 10,  # Limited for testing
            "job_post_time": "r86400",  # Last 24 hours
        }

        print(f"\nWorkflow ID: {workflow_id}")
        print(f"Config: {config}")
        print("\nStarting workflow...")

        # Start workflow
        handle = await client.execute_workflow(
            "LinkedInApifyScraperWorkflow",
            config,
            id=workflow_id,
            task_queue=task_queue,
        )

        print(f"✅ Workflow completed!")
        print("\n" + "=" * 70)
        print("Workflow Results")
        print("=" * 70)

        result = handle
        print(f"Source: {result.get('source', 'N/A')}")
        print(f"Jobs Scraped: {result.get('jobs_scraped', 0)}")
        print(f"Jobs Classified: {result.get('jobs_classified', 0)}")
        print(f"Jobs Fractional: {result.get('jobs_fractional', 0)}")
        print(f"Jobs Added to Neon: {result.get('jobs_added_to_neon', 0)}")
        print(f"Jobs Updated in Neon: {result.get('jobs_updated_in_neon', 0)}")
        print(f"Jobs Synced to ZEP: {result.get('jobs_synced_to_zep', 0)}")
        print(f"Duration: {result.get('duration_seconds', 0):.2f}s")

        if result.get("errors"):
            print(f"\n⚠️  Errors encountered:")
            for error in result["errors"]:
                print(f"   - {error}")
        else:
            print("\n✅ No errors!")

        print("=" * 70 + "\n")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n⚠️  Make sure the worker is running in another terminal:")
    print("   python -m src.worker\n")

    success = asyncio.run(trigger_linkedin_scrape())
    sys.exit(0 if success else 1)
