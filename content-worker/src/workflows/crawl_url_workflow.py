"""
Crawl URL Workflow

Child workflow for crawling individual URLs.
Called by CountryGuideCreationWorkflow for each research URL.

Benefits of individual workflows:
- Each URL has its own execution context
- Failures are isolated (one URL failing doesn't block others)
- Can be retried independently
- Clearer monitoring in Temporal UI

Supports 50/50 split between:
- Serper scrape API (fast, reliable, uses credits)
- Crawl4AI (free, browser automation, sometimes slow)
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import Dict, Any


@workflow.defn
class CrawlUrlWorkflow:
    """
    Crawl a single URL for country guide research.

    Supports two crawlers (50/50 split):
    - serper: Uses Serper.dev scrape API (faster, uses credits)
    - crawl4ai: Uses Crawl4AI service (free, browser automation)

    Timeline: 30-60 seconds per URL
    """

    @workflow.run
    async def run(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute URL crawl workflow.

        Args:
            input_dict: {
                "url": "https://example.com/article",
                "topic": "Portugal relocation visa",  # For logging/context
                "country_code": "PT",  # For linking
                "crawler": "serper" | "crawl4ai"  # Which crawler to use
            }

        Returns:
            Dict with success, url, title, content, source
        """
        url = input_dict["url"]
        topic = input_dict.get("topic", "")
        country_code = input_dict.get("country_code", "")
        crawler = input_dict.get("crawler", "crawl4ai")  # Default to crawl4ai

        workflow.logger.info(f"CrawlUrlWorkflow [{crawler}]: {url[:60]}...")

        # Choose activity based on crawler type
        if crawler == "serper":
            # Use Serper scrape API (faster, uses credits)
            crawl_result = await workflow.execute_activity(
                "serper_scrape",
                args=[url],
                start_to_close_timeout=timedelta(seconds=90),
                retry_policy=RetryPolicy(
                    maximum_attempts=2,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0
                )
            )
            # Serper activity returns in same format we need
            if crawl_result.get("success"):
                return {
                    "success": True,
                    "url": url,
                    "title": crawl_result.get("title", ""),
                    "content": crawl_result.get("content", "")[:15000],
                    "content_length": crawl_result.get("content_length", 0),
                    "crawler": "serper",
                    "country_code": country_code,
                    "topic": topic
                }
            else:
                workflow.logger.warning(f"Serper scrape failed: {crawl_result.get('error')}")
                return {
                    "success": False,
                    "url": url,
                    "error": crawl_result.get("error", "Serper scrape failed"),
                    "crawler": "serper"
                }
        else:
            # Use Crawl4AI (free, browser automation)
            crawl_result = await workflow.execute_activity(
                "crawl4ai_crawl",  # This is crawl4ai_service_crawl with alias
                args=[url],
                start_to_close_timeout=timedelta(seconds=90),
                retry_policy=RetryPolicy(
                    maximum_attempts=2,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0
                )
            )

        if not crawl_result.get("success"):
            workflow.logger.warning(f"Crawl failed for {url[:50]}: {crawl_result.get('error', 'unknown')}")
            return {
                "success": False,
                "url": url,
                "error": crawl_result.get("error", "Crawl failed"),
                "crawler": crawl_result.get("crawler", "unknown")
            }

        # Extract content from pages
        pages = crawl_result.get("pages", [])
        if not pages:
            workflow.logger.warning(f"No pages returned for {url[:50]}")
            return {
                "success": False,
                "url": url,
                "error": "No pages returned",
                "crawler": crawl_result.get("crawler", "unknown")
            }

        page = pages[0]  # Single URL = single page
        content = page.get("content", "")
        title = page.get("title", "")

        if not content or len(content) < 100:
            workflow.logger.warning(f"Insufficient content for {url[:50]}: {len(content)} chars")
            return {
                "success": False,
                "url": url,
                "error": f"Insufficient content: {len(content)} chars",
                "crawler": crawl_result.get("crawler", "unknown")
            }

        workflow.logger.info(f"Crawl success: {url[:50]} - {len(content)} chars")

        return {
            "success": True,
            "url": url,
            "title": title,
            "content": content[:15000],  # Cap at 15k chars per URL
            "content_length": len(content),
            "crawler": crawl_result.get("crawler", "unknown"),
            "country_code": country_code,
            "topic": topic
        }
