"""
Test Zep Context Flow in Article Creation

This test verifies that:
1. Zep graph context is properly queried with the correct graph_id for the app
2. Edge data (facts/relationships) is extracted, not just entity names
3. Zep context is actually used in the article generation prompt

Run: python test_zep_context_flow.py
"""

import asyncio
import os
import json
from zep_cloud.client import AsyncZep

# Load from environment or use test key
ZEP_API_KEY = os.getenv("ZEP_API_KEY", "z_1dWlkIjoiMmNkYWVjZjktYTU5Ny00ZDlkLWIyMWItNTZjOWI5OTE5MTE4In0.Ssyb_PezcGgacQFq6Slg3fyFoqs8hBhvp6WsE8rO4VK_D70CT5tqDbFOs6ZTf8rw7qYfTRhLz5YFm8RR854rHg")


def get_graph_id_for_app(app: str) -> str:
    """Map app type to Zep graph ID (same logic as zep_integration.py)."""
    finance_graph = os.getenv("ZEP_GRAPH_ID_FINANCE", "finance-knowledge")
    relocation_graph = os.getenv("ZEP_GRAPH_ID_RELOCATION", "relocation")
    jobs_graph = os.getenv("ZEP_GRAPH_ID_JOBS", "jobs")

    graph_mapping = {
        "placement": finance_graph,
        "pe_news": finance_graph,
        "relocation": relocation_graph,
        "jobs": jobs_graph,
        "recruiter": jobs_graph,
    }
    return graph_mapping.get(app, finance_graph)


async def test_zep_edge_extraction():
    """Test that we're properly extracting EDGE data (facts), not just entities."""
    print("=" * 60)
    print("TEST 1: Zep Edge Data Extraction (scope=edges)")
    print("=" * 60)

    client = AsyncZep(api_key=ZEP_API_KEY)

    # Test with a known company in the finance graph
    test_query = "Evercore"
    graph_id = get_graph_id_for_app("placement")

    print(f"\nQuerying graph '{graph_id}' for: {test_query}")
    print("Using: scope='edges', reranker='cross_encoder'")

    # Search edges with scope="edges" - the correct way per Zep docs
    try:
        results = await client.graph.search(
            graph_id=graph_id,
            query=test_query,
            scope="edges",  # This is the key! Returns facts
            reranker="cross_encoder",  # Best relevance ranking
            limit=20
        )

        print(f"\nResults type: {type(results)}")
        print(f"Has edges: {hasattr(results, 'edges')}")
        print(f"Has nodes: {hasattr(results, 'nodes')}")

        # Check edges (relationships/facts)
        if hasattr(results, 'edges') and results.edges:
            print(f"\n✅ Found {len(results.edges)} EDGES (facts/relationships)")
            print("\n--- EDGE DATA (This is what we should use for context) ---")

            for i, edge in enumerate(results.edges[:5]):
                print(f"\nEdge {i+1}:")
                print(f"  - Name: {getattr(edge, 'name', 'N/A')}")
                print(f"  - Fact: {getattr(edge, 'fact', 'N/A')[:200]}..." if getattr(edge, 'fact', '') else "  - Fact: N/A")
                print(f"  - Source UUID: {getattr(edge, 'source_node_uuid', 'N/A')}")
                print(f"  - Target UUID: {getattr(edge, 'target_node_uuid', 'N/A')}")

                # This is the VALUABLE data that should go into article context
                fact = getattr(edge, 'fact', '')
                if fact:
                    print(f"  ⭐ VALUABLE FACT: {fact[:300]}")
        else:
            print("\n❌ No edges found - this is a problem!")

        # Check nodes (entities)
        if hasattr(results, 'nodes') and results.nodes:
            print(f"\n📦 Found {len(results.nodes)} NODES (entities)")
            for i, node in enumerate(results.nodes[:3]):
                print(f"  Node {i+1}: {getattr(node, 'name', 'N/A')} (type: {getattr(node, 'type', 'N/A')})")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_graph_id_mapping():
    """Test that different apps map to correct graph IDs."""
    print("\n" + "=" * 60)
    print("TEST 2: Graph ID Mapping")
    print("=" * 60)

    test_cases = [
        ("placement", "finance-knowledge"),
        ("pe_news", "finance-knowledge"),
        ("relocation", "relocation"),
        ("jobs", "jobs"),
        ("recruiter", "jobs"),
        ("unknown_app", "finance-knowledge"),  # Default fallback
    ]

    all_passed = True
    for app, expected in test_cases:
        actual = get_graph_id_for_app(app)
        status = "✅" if actual == expected else "❌"
        if actual != expected:
            all_passed = False
        print(f"  {status} App '{app}' -> graph '{actual}' (expected: '{expected}')")

    if all_passed:
        print("\n✅ All graph mappings correct")
    else:
        print("\n❌ Some graph mappings failed!")


