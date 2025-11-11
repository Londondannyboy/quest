import asyncio
import os
from temporalio.client import Client

async def check_workflow():
    client = await Client.connect(
        target_host="europe-west3.gcp.api.temporal.io:7233",
        namespace="quickstart-quest.zivkb",
        api_key=os.getenv("TEMPORAL_PROD_API_KEY")
    )
    
    # Get workflow handle
    handle = client.get_workflow_handle("campbell-lutyens-0")
    
    # Check if it's running
    try:
        result = await handle.describe()
        print(f"Workflow Status: {result.status}")
        print(f"Run ID: {result.run_id}")
        print(f"Start Time: {result.start_time}")
        
        # Try to get the result if completed
        if result.status.name == "COMPLETED":
            workflow_result = await handle.result()
            print(f"\nWorkflow Result: {workflow_result}")
        elif result.status.name == "RUNNING":
            print("\n⚠️ Workflow is still running...")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(check_workflow())
