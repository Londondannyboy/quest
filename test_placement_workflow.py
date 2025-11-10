#!/usr/bin/env python3
"""
Test PlacementWorkflow - Simple dedicated workflow with hardcoded image prompts
"""

import asyncio
import os
import time
from datetime import timedelta
from temporalio.client import Client
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Test the new PlacementWorkflow with simple image generation"""

    temporal_address = os.getenv("TEMPORAL_ADDRESS")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    print("=" * 80)
    print("🚀 Testing PlacementWorkflow - Dedicated workflow with simple images")
    print("=" * 80)
    print(f"   Topic: Goldman Sachs M&A advisory record quarter")
    print(f"   Expected: Bloomberg-style corporate imagery (no config loading)")
    print("=" * 80)
    print()

    # Connect to Temporal
    print("✅ Connected to Temporal Cloud")
    print()

    client = await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
        api_key=temporal_api_key,
        tls=True,
    )

    # Start workflow
    workflow_id = f"placement-test-{int(time.time())}"

    print(f"📝 Starting PlacementWorkflow: {workflow_id}")
    print()

    handle = await client.start_workflow(
        "PlacementWorkflow",
        args=[
            "Goldman Sachs M&A advisory record quarter",
            1500,  # target_word_count
            True,  # auto_approve
            True,  # skip_zep_check
        ],
        task_queue=task_queue,
        id=workflow_id,
        execution_timeout=timedelta(minutes=30),
    )

    print("✅ Workflow started")
    print(f"   Workflow ID: {workflow_id}")
    print(f"   Run ID: {handle.result_run_id}")
    print()

    print("⏳ Waiting for completion (may take 5-10 minutes)...")
    print()

    # Wait for result
    result = await handle.result()

    print()
    print("=" * 80)
    print("✅ WORKFLOW COMPLETED")
    print("=" * 80)
    print(f"   Title: {result.get('title', 'Unknown')}")
    print(f"   Slug: {result.get('slug', 'Unknown')}")
    print(f"   Word Count: {result.get('word_count', 0)}")
    print(f"   Citation Count: {result.get('citation_count', 0)}")
    print(f"   Status: {result.get('status', 'Unknown')}")
    print(f"   App: placement (hardcoded)")
    print()

    # Check images
    images = result.get('images', {})
    print("🎨 IMAGE GENERATION:")
    if images.get('hero'):
        print(f"   ✅ Hero image: {images['hero'][:80]}...")
    else:
        print("   ❌ No hero image")

    if images.get('featured'):
        print(f"   ✅ Featured image: {images['featured'][:80]}...")
    else:
        print("   ⚠️  No featured image")

    if images.get('content'):
        print(f"   ✅ Content image: {images['content'][:80]}...")
    else:
        print("   ⚠️  No content image")

    print()
    print("=" * 80)
    print()
    print(f"🌐 View at: https://placement.quest/{result.get('slug', '')}")


if __name__ == "__main__":
    asyncio.run(main())
