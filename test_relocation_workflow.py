#!/usr/bin/env python3
"""
Test Relocation Workflow

Test relocation app with Phase 3 app-specific images.
"""

import asyncio
import os
import sys
from datetime import timedelta
from temporalio.client import Client
from dotenv import load_dotenv

load_dotenv()

async def test_relocation():
    """Test relocation workflow with UK visa topic"""

    temporal_address = os.getenv("TEMPORAL_ADDRESS")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    print("\n" + "=" * 80)
    print("🚀 Testing Relocation Workflow (Phase 3 - App-Specific Images)")
    print("=" * 80)
    print(f"   Topic: Guide to Portugal Digital Nomad Visa 2025")
    print(f"   App: relocation")
    print(f"   Expected: Practical, expat-focused content and imagery")
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

        # Start workflow
        workflow_id = f"relocation-test-{int(asyncio.get_event_loop().time())}"

        print(f"📝 Starting workflow: {workflow_id}\n")

        handle = await client.start_workflow(
            "NewsroomWorkflow",
            args=[
                "Complete guide to Portugal Digital Nomad Visa 2025: requirements, application process, and cost",
                1400,  # target_word_count
                True,  # auto_approve
                "relocation",  # app
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
        if result.get('hero_image'):
            print(f"\n✅ Hero image generated!")
        else:
            print(f"\n⚠️  No hero image (Replicate might not be configured)")

        # Check metadata for quality issues
        metadata = result.get('metadata', {})
        if 'quality_issues' in metadata:
            print(f"\n⚠️  Quality Issues:")
            for issue in metadata['quality_issues']:
                print(f"     - {issue}")
        else:
            print(f"\n✅ No quality issues - article meets all standards!")

        print("=" * 80 + "\n")

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
        result = asyncio.run(test_relocation())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
