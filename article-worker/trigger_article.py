#!/usr/bin/env python3
"""Simple article creation trigger"""

import asyncio
import sys
from temporalio.client import Client
from src.utils.config import config


async def main():
    """Trigger article creation for Digital Nomad Visa Greece"""

    print("🚀 Triggering Digital Nomad Visa Greece article...")

    # Connect to Temporal
    client = await Client.connect(
        config.TEMPORAL_ADDRESS,
        namespace=config.TEMPORAL_NAMESPACE,
        api_key=config.TEMPORAL_API_KEY,
        tls=True
    )

    # Import workflow
    from src.workflows.article_creation import ArticleCreationWorkflow

    # Workflow input
    workflow_input = {
        "topic": "Digital Nomad Visa Greece",
        "app": "relocation",
        "target_word_count": 1500,
        "article_format": "article",
        "jurisdiction": "EU",
        "num_research_sources": 10,
        "deep_crawl_enabled": True,
        "generate_images": True,
        "auto_publish": False,
        "skip_zep_sync": False,
        "target_keywords": ["digital nomad", "Greece visa", "remote work", "relocation"],
        "author": "Quest Editorial Team"
    }

    # Start workflow
    handle = await client.start_workflow(
        ArticleCreationWorkflow.run,
        workflow_input,
        id=f"digital-nomad-greece-{int(asyncio.get_event_loop().time())}",
        task_queue=config.TEMPORAL_TASK_QUEUE
    )

    print(f"✅ Workflow started: {handle.id}")
    print(f"🔗 View at: https://cloud.temporal.io/namespaces/{config.TEMPORAL_NAMESPACE}/workflows/{handle.id}")
    print("\n⏰ Waiting for completion (5-12 minutes)...\n")

    # Wait for result
    try:
        result = await handle.result()

        print("\n" + "="*70)
        print("🎉 ARTICLE CREATED!")
        print("="*70)
        print(f"\n🆔 Article ID: {result['article_id']}")
        print(f"🔗 Slug: {result['slug']}")
        print(f"📝 Title: {result['title']}")
        print(f"\n📊 Metrics:")
        print(f"   Word Count: {result.get('word_count', 0)}")
        print(f"   Sections: {result.get('section_count', 0)}")
        print(f"   Companies Mentioned: {result.get('company_mentions', 0)}")
        print(f"\n🎨 Images:")
        print(f"   Featured: {result.get('featured_image_url', 'N/A')}")
        print(f"   Hero: {result.get('hero_image_url', 'N/A')}")
        print(f"\n💰 Cost: ${result.get('research_cost', 0):.4f}")
        print(f"📊 Completeness: {result.get('completeness_score', 0):.1f}%")
        print(f"📄 Status: {result.get('publication_status', 'draft')}\n")

        return result

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
