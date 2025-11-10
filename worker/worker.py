"""
Quest Worker - Temporal Python Worker

Executes NewsroomWorkflow for content generation across multiple apps.
"""

import asyncio
import os
import sys

from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import workflows (relative imports for Railway deployment)
from workflows.newsroom import NewsroomWorkflow
from workflows.placement import PlacementWorkflow
from workflows.relocation import RelocationWorkflow

# Import all activities
from activities import (
    # Database
    save_to_neon,

    # Research
    search_news_serper,
    deep_scrape_sources,
    extract_entities_from_news,
    extract_entities_citations,
    calculate_quality_score,
    sync_to_zep,  # Legacy

    # Zep Graph
    check_zep_coverage,
    sync_article_to_zep,
    extract_facts_to_zep,

    # Generation
    generate_article,

    # Images - Original (multi-app with config)
    generate_article_images,
)

# Import new dedicated image activities
from activities.images_placement import generate_placement_images
from activities.images_relocation import generate_relocation_images


async def main():
    """Start the Temporal worker"""

    # Get Temporal configuration from environment
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    print("🔧 Quest Worker Configuration:")
    print(f"   Temporal Address: {temporal_address}")
    print(f"   Namespace: {temporal_namespace}")
    print(f"   Task Queue: {task_queue}")
    print(f"   API Key: {'✅ Set' if temporal_api_key else '❌ Not set'}")

    # Validate required environment variables
    required_vars = [
        "DATABASE_URL",
        "GOOGLE_API_KEY",
        "SERPER_API_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please set them in .env file or environment")
        sys.exit(1)

    print("✅ All required environment variables present")

    # Connect to Temporal Cloud
    print(f"\n🔗 Connecting to Temporal Cloud...")

    try:
        if temporal_api_key:
            # Connect to Temporal Cloud with API key and TLS
            client = await Client.connect(
                temporal_address,
                namespace=temporal_namespace,
                api_key=temporal_api_key,
                tls=True,  # Enable TLS for Temporal Cloud
            )
        else:
            # Connect to local Temporal (no API key, no TLS)
            client = await Client.connect(
                temporal_address,
                namespace=temporal_namespace,
            )

        print("✅ Connected to Temporal")

    except Exception as e:
        print(f"❌ Failed to connect to Temporal: {e}")
        sys.exit(1)

    # Create worker with all workflows and activities
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[NewsroomWorkflow, PlacementWorkflow, RelocationWorkflow],
        activities=[
            # Database
            save_to_neon,

            # Research
            search_news_serper,
            deep_scrape_sources,
            extract_entities_from_news,
            extract_entities_citations,
            calculate_quality_score,
            sync_to_zep,  # Legacy

            # Zep Graph
            check_zep_coverage,
            sync_article_to_zep,
            extract_facts_to_zep,

            # Generation
            generate_article,

            # Images - Original (multi-app with config)
            generate_article_images,

            # Images - Dedicated per app (simple, no config)
            generate_placement_images,
            generate_relocation_images,
        ],
    )

    print("\n" + "=" * 60)
    print("🚀 Quest Worker Started Successfully!")
    print("=" * 60)
    print(f"   Task Queue: {task_queue}")
    print("=" * 60)
    print("\n📋 Registered Workflows:")
    print("   - NewsroomWorkflow (multi-app)")
    print("   - PlacementWorkflow (dedicated)")
    print("   - RelocationWorkflow (dedicated)")
    print("\n📋 Registered Activities:")
    print("   Database:")
    print("     - save_to_neon")
    print("   Research:")
    print("     - search_news_serper")
    print("     - deep_scrape_sources")
    print("     - extract_entities_from_news")
    print("     - extract_entities_citations")
    print("     - calculate_quality_score")
    print("   Zep Graph:")
    print("     - check_zep_coverage")
    print("     - sync_article_to_zep")
    print("     - extract_facts_to_zep")
    print("   Generation:")
    print("     - generate_article")
    print("   Images:")
    print("     - generate_article_images (original multi-app)")
    print("     - generate_placement_images (dedicated, no config)")
    print("     - generate_relocation_images (dedicated, no config)")
    print("\n✅ Worker is ready to process workflows...")
    print("   Press Ctrl+C to stop\n")

    # Run worker (blocks until interrupted)
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Worker crashed: {e}")
        sys.exit(1)
