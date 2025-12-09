#!/usr/bin/env python3
"""Test ZEP API connection and graph access."""

import asyncio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

async def test_zep():
    """Test ZEP API connection."""
    zep_api_key = os.getenv("ZEP_API_KEY")
    zep_base_url = os.getenv("ZEP_BASE_URL", "https://api.getzep.com")
    graph_id = os.getenv("ZEP_GRAPH_ID", "jobs-tech")

    print(f"ZEP Base URL: {zep_base_url}")
    print(f"Graph ID: {graph_id}")
    print(f"API Key: {zep_api_key[:20]}..." if zep_api_key else "Not set")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test 1: List graphs
        print("\n1. Testing GET /v2/graphs")
        try:
            response = await client.get(
                f"{zep_base_url}/v2/graphs",
                headers={"Authorization": f"Bearer {zep_api_key}"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 2: Check specific graph
        print(f"\n2. Testing GET /v2/graphs/{graph_id}")
        try:
            response = await client.get(
                f"{zep_base_url}/v2/graphs/{graph_id}",
                headers={"Authorization": f"Bearer {zep_api_key}"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 3: Try creating an episode
        print(f"\n3. Testing POST /v2/graphs/{graph_id}/episodes")
        try:
            response = await client.post(
                f"{zep_base_url}/v2/graphs/{graph_id}/episodes",
                headers={
                    "Authorization": f"Bearer {zep_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "type": "test",
                    "content": "Test episode",
                    "entities": [
                        {
                            "uuid": "test-1",
                            "name": "Test Entity",
                            "entity_type": "Test"
                        }
                    ]
                }
            )
            print(f"Status: {response.status_code}")
            if response.status_code in [200, 201]:
                print(f"✅ Success: {response.json()}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_zep())
