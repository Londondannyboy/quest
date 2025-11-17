#!/usr/bin/env python3
import asyncio
import os
import json
from temporalio.client import Client

async def main():
    client = await Client.connect(
        os.environ["TEMPORAL_ADDRESS"],
        namespace=os.environ["TEMPORAL_NAMESPACE"],
        api_key=os.environ["TEMPORAL_API_KEY"],
        tls=True
    )

    workflow_id = "first-avenue-0.381638083"
    
    try:
        handle = client.get_workflow_handle(workflow_id)
        result = await handle.result()
        print("🎉 Workflow Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
