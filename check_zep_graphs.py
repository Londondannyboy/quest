#!/usr/bin/env python3
"""Check what graphs exist in Zep and search for Cyprus data"""

import os
from zep_cloud.client import Zep

# Get credentials
ZEP_API_KEY = os.getenv("ZEP_API_KEY")

if not ZEP_API_KEY:
    print("ERROR: ZEP_API_KEY not set")
    exit(1)

# Initialize client
client = Zep(api_key=ZEP_API_KEY)

print("=" * 60)
print("LISTING ALL ZEP GRAPHS")
print("=" * 60)

try:
    # List all graphs
    graphs_response = client.graph.list_all(page_size=100)

    if hasattr(graphs_response, 'graphs') and graphs_response.graphs:
        print(f"\nFound {len(graphs_response.graphs)} graphs:")
        for graph in graphs_response.graphs:
            print(f"\n  Graph: {graph.name if hasattr(graph, 'name') else graph}")
            if hasattr(graph, 'user_id'):
                print(f"  User ID: {graph.user_id}")
    else:
        print("\nNo graphs found or graphs attribute not available")
        print(f"Response: {graphs_response}")

except Exception as e:
    print(f"Error listing graphs: {e}")

print("\n" + "=" * 60)
print("SEARCHING FOR CYPRUS IN DIFFERENT WAYS")
print("=" * 60)

# Try different search queries
search_queries = [
    ("Cyprus", "edges"),
    ("relocation Cyprus", "edges"),
    ("Cyprus visa", "edges"),
]

for query, scope in search_queries:
    print(f"\n--- Query: '{query}' (scope: {scope}) ---")
    try:
        results = client.graph.search(
            user_id="newsroom-system",
            query=query,
            scope=scope
        )

        if hasattr(results, 'edges') and results.edges:
            print(f"Found {len(results.edges)} results:")
            for i, edge in enumerate(results.edges[:3], 1):
                fact = edge.fact if hasattr(edge, 'fact') else str(edge)
                score = edge.score if hasattr(edge, 'score') else 'N/A'
                print(f"  {i}. [{score}] {fact[:100]}...")
        else:
            print("No results found")

    except Exception as e:
        print(f"Error: {e}")
