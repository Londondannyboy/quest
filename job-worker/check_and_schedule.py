#!/usr/bin/env python3
"""
Check recent workflow runs and create daily schedule for 10am UK time
"""

import asyncio
import os
from datetime import datetime, timedelta
from temporalio.client import Client, TLSConfig, Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec
from dotenv import load_dotenv

load_dotenv()


async def check_recent_runs():
    """Check when the last job scraping workflow ran"""

    print("🔍 Checking Recent Temporal Workflows")
    print("="*60)

    temporal_host = os.getenv("TEMPORAL_HOST", "europe-west3.gcp.api.temporal.io:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "quickstart-quest.zivkb")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")

    if not temporal_api_key:
        print("❌ No TEMPORAL_API_KEY found")
        return

    try:
        client = await Client.connect(
            temporal_host,
            namespace=temporal_namespace,
            tls=TLSConfig(),
            rpc_metadata={"temporal-namespace": temporal_namespace},
            api_key=temporal_api_key,
        )

        print(f"✅ Connected to Temporal")
        print(f"   Namespace: {temporal_namespace}\n")

        # List recent workflows
        print("📋 Recent Greenhouse scraper workflows:")
        print("-"*60)

        async for workflow in client.list_workflows('WorkflowType="GreenhouseScraperWorkflow"'):
            start_time = workflow.start_time
            status = workflow.status.name
            workflow_id = workflow.id

            # Calculate time ago
            now = datetime.now(start_time.tzinfo)
            time_ago = now - start_time

            if time_ago < timedelta(hours=1):
                time_str = f"{int(time_ago.total_seconds() / 60)} minutes ago"
            elif time_ago < timedelta(days=1):
                time_str = f"{int(time_ago.total_seconds() / 3600)} hours ago"
            else:
                time_str = f"{int(time_ago.days)} days ago"

            print(f"  {workflow_id}")
            print(f"    Status: {status}")
            print(f"    Started: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')} ({time_str})")
            print()

            # Only show first 5
            if workflow.id.split('-')[0] == workflow_id.split('-')[0]:
                count = 1
                if count >= 5:
                    break

        return client

    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None


async def create_daily_schedule(client):
    """Create a schedule to run job scraping daily at 10am UK time"""

    print("\n📅 Creating Daily Schedule")
    print("="*60)

    schedule_id = "daily-job-scrape-10am-uk"

    try:
        # Check if schedule already exists
        try:
            handle = client.get_schedule_handle(schedule_id)
            desc = await handle.describe()
            print(f"⚠️  Schedule already exists: {schedule_id}")
            print(f"   Next run: {desc.info.next_action_times[0] if desc.info.next_action_times else 'Unknown'}")

            response = input("\n   Update existing schedule? (y/n): ")
            if response.lower() != 'y':
                print("   Keeping existing schedule")
                return

            # Delete old schedule
            await handle.delete()
            print("   Deleted old schedule")

        except Exception:
            # Schedule doesn't exist, that's fine
            pass

        # Create schedule for 10am UK time daily
        # UK is UTC in winter, UTC+1 in summer (BST)
        # For simplicity, schedule at 10am UTC which is 10am UK winter / 11am UK summer
        # Or schedule at 9am UTC which is 9am UK winter / 10am UK summer

        print(f"\n   Creating schedule: {schedule_id}")
        print(f"   Frequency: Daily at 10:00 UTC (10am UK winter time)")
        print(f"   Workflow: GreenhouseScraperWorkflow")
        print(f"   Task Queue: fractional-jobs-queue")

        # List of companies to scrape (add your actual companies here)
        companies_to_scrape = [
            {
                "name": "Example1",
                "board_url": "https://boards.greenhouse.io/example1",
                "board_type": "greenhouse"
            },
            {
                "name": "Example2",
                "board_url": "https://boards.greenhouse.io/example2",
                "board_type": "greenhouse"
            }
        ]

        # For now, just schedule one company as a test
        test_company = companies_to_scrape[0]

        schedule = await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    "GreenhouseScraperWorkflow",
                    test_company,
                    id=f"scheduled-{test_company['name']}-{{.timestamp}}",
                    task_queue="fractional-jobs-queue",
                ),
                spec=ScheduleSpec(
                    # Run daily at 10:00 UTC
                    cron_expressions=["0 10 * * *"],
                ),
            ),
        )

        print(f"\n✅ Schedule created successfully!")
        print(f"   Schedule ID: {schedule_id}")
        print(f"   Next run: Check Temporal UI for next execution time")

        # Get schedule details
        handle = client.get_schedule_handle(schedule_id)
        desc = await handle.describe()

        if desc.info.next_action_times:
            next_run = desc.info.next_action_times[0]
            print(f"   Next scheduled run: {next_run}")

        print("\n💡 To scrape multiple companies:")
        print("   1. Create separate schedules for each company, or")
        print("   2. Use a master workflow that fans out to multiple companies")

    except Exception as e:
        print(f"❌ Failed to create schedule: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function"""

    # Check recent runs
    client = await check_recent_runs()

    if client:
        # Create schedule
        await create_daily_schedule(client)

    print("\n" + "="*60)
    print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
