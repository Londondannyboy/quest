#!/usr/bin/env python3
"""Trigger First Avenue company workflow for testing."""
import asyncio
from temporalio.client import Client
import os

async def main():
    # Connect to Temporal Cloud
    client = await Client.connect(
        os.environ["TEMPORAL_ADDRESS"],
        namespace=os.environ["TEMPORAL_NAMESPACE"],
        api_key=os.environ["TEMPORAL_API_KEY"],
    )

    # Trigger workflow
    workflow_id = f"company-creation-firstavenue-test-2"

    handle = await client.start_workflow(
        "create_company_workflow",
        {
            "url": "https://www.firstavenue.com",
            "app": "placement",
            "category": "placement_agent",
            "force_update": True,  # Force regeneration
        },
        id=workflow_id,
        task_queue="company-worker-queue",
    )

    print(f"✅ Started workflow: {workflow_id}")
    print(f"   URL: https://cloud.temporal.io/namespaces/{os.environ['TEMPORAL_NAMESPACE']}/workflows/{workflow_id}")
    print(f"\n   Waiting for completion...")

    # Wait for result
    result = await handle.result()
    print(f"\n✅ Workflow completed!")
    print(f"   Status: {result.get('status')}")
    print(f"   Company ID: {result.get('company_id')}")

if __name__ == "__main__":
    asyncio.run(main())
