"""
News Source Crawling

Crawl news article URLs to extract full content.
"""

from __future__ import annotations
from temporalio import activity
from crawl4ai import AsyncWebCrawler
import asyncio


@activity.defn
async def crawl_news_sources(urls: list[str]) -> dict:
    """
    Crawl news article URLs using Crawl4AI.

    Args:
        urls: List of news article URLs to crawl

    Returns:
        Dict with pages, success
    """
    if not urls:
        return {"pages": [], "success": False}

    pages = []

    try:
        async with AsyncWebCrawler() as crawler:
            # Crawl all URLs in parallel (limit to 10 at a time)
            tasks = [crawler.arun(url=url) for url in urls[:10]]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    activity.logger.warning(f"Failed to crawl {urls[i]}: {result}")
                    continue

                if result.success:
                    pages.append({
                        "url": urls[i],
                        "markdown": result.markdown,
                        "text": result.cleaned_html,
                        "title": result.title if hasattr(result, 'title') else ""
                    })

        activity.logger.info(f"Crawled {len(pages)} / {len(urls)} news sources")

        return {
            "pages": pages,
            "success": len(pages) > 0
        }

    except Exception as e:
        activity.logger.error(f"News crawling failed: {e}")
        return {"pages": [], "success": False}
