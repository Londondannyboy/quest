"""
Video Worker - Temporal Python Worker for Video Enrichment

Executes VideoEnrichmentWorkflow for adding videos to existing articles.
"""

import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import workflow
from src.workflows.video_enrichment_workflow import VideoEnrichmentWorkflow

# Import activities
from src.activities.storage.neon_database import (
    get_article_by_slug,
    update_article_four_act_content,
)
from src.activities.generation.article_generation import (
    generate_four_act_video_prompt_brief,
    generate_four_act_video_prompt,
)
from src.activities.media.video_generation import (
    generate_four_act_video,
)
from src.activities.media.mux_client import (
    upload_video_to_mux,
)

from src.utils.config import config


async def main():
    """Start the Video Worker"""

    print("=" * 70)
    print("🎬 Video Worker - Starting...")
    print("=" * 70)

    # Display configuration
    print("\n🔧 Configuration:")
    print(f"   Temporal Address: {config.TEMPORAL_ADDRESS}")
    print(f"   Namespace: {config.TEMPORAL_NAMESPACE}")
    print(f"   Task Queue: {config.TEMPORAL_TASK_QUEUE}")
    print(f"   API Key: {'✅ Set' if config.TEMPORAL_API_KEY else '❌ Not set'}")
    print(f"   Environment: {config.ENVIRONMENT}")

    # Validate required environment variables
    missing = config.validate_required()

    if missing:
        print(f"\n❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n   Please set them in .env file or environment")
        sys.exit(1)

    print("\n✅ All required environment variables present")

    # Connect to Temporal
    print(f"\n🔗 Connecting to Temporal Cloud...")

    try:
        if config.TEMPORAL_API_KEY:
            # Temporal Cloud with TLS
            client = await Client.connect(
                config.TEMPORAL_ADDRESS,
                namespace=config.TEMPORAL_NAMESPACE,
                api_key=config.TEMPORAL_API_KEY,
                tls=True,
            )
        else:
            # Local Temporal (development)
            client = await Client.connect(
                config.TEMPORAL_ADDRESS,
                namespace=config.TEMPORAL_NAMESPACE,
            )

        print("✅ Connected to Temporal successfully")

    except Exception as e:
        print(f"❌ Failed to connect to Temporal: {e}")
        sys.exit(1)

    # Create worker with video enrichment workflow
    worker = Worker(
        client,
        task_queue=config.TEMPORAL_TASK_QUEUE,
        workflows=[VideoEnrichmentWorkflow],
        activities=[
            # Database
            get_article_by_slug,
            update_article_four_act_content,

            # Video prompt generation
            generate_four_act_video_prompt_brief,
            generate_four_act_video_prompt,

            # Video generation
            generate_four_act_video,

            # MUX upload
            upload_video_to_mux,
        ],
    )

    print("\n" + "=" * 70)
    print("🚀 Video Worker Started Successfully!")
    print("=" * 70)
    print(f"   Task Queue: {config.TEMPORAL_TASK_QUEUE}")
    print(f"   Environment: {config.ENVIRONMENT}")
    print("=" * 70)

    print("\n📋 Registered Workflows:")
    print("   - VideoEnrichmentWorkflow (Dashboard-triggered video enrichment)")

    print("\n📋 Registered Activities:")
    print("   - get_article_by_slug")
    print("   - update_article_four_act_content")
    print("   - generate_four_act_video_prompt_brief")
    print("   - generate_four_act_video_prompt")
    print("   - generate_four_act_video")
    print("   - upload_video_to_mux")

    print("\n✅ Worker is ready to process video enrichment workflows")
    print("   Press Ctrl+C to stop\n")

    # Run worker (blocks until interrupted)
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Video Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Video Worker crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
