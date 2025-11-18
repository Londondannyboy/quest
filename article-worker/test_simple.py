#!/usr/bin/env python3
"""Simplest possible test with explicit queue"""

import asyncio
import os
from temporalio.client import Client

async def main():
    print("🧪 Connecting to Temporal...")

    # Use environment variables
    client = await Client.connect(
        os.getenv("TEMPORAL_ADDRESS", "europe-west3.gcp.api.temporal.io:7233"),
        namespace=os.getenv("TEMPORAL_NAMESPACE", "quickstart-quest.zivkb"),
        api_key=os.getenv("TEMPORAL_API_KEY"),
        tls=True
    )

    print("✅ Connected!")

    # Import workflow
    from src.workflows.article_creation import ArticleCreationWorkflow

    # Minimal input
    workflow_input = {
        "topic": "Digital Nomad Visa Greece",
        "app": "relocation",
        "target_word_count": 500,
        "generate_images": False,  # Disabled
        "skip_zep_sync": True,  # Disabled
        "deep_crawl_enabled": False,  # Disabled
    }

    print(f"\n🚀 Starting: {workflow_input['topic']}")
    print(f"📋 Queue: quest-article-queue")

    # Start workflow with explicit queue
    handle = await client.start_workflow(
        ArticleCreationWorkflow.run,
        workflow_input,
        id=f"test-greece-{int(asyncio.get_event_loop().time())}",
        task_queue="quest-article-queue"  # Explicit!
    )

    print(f"✅ Started: {handle.id}")
    print(f"\n🔗 Monitor at:")
    print(f"   https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows/{handle.id}")
    print(f"\n⏰ Waiting (max 2 min)...\n")

    try:
        result = await asyncio.wait_for(handle.result(), timeout=120)
        print("\n✅ SUCCESS!")
        print(f"Result: {result}")
    except asyncio.TimeoutError:
        print("\n⏱️ Timeout - check Temporal UI")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
