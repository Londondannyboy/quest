#!/usr/bin/env python3
"""Check what Exa research found vs what was saved"""
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
    
    # Get workflow history to see activity results
    handle = client.get_workflow_handle(workflow_id)
    
    async for event in handle.fetch_history_events():
        # Look for activity completed events with "exa" or "research" in them
        if hasattr(event, 'activity_task_completed_event_attributes'):
            attrs = event.activity_task_completed_event_attributes
            if attrs and attrs.result:
                # Try to decode and print
                try:
                    import json
                    from temporalio.api.common.v1 import Payload
                    # This is simplified - real decoding is more complex
                    print(f"\n{'='*60}")
                    print(f"Activity Result (truncated)")
                    print(f"{'='*60}")
                    result_str = str(attrs.result)[:500]
                    print(result_str)
                except Exception as e:
                    pass

if __name__ == "__main__":
    asyncio.run(main())
