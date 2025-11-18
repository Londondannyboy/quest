#!/usr/bin/env python3
"""Direct workflow test - minimal version to debug"""

import asyncio
from temporalio.client import Client
from src.utils.config import config


async def main():
    """Test workflow with minimal input"""

    print("=" * 70)
    print("🧪 TESTING ARTICLE WORKFLOW (MINIMAL)")
    print("=" * 70)

    # Connect to Temporal
    print(f"\n📡 Connecting to Temporal...")
    print(f"   Address: {config.TEMPORAL_ADDRESS}")
    print(f"   Namespace: {config.TEMPORAL_NAMESPACE}")
    print(f"   Task Queue: {config.TEMPORAL_TASK_QUEUE}")

    client = await Client.connect(
        config.TEMPORAL_ADDRESS,
        namespace=config.TEMPORAL_NAMESPACE,
        api_key=config.TEMPORAL_API_KEY,
        tls=True
    )

    print("✅ Connected")

    # Import workflow
    from src.workflows.article_creation import ArticleCreationWorkflow

    # Minimal input
    workflow_input = {
        "topic": "Test Article",
        "app": "relocation",
        "target_word_count": 500,  # Minimal
        "article_format": "article",
        "num_research_sources": 3,  # Minimal
        "deep_crawl_enabled": False,  # Disable to speed up
        "generate_images": False,  # Disable to speed up
        "auto_publish": False,
        "skip_zep_sync": True,  # Skip to speed up
    }

    print(f"\n🚀 Starting workflow: {workflow_input['topic']}")

    # Start workflow
    workflow_id = f"test-article-{int(asyncio.get_event_loop().time())}"

    handle = await client.start_workflow(
        ArticleCreationWorkflow.run,
        workflow_input,
        id=workflow_id,
        task_queue=config.TEMPORAL_TASK_QUEUE
    )

    print(f"✅ Workflow started: {handle.id}")
    print(f"🔗 View at: https://cloud.temporal.io/namespaces/{config.TEMPORAL_NAMESPACE}/workflows/{handle.id}")

    print("\n⏰ Waiting for result (timeout 3 min)...")

    try:
        result = await asyncio.wait_for(handle.result(), timeout=180)

        print("\n" + "=" * 70)
        print("✅ WORKFLOW COMPLETED!")
        print("=" * 70)
        print(f"\nResult: {result}")

    except asyncio.TimeoutError:
        print("\n" + "=" * 70)
        print("⏱️  WORKFLOW STILL RUNNING (timeout)")
        print("=" * 70)
        print(f"\n🔗 Check status at: https://cloud.temporal.io/namespaces/{config.TEMPORAL_NAMESPACE}/workflows/{workflow_id}")

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ WORKFLOW FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
