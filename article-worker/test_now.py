#!/usr/bin/env python3
import asyncio
import os
from temporalio.client import Client

async def main():
    print("🧪 Testing ArticleCreationWorkflow...")
    print(f"   Queue: quest-content-queue")
    
    client = await Client.connect(
        os.getenv("TEMPORAL_ADDRESS", "europe-west3.gcp.api.temporal.io:7233"),
        namespace=os.getenv("TEMPORAL_NAMESPACE", "quickstart-quest.zivkb"),
        api_key=os.getenv("TEMPORAL_API_KEY"),
        tls=True
    )
    
    print("✅ Connected to Temporal")
    
    from src.workflows.article_creation import ArticleCreationWorkflow
    
    workflow_input = {
        "topic": "Digital Nomad Visa Greece",
        "app": "relocation",
        "target_word_count": 500,
        "article_format": "article",
        "generate_images": False,
        "skip_zep_sync": True,
        "deep_crawl_enabled": False,
        "num_research_sources": 3,
        "auto_publish": False
    }
    
    workflow_id = f"greece-test-{int(asyncio.get_event_loop().time())}"
    
    handle = await client.start_workflow(
        ArticleCreationWorkflow.run,
        workflow_input,
        id=workflow_id,
        task_queue="quest-content-queue"
    )
    
    print(f"\n✅ Workflow started: {workflow_id}")
    print(f"🔗 Monitor at: https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows/{workflow_id}")
    print(f"\n⏰ Waiting for result (max 3 min)...\n")
    
    try:
        result = await asyncio.wait_for(handle.result(), timeout=180)
        print("\n✅ SUCCESS!")
        print(f"\n📝 Result:")
        print(f"   Article ID: {result.get('article_id')}")
        print(f"   Slug: {result.get('slug')}")
        print(f"   Title: {result.get('title')}")
        print(f"   Word Count: {result.get('word_count')}")
        print(f"   Status: {result.get('publication_status')}")
        return result
    except asyncio.TimeoutError:
        print("\n⏱️  Still running after 3 min - check Temporal UI")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
