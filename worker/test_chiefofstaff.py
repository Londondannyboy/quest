"""
Test Chief of Staff Workflow

Triggers a ChiefOfStaffWorkflow to generate an executive leadership article.
"""

import asyncio
import os
from uuid import uuid4
from temporalio.client import Client
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Trigger a Chief of Staff workflow"""

    # Get Temporal configuration
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")

    print("🚀 Testing Chief of Staff Workflow")
    print("=" * 60)
    print(f"Temporal Address: {temporal_address}")
    print(f"Namespace: {temporal_namespace}")
    print("=" * 60)

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

    print("✅ Connected to Temporal\n")

    # Define test topic
    topic = "Executive leadership frameworks for chiefs of staff in 2025"
    target_word_count = 1500
    auto_approve = True
    skip_zep_check = True

    print(f"📰 Topic: {topic}")
    print(f"📊 Target words: {target_word_count}")
    print(f"🎯 App: chiefofstaff")
    print()

    # Generate workflow ID
    workflow_id = f"chiefofstaff-test-{uuid4()}"

    print(f"🔄 Starting workflow: {workflow_id}")
    print()

    # Start the workflow
    handle = await client.start_workflow(
        "ChiefOfStaffWorkflow",
        args=[topic, target_word_count, auto_approve, skip_zep_check],
        id=workflow_id,
        task_queue="quest-content-queue",
    )

    print(f"✅ Workflow started!")
    print(f"   Workflow ID: {workflow_id}")
    print(f"   Run ID: {handle.first_execution_run_id}")
    print()
    print("⏳ Waiting for workflow to complete...")
    print("   (This may take 5-10 minutes)")
    print()

    # Wait for result
    try:
        result = await handle.result()

        print("=" * 60)
        print("🎉 WORKFLOW COMPLETE!")
        print("=" * 60)
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Words: {result.get('word_count', 0)}")
        print(f"App: {result.get('app', 'N/A')}")
        print(f"Neon Saved: {result.get('neon_saved', False)}")
        print(f"Zep Episode: {result.get('zep_episode_id', 'N/A')}")
        print()

        if result.get('images'):
            print("🎨 Images Generated:")
            for img_type, url in result['images'].items():
                if url:
                    print(f"   {img_type}: {url[:80]}...")

        print("=" * 60)

    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