async def test_context_used_in_prompt():
    """
    Test that verifies whether zep_context would be included in the article prompt.

    This is a code analysis test - it checks if build_prompt() handles zep_context.
    """
    print("\n" + "=" * 60)
    print("TEST 3: Zep Context Usage in Article Prompt")
    print("=" * 60)

    # Read the article_generation.py file and check if zep_context is processed
    try:
        with open("src/activities/generation/article_generation.py", "r") as f:
            content = f.read()

        # Check if build_prompt handles zep_context
        if "zep_context" in content:
            # Find the build_prompt function
            if 'def build_prompt' in content:
                # Extract the function
                start = content.find('def build_prompt')
                end = content.find('\ndef ', start + 1)
                if end == -1:
                    end = len(content)
                build_prompt_code = content[start:end]

                if 'zep_context' in build_prompt_code:
                    print("✅ build_prompt() DOES reference zep_context")

                    # Check if it actually adds to parts
                    if 'parts.append' in build_prompt_code and 'zep' in build_prompt_code.lower():
                        print("✅ zep_context is added to prompt parts")
                    else:
                        print("❌ zep_context is referenced but NOT added to prompt parts!")
                        print("\n⚠️  THIS IS THE BUG: Zep context is collected but never used!")
                else:
                    print("❌ build_prompt() does NOT use zep_context!")
                    print("\n⚠️  THIS IS THE BUG: Zep context is collected but never used in the prompt!")
            else:
                print("❌ Could not find build_prompt function")
        else:
            print("❌ No reference to zep_context in article_generation.py")

    except FileNotFoundError:
        print("⚠️  Could not read article_generation.py (run from content-worker directory)")


async def test_full_context_extraction():
    """
    Full integration test: Query Zep and show what context SHOULD be passed to article generation.
    """
    print("\n" + "=" * 60)
    print("TEST 4: Full Context Extraction (What Should Be Passed)")
    print("=" * 60)

    client = AsyncZep(api_key=ZEP_API_KEY)

    # Test with a topic that should have Zep context
    test_topic = "Evercore investment banking"
    app = "placement"
    graph_id = get_graph_id_for_app(app)

    print(f"\nTopic: {test_topic}")
    print(f"App: {app}")
    print(f"Graph ID: {graph_id}")

    try:
        # Search edges (facts) - this is what query_zep_for_context now does
        edge_results = await client.graph.search(
            graph_id=graph_id,
            query=test_topic,
            scope="edges",  # Key: returns facts
            reranker="cross_encoder",
            limit=30
        )

        # Search nodes (entities)
        node_results = await client.graph.search(
            graph_id=graph_id,
            query=test_topic,
            scope="nodes",
            limit=20
        )

        # Extract VALUABLE context (facts from edges)
        valuable_facts = []
        entities = {"companies": [], "people": [], "deals": []}

        if hasattr(edge_results, 'edges') and edge_results.edges:
            for edge in edge_results.edges:
                fact = getattr(edge, 'fact', '')
                if fact and len(fact) > 20:  # Skip empty/trivial facts
                    valuable_facts.append(fact)

        if hasattr(node_results, 'nodes') and node_results.nodes:
            for node in node_results.nodes:
                node_type = getattr(node, 'type', '').lower()
                node_name = getattr(node, 'name', '')
                if 'company' in node_type:
                    entities["companies"].append(node_name)
                elif 'person' in node_type:
                    entities["people"].append(node_name)
                elif 'deal' in node_type:
                    entities["deals"].append(node_name)

        print(f"\n--- Context That SHOULD Be Passed to Article Generation ---")
        print(f"\nValuable Facts ({len(valuable_facts)} total):")
        for i, fact in enumerate(valuable_facts[:5]):
            print(f"  {i+1}. {fact[:200]}...")

        print(f"\nExtracted Entities:")
        print(f"  - Companies: {entities['companies'][:5]}")
        print(f"  - People: {entities['people'][:5]}")
        print(f"  - Deals: {entities['deals'][:5]}")

        print(f"\n--- What The Prompt SHOULD Include ---")
        if valuable_facts:
            print("\n=== ZEP KNOWLEDGE GRAPH CONTEXT ===")
            print(f"Previous coverage found in {graph_id} graph:")
            print("\nKEY FACTS FROM KNOWLEDGE GRAPH:")
            for fact in valuable_facts[:10]:
                print(f"• {fact[:200]}")
            print("\n")
        else:
            print("\n⚠️  No valuable facts found - Zep may be empty for this topic")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ZEP CONTEXT FLOW TEST SUITE")
    print("Testing: Graph ID mapping, Edge extraction, Prompt usage")
    print("=" * 60)

    await test_graph_id_mapping()
    await test_zep_edge_extraction()
    await test_context_used_in_prompt()
    await test_full_context_extraction()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("""
Key findings to check:
1. Graph ID mapping: Should map apps to correct graphs
2. Edge extraction: Should get FACTS, not just entity names
3. Prompt usage: Zep context should be USED in build_prompt()
4. Full context: Shows what valuable data is available

If Test 3 shows zep_context is NOT used in prompt, that's the bug!
The fix is to add zep_context handling in build_prompt() in article_generation.py
""")


if __name__ == "__main__":
    asyncio.run(main())
