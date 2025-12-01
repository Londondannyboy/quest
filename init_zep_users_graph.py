#!/usr/bin/env python3
"""
Initialize ZEP Users Graph

Run this script to create the "users" graph in ZEP for storing user profile facts.

Usage:
    python init_zep_users_graph.py
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ZEP_API_KEY = os.getenv("ZEP_API_KEY")

if not ZEP_API_KEY:
    print("ERROR: ZEP_API_KEY not set")
    print("Please ensure ZEP_API_KEY is in your .env file")
    exit(1)


async def main():
    from zep_cloud.client import AsyncZep

    client = AsyncZep(api_key=ZEP_API_KEY)

    print("=" * 60)
    print("ZEP Users Graph Initialization")
    print("=" * 60)

    # 1. Create the users graph
    print("\n1. Creating 'users' graph...")
    try:
        graph = await client.graph.create(
            graph_id="users",
            name="User Profiles",
            description="Knowledge graph of user relocation profiles, facts, and preferences across all Quest apps"
        )
        print(f"   Created graph: {graph}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("   Graph 'users' already exists - OK")
        else:
            print(f"   Warning: {e}")

    # 2. List all graphs to confirm
    print("\n2. Listing all graphs...")
    try:
        graphs_response = await client.graph.list_all(page_size=100)
        if hasattr(graphs_response, 'graphs') and graphs_response.graphs:
            print(f"   Found {len(graphs_response.graphs)} graphs:")
            for g in graphs_response.graphs:
                name = g.name if hasattr(g, 'name') else g
                print(f"   - {name}")
        else:
            print(f"   Response: {graphs_response}")
    except Exception as e:
        print(f"   Error listing graphs: {e}")

    # 3. Test adding sample user data
    print("\n3. Adding test user data...")
    try:
        import json

        test_user_data = {
            "user_id": "test_user_123",
            "app_id": "relocation",
            "entity": {
                "type": "User",
                "id": "test_user_123",
                "current_location": "London, UK",
                "destinations": ["Portugal", "Spain"],
                "profession": "Software Engineer",
                "remote_work": True,
                "budget": 3000,
                "timeline": "6-12months"
            },
            "summary": (
                "User test_user_123 from relocation application. "
                "Currently located in London, UK. "
                "Interested in relocating to: Portugal, Spain. "
                "Works as Software Engineer. "
                "Has remote work capability. "
                "Monthly budget: $3000. "
                "Timeline: 6-12 months."
            ),
            "entity_type": "user_profile"
        }

        response = await client.graph.add(
            graph_id="users",
            type="json",
            data=json.dumps(test_user_data)
        )
        print(f"   Added test data: {response}")

    except Exception as e:
        print(f"   Error adding test data: {e}")

    # 4. Search for the test user
    print("\n4. Searching for test user data...")
    try:
        results = await client.graph.search(
            graph_id="users",
            query="test_user_123 Portugal",
            scope="edges",
            limit=10
        )

        if hasattr(results, 'edges') and results.edges:
            print(f"   Found {len(results.edges)} facts:")
            for edge in results.edges[:5]:
                fact = edge.fact if hasattr(edge, 'fact') else str(edge)
                print(f"   - {fact[:100]}...")
        else:
            print("   No results yet (graph may need time to index)")

    except Exception as e:
        print(f"   Error searching: {e}")

    print("\n" + "=" * 60)
    print("Initialization complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
