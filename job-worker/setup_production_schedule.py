#!/usr/bin/env python3
"""
Set up production schedule with actual companies from database
"""

import asyncio
import asyncpg
import os
from datetime import timedelta
from temporalio.client import Client, TLSConfig, Schedule, ScheduleActionStartWorkflow, ScheduleSpec
from dotenv import load_dotenv

load_dotenv()


async def get_active_companies():
    """Get list of active companies to scrape from database"""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ No DATABASE_URL found")
        return []

    print("🔍 Fetching active companies from database...")

    try:
        conn = await asyncpg.connect(database_url)

        # Get active job boards
        rows = await conn.fetch("""
            SELECT company_name, url, board_type
            FROM job_boards
            WHERE is_active = true
            ORDER BY company_name
        """)

        companies = []
        for row in rows:
            companies.append({
                "name": row["company_name"],
                "board_url": row["url"],
                "board_type": row["board_type"]
            })

        await conn.close()

        print(f"✅ Found {len(companies)} active companies:")
        for i, company in enumerate(companies[:10], 1):
            print(f"   {i}. {company['name']} ({company['board_type']})")
        if len(companies) > 10:
            print(f"   ... and {len(companies) - 10} more")

        return companies

    except Exception as e:
        print(f"❌ Failed to get companies: {e}")
        return []


async def create_schedule_for_companies(companies):
    """Create or update schedule for all companies"""

    print(f"\n📅 Setting up schedule for {len(companies)} companies")
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

        print(f"✅ Connected to Temporal\n")

        # Strategy: Create one schedule that triggers a master workflow
        # The master workflow will fan out to scrape all companies
        schedule_id = "daily-all-companies-10am-uk"

        # Check if schedule exists
        try:
            handle = client.get_schedule_handle(schedule_id)
            await handle.describe()
            print(f"⚠️  Schedule exists: {schedule_id}")

            # Delete and recreate
            await handle.delete()
            print(f"   Deleted old schedule\n")
        except:
            pass

        # Create schedule that triggers master workflow
        print(f"   Creating schedule: {schedule_id}")
        print(f"   Time: Daily at 10:00 UTC (10am UK winter time)")
        print(f"   Workflow: MasterScraperWorkflow")
        print(f"   Companies: {len(companies)}")

        await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    "MasterScraperWorkflow",
                    {
                        "max_concurrent": 3,  # Scrape 3 companies at a time
                        "companies": companies
                    },
                    id=f"daily-scrape-{{.timestamp}}",
                    task_queue="fractional-jobs-queue",
                    execution_timeout=timedelta(hours=2),  # Give it time for all companies
                ),
                spec=ScheduleSpec(
                    # Run daily at 10:00 UTC
                    cron_expressions=["0 10 * * *"],
                ),
            ),
        )

        print(f"\n✅ Production schedule created!")
        print(f"   Schedule ID: {schedule_id}")

        # Get next run time
        handle = client.get_schedule_handle(schedule_id)
        desc = await handle.describe()

        if desc.info.next_action_times:
            next_run = desc.info.next_action_times[0]
            print(f"   Next run: {next_run}")

        print(f"\n📊 What will happen at 10am UK time daily:")
        print(f"   1. MasterScraperWorkflow starts")
        print(f"   2. Scrapes {len(companies)} companies (3 at a time)")
        print(f"   3. For each company:")
        print(f"      - Scrape jobs from board")
        print(f"      - Classify with Gemini")
        print(f"      - Save to Neon DB")
        print(f"      - Save to ZEP graph ✨")
        print(f"   4. Returns summary of all results")

    except Exception as e:
        print(f"❌ Failed to create schedule: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function"""

    print("🚀 Production Schedule Setup")
    print("="*60)

    # Get companies from database
    companies = await get_active_companies()

    if not companies:
        print("\n⚠️  No companies found in database")
        print("   Add companies to job_boards table first")
        return

    # Create schedule
    await create_schedule_for_companies(companies)

    print("\n" + "="*60)
    print("✅ Production schedule ready!")
    print("\n💡 To test immediately:")
    print("   - Trigger the schedule manually in Temporal UI, or")
    print("   - Wait until tomorrow 10am UK time")


if __name__ == "__main__":
    asyncio.run(main())
