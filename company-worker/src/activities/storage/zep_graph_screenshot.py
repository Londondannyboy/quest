"""
Zep Graph Screenshot Activity

Uses Playwright to screenshot Zep's graph visualization and upload to Cloudinary.
"""

from temporalio import activity
from typing import Dict, Any
import asyncio
import base64
from playwright.async_api import async_playwright
import cloudinary
import cloudinary.uploader

from src.utils.config import config


@activity.defn
async def capture_zep_graph_screenshot(
    company_name: str,
    graph_id: str = "finance-knowledge"
) -> Dict[str, Any]:
    """
    Capture screenshot of Zep graph visualization for a company.

    Args:
        company_name: Company name to focus on in graph
        graph_id: Zep graph ID (default: finance-knowledge)

    Returns:
        Dict with cloudinary_url and success status
    """
    activity.logger.info(f"Capturing Zep graph screenshot for: {company_name}")

    if not config.CLOUDINARY_CLOUD_NAME or not config.CLOUDINARY_API_KEY:
        activity.logger.warning("Cloudinary not configured")
        return {
            "success": False,
            "cloudinary_url": None,
            "error": "Cloudinary not configured"
        }

    try:
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=config.CLOUDINARY_CLOUD_NAME,
            api_key=config.CLOUDINARY_API_KEY,
            api_secret=config.CLOUDINARY_API_SECRET
        )

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()

            # Navigate to Zep app graph page
            # URL format: /projects/{project_id}/groups/{group_id}
            zep_project_id = "7d00497e-a7ef-47dd-9763-112a6bbe92f2"
            zep_url = f"https://app.getzep.com/projects/{zep_project_id}/groups/{graph_id}"

            activity.logger.info(f"Navigating to: {zep_url}")

            # Set authentication header with API key
            await context.set_extra_http_headers({
                "Authorization": f"Api-Key {config.ZEP_API_KEY}"
            })

            await page.goto(zep_url, wait_until="networkidle", timeout=30000)

            # Wait for graph to render
            await asyncio.sleep(3)  # Give graph time to render

            # Search for company in graph (if search is available)
            try:
                # Try to find and click search/filter
                search_input = await page.query_selector('input[placeholder*="search" i], input[type="search"]')
                if search_input:
                    await search_input.fill(company_name)
                    await asyncio.sleep(2)  # Wait for filter
            except Exception as e:
                activity.logger.warning(f"Could not search for company: {e}")

            # Take screenshot
            screenshot_bytes = await page.screenshot(
                full_page=False,
                type="png"
            )

            await browser.close()

        # Upload to Cloudinary
        activity.logger.info("Uploading screenshot to Cloudinary")
        upload_result = cloudinary.uploader.upload(
            screenshot_bytes,
            folder="zep-graphs",
            public_id=f"graph_{company_name.lower().replace(' ', '_')}",
            overwrite=True,
            resource_type="image"
        )

        cloudinary_url = upload_result.get("secure_url")
        activity.logger.info(f"Screenshot uploaded: {cloudinary_url}")

        return {
            "success": True,
            "cloudinary_url": cloudinary_url,
            "width": 1920,
            "height": 1080
        }

    except Exception as e:
        activity.logger.warning(f"Graph screenshot capture failed (non-critical): {e}")
        # Return graceful failure - don't break workflow
        return {
            "success": False,
            "cloudinary_url": None,
            "error": str(e),
            "message": "Screenshot unavailable - graph data still synced to Zep"
        }
