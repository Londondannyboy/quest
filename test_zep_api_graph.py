"""
Test Zep Graph API Data Fetching

Test fetching graph nodes/edges via Zep API (no Playwright needed).
"""

import asyncio
from zep_cloud.client import AsyncZep

ZEP_API_KEY = "z_1dWlkIjoiMmNkYWVjZjktYTU5Ny00ZDlkLWIyMWItNTZjOWI5OTE5MTE4In0.Ssyb_PezcGgacQFq6Slg3fyFoqs8hBhvp6WsE8rO4VK_D70CT5tqDbFOs6ZTf8rw7qYfTRhLz5YFm8RR854rHg"


async def test_graph_api():
    """Test fetching graph data from Zep API."""
    print("🚀 Testing Zep Graph API...")

    client = AsyncZep(api_key=ZEP_API_KEY)

    try:
        # Search for Evercore in the graph
        print("\n📊 Searching for 'Evercore' in finance-knowledge graph...")
        results = await client.graph.search(
            graph_id="finance-knowledge",
            query="Evercore",
            limit=50
        )

        print(f"\n✅ Found {len(results.edges)} edges")

        # Extract nodes from edges
        node_map = {}
        edges_list = []

        for edge in results.edges:
            source_uuid = getattr(edge, 'source_node_uuid', None)
            target_uuid = getattr(edge, 'target_node_uuid', None)
            edge_name = getattr(edge, 'name', 'RELATED_TO')
            fact = getattr(edge, 'fact', '')

            # Create nodes
            if source_uuid and source_uuid not in node_map:
                node_map[source_uuid] = {
                    "id": source_uuid,
                    "label": "Evercore",  # Will extract from fact in real code
                    "group": "company"
                }

            if target_uuid and target_uuid not in node_map:
                node_map[target_uuid] = {
                    "id": target_uuid,
                    "label": fact.split()[-1] if fact else "Entity",
                    "group": "entity"
                }

            edges_list.append({
                "from": source_uuid,
                "to": target_uuid,
                "label": edge_name.replace('_', ' ').title(),
                "title": fact
            })

            print(f"  Edge: {fact[:80]}...")

        nodes_list = list(node_map.values())

        print(f"\n📈 Graph Data Summary:")
        print(f"  Nodes: {len(nodes_list)}")
        print(f"  Edges: {len(edges_list)}")

        if nodes_list:
            print("\n✅ SUCCESS - Graph data can be fetched via API!")
            print("   This data can be rendered with vis-network on the frontend")
        else:
            print("\n⚠️  No nodes found - graph may be empty for this company")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_graph_api())
