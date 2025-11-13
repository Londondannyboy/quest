#!/usr/bin/env python3
"""
Standalone test script for Crawl4AI on Railway

Tests scraping Evercore.com to evaluate quality vs current scrapers.

Usage:
    python test_crawl4ai.py
"""
import asyncio
import sys
import json
from datetime import datetime

try:
    from crawl4ai import AsyncWebCrawler
except ImportError:
    print("❌ crawl4ai not installed. Run: pip install crawl4ai playwright")
    print("   Then run: playwright install")
    sys.exit(1)


async def test_crawl4ai_scraper(url: str = "https://www.evercore.com"):
    """
    Test Crawl4AI web scraping on a given URL

    Args:
        url: Website to scrape

    Returns:
        dict with scraping results
    """
    print(f"\n{'='*70}")
    print(f"🕷️  Crawl4AI Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    print(f"🔗 Target: {url}\n")

    results = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "error": None,
        "content_length": 0,
        "title": None,
        "markdown": None,
        "metadata": {}
    }

    try:
        # Initialize crawler with sensible defaults
        async with AsyncWebCrawler(
            verbose=True,
            headless=True,  # Important for Railway
        ) as crawler:

            print("📥 Starting crawl...")

            # Run the crawler
            result = await crawler.arun(
                url=url,
                bypass_cache=True,
                word_count_threshold=10,  # Filter out tiny text blocks
                excluded_tags=['form', 'nav', 'footer'],  # Skip navigation
                remove_overlay_elements=True,  # Remove popups/modals
            )

            # Process results
            results["success"] = result.success
            results["content_length"] = len(result.markdown) if result.markdown else 0
            results["title"] = result.metadata.get("title", "N/A")
            results["markdown"] = result.markdown
            results["metadata"] = {
                "final_url": result.url,
                "status_code": result.status_code if hasattr(result, 'status_code') else None,
                "has_links": bool(result.links) if hasattr(result, 'links') else None,
                "has_media": bool(result.media) if hasattr(result, 'media') else None,
            }

            # Print summary
            print(f"\n{'='*70}")
            print(f"✅ Crawl Status: {'SUCCESS' if result.success else 'FAILED'}")
            print(f"📏 Content Length: {results['content_length']:,} characters")
            print(f"📄 Page Title: {results['title']}")
            print(f"🔗 Final URL: {results['metadata']['final_url']}")
            print(f"{'='*70}\n")

            # Show content preview
            if result.markdown:
                print("📝 Content Preview (first 2000 chars):")
                print("-" * 70)
                print(result.markdown[:2000])
                if len(result.markdown) > 2000:
                    print(f"\n... ({len(result.markdown) - 2000:,} more characters)")
                print("-" * 70)

            # Save full output to file
            output_file = "/tmp/crawl4ai_evercore_output.md"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Crawl4AI Output - {url}\n\n")
                    f.write(f"**Timestamp:** {results['timestamp']}\n")
                    f.write(f"**Success:** {results['success']}\n")
                    f.write(f"**Length:** {results['content_length']:,} chars\n")
                    f.write(f"**Title:** {results['title']}\n\n")
                    f.write("---\n\n")
                    f.write(result.markdown or "No content")

                print(f"\n💾 Full output saved to: {output_file}\n")
            except Exception as e:
                print(f"⚠️  Could not save output file: {e}")

    except Exception as e:
        results["error"] = str(e)
        print(f"\n❌ Error during crawl:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    return results


async def compare_with_current_scrapers():
    """
    Optional: Compare Crawl4AI with existing scrapers
    """
    print("\n" + "="*70)
    print("📊 Comparison with Current Scrapers")
    print("="*70)

    print("""
Current scraping setup (from company.py):
- 4 parallel scrapers: Exa, Firecrawl, Tavily, Direct
- Cost: ~$0.17-0.50 per scrape
- Time: 5-30 seconds
- Selection: Most content wins (char count)

Crawl4AI benefits:
- Single scraper (simpler)
- Free/open-source (no API costs)
- Fast (2-5 seconds)
- Good markdown formatting
- Handles JavaScript rendering

Potential issues:
- Needs browser/Playwright (heavier)
- May need headless mode tuning for Railway
- No multi-page crawling (like Exa)
    """)


async def main():
    """Main test execution"""

    # Test Evercore
    results = await test_crawl4ai_scraper("https://www.evercore.com")

    # Show comparison info
    await compare_with_current_scrapers()

    # Summary
    print("\n" + "="*70)
    print("🎯 Test Summary")
    print("="*70)
    print(f"Success: {'✅ YES' if results['success'] else '❌ NO'}")
    print(f"Content: {results['content_length']:,} characters")
    print(f"Quality: {'Good' if results['content_length'] > 5000 else 'Needs review'}")
    print("="*70 + "\n")

    if not results["success"]:
        print("❌ Test failed. Check error above.")
        sys.exit(1)

    print("✅ Test completed successfully!")

    return results


if __name__ == "__main__":
    asyncio.run(main())
