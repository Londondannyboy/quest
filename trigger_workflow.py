#!/usr/bin/env python3
"""Trigger First Avenue workflow via Temporal Cloud API"""
import asyncio
import os
from temporalio.client import Client

async def main():
    # Connect to Temporal Cloud
    from temporalio.client import TLSConfig

    client = await Client.connect(
        os.environ["TEMPORAL_ADDRESS"],
        namespace=os.environ["TEMPORAL_NAMESPACE"],
        api_key=os.environ["TEMPORAL_API_KEY"],
        tls=True
    )

    # Trigger workflow
    workflow_input = {
        "url": "https://www.firstavenue.com/",
        "category": "placement",
        "app": "placement",
        "jurisdiction": "US",
        "force_update": False
    }

    print("🏢 Triggering First Avenue workflow...")
    print(f"   Input: {workflow_input}")

    handle = await client.start_workflow(
        "CompanyCreationWorkflow",
        workflow_input,
        id=f"first-avenue-{asyncio.get_event_loop().time()}",
        task_queue="quest-company-queue"
    )

    print(f"✅ Workflow started!")
    print(f"   Workflow ID: {handle.id}")
    print(f"   Run ID: {handle.result_run_id}")
    print(f"\n📊 Monitor at: https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows/{handle.id}")

if __name__ == "__main__":
    asyncio.run(main())
