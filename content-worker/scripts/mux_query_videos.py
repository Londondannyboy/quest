#!/usr/bin/env python3
"""
Mux Video Query CLI

Command-line tool for querying Mux video assets by country, mode, or article.

Usage:
    python scripts/mux_query_videos.py --country SI
    python scripts/mux_query_videos.py --mode guide
    python scripts/mux_query_videos.py --article-id 155
    python scripts/mux_query_videos.py --summary
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.activities.media.mux_catalog import (
    query_videos_by_country,
    query_videos_by_mode,
    query_videos_by_article,
    get_all_videos_summary
)


async def main():
    parser = argparse.ArgumentParser(
        description="Query Mux video assets",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Query options (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--country", help="Query by country code (e.g., SI, PT, MT)")
    group.add_argument("--mode", help="Query by article mode (story, guide, yolo, voices)")
    group.add_argument("--article-id", type=int, help="Query by article ID")
    group.add_argument("--summary", action="store_true", help="Get summary statistics")

    # Additional filters
    parser.add_argument(
        "--country-filter",
        help="Additional country filter for mode queries"
    )
    parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Output format (default: table)"
    )

    args = parser.parse_args()

    try:
        # Execute query based on arguments
        if args.country:
            print(f"Querying videos for country: {args.country}")
            results = await query_videos_by_country(args.country)

        elif args.mode:
            print(f"Querying videos for mode: {args.mode}")
            results = await query_videos_by_mode(args.mode, args.country_filter)

        elif args.article_id:
            print(f"Querying videos for article: {args.article_id}")
            results = await query_videos_by_article(args.article_id)

        elif args.summary:
            print("Generating video summary statistics...")
            results = await get_all_videos_summary()

        # Format output
        if args.format == "json":
            print(json.dumps(results, indent=2))
        else:
            print_table(results)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def print_table(results):
    """Print results in table format"""
    if isinstance(results, dict):
        # Summary format
        print("\n=== Video Summary ===")
        print(f"Total Videos: {results.get('total_videos', 0)}")
        print(f"Total Duration: {results.get('total_duration', 0):.1f}s")

        if results.get('by_country'):
            print("\nBy Country:")
            for country, count in sorted(results['by_country'].items()):
                print(f"  {country}: {count}")

        if results.get('by_mode'):
            print("\nBy Mode:")
            for mode, count in sorted(results['by_mode'].items()):
                print(f"  {mode}: {count}")

        if results.get('note'):
            print(f"\nNote: {results['note']}")

    elif isinstance(results, list):
        # Video list format
        if not results:
            print("\nNo videos found.")
            print("\nNote: MCP client not yet authenticated.")
            print("To set up:")
            print("1. Sign up at https://mcp.mux.com")
            print("2. Authenticate via Mux dashboard")
            print("3. Run this script again")
            return

        print(f"\nFound {len(results)} videos:")
        print("-" * 80)
        for i, video in enumerate(results, 1):
            print(f"{i}. Playback ID: {video.get('playback_id', 'N/A')}")
            print(f"   Asset ID: {video.get('asset_id', 'N/A')}")
            print(f"   Duration: {video.get('duration', 0):.1f}s")
            print(f"   Status: {video.get('status', 'unknown')}")
            if video.get('passthrough'):
                print(f"   Metadata: {video['passthrough']}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
