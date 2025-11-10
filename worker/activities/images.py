"""
Image Generation Activities

Real Replicate + Cloudinary image generation with responsive variants.
Generates 3 distinct images and uploads to Cloudinary with transformations.
"""

import os
import asyncio
from temporalio import activity
from typing import Dict, Any, List
import replicate
import cloudinary
import cloudinary.uploader


# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


@activity.defn(name="generate_article_images")
async def generate_article_images(
    article_id: str,
    article_title: str,
    article_angle: str
) -> Dict[str, str]:
    """
    Generate 3 distinct images using Replicate + upload to Cloudinary

    Pipeline:
    1. Generate image prompts from article context
    2. Generate images in parallel via Replicate Ideogram V3 Turbo
    3. Upload to Cloudinary with responsive transformations

    Args:
        article_id: Article ID for linking
        article_title: Article title for context
        article_angle: Article angle for image generation

    Returns:
        Dict with Cloudinary URLs for hero, content, featured images
    """
    activity.logger.info(f"🎨 Generating images for: {article_title[:50]}")

    # Check API keys
    if not os.getenv("REPLICATE_API_TOKEN"):
        activity.logger.warning("⚠️  REPLICATE_API_TOKEN not set, skipping image generation")
        return {"hero": None, "content": None, "featured": None}

    if not os.getenv("CLOUDINARY_CLOUD_NAME"):
        activity.logger.warning("⚠️  Cloudinary not configured, skipping image generation")
        return {"hero": None, "content": None, "featured": None}

    try:
        # Generate image prompts
        prompts = [
            {
                "purpose": "hero",
                "aspect_ratio": "16:9",
                "description": f"Professional hero image for article about: {article_title}. {article_angle}. Modern, clean, business-focused."
            },
            {
                "purpose": "featured",
                "aspect_ratio": "3:2",
                "description": f"Featured image for article about: {article_title}. Focus on key concept: {article_angle}."
            },
            {
                "purpose": "content",
                "aspect_ratio": "4:3",
                "description": f"Supporting content image for: {article_title}. Illustrate: {article_angle}."
            }
        ]

        # Generate images with Replicate (parallel)
        replicate_urls = await _generate_with_replicate(prompts)

        # Upload to Cloudinary with transformations (parallel)
        cloudinary_urls = await _upload_to_cloudinary(replicate_urls, article_id)

        activity.logger.info(f"✅ Generated {len(cloudinary_urls)} images successfully")
        return cloudinary_urls

    except Exception as e:
        activity.logger.error(f"❌ Image generation failed: {e}")
        return {"hero": None, "content": None, "featured": None}


async def _generate_with_replicate(prompts: List[Dict]) -> Dict[str, str]:
    """Generate images in parallel using Replicate Ideogram V3 Turbo"""
    activity.logger.info(f"🎨 Generating {len(prompts)} images with Replicate...")

    async def generate_single(prompt: Dict) -> tuple[str, str]:
        """Generate single image"""
        purpose = prompt["purpose"]
        activity.logger.info(f"   Generating {purpose} image ({prompt['aspect_ratio']})...")

        output = await asyncio.to_thread(
            replicate.run,
            "ideogram-ai/ideogram-v3-turbo",
            input={
                "prompt": prompt["description"],
                "aspect_ratio": prompt["aspect_ratio"],
                "magic_prompt_option": "Auto",
                "style_type": "General"
            }
        )

        # Handle different output formats
        if isinstance(output, str):
            url = output
        elif isinstance(output, list) and len(output) > 0:
            url = str(output[0])
        elif hasattr(output, 'url'):
            url = output.url
        else:
            url = str(output)

        activity.logger.info(f"   ✅ Generated {purpose}: {url[:60]}...")
        return (purpose, url)

    # Generate all in parallel
    results = await asyncio.gather(*[generate_single(p) for p in prompts])
    return dict(results)


async def _upload_to_cloudinary(image_urls: Dict[str, str], article_id: str) -> Dict[str, str]:
    """Upload images to Cloudinary with responsive transformations"""
    activity.logger.info(f"☁️  Uploading {len(image_urls)} images to Cloudinary...")

    # Define responsive transformations
    responsive_transformations = [
        {'width': 600, 'crop': 'scale', 'quality': 'auto:good', 'format': 'auto'},  # Mobile
        {'width': 1200, 'crop': 'scale', 'quality': 'auto:good', 'format': 'auto'},  # Tablet
        {'width': 1920, 'crop': 'scale', 'quality': 'auto:best', 'format': 'auto'},  # Desktop
    ]

    async def upload_single(purpose: str, replicate_url: str) -> tuple[str, str]:
        """Upload single image"""
        activity.logger.info(f"   Uploading {purpose} to Cloudinary...")

        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            replicate_url,
            folder="quest-articles",
            public_id=f"article_{purpose}_{article_id}",
            overwrite=True,
            resource_type="image",
            eager=responsive_transformations,
            eager_async=False,  # Wait for transformations
        )

        cdn_url = result["secure_url"]
        eager_count = len(result.get("eager", []))

        activity.logger.info(f"   ✅ Uploaded {purpose}: {cdn_url[:60]}... ({eager_count} variants)")
        return (purpose, cdn_url)

    # Upload all in parallel
    results = await asyncio.gather(*[
        upload_single(purpose, url)
        for purpose, url in image_urls.items()
    ])

    return dict(results)
