"""
Setup Temporal Schedules for News Creation

Creates daily schedules for each app to run NewsCreationWorkflow.
Each app gets its own schedule with app-specific configuration.
"""

import asyncio
import os
from datetime import timedelta, datetime
from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec, ScheduleState
from dotenv import load_dotenv

load_dotenv()

# App configurations for scheduling
APP_CONFIGS = {
    "placement": {
        "min_relevance_score": 0.7,
        "max_articles_to_create": 3,
        "note": "Daily news articles for placement agents - creates up to 3 articles"
    },
    "relocation": {
        "min_relevance_score": 0.7,
        "max_articles_to_create": 3,
        "note": "Daily news articles for relocation - creates up to 3 articles"
    }
}


async def create_news_creation_schedule(app: str, config: dict):
    """Create daily schedule for news creation workflow for a specific app."""

    # Connect to Temporal
    client = await Client.connect(
        os.getenv("TEMPORAL_ADDRESS"),
        namespace=os.getenv("TEMPORAL_NAMESPACE"),
        api_key=os.getenv("TEMPORAL_API_KEY"),
        tls=True,
    )

    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    # Schedule ID - includes technique (4act) for clarity
    schedule_id = f"{app}-4act-news-daily"

    # Workflow input - with intelligent video prompts
    workflow_input = {
        "app": app,
        "min_relevance_score": config["min_relevance_score"],
        "auto_create_articles": True,
        "max_articles_to_create": config["max_articles_to_create"]
    }

    try:
        # Delete existing schedule if it exists (check both old and new naming)
        for old_id in [schedule_id, f"daily-{app}-news-creation"]:
            try:
                handle = client.get_schedule_handle(old_id)
                await handle.delete()
                print(f"Deleted existing schedule: {old_id}")
            except Exception:
                pass  # Schedule doesn't exist

        # Create new schedule - runs every 24 hours
        # Workflow ID includes date for easy identification
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

        await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    "NewsCreationWorkflow",
                    workflow_input,
                    id=f"4act-news-{app}-{date_str}",
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
                    note=config["note"]
                )
            )
        )

        print(f"✅ Created schedule: {schedule_id}")
        print(f"   App: {app}")
        print(f"   Technique: 4-act video workflow")
        print(f"   Parent workflow ID pattern: 4act-news-{app}-YYYY-MM-DD")
        print(f"   Child workflow ID pattern: 4act-{app}-<topic-slug>-<uuid>")
        print(f"   Runs every 24 hours")
        print(f"   Task queue: {task_queue}")
        print(f"   Max articles: {config['max_articles_to_create']}")

    except Exception as e:
        print(f"❌ Failed to create schedule for {app}: {e}")
        raise


async def main():
    print("=" * 70)
    print("Setting up Temporal Schedules for News Creation")
    print("=" * 70)

    # Create schedules for all apps
    for app, config in APP_CONFIGS.items():
        print(f"\n📅 Setting up schedule for {app}...")
        await create_news_creation_schedule(app, config)

    print("\n" + "=" * 70)
    print("✅ All schedules created!")
    print("   View in Temporal Cloud UI")
    print("   Workflows will run daily with intelligent video prompts")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
