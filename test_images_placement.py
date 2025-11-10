#!/usr/bin/env python3
"""
Test Placement Workflow with Images - Phase 3 Validation

Tests app-specific image generation with Bloomberg-style imagery.
"""

import asyncio
import os
import sys
from datetime import timedelta
from temporalio.client import Client
from dotenv import load_dotenv

load_dotenv()

async def test_placement_images():
    """Test placement workflow with Phase 3 app-specific images"""

    temporal_address = os.getenv("TEMPORAL_ADDRESS")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    print("\n" + "=" * 80)
    print("🚀 Testing Placement Workflow - Phase 3 Image Generation")
    print("=" * 80)
    print(f"   Topic: Goldman Sachs M&A advisory revenue hits record")
    print(f"   App: placement")
    print(f"   Expected: Bloomberg-style corporate financial imagery")
    print("=" * 80 + "\n")

    try:
        # Connect to Temporal
        if temporal_api_key:
            client = await Client.connect(
                temporal_address,
                namespace=temporal_namespace,
                api_key=temporal_api_key,
                tls=True,
            )
        else:
            client = await Client.connect(
                temporal_address,
                namespace=temporal_namespace,
            )

        print("✅ Connected to Temporal Cloud\n")

        # Start workflow with unique ID
        import time
        workflow_id = f"placement-images-test-{int(time.time())}"

        print(f"📝 Starting workflow: {workflow_id}\n")

        handle = await client.start_workflow(
            "NewsroomWorkflow",
            args=[
                "Barclays announces major expansion of investment banking division in Asia Pacific region",
                1500,  # target_word_count
                True,  # auto_approve
                "placement",  # app
                # skip_zep_check defaults to True now
            ],
            task_queue=task_queue,
            id=workflow_id,
            execution_timeout=timedelta(minutes=30),
        )

        print(f"✅ Workflow started")
        print(f"   Workflow ID: {workflow_id}")
        print(f"   Run ID: {handle.result_run_id}")
        print(f"\n⏳ Waiting for completion (may take 5-10 minutes)...\n")

        # Wait for result
        result = await asyncio.wait_for(
            handle.result(),
            timeout=1800.0
        )

        print("\n" + "=" * 80)
        print("✅ WORKFLOW COMPLETED")
        print("=" * 80)
        print(f"   Title: {result.get('title', 'Unknown')}")
        print(f"   Slug: {result.get('slug', 'Unknown')}")
        print(f"   Word Count: {result.get('word_count', 0)}")
        print(f"   Citation Count: {result.get('citation_count', 0)}")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   App: {result.get('app', 'Unknown')}")

        # Check for images
        images = result.get('images', {})
        if images:
            print(f"\n🎨 IMAGE GENERATION:")
            if images.get('hero'):
                print(f"   ✅ Hero image: {images['hero'][:60]}...")
            else:
                print(f"   ❌ No hero image")

            if images.get('featured'):
                print(f"   ✅ Featured image: {images['featured'][:60]}...")
            else:
                print(f"   ⚠️  No featured image")

            if images.get('content'):
                print(f"   ✅ Content image: {images['content'][:60]}...")
            else:
                print(f"   ⚠️  No content image")
        else:
            print(f"\n⚠️  No images generated (check Replicate/Cloudinary config)")

        # Check metadata for quality issues
        metadata = result.get('metadata', {})
        if 'quality_issues' in metadata:
            print(f"\n⚠️  Quality Issues:")
            for issue in metadata['quality_issues']:
                print(f"     - {issue}")
        else:
            print(f"\n✅ No quality issues - article meets all standards!")

        print("=" * 80 + "\n")
        print(f"🌐 View at: https://placement.quest/{result.get('slug', '')}\n")

        return result

    except asyncio.TimeoutError:
        print("\n❌ Workflow timed out after 30 minutes")
        return None
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    try:
        result = asyncio.run(test_placement_images())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
