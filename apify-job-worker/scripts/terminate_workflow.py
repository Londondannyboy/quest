#!/usr/bin/env python3
"""Terminate a specific workflow by ID."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from temporalio.client import Client

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings


async def terminate_workflow(workflow_id: str, reason: str = "Manually terminated"):
    """Terminate a workflow by ID."""

    load_dotenv(Path(__file__).parent.parent / ".env")
    settings = get_settings()

    print(f"Connecting to Temporal...")
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
        api_key=settings.temporal_api_key,
        tls=settings.temporal_tls,
    )
    print(f"✅ Connected")

    print(f"\nTerminating workflow: {workflow_id}")
    print(f"Reason: {reason}")

    handle = client.get_workflow_handle(workflow_id)
    await handle.terminate(reason)

    print(f"✅ Workflow terminated successfully")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python terminate_workflow.py <workflow_id> [reason]")
        sys.exit(1)

    workflow_id = sys.argv[1]
    reason = sys.argv[2] if len(sys.argv) > 2 else "Manually terminated"

    asyncio.run(terminate_workflow(workflow_id, reason))
