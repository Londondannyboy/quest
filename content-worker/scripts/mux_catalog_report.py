#!/usr/bin/env python3
"""
Mux Video Catalog Report Generator

Generates HTML report of all Mux video assets organized by country and mode.

Usage:
    python scripts/mux_catalog_report.py --output catalog.html
    python scripts/mux_catalog_report.py --country SI --output slovenia_videos.html
"""

import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.activities.media.mux_catalog import get_all_videos_summary, query_videos_by_country


async def generate_html_report(
    summary: dict,
    output_file: str,
    country_filter: str = None
):
    """Generate HTML catalog report"""

    total = summary.get('total_videos', 0)
    duration = summary.get('total_duration', 0)
    by_country = summary.get('by_country', {})
    by_mode = summary.get('by_mode', {})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mux Video Catalog - Relocation Quest</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 py-12">
        <header class="mb-8">
            <h1 class="text-4xl font-bold text-gray-900 mb-2">
                Mux Video Catalog
            </h1>
            <p class="text-gray-600">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <!-- Summary Stats -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div class="text-sm text-gray-500 mb-1">Total Videos</div>
                <div class="text-3xl font-bold text-gray-900">{total}</div>
            </div>
            <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div class="text-sm text-gray-500 mb-1">Total Duration</div>
                <div class="text-3xl font-bold text-gray-900">{duration:.1f}s</div>
                <div class="text-sm text-gray-500 mt-1">{duration/60:.1f} minutes</div>
            </div>
            <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div class="text-sm text-gray-500 mb-1">Countries</div>
                <div class="text-3xl font-bold text-gray-900">{len(by_country)}</div>
            </div>
        </div>

        <!-- By Country -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold text-gray-900 mb-4">Videos by Country</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                {chr(10).join(f'''
                <div class="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                    <div class="text-sm text-gray-500">{country}</div>
                    <div class="text-2xl font-bold text-gray-900">{count}</div>
                </div>
                ''' for country, count in sorted(by_country.items(), key=lambda x: -x[1]))}
            </div>
        </section>

        <!-- By Mode -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold text-gray-900 mb-4">Videos by Mode</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                {chr(10).join(f'''
                <div class="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                    <div class="text-sm text-gray-500">{mode.title()}</div>
                    <div class="text-2xl font-bold text-gray-900">{count}</div>
                </div>
                ''' for mode, count in sorted(by_mode.items(), key=lambda x: -x[1]))}
            </div>
        </section>

        <!-- Setup Note (if no videos) -->
        {f'''
        <div class="bg-amber-50 border border-amber-200 rounded-xl p-6">
            <h3 class="text-lg font-semibold text-amber-900 mb-2">⚠️ MCP Setup Required</h3>
            <p class="text-amber-800 mb-4">{summary.get('note', '')}</p>
            <div class="space-y-2 text-sm text-amber-900">
                <p><strong>To set up Mux MCP:</strong></p>
                <ol class="list-decimal list-inside space-y-1 ml-4">
                    <li>Visit <a href="https://mcp.mux.com" class="text-amber-600 underline">https://mcp.mux.com</a></li>
                    <li>Authenticate via Mux dashboard (auto-login)</li>
                    <li>Run this script again to generate full catalog</li>
                </ol>
            </div>
        </div>
        ''' if total == 0 else ''}
    </div>
</body>
</html>"""

    # Write to file
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"\n✅ Catalog report generated: {output_file}")


async def main():
    parser = argparse.ArgumentParser(description="Generate Mux video catalog HTML report")
    parser.add_argument("--output", default="mux_catalog.html", help="Output HTML file path")
    parser.add_argument("--country", help="Filter by country code")

    args = parser.parse_args()

    try:
        if args.country:
            print(f"Generating catalog for country: {args.country}")
            videos = await query_videos_by_country(args.country)
            # Create summary from filtered results
            summary = {
                "total_videos": len(videos),
                "by_country": {args.country: len(videos)},
                "by_mode": {},
                "total_duration": sum(v.get('duration', 0) for v in videos)
            }
        else:
            print("Generating full video catalog...")
            summary = await get_all_videos_summary()

        await generate_html_report(summary, args.output, args.country)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
