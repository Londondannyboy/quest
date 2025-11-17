"""
Trigger Evercore Regeneration

Regenerate Evercore profile with new V2 prompt (deals, resources, links, better formatting)
"""

import asyncio
from temporalio.client import Client
from gateway.temporal_client import TemporalClientManager
from dotenv import load_dotenv

load_dotenv()


async def trigger_evercore_regen():
    """Trigger Evercore company profile regeneration"""

    # Get Temporal client
    client = await TemporalClientManager.get_client()

    # Company input data
    company_input = {
        "url": "https://www.evercore.com",
        "category": "placement_agent",
        "jurisdiction": "US",
        "app": "placement",
        "force_update": True  # Force regeneration
    }

    print("=" * 70)
    print("🔄 Triggering Evercore Regeneration")
    print("=" * 70)
    print(f"URL: {company_input['url']}")
    print(f"Category: {company_input['category']}")
    print(f"Force Update: {company_input['force_update']}")
    print()

    # Start workflow
    workflow_id = f"company-evercore-regen-{asyncio.get_event_loop().time()}"

    handle = await client.start_workflow(
        "CompanyCreationWorkflow",
        company_input,
        id=workflow_id,
        task_queue="quest-company-queue",
    )

    print(f"✅ Workflow started: {workflow_id}")
    print(f"🔗 Workflow ID: {handle.id}")
    print(f"⏳ Waiting for completion...")
    print()

    # Wait for result
    try:
        result = await handle.result()
        print("=" * 70)
        print("✅ Evercore Regeneration Complete!")
        print("=" * 70)
        print(f"Status: {result.get('status')}")
        print(f"Company ID: {result.get('company_id')}")
        print(f"Slug: {result.get('slug')}")
        print(f"Data Completeness: {result.get('data_completeness')}%")
        print(f"Research Cost: ${result.get('research_cost', 0):.4f}")
        print(f"Research Confidence: {result.get('research_confidence', 0):.2f}")
        print()
        print(f"🌐 View at: https://placement.quest/private-equity-placement-agents/{result.get('slug')}")

    except Exception as e:
        print("=" * 70)
        print("❌ Workflow Failed")
        print("=" * 70)
        print(f"Error: {e}")

    # Close client
    await TemporalClientManager.close()


if __name__ == "__main__":
    asyncio.run(trigger_evercore_regen())
