#!/usr/bin/env python3
"""
Trigger ArticleWorkflow directly via Temporal
"""
import asyncio
import os
from temporalio.client import Client

async def trigger_article_workflow():
    """Trigger ArticleWorkflow for Digital Nomad Visa Portugal"""

    # Temporal configuration
    temporal_address = "europe-west3.gcp.api.temporal.io:7233"
    temporal_namespace = "quickstart-quest.zivkb"
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")

    if not temporal_api_key:
        print("❌ TEMPORAL_API_KEY not set")
        return

    print(f"🔗 Connecting to Temporal...")
    print(f"   Address: {temporal_address}")
    print(f"   Namespace: {temporal_namespace}")

    # Connect to Temporal Cloud
    client = await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
        api_key=temporal_api_key,
        tls=True,
    )

    print("✅ Connected to Temporal")

    # Workflow parameters
    workflow_id = "article-research-relocation-digital-nomad-visa-portugal-test"
    topic = "Digital Nomad Visa Portugal"
    app = "relocation"
    target_word_count = 2000
    num_research_sources = 7
    deep_crawl_enabled = True
    skip_zep_sync = False

    print(f"\n🚀 Starting ArticleWorkflow...")
    print(f"   Topic: {topic}")
    print(f"   App: {app}")
    print(f"   Word Count: {target_word_count}")
    print(f"   Research Sources: {num_research_sources}")
    print(f"   Deep Crawl: {deep_crawl_enabled}")

    try:
        # Start workflow
        handle = await client.start_workflow(
            "ArticleWorkflow",
            args=[
                topic,
                app,
                target_word_count,
                num_research_sources,
                deep_crawl_enabled,
                skip_zep_sync,
            ],
            id=workflow_id,
            task_queue="quest-content-queue",
        )

        print(f"\n✅ Workflow started successfully!")
        print(f"   Workflow ID: {handle.id}")
        print(f"   Run ID: {handle.result_run_id}")
        print(f"\n📊 Monitor progress at:")
        print(f"   https://cloud.temporal.io/namespaces/{temporal_namespace}/workflows/{workflow_id}")

        return handle.id

    except Exception as e:
        print(f"\n❌ Failed to start workflow: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(trigger_article_workflow())
