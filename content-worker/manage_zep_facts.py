#!/usr/bin/env python3
"""
Zep Facts Management Tool

Admin script for managing facts in the Zep knowledge graph.

Usage:
    python manage_zep_facts.py search "Evercore"           # Search facts
    python manage_zep_facts.py search "Evercore" --graph relocation  # Search specific graph
    python manage_zep_facts.py delete <uuid>               # Delete a fact by UUID
    python manage_zep_facts.py article <article_id>        # View facts used in article
    python manage_zep_facts.py list-graphs                 # List available graphs
"""

import asyncio
import argparse
import os
import sys
import json
from datetime import datetime

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zep_cloud.client import AsyncZep

# Configuration
ZEP_API_KEY = os.getenv("ZEP_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Graph mappings (same as zep_integration.py)
GRAPH_MAPPING = {
    "placement": os.getenv("ZEP_GRAPH_ID_FINANCE", "finance-knowledge"),
    "pe_news": os.getenv("ZEP_GRAPH_ID_FINANCE", "finance-knowledge"),
    "relocation": os.getenv("ZEP_GRAPH_ID_RELOCATION", "relocation"),
    "jobs": os.getenv("ZEP_GRAPH_ID_JOBS", "jobs"),
    "recruiter": os.getenv("ZEP_GRAPH_ID_JOBS", "jobs"),
    "finance": os.getenv("ZEP_GRAPH_ID_FINANCE", "finance-knowledge"),
}


def format_date(date_str):
    """Format date string for display."""
    if not date_str:
        return "N/A"
    try:
        if isinstance(date_str, str):
            return date_str[:10]
        return str(date_str)[:10]
    except:
        return str(date_str)


async def search_facts(query: str, graph_id: str = None, limit: int = 20):
    """Search for facts in Zep knowledge graph."""
    if not ZEP_API_KEY:
        print("Error: ZEP_API_KEY environment variable not set")
        return

    client = AsyncZep(api_key=ZEP_API_KEY)

    # Default to finance graph if not specified
    if not graph_id:
        graph_id = GRAPH_MAPPING.get("finance", "finance-knowledge")
    elif graph_id in GRAPH_MAPPING:
        graph_id = GRAPH_MAPPING[graph_id]

    print(f"\nSearching graph '{graph_id}' for: {query}")
    print("=" * 70)

    try:
        results = await client.graph.search(
            graph_id=graph_id,
            query=query,
            scope="edges",
            reranker="cross_encoder",
            limit=limit
        )

        if not results.edges:
            print("No facts found.")
            return

        print(f"Found {len(results.edges)} facts:\n")

        for i, edge in enumerate(results.edges, 1):
            uuid = getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', 'N/A')
            fact = getattr(edge, 'fact', 'N/A')
            valid_at = format_date(getattr(edge, 'valid_at', None))
            invalid_at = getattr(edge, 'invalid_at', None)
            name = getattr(edge, 'name', 'N/A')

            status = "CURRENT" if invalid_at is None else f"INVALID (since {format_date(invalid_at)})"

            print(f"{i}. [{status}]")
            print(f"   Fact: {fact}")
            print(f"   Type: {name}")
            print(f"   Valid from: {valid_at}")
            print(f"   UUID: {uuid}")
            print()

    except Exception as e:
        print(f"Error searching: {e}")


async def delete_fact(uuid: str):
    """Delete a fact from Zep by UUID."""
    if not ZEP_API_KEY:
        print("Error: ZEP_API_KEY environment variable not set")
        return

    client = AsyncZep(api_key=ZEP_API_KEY)

    print(f"\nDeleting fact with UUID: {uuid}")

    # Confirm deletion
    confirm = input("Are you sure? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return

    try:
        await client.graph.edge.delete(uuid_=uuid)
        print(f"Successfully deleted fact: {uuid}")
    except Exception as e:
        print(f"Error deleting fact: {e}")


async def view_article_facts(article_id: str):
    """View Zep facts used in a specific article."""
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        return

    import psycopg

    print(f"\nFetching Zep facts for article ID: {article_id}")
    print("=" * 70)

    try:
        async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT title, slug, zep_facts, created_at
                    FROM articles
                    WHERE id = %s
                """, (article_id,))

                result = await cur.fetchone()

                if not result:
                    print(f"Article not found: {article_id}")
                    return

                title, slug, zep_facts, created_at = result

                print(f"Article: {title}")
                print(f"Slug: {slug}")
                print(f"Created: {created_at}")
                print()

                if not zep_facts:
                    print("No Zep facts stored for this article.")
                    return

                facts = json.loads(zep_facts) if isinstance(zep_facts, str) else zep_facts
                print(f"Found {len(facts)} Zep facts used:\n")

                for i, fact_obj in enumerate(facts, 1):
                    if isinstance(fact_obj, dict):
                        fact = fact_obj.get("fact", "N/A")
                        uuid = fact_obj.get("uuid", "N/A")
                        valid_at = format_date(fact_obj.get("valid_at"))
                        invalid_at = fact_obj.get("invalid_at")
                        name = fact_obj.get("name", "N/A")

                        status = "CURRENT" if invalid_at is None else f"INVALID"

                        print(f"{i}. [{status}] {fact}")
                        print(f"   Type: {name} | Valid from: {valid_at}")
                        print(f"   UUID: {uuid}")
                        print()
                    else:
                        print(f"{i}. {fact_obj}")

    except Exception as e:
        print(f"Error: {e}")


async def list_graphs():
    """List available graph mappings."""
    print("\nAvailable Graph Mappings:")
    print("=" * 50)

    seen = set()
    for app, graph_id in sorted(GRAPH_MAPPING.items()):
        if graph_id not in seen:
            apps = [a for a, g in GRAPH_MAPPING.items() if g == graph_id]
            print(f"\n{graph_id}:")
            print(f"  Apps: {', '.join(apps)}")
            seen.add(graph_id)


async def search_articles_with_fact(fact_uuid: str):
    """Find articles that used a specific fact."""
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        return

    import psycopg

    print(f"\nSearching for articles using fact UUID: {fact_uuid}")
    print("=" * 70)

    try:
        async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
            async with conn.cursor() as cur:
                # Search for articles containing this fact UUID in zep_facts
                await cur.execute("""
                    SELECT id, title, slug, created_at
                    FROM articles
                    WHERE zep_facts::text LIKE %s
                    ORDER BY created_at DESC
                    LIMIT 20
                """, (f'%{fact_uuid}%',))

                results = await cur.fetchall()

                if not results:
                    print("No articles found using this fact.")
                    return

                print(f"Found {len(results)} article(s) using this fact:\n")

                for article_id, title, slug, created_at in results:
                    print(f"  ID: {article_id}")
                    print(f"  Title: {title}")
                    print(f"  Slug: {slug}")
                    print(f"  Created: {created_at}")
                    print()

    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage Zep knowledge graph facts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_zep_facts.py search "Evercore"
  python manage_zep_facts.py search "Cyprus visa" --graph relocation
  python manage_zep_facts.py delete abc123-uuid-here
  python manage_zep_facts.py article 42
  python manage_zep_facts.py find-usage abc123-uuid-here
  python manage_zep_facts.py list-graphs
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for facts")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--graph", "-g", help="Graph ID or app name (default: finance)")
    search_parser.add_argument("--limit", "-l", type=int, default=20, help="Max results")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a fact by UUID")
    delete_parser.add_argument("uuid", help="Fact UUID to delete")

    # Article facts command
    article_parser = subparsers.add_parser("article", help="View facts used in an article")
    article_parser.add_argument("article_id", help="Article ID")

    # Find usage command
    usage_parser = subparsers.add_parser("find-usage", help="Find articles using a fact")
    usage_parser.add_argument("uuid", help="Fact UUID to search for")

    # List graphs command
    subparsers.add_parser("list-graphs", help="List available graphs")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "search":
        asyncio.run(search_facts(args.query, args.graph, args.limit))
    elif args.command == "delete":
        asyncio.run(delete_fact(args.uuid))
    elif args.command == "article":
        asyncio.run(view_article_facts(args.article_id))
    elif args.command == "find-usage":
        asyncio.run(search_articles_with_fact(args.uuid))
    elif args.command == "list-graphs":
        asyncio.run(list_graphs())


if __name__ == "__main__":
    main()
