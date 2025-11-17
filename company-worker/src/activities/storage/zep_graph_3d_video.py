"""
Zep Graph 3D Video Capture Activity

Uses Playwright to render 3D Force Graph and capture as video.
"""

from temporalio import activity
from typing import Dict, Any
import asyncio
import os
import json
from pathlib import Path
from playwright.async_api import async_playwright
import cloudinary
import cloudinary.uploader

from src.utils.config import config


@activity.defn
async def capture_graph_3d_video(
    company_name: str,
    graph_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Render 3D force graph and capture as video.

    Args:
        company_name: Company name for video title
        graph_data: Graph data with nodes and edges

    Returns:
        Dict with video_url (WebP or MP4) and success status
    """
    activity.logger.info(f"Capturing 3D graph video for: {company_name}")

    if not config.CLOUDINARY_CLOUD_NAME or not config.CLOUDINARY_API_KEY:
        activity.logger.warning("Cloudinary not configured")
        return {
            "success": False,
            "video_url": None,
            "error": "Cloudinary not configured"
        }

    if not graph_data.get("nodes") or len(graph_data["nodes"]) == 0:
        activity.logger.warning("No graph data available")
        return {
            "success": False,
            "video_url": None,
            "error": "No graph data available"
        }

    try:
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=config.CLOUDINARY_CLOUD_NAME,
            api_key=config.CLOUDINARY_API_KEY,
            api_secret=config.CLOUDINARY_API_SECRET
        )

        # Load HTML template
        template_path = Path(__file__).parent / "graph_3d_template.html"
        with open(template_path, 'r') as f:
            html_template = f.read()

        # Inject graph data
        html_content = html_template.replace(
            '{{GRAPH_DATA}}',
            json.dumps(graph_data)
        )

        # Create temp HTML file
        temp_html = f"/tmp/graph_3d_{company_name.lower().replace(' ', '_')}.html"
        with open(temp_html, 'w') as f:
            f.write(html_content)

        # Create temp video file
        temp_video = f"/tmp/graph_3d_{company_name.lower().replace(' ', '_')}.webm"

        async with async_playwright() as p:
            # Launch browser with WebGL support
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-gpu',
                    '--enable-webgl',
                    '--use-gl=swiftshader',  # Software GL for headless
                    '--disable-software-rasterizer',
                    '--enable-features=WebRTC-PipeWireCapturer'
                ]
            )

            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir="/tmp",
                record_video_size={"width": 1920, "height": 1080}
            )

            page = await context.new_page()

            activity.logger.info(f"Loading 3D graph HTML: {temp_html}")

            # Navigate to local HTML file
            await page.goto(f"file://{temp_html}", wait_until="networkidle", timeout=30000)

            # Wait for graph to be ready
            await page.wait_for_function("window.graphReady === true", timeout=10000)

            activity.logger.info("Graph rendered, capturing video for 10 seconds...")

            # Let graph animate for 10 seconds
            await asyncio.sleep(10)

            # Close page to save video
            await page.close()

            # Get video path
            video_path = await context.video_path(page)
            await context.close()
            await browser.close()

            activity.logger.info(f"Video captured: {video_path}")

            # Upload to Cloudinary as video
            upload_result = cloudinary.uploader.upload(
                video_path,
                folder="zep-graphs-3d",
                public_id=f"graph_3d_{company_name.lower().replace(' ', '_')}",
                resource_type="video",
                overwrite=True,
                format="webm"  # Keep as WebM for web playback
            )

            video_url = upload_result.get("secure_url")
            activity.logger.info(f"Video uploaded: {video_url}")

            # Cleanup temp files
            if os.path.exists(temp_html):
                os.remove(temp_html)
            if video_path and os.path.exists(video_path):
                os.remove(video_path)

            return {
                "success": True,
                "video_url": video_url,
                "format": "webm",
                "width": 1920,
                "height": 1080,
                "duration_seconds": 10
            }

    except Exception as e:
        activity.logger.warning(f"3D graph video capture failed (non-critical): {e}")
        return {
            "success": False,
            "video_url": None,
            "error": str(e),
            "message": "3D video unavailable - other visualization methods may be available"
        }
