#!/usr/bin/env python3
"""Check workflow execution details"""
import asyncio
import os
from temporalio.client import Client

async def main():
    client = await Client.connect(
        os.environ["TEMPORAL_ADDRESS"],
        namespace=os.environ["TEMPORAL_NAMESPACE"],
        api_key=os.environ["TEMPORAL_API_KEY"],
        tls=True
    )

    workflow_id = "first-avenue-0.351911208"

    try:
        handle = client.get_workflow_handle(workflow_id)
        result = await handle.result()
        print("🎉 Workflow Result:")
        print(result)
    except Exception as e:
        print(f"❌ Error: {e}")

        # Try to get workflow history
        print("\n📋 Attempting to describe workflow...")
        desc = await handle.describe()
        print(f"Status: {desc.status}")
        print(f"Run ID: {desc.run_id}")

if __name__ == "__main__":
    asyncio.run(main())
