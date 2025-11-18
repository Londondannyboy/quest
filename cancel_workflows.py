#!/usr/bin/env python3
"""Cancel all scheduled/running workflows in Temporal."""
import asyncio
from temporalio.client import Client, WorkflowExecutionStatus
import os

async def main():
    print("🔌 Connecting to Temporal Cloud...")
    client = await Client.connect(
        os.environ["TEMPORAL_ADDRESS"],
        namespace=os.environ["TEMPORAL_NAMESPACE"],
        api_key=os.environ["TEMPORAL_API_KEY"],
    )
    print("   ✅ Connected!\n")

    # List all workflows (running, scheduled, etc.)
    print("📋 Listing all workflows...")

    workflows = []
    async for workflow in client.list_workflows(
        query="ExecutionStatus='Running' OR ExecutionStatus='ContinuedAsNew'"
    ):
        workflows.append(workflow)

    if not workflows:
        print("   ✅ No running workflows found!")
        return

    print(f"   Found {len(workflows)} running workflows\n")

    # Show workflows
    print("=" * 60)
    for i, wf in enumerate(workflows, 1):
        print(f"{i}. ID: {wf.id}")
        print(f"   Type: {wf.workflow_type}")
        print(f"   Status: {wf.status}")
        print(f"   Start Time: {wf.start_time}")
        print()

    print("=" * 60)
    confirm = input(f"\n❗ Cancel ALL {len(workflows)} workflows? (yes/no): ")

    if confirm.lower() != "yes":
        print("❌ Cancelled - no workflows terminated")
        return

    print(f"\n🛑 Cancelling {len(workflows)} workflows...\n")

    cancelled = 0
    failed = 0

    for wf in workflows:
        try:
            handle = client.get_workflow_handle(wf.id)
            await handle.cancel()
            print(f"   ✅ Cancelled: {wf.id}")
            cancelled += 1
        except Exception as e:
            print(f"   ❌ Failed to cancel {wf.id}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"✨ Summary:")
    print(f"   Cancelled: {cancelled}")
    print(f"   Failed: {failed}")
    print(f"   Total: {len(workflows)}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
