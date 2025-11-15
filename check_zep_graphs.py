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
print("SEARCHING FOR CYPRUS IN 'relocation' GRAPH")
print("=" * 60)

try:
    # Search for Cyprus in relocation graph
    results = client.graph.search(
        user_id="newsroom-system",
        query="Cyprus relocation",
        scope="edges"
    )

    print(f"\nSearch results for 'Cyprus' in newsroom-system:")
    if hasattr(results, 'edges') and results.edges:
        print(f"Found {len(results.edges)} results:")
        for i, edge in enumerate(results.edges[:5], 1):
            print(f"\n  Result {i}:")
            if hasattr(edge, 'fact'):
                print(f"    Fact: {edge.fact}")
            if hasattr(edge, 'score'):
                print(f"    Score: {edge.score}")
    else:
        print("No results found")
        print(f"Response: {results}")

except Exception as e:
    print(f"Error searching: {e}")
