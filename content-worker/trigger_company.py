#!/usr/bin/env python3
"""Simple company creation trigger"""

import asyncio
import sys
from temporalio.client import Client
from src.utils.config import config


async def main():
    """Trigger company creation for First Avenue"""

    print("🚀 Triggering First Avenue workflow...")

    # Connect to Temporal
    client = await Client.connect(
        config.TEMPORAL_ADDRESS,
        namespace=config.TEMPORAL_NAMESPACE,
        api_key=config.TEMPORAL_API_KEY,
        tls=True
    )

    # Import workflow
    from src.workflows.company_creation import CompanyCreationWorkflow

    # Workflow input
    workflow_input = {
        "url": "https://www.firstavenue.com/",
        "category": "placement",
        "app": "placement",
        "jurisdiction": "US",
        "force_update": False
    }

    # Start workflow
    handle = await client.start_workflow(
        CompanyCreationWorkflow.run,
        workflow_input,
        id=f"first-avenue-{int(asyncio.get_event_loop().time())}",
        task_queue=config.TEMPORAL_TASK_QUEUE
    )

    print(f"✅ Workflow started: {handle.id}")
    print(f"🔗 View at: https://cloud.temporal.io/namespaces/{config.TEMPORAL_NAMESPACE}/workflows/{handle.id}")
    print("\n⏰ Waiting for completion (2-3 minutes)...\n")

    # Wait for result
    result = await handle.result()

    print("\n" + "="*70)
    print("🎉 FIRST AVENUE CREATED!")
    print("="*70)
    print(f"\n🆔 Company ID: {result['company_id']}")
    print(f"🔗 Slug: {result['slug']}")
    print(f"\n🎨 SEMI-CARTOON IMAGES:")
    print(f"   Featured: {result.get('featured_image_url', 'N/A')}")
    print(f"   Hero: {result.get('hero_image_url', 'N/A')}")
    print(f"\n💰 Cost: ${result.get('research_cost', 0):.4f}")
    print(f"📊 Confidence: {result.get('research_confidence', 0):.2%}\n")

    return result


if __name__ == "__main__":
    asyncio.run(main())
