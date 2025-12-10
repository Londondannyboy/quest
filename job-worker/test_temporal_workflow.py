#!/usr/bin/env python3
"""
Test the full Temporal workflow with ZEP sync
"""

import asyncio
import os
from datetime import timedelta
from temporalio.client import Client, TLSConfig
from dotenv import load_dotenv

load_dotenv()


async def test_workflow():
    """Test the Greenhouse scraper workflow with ZEP sync"""

    print("🚀 Testing Temporal Workflow with ZEP Sync")
    print("="*60)

    # Get Temporal connection details
    temporal_host = os.getenv("TEMPORAL_HOST", "europe-west3.gcp.api.temporal.io:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "quickstart-quest.zivkb")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")

    if not temporal_api_key:
        print("❌ No TEMPORAL_API_KEY found in environment")
        return

    print(f"\n📡 Connecting to Temporal...")
    print(f"   Host: {temporal_host}")
    print(f"   Namespace: {temporal_namespace}")

    try:
        # Connect to Temporal Cloud
        client = await Client.connect(
            temporal_host,
            namespace=temporal_namespace,
            tls=TLSConfig(
                client_cert=None,
                client_private_key=None,
            ),
            rpc_metadata={"temporal-namespace": temporal_namespace},
            api_key=temporal_api_key,
        )

        print("✅ Connected to Temporal Cloud")

    except Exception as e:
        print(f"❌ Failed to connect to Temporal: {e}")
        return

    # Test company - using a real one from the summary
    test_company = {
        "name": "TestCompany",
        "board_url": "https://boards.greenhouse.io/testcompany",
        "board_type": "greenhouse"
    }

    print(f"\n🏢 Running workflow for: {test_company['name']}")
    print(f"   Board URL: {test_company['board_url']}")

    try:
        # Start the workflow
        result = await client.execute_workflow(
            "GreenhouseScraperWorkflow",
            test_company,
            id=f"test-greenhouse-{test_company['name']}-{int(asyncio.get_event_loop().time())}",
            task_queue="fractional-jobs-queue",
            execution_timeout=timedelta(minutes=10),
        )

        print("\n✅ Workflow completed successfully!")
        print("\n📊 Results:")
        print(f"   Company: {result.get('company_name')}")
        print(f"   Jobs found: {result.get('jobs_found', 0)}")
        print(f"   Jobs deep scraped: {result.get('jobs_deep_scraped', 0)}")
        print(f"   Jobs classified: {result.get('jobs_classified', 0)}")
        print(f"   Fractional jobs: {result.get('jobs_fractional', 0)}")
        print(f"   Jobs added to DB: {result.get('jobs_added', 0)}")
        print(f"   Jobs updated in DB: {result.get('jobs_updated', 0)}")
        print(f"   Jobs saved to ZEP: {result.get('jobs_saved_to_zep', 0)}")
        print(f"   ZEP skipped duplicates: {result.get('zep_skipped_duplicates', 0)}")
        print(f"   Duration: {result.get('duration_seconds', 0):.2f}s")

        if result.get('errors'):
            print(f"\n⚠️  Errors:")
            for error in result['errors']:
                print(f"   - {error}")

        print("\n" + "="*60)
        print("✅ Test complete!")

        if result.get('jobs_saved_to_zep', 0) > 0:
            print(f"\n✨ Successfully saved {result['jobs_saved_to_zep']} jobs to ZEP!")
            print("   The job skill graph is now populated and ready for retrieval.")
        else:
            print("\n⚠️  No jobs were saved to ZEP. Check the logs for details.")

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_workflow())
