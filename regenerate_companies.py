#!/usr/bin/env python3
"""Regenerate companies with proper profiles and images."""
import asyncio
from temporalio.client import Client
import os

async def trigger_company(client, url: str, company_name: str):
    """Trigger workflow for a company."""
    workflow_id = f"company-regenerate-{company_name.lower()}-{int(asyncio.get_event_loop().time())}"

    print(f"\n🔄 Triggering {company_name}...")
    print(f"   URL: {url}")

    handle = await client.start_workflow(
        "create_company_workflow",
        {
            "url": url,
            "app": "placement",
            "category": "placement_agent",
            "force_update": True,  # Force complete regeneration
        },
        id=workflow_id,
        task_queue="company-worker-queue",
    )

    print(f"   ✅ Started: {workflow_id}")
    print(f"   📊 Monitor: https://cloud.temporal.io/namespaces/{os.environ['TEMPORAL_NAMESPACE']}/workflows/{workflow_id}")

    return handle

async def main():
    # Connect to Temporal Cloud
    print("🔌 Connecting to Temporal Cloud...")
    client = await Client.connect(
        os.environ["TEMPORAL_ADDRESS"],
        namespace=os.environ["TEMPORAL_NAMESPACE"],
        api_key=os.environ["TEMPORAL_API_KEY"],
    )
    print("   ✅ Connected!\n")

    # Companies to regenerate
    companies = [
        ("https://www.evercore.com", "Evercore"),
        ("https://www.firstavenue.com", "First Avenue"),
    ]

    # Trigger all workflows
    handles = []
    for url, name in companies:
        handle = await trigger_company(client, url, name)
        handles.append((name, handle))
        await asyncio.sleep(2)  # Small delay between triggers

    print("\n" + "="*60)
    print("🎯 All workflows triggered! Waiting for completion...")
    print("="*60 + "\n")

    # Wait for results
    for name, handle in handles:
        print(f"⏳ Waiting for {name}...")
        try:
            result = await handle.result()
            print(f"   ✅ {name} completed!")
            print(f"      Status: {result.get('status')}")
            print(f"      Company ID: {result.get('company_id')}")
            if 'section_count' in result:
                print(f"      Sections: {result.get('section_count')}")
        except Exception as e:
            print(f"   ❌ {name} failed: {e}")

    print("\n" + "="*60)
    print("✨ Regeneration complete!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
