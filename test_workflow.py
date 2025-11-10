#!/usr/bin/env python3
"""
Test Workflow Trigger

Triggers NewsroomWorkflow with test topics for Placement and Relocation apps
to validate app-specific content generation.
"""

import asyncio
import os
import sys
from datetime import timedelta
from temporalio.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def trigger_workflow(topic: str, app: str, target_word_count: int = 1500):
    """
    Trigger a NewsroomWorkflow execution

    Args:
        topic: Topic to generate article about
        app: App identifier ("placement" or "relocation")
        target_word_count: Target word count for article
    """
    # Get Temporal configuration
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    print(f"\n{'=' * 80}")
    print(f"🚀 Triggering Workflow: {app.upper()}")
    print(f"{'=' * 80}")
    print(f"   Topic: {topic}")
    print(f"   App: {app}")
    print(f"   Target Words: {target_word_count}")
    print(f"   Temporal: {temporal_address}")
    print(f"   Namespace: {temporal_namespace}")
    print(f"   Queue: {task_queue}")
    print(f"{'=' * 80}\n")

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

        print("✅ Connected to Temporal Cloud")

        # Generate workflow ID
        workflow_id = f"newsroom-test-{app}-{int(asyncio.get_event_loop().time())}"

        # Start workflow
        print(f"\n📝 Starting workflow: {workflow_id}")

        handle = await client.start_workflow(
            "NewsroomWorkflow",
            args=[
                topic,
                target_word_count,
                True,  # auto_approve
                app,
                False,  # skip_zep_check - Enable Zep check for real test
            ],
            task_queue=task_queue,
            id=workflow_id,
            execution_timeout=timedelta(minutes=30),
        )

        print(f"✅ Workflow started")
        print(f"   Workflow ID: {workflow_id}")
        print(f"   Run ID: {handle.result_run_id}")
        print(f"\n⏳ Waiting for workflow to complete...")
        print(f"   (This may take 5-10 minutes)")

        # Wait for result (with timeout)
        result = await asyncio.wait_for(
            handle.result(),
            timeout=1800.0  # 30 minute timeout
        )

        print(f"\n{'=' * 80}")
        print(f"✅ WORKFLOW COMPLETED SUCCESSFULLY")
        print(f"{'=' * 80}")
        print(f"   Title: {result.get('title', 'Unknown')}")
        print(f"   Slug: {result.get('slug', 'Unknown')}")
        print(f"   Word Count: {result.get('word_count', 0)}")
        print(f"   Citation Count: {result.get('citation_count', 0)}")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   App: {result.get('app', 'Unknown')}")
        print(f"   Neon Saved: {result.get('neon_saved', False)}")
        print(f"   Zep Episode ID: {result.get('zep_episode_id', 'N/A')}")

        # Check for quality issues in metadata
        metadata = result.get('metadata', {})
        if 'quality_issues' in metadata:
            print(f"\n⚠️  Quality Issues Detected:")
            for issue in metadata['quality_issues']:
                print(f"     - {issue}")

        print(f"{'=' * 80}\n")

        return result

    except asyncio.TimeoutError:
        print(f"\n❌ Workflow timed out after 30 minutes")
        return None
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run workflow tests for both apps"""

    print("\n" + "=" * 80)
    print("QUEST WORKFLOW TESTING - App-Specific Content Generation")
    print("=" * 80)

    # Check required environment variables
    required_vars = [
        "TEMPORAL_ADDRESS",
        "TEMPORAL_NAMESPACE",
        "TEMPORAL_API_KEY",
        "DATABASE_URL",
        "GOOGLE_API_KEY",
        "SERPER_API_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set them in .env file or environment")
        sys.exit(1)

    print("\n✅ All required environment variables present")

    # Test scenarios
    tests = [
        {
            "app": "placement",
            "topic": "KKR acquires software company in $2.5 billion deal",
            "target_word_count": 1500,
        },
        {
            "app": "relocation",
            "topic": "UK visa requirements for skilled workers 2025",
            "target_word_count": 1400,
        },
    ]

    results = []

    for i, test in enumerate(tests, 1):
        print(f"\n\n{'#' * 80}")
        print(f"TEST {i} of {len(tests)}")
        print(f"{'#' * 80}")

        result = await trigger_workflow(
            topic=test["topic"],
            app=test["app"],
            target_word_count=test["target_word_count"]
        )

        results.append({
            "test": test,
            "result": result,
            "success": result is not None
        })

        # Brief pause between tests
        if i < len(tests):
            print("\n⏸️  Pausing 10 seconds before next test...")
            await asyncio.sleep(10)

    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for i, test_result in enumerate(results, 1):
        test = test_result["test"]
        success = test_result["success"]
        result = test_result["result"]

        status_emoji = "✅" if success else "❌"
        print(f"\n{status_emoji} Test {i}: {test['app'].upper()}")
        print(f"   Topic: {test['topic']}")

        if success and result:
            print(f"   Title: {result.get('title', 'N/A')}")
            print(f"   Words: {result.get('word_count', 0)}")
            print(f"   Citations: {result.get('citation_count', 0)}")
            print(f"   Status: {result.get('status', 'N/A')}")
        else:
            print(f"   Status: FAILED")

    success_count = sum(1 for r in results if r["success"])
    print(f"\n{'=' * 80}")
    print(f"Overall: {success_count}/{len(tests)} tests passed")
    print(f"{'=' * 80}\n")

    return success_count == len(tests)


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
