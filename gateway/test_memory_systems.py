#!/usr/bin/env python3
"""
Test script for ZEP + SuperMemory integration.

Run locally to test both memory systems:
    python test_memory_systems.py

Or test against deployed gateway:
    python test_memory_systems.py --url https://your-gateway.railway.app
"""

import asyncio
import os
import sys
import json
import httpx
from datetime import datetime

# Load env vars
from dotenv import load_dotenv
load_dotenv()


async def test_supermemory_direct():
    """Test SuperMemory API directly"""
    print("\n" + "="*60)
    print("SUPERMEMORY DIRECT TEST")
    print("="*60)

    api_key = os.getenv("SUPERMEMORY_API_KEY")
    if not api_key:
        print("SUPERMEMORY_API_KEY not set")
        return False

    base_url = "https://api.supermemory.ai/v3"
    test_user = f"test-user-{int(datetime.now().timestamp())}"

    async with httpx.AsyncClient() as client:
        # Test 1: Add a memory
        print(f"\n1. Adding memory for user: {test_user}")
        try:
            response = await client.post(
                f"{base_url}/documents",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "content": "User is interested in relocating to Cyprus. They have 2 kids and work remotely.",
                    "containerTag": f"user-{test_user}",
                    "metadata": {
                        "user_id": test_user,
                        "memory_type": "test",
                        "destination": "Cyprus",
                        "family": "with children"
                    }
                },
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
            print(f"   Added document: {result.get('id')}")
            print(f"   Status: {result.get('status')}")
        except Exception as e:
            print(f"   ERROR adding memory: {e}")
            return False

        # Wait for indexing
        print("\n2. Waiting 2s for indexing...")
        await asyncio.sleep(2)

        # Test 2: Search memories
        print(f"\n3. Searching memories for user: {test_user}")
        try:
            response = await client.get(
                f"{base_url}/search",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                params={
                    "q": "Cyprus relocation family",
                    "containerTag": f"user-{test_user}",
                    "limit": 5
                },
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
            memories = result.get("results", [])
            print(f"   Found {len(memories)} memories")
            for i, mem in enumerate(memories[:3]):
                content = mem.get("content", mem.get("text", ""))[:100]
                print(f"   [{i+1}] {content}...")
        except Exception as e:
            print(f"   ERROR searching: {e}")
            return False

    print("\nSuperMemory: OK")
    return True


async def test_zep_direct():
    """Test ZEP API directly"""
    print("\n" + "="*60)
    print("ZEP DIRECT TEST")
    print("="*60)

    api_key = os.getenv("ZEP_API_KEY")
    if not api_key:
        print("ZEP_API_KEY not set")
        return False

    graph_id = os.getenv("ZEP_GRAPH_ID", "relocation")

    try:
        from zep_cloud.client import Zep
        client = Zep(api_key=api_key)
        print(f"\n1. ZEP client initialized")
        print(f"   Graph ID: {graph_id}")

        # Test search
        print(f"\n2. Searching graph for 'Cyprus visa requirements'...")
        try:
            results = client.graph.search(
                graph_id=graph_id,
                query="Cyprus visa requirements",
                scope="edges",
                limit=5
            )

            edges = results.edges if hasattr(results, 'edges') else []
            print(f"   Found {len(edges)} edges (facts)")
            for i, edge in enumerate(edges[:3]):
                fact = getattr(edge, 'fact', str(edge))[:100]
                print(f"   [{i+1}] {fact}...")

        except Exception as e:
            print(f"   Search error: {e}")

        # Test node search
        print(f"\n3. Searching for nodes (entities)...")
        try:
            results = client.graph.search(
                graph_id=graph_id,
                query="Cyprus",
                scope="nodes",
                limit=5
            )

            nodes = results.nodes if hasattr(results, 'nodes') else []
            print(f"   Found {len(nodes)} nodes")
            for i, node in enumerate(nodes[:3]):
                name = getattr(node, 'name', 'unknown')
                print(f"   [{i+1}] {name}")

        except Exception as e:
            print(f"   Node search error: {e}")

        print("\nZEP: OK")
        return True

    except ImportError:
        print("zep-cloud package not installed")
        return False
    except Exception as e:
        print(f"ZEP error: {e}")
        return False


async def test_gateway_endpoints(base_url: str = "http://localhost:8000"):
    """Test gateway memory endpoints"""
    print("\n" + "="*60)
    print(f"GATEWAY ENDPOINT TESTS ({base_url})")
    print("="*60)

    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("\n1. Health check...")
        try:
            response = await client.get(f"{base_url}/voice/health", timeout=10.0)
            health = response.json()
            print(f"   ZEP: {health.get('zep', {})}")
            print(f"   SuperMemory: {health.get('supermemory', {})}")
            print(f"   Ready: {health.get('ready')}")
        except Exception as e:
            print(f"   ERROR: {e}")
            return False

        # Test 2: Memory debug endpoint
        test_user = "test-user-123"
        print(f"\n2. Memory debug for {test_user}...")
        try:
            response = await client.get(f"{base_url}/voice/memory/debug/{test_user}", timeout=10.0)
            debug = response.json()
            print(f"   ZEP enabled: {debug.get('zep', {}).get('enabled')}")
            print(f"   SuperMemory enabled: {debug.get('supermemory', {}).get('enabled')}")
            if debug.get('supermemory', {}).get('data'):
                print(f"   SuperMemory memories: {debug['supermemory']['data'].get('memory_count', 0)}")
        except Exception as e:
            print(f"   ERROR: {e}")

        # Test 3: Memory roundtrip test
        print("\n3. Memory roundtrip test...")
        try:
            response = await client.post(
                f"{base_url}/voice/memory/test",
                json={
                    "user_id": f"test-{int(datetime.now().timestamp())}",
                    "message": "I'm moving from London to Cyprus with my wife and 2 kids. I work remotely."
                },
                timeout=15.0
            )
            result = response.json()
            print(f"   Extracted: {result.get('extracted_info')}")
            print(f"   SuperMemory: {result.get('storage_results', {}).get('supermemory')}")
            print(f"   ZEP: {result.get('retrieval_test', {}).get('zep')}")
        except Exception as e:
            print(f"   ERROR: {e}")

    print("\nGateway: OK")
    return True


async def test_conversation_flow(base_url: str = "http://localhost:8000"):
    """Simulate a multi-turn conversation to test memory persistence"""
    print("\n" + "="*60)
    print("CONVERSATION FLOW TEST")
    print("="*60)

    test_user = f"conv-test-{int(datetime.now().timestamp())}"
    print(f"\nUser ID: {test_user}")

    messages = [
        "Hi, I'm thinking about relocating. I currently live in London.",
        "I'm interested in Cyprus. I have a wife and 2 kids.",
        "What's the cost of living like there?",
        "Tell me about visa requirements."  # Should remember Cyprus context
    ]

    async with httpx.AsyncClient() as client:
        for i, message in enumerate(messages):
            print(f"\n--- Turn {i+1} ---")
            print(f"User: {message}")

            try:
                response = await client.post(
                    f"{base_url}/voice/query",
                    params={"query": message, "user_id": test_user},
                    timeout=30.0
                )
                result = response.json()

                # Parse response for memory metadata
                response_text = result.get("response", "")

                # Check for memory metadata
                if "---MEMORY---" in response_text:
                    parts = response_text.split("---MEMORY---")
                    voice_response = parts[0].strip()
                    memory_json = parts[1].strip() if len(parts) > 1 else "{}"
                    try:
                        memory_meta = json.loads(memory_json)
                        print(f"Memory: SM={memory_meta.get('supermemory_used')}, "
                              f"ZEP_thread={memory_meta.get('zep_thread_used')}, "
                              f"ZEP_kg={memory_meta.get('zep_knowledge_used')}")
                    except:
                        pass
                    print(f"Assistant: {voice_response[:200]}...")
                else:
                    print(f"Assistant: {response_text[:200]}...")

            except Exception as e:
                print(f"ERROR: {e}")

            # Small delay between turns
            await asyncio.sleep(1)

        # Final: Check what was stored
        print(f"\n--- Checking stored memories for {test_user} ---")
        try:
            response = await client.get(f"{base_url}/voice/memory/debug/{test_user}", timeout=10.0)
            debug = response.json()
            sm_data = debug.get('supermemory', {}).get('data', {})
            print(f"SuperMemory memories stored: {sm_data.get('memory_count', 0)}")
            if sm_data.get('memories'):
                for mem in sm_data['memories'][:3]:
                    print(f"  - {mem.get('content', '')[:80]}...")
        except Exception as e:
            print(f"ERROR checking memories: {e}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test ZEP + SuperMemory integration")
    parser.add_argument("--url", default="http://localhost:8000", help="Gateway base URL")
    parser.add_argument("--direct-only", action="store_true", help="Only test direct API calls")
    parser.add_argument("--gateway-only", action="store_true", help="Only test gateway endpoints")
    parser.add_argument("--conversation", action="store_true", help="Run conversation flow test")
    args = parser.parse_args()

    print("="*60)
    print("QUEST MEMORY SYSTEMS TEST")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*60)

    if args.conversation:
        await test_conversation_flow(args.url)
        return

    if not args.gateway_only:
        await test_supermemory_direct()
        await test_zep_direct()

    if not args.direct_only:
        await test_gateway_endpoints(args.url)

    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
