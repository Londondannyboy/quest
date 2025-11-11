"""
Create Temporal Schedule for Chief of Staff Daily Workflow

Run this script once to create the daily schedule.
"""

import asyncio
import os
from datetime import timedelta
from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec
from temporalio.common import SearchAttributeKey
from dotenv import load_dotenv

load_dotenv()


async def create_schedule():
    """Create the Chief of Staff daily schedule"""

    # Get Temporal configuration
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")

    print("🔧 Creating Chief of Staff Daily Schedule")
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

    # Define the schedule
    schedule_id = "chief-of-staff-daily"

    # Workflow arguments
    search_topic = "chief of staff OR new chief of staff OR appointed chief of staff"
    target_word_count = 1500
    auto_approve = True
    skip_zep_check = True

    print(f"📅 Creating schedule: {schedule_id}")
    print(f"   Search topic: {search_topic}")
    print(f"   Schedule: Daily at 10 PM GMT (22:00 UTC)")
    print(f"   Workflow: ChiefOfStaffWorkflow")
    print()

    try:
        # Create the schedule
        await client.create_schedule(
            id=schedule_id,
            schedule=Schedule(
                action=ScheduleActionStartWorkflow(
                    workflow="ChiefOfStaffWorkflow",
                    args=[search_topic, target_word_count, auto_approve, skip_zep_check],
                    id=f"article-chief-of-staff-scheduled-{{{{.ScheduledTime.Unix}}}}",
                    task_queue="quest-content-queue",
                ),
                spec=ScheduleSpec(
                    # Run daily at 10 PM GMT (22:00 UTC)
                    cron_expressions=["0 22 * * *"],
                ),
            ),
        )

        print("=" * 60)
        print("🎉 SUCCESS! Schedule created!")
        print("=" * 60)
        print(f"Schedule ID: {schedule_id}")
        print(f"Next execution: Daily at 10:00 PM GMT")
        print()
        print("To view the schedule:")
        print(f"  Temporal Cloud UI → Schedules → {schedule_id}")
        print()
        print("To pause the schedule:")
        print(f"  temporal schedule toggle --schedule-id {schedule_id} --pause")
        print()
        print("To delete the schedule:")
        print(f"  temporal schedule delete --schedule-id {schedule_id}")
        print("=" * 60)

    except Exception as e:
        if "already exists" in str(e).lower():
            print("⚠️  Schedule already exists!")
            print(f"   Schedule ID: {schedule_id}")
            print()
            print("To update the existing schedule, first delete it:")
            print(f"  temporal schedule delete --schedule-id {schedule_id}")
            print()
            print("Then run this script again.")
        else:
            print(f"❌ Failed to create schedule: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(create_schedule())
