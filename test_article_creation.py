#!/usr/bin/env python3
"""
Test ArticleCreationWorkflow directly on quest-company-queue
"""
import asyncio
import os
from temporalio.client import Client

async def test_article_creation():
    """Test the ArticleCreationWorkflow in company-worker"""

    # Temporal configuration
    temporal_address = "europe-west3.gcp.api.temporal.io:7233"
    temporal_namespace = "quickstart-quest.zivkb"
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")

    if not temporal_api_key:
        print("❌ TEMPORAL_API_KEY not set")
        return

    print(f"🔗 Connecting to Temporal...")

    client = await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
        api_key=temporal_api_key,
        tls=True,
    )

    print("✅ Connected to Temporal")

    # Workflow parameters
    workflow_id = "test-article-creation-topgolf"

    input_dict = {
        "topic": "Leonard Green takes control of Topgolf in $1.1bn carve-out from Callaway",
        "article_type": "news",
        "app": "placement",
        "target_word_count": 1500,
        "jurisdiction": "US",
        "generate_images": False,  # Skip images for faster test
        "num_research_sources": 5
    }

    print(f"\n🚀 Starting ArticleCreationWorkflow...")
    print(f"   Topic: {input_dict['topic']}")
    print(f"   Task Queue: quest-company-queue")

    try:
        handle = await client.start_workflow(
            "ArticleCreationWorkflow",
            args=[input_dict],
            id=workflow_id,
            task_queue="quest-company-queue",  # Company worker queue!
        )

        print(f"\n✅ Workflow started!")
        print(f"   Workflow ID: {handle.id}")
        print(f"\n📊 Monitor at:")
        print(f"   https://cloud.temporal.io/namespaces/{temporal_namespace}/workflows/{workflow_id}")

        # Wait for result
        print("\n⏳ Waiting for result...")
        result = await handle.result()

        print("\n✅ Workflow completed!")
        print(f"   Title: {result.get('title', 'N/A')}")
        print(f"   Word Count: {result.get('word_count', 0)}")
        print(f"   Success: {result.get('article', {}).get('content', '')[:200]}...")

        return result

    except Exception as e:
        print(f"\n❌ Failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_article_creation())
