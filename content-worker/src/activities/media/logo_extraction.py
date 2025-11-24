"""
Logo Extraction and Processing Activity

Extract company logo from website and process it for display.
Upload to Cloudinary for hosting.
"""

from __future__ import annotations

import httpx
import cloudinary
import cloudinary.uploader
from temporalio import activity
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO

from src.utils.config import config


@activity.defn
async def extract_and_process_logo(
    url: str,
    company_name: str
) -> Dict[str, Any]:
    """
    Extract logo from website, process it, and upload to Cloudinary.

    Process:
    1. Find logo URLs from website
    2. Download best candidate
    3. Process (resize to 400x400, optimize)
    4. Upload to Cloudinary

    Args:
        url: Company website URL
        company_name: Company name (for fallback)

    Returns:
        Dict with logo_url, method, cost
    """
    activity.logger.info(f"Extracting logo for {company_name}")

    # Configure Cloudinary
    if config.CLOUDINARY_URL:
        cloudinary.config(cloudinary_url=config.CLOUDINARY_URL)
    else:
        activity.logger.warning("CLOUDINARY_URL not configured")
        return {
            "logo_url": None,
            "method": "none",
            "cost": 0.0,
            "error": "Cloudinary not configured"
        }

    try:
        # Step 1: Find logo URLs
        logo_candidates = await find_logo_urls(url)

        if not logo_candidates:
            activity.logger.warning("No logo candidates found")
            return {
                "logo_url": None,
                "method": "not_found",
                "cost": 0.0,
                "error": "No logo found on website"
            }

        activity.logger.info(f"Found {len(logo_candidates)} logo candidates")

        # Step 2: Download and process best candidate
        for candidate_url in logo_candidates:
            try:
                logo_bytes = await download_image(candidate_url)

                if not logo_bytes:
                    continue

                # Step 3: Process image
                processed = process_logo(logo_bytes)

                if not processed:
                    continue

                # Step 4: Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    processed,
                    folder="company-logos",
                    public_id=f"{company_name.lower().replace(' ', '-')}",
                    overwrite=True,
                    resource_type="image",
                    transformation=[
                        {"width": 400, "height": 400, "crop": "fit"},
                        {"quality": "auto", "fetch_format": "auto"}
                    ]
                )

                logo_url = upload_result.get("secure_url")

                activity.logger.info(f"Logo uploaded: {logo_url}")

                return {
                    "logo_url": logo_url,
                    "method": "extracted",
                    "source_url": candidate_url,
                    "cloudinary_id": upload_result.get("public_id"),
                    "cost": 0.0  # Cloudinary free tier
                }

            except Exception as e:
                activity.logger.warning(f"Failed to process {candidate_url}: {e}")
                continue

        # All candidates failed
        activity.logger.error("All logo candidates failed to process")
        return {
            "logo_url": None,
            "method": "processing_failed",
            "cost": 0.0,
            "error": "Failed to process logo candidates"
        }

    except Exception as e:
        activity.logger.error(f"Logo extraction failed: {e}")
        return {
            "logo_url": None,
            "method": "error",
            "cost": 0.0,
            "error": str(e)
        }


async def find_logo_urls(url: str) -> list[str]:
    """
    Find logo image URLs from website.

    Strategies:
    1. Look for <img> with "logo" in class/id/alt
    2. Look for <img> in header/nav
    3. Look for <link rel="icon">

    Args:
        url: Website URL

    Returns:
        List of candidate logo URLs
    """
    candidates = []

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; QuestBot/1.0)"
                }
            )

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Strategy 1: Find images with "logo" in attributes
            logo_imgs = soup.find_all('img', {
                'class': lambda x: x and 'logo' in x.lower(),
            })
            logo_imgs += soup.find_all('img', {
                'id': lambda x: x and 'logo' in x.lower(),
            })
            logo_imgs += soup.find_all('img', {
                'alt': lambda x: x and 'logo' in x.lower(),
            })

            for img in logo_imgs:
                src = img.get('src') or img.get('data-src')
                if src:
                    full_url = urljoin(url, src)
                    if full_url not in candidates:
                        candidates.append(full_url)

            # Strategy 2: Find images in header/nav
            header = soup.find('header') or soup.find('nav')
            if header:
                header_imgs = header.find_all('img')
                for img in header_imgs[:3]:  # First 3 images
                    src = img.get('src') or img.get('data-src')
                    if src:
                        full_url = urljoin(url, src)
                        if full_url not in candidates:
                            candidates.append(full_url)

            # Strategy 3: Favicon
            icon_link = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            if icon_link:
                href = icon_link.get('href')
                if href:
                    full_url = urljoin(url, href)
                    candidates.append(full_url)

    except Exception as e:
        activity.logger.error(f"Failed to parse website for logos: {e}")

    return candidates[:5]  # Return top 5 candidates


async def download_image(url: str) -> Optional[bytes]:
    """
    Download image from URL.

    Args:
        url: Image URL

    Returns:
        Image bytes or None
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)

            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    return response.content

    except Exception as e:
        activity.logger.debug(f"Failed to download {url}: {e}")

    return None


def process_logo(image_bytes: bytes) -> bytes | None:
    """
    Process logo image (resize, optimize).

    Args:
        image_bytes: Raw image bytes

    Returns:
        Processed image bytes or None
    """
    try:
        # Open image
        img = Image.open(BytesIO(image_bytes))

        # Convert to RGBA if necessary
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')

        # Resize to 400x400 (maintain aspect ratio)
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)

        # Save to bytes
        output = BytesIO()
        img.save(output, format='PNG', optimize=True)
        output.seek(0)

        return output.read()

    except Exception as e:
        activity.logger.debug(f"Failed to process image: {e}")
        return None
