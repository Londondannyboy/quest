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

    # Workflow input - with video-first configuration
    workflow_input = {
        "url": "https://www.firstavenue.com/",
        "category": "placement",
        "app": "placement",
        "jurisdiction": "US",
        "generate_images": True,
        "video_quality": None,  # None, "low", "medium", "high" - generates video for hero
        "video_model": "seedance",  # "seedance" or "wan-2.5"
        "video_prompt": None,  # Optional custom prompt for video generation
        "content_images": "with_content",  # "with_content" or "without_content"
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

    # Show video or images depending on what was generated
    if result.get('video_url'):
        print(f"\n🎬 VIDEO-FIRST ASSETS:")
        print(f"   Video Playback ID: {result.get('video_playback_id', 'N/A')}")
        print(f"   Featured GIF: {result.get('featured_image_url', 'N/A')}")
    else:
        print(f"\n🎨 CONTEXTUAL BRAND IMAGES:")
        print(f"   Featured: {result.get('featured_image_url', 'N/A')}")
        print(f"   Hero: {result.get('hero_image_url', 'N/A')}")

    print(f"\n💰 Cost: ${result.get('research_cost', 0):.4f}")
    print(f"📊 Confidence: {result.get('research_confidence', 0):.2%}")
    print(f"📈 Data Completeness: {result.get('data_completeness', 0)}%\n")

    return result


if __name__ == "__main__":
    asyncio.run(main())
