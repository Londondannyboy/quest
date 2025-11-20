"""
Setup Temporal Schedules for News Monitoring

Creates daily schedules for each app to run NewsMonitorWorkflow.
"""

import asyncio
import os
from datetime import timedelta
from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec, ScheduleState
from dotenv import load_dotenv

load_dotenv()


async def create_news_monitor_schedule():
    """Create daily schedule for placement news monitoring."""

    # Connect to Temporal
    client = await Client.connect(
        os.getenv("TEMPORAL_ADDRESS"),
        namespace=os.getenv("TEMPORAL_NAMESPACE"),
        api_key=os.getenv("TEMPORAL_API_KEY"),
        tls=True,
    )

    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-company-queue")

    # Schedule ID
    schedule_id = "daily-placement-news-monitor"

    # Workflow input
    workflow_input = {
        "app": "placement",
        "min_relevance_score": 0.7,
        "auto_create_articles": True,
        "max_articles_to_create": 3
    }

    try:
        # Delete existing schedule if it exists
        try:
            handle = client.get_schedule_handle(schedule_id)
            await handle.delete()
            print(f"Deleted existing schedule: {schedule_id}")
        except Exception:
            pass  # Schedule doesn't exist

        # Create new schedule - runs every 24 hours
        await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    "NewsMonitorWorkflow",
                    workflow_input,
                    id=f"news-monitor-placement-scheduled",
                    task_queue=task_queue,
                ),
                spec=ScheduleSpec(
                    intervals=[
                        ScheduleIntervalSpec(
                            every=timedelta(hours=24),
                            offset=timedelta(hours=2)  # Start 2 hours from now
                        )
                    ]
                ),
                state=ScheduleState(
                    note="Daily placement news monitoring - creates up to 3 articles"
                )
            )
        )

        print(f"✅ Created schedule: {schedule_id}")
        print(f"   Runs every 24 hours")
        print(f"   First run in ~2 hours")
        print(f"   Task queue: {task_queue}")
        print(f"   Max articles: 3")

    except Exception as e:
        print(f"❌ Failed to create schedule: {e}")
        raise


async def main():
    print("=" * 60)
    print("Setting up Temporal Schedules")
    print("=" * 60)

    await create_news_monitor_schedule()

    print("\n✅ All schedules created!")
    print("   View in Temporal Cloud UI")


if __name__ == "__main__":
    asyncio.run(main())
