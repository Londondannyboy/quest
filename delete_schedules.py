#!/usr/bin/env python3
"""Delete all Temporal Schedules (not just workflow executions)."""
import asyncio
from temporalio.client import Client
import os

async def main():
    print("🔌 Connecting to Temporal Cloud...")
    client = await Client.connect(
        os.environ["TEMPORAL_ADDRESS"],
        namespace=os.environ["TEMPORAL_NAMESPACE"],
        api_key=os.environ["TEMPORAL_API_KEY"],
    )
    print("   ✅ Connected!\n")

    print("📋 Listing all schedules...")

    schedules = []
    async for schedule in client.list_schedules():
        schedules.append(schedule)

    if not schedules:
        print("   ✅ No schedules found!")
        return

    print(f"   Found {len(schedules)} schedules\n")

    # Show schedules
    print("=" * 60)
    for i, sched in enumerate(schedules, 1):
        print(f"{i}. Schedule ID: {sched.id}")
        print(f"   Workflow Type: {sched.workflow_type}")
        if hasattr(sched, 'spec') and sched.spec:
            print(f"   Spec: {sched.spec}")
        print()

    print("=" * 60)
    print(f"\n❗ WARNING: This will PERMANENTLY DELETE all {len(schedules)} schedules!")
    print("   They will NOT restart or create new workflows.\n")

    confirm = input(f"Delete ALL {len(schedules)} schedules? (type 'DELETE' to confirm): ")

    if confirm != "DELETE":
        print("❌ Cancelled - no schedules deleted")
        return

    print(f"\n🗑️  Deleting {len(schedules)} schedules...\n")

    deleted = 0
    failed = 0

    for sched in schedules:
        try:
            handle = client.get_schedule_handle(sched.id)
            await handle.delete()
            print(f"   ✅ Deleted: {sched.id}")
            deleted += 1
        except Exception as e:
            print(f"   ❌ Failed to delete {sched.id}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"✨ Summary:")
    print(f"   Deleted: {deleted}")
    print(f"   Failed: {failed}")
    print(f"   Total: {len(schedules)}")
    print("=" * 60)
    print("\n✅ Schedules permanently deleted - no more auto-spawning workflows!")

if __name__ == "__main__":
    asyncio.run(main())
