"""
Test script for VideoEnrichmentWorkflow

Tests video enrichment for a specific article by directly triggering the Temporal workflow.
"""

import asyncio
import os
from temporalio.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_video_enrichment():
    """Test video enrichment for France article"""

    # Article details
    article_url = "https://relocation.quest/hubs/france-relocation-visa-application-cost-living-company-tax-rate-guide"
    article_slug = "france-relocation-visa-application-cost-living-company-tax-rate-guide"

    print("=" * 70)
    print("🎬 Testing Video Enrichment Workflow")
    print("=" * 70)
    print(f"Article URL: {article_url}")
    print(f"Article Slug: {article_slug}")
    print()

    # Configuration
    TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "europe-west3.gcp.api.temporal.io:7233")
    TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "quickstart-quest.zivkb")
    TEMPORAL_API_KEY = os.getenv("TEMPORAL_API_KEY")
    TASK_QUEUE = "quest-content-queue"

    print("🔗 Connecting to Temporal...")
    print(f"   Address: {TEMPORAL_ADDRESS}")
    print(f"   Namespace: {TEMPORAL_NAMESPACE}")
    print(f"   Task Queue: {TASK_QUEUE}")
    print()

    # Connect to Temporal
    client = await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=TEMPORAL_NAMESPACE,
        api_key=TEMPORAL_API_KEY,
        tls=True,
    )

    print("✅ Connected to Temporal")
    print()

    # Generate workflow ID
    workflow_id = f"video-enrichment-test-{article_slug}"

    print("🚀 Starting VideoEnrichmentWorkflow...")
    print(f"   Workflow ID: {workflow_id}")
    print()

    # Workflow parameters
    params = {
        "slug": article_slug,
        "app": "relocation",
        "video_model": "seedance-1-pro-fast",
        "min_sections": 4,
        "force_regenerate": False
    }

    print("📋 Workflow Parameters:")
    for key, value in params.items():
        print(f"   {key}: {value}")
    print()

    try:
        # Start workflow
        handle = await client.start_workflow(
            "VideoEnrichmentWorkflow",
            args=[
                params["slug"],
                params["app"],
                params["video_model"],
                params["min_sections"],
                params["force_regenerate"]
            ],
            id=workflow_id,
            task_queue=TASK_QUEUE
        )

        print("✅ Workflow started successfully!")
        print()
        print("📊 Monitor workflow:")
        temporal_url = f"https://cloud.temporal.io/namespaces/{TEMPORAL_NAMESPACE}/workflows/{workflow_id}"
        print(f"   {temporal_url}")
        print()
        print("⏳ Waiting for workflow to complete (this may take 2-5 minutes)...")
        print()

        # Wait for result
        result = await handle.result()

        print("=" * 70)
        print("✅ Video Enrichment Completed Successfully!")
        print("=" * 70)
        print()
        print("📊 Results:")
        for key, value in result.items():
            print(f"   {key}: {value}")
        print()

    except Exception as e:
        print("=" * 70)
        print("❌ Error occurred during workflow execution")
        print("=" * 70)
        print(f"   Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_video_enrichment())
