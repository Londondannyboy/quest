#!/usr/bin/env python3
"""List all available ZEP graphs"""

import asyncio
import os
from zep_cloud.client import AsyncZep
from dotenv import load_dotenv

load_dotenv()


async def list_graphs():
    """List all available graphs"""

    zep_api_key = os.getenv("ZEP_API_KEY")
    if not zep_api_key:
        print("❌ No ZEP_API_KEY found in environment")
        return

    print("📋 Listing available ZEP graphs...")
    print("="*60)

    zep = AsyncZep(api_key=zep_api_key)

    try:
        # List all graphs
        graphs = await zep.graph.list_graphs()

        if hasattr(graphs, 'graphs') and graphs.graphs:
            print(f"\nFound {len(graphs.graphs)} graphs:")
            for graph in graphs.graphs:
                print(f"\n  Graph ID: {graph.graph_id}")
                if hasattr(graph, 'name'):
                    print(f"  Name: {graph.name}")
                if hasattr(graph, 'description'):
                    print(f"  Description: {graph.description}")
                print("  " + "-"*56)
        else:
            print("\n No graphs found or different response structure")
            print(f" Response: {graphs}")

    except Exception as e:
        print(f"❌ Failed to list graphs: {e}")

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(list_graphs())
