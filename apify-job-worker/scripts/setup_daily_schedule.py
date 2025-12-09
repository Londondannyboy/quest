#!/usr/bin/env python3
"""
Set up daily schedule for LinkedIn Apify job scraping at 10am UK time
"""

import asyncio
import os
from datetime import timedelta
from temporalio.client import Client, TLSConfig, Schedule, ScheduleActionStartWorkflow, ScheduleSpec
from dotenv import load_dotenv

load_dotenv()


async def create_daily_schedule():
    """Create schedule for LinkedIn job scraping at 10am UK time"""

    print("🚀 Setting up Daily LinkedIn Job Scraping Schedule")
    print("="*60)

    temporal_host = os.getenv("TEMPORAL_HOST", "europe-west3.gcp.api.temporal.io:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "quickstart-quest.zivkb")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")

    if not temporal_api_key:
        print("❌ No TEMPORAL_API_KEY found in .env")
        return

    print(f"✅ Connecting to Temporal Cloud")
    print(f"   Host: {temporal_host}")
    print(f"   Namespace: {temporal_namespace}\n")

    try:
        client = await Client.connect(
            temporal_host,
            namespace=temporal_namespace,
            tls=TLSConfig(),
            rpc_metadata={"temporal-namespace": temporal_namespace},
            api_key=temporal_api_key,
        )

        print("✅ Connected to Temporal\n")

        schedule_id = "daily-linkedin-apify-10am-uk"

        # Check if schedule exists
        try:
            handle = client.get_schedule_handle(schedule_id)
            desc = await handle.describe()
            print(f"⚠️  Schedule already exists: {schedule_id}")
            print(f"   Current next run: {desc.info.next_action_times[0] if desc.info.next_action_times else 'Unknown'}\n")
            # Auto-delete and recreate
            await handle.delete()
            print("   Deleted old schedule\n")
        except:
            # Schedule doesn't exist, that's fine
            pass

        # Default scraping config
        scrape_config = {
            "location": "United Kingdom",
            "keywords": "fractional OR part-time OR contract OR interim",
            "jobs_entries": 10,
            "job_post_time": "r86400"
        }

        print(f"📅 Creating schedule: {schedule_id}")
        print(f"   Frequency: Daily at 10:00 UTC (10am UK winter time)")
        print(f"   Workflow: LinkedInApifyScraperWorkflow")
        print(f"   Task Queue: apify-linkedin-queue")

        await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    "LinkedInApifyScraperWorkflow",
                    scrape_config,
                    id=f"linkedin-daily-{{.timestamp}}",
                    task_queue="apify-linkedin-queue",
                    execution_timeout=timedelta(minutes=30),
                ),
                spec=ScheduleSpec(
                    cron_expressions=["0 10 * * *"],
                ),
            ),
        )

        print(f"✅ Schedule created successfully!\n")

        handle = client.get_schedule_handle(schedule_id)
        desc = await handle.describe()

        if desc.info.next_action_times:
            next_run = desc.info.next_action_times[0]
            print(f"   Next run: {next_run}")

    except Exception as e:
        print(f"❌ Failed: {e}")


if __name__ == "__main__":
    asyncio.run(create_daily_schedule())
