"""
Image Generation Activities

Real Replicate + Cloudinary image generation with responsive variants.
Generates 3 distinct images and uploads to Cloudinary with transformations.
Uses app-specific image templates from config.
"""

import os
import sys
import asyncio
from temporalio import activity
from typing import Dict, Any, List
import replicate
import cloudinary
import cloudinary.uploader

# Import app config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_app_config


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
    article_angle: str,
    app: str = "placement"
) -> Dict[str, str]:
    """
    Generate 6 distinct images using Replicate + upload to Cloudinary
    Uses app-specific image templates from config.

    Pipeline:
    1. Load app config and get image templates
    2. Generate prompts from templates with article context
    3. Generate images in parallel via Replicate Ideogram V3 Turbo
    4. Upload to Cloudinary with responsive transformations

    Args:
        article_id: Article ID for linking
        article_title: Article title for context
        article_angle: Article angle for image generation
        app: App name (placement, relocation) for config

    Returns:
        Dict with Cloudinary URLs for hero, featured, content, content2, content3, content4 images
    """
    activity.logger.info(f"🎨 Generating images for {app}: {article_title[:50]}")

    # Check API keys
    if not os.getenv("REPLICATE_API_TOKEN"):
        activity.logger.warning("⚠️  REPLICATE_API_TOKEN not set, skipping image generation")
        return {"hero": None, "featured": None, "content": None, "content2": None, "content3": None, "content4": None}

    if not os.getenv("CLOUDINARY_CLOUD_NAME"):
        activity.logger.warning("⚠️  Cloudinary not configured, skipping image generation")
        return {"hero": None, "featured": None, "content": None, "content2": None, "content3": None, "content4": None}

    try:
        # Load app config
        app_config = get_app_config(app)
        activity.logger.info(f"📋 Using {app_config.display_name} image style: {app_config.image_style[:50]}...")

        # Generate image prompts from app-specific templates
        prompts = [
            {
                "purpose": "hero",
                "aspect_ratio": "16:9",
                "description": app_config.hero_image_prompt_template.format(
                    theme=article_title,
                    topic=article_title,
                    metric=article_angle
                )
            },
            {
                "purpose": "featured",
                "aspect_ratio": "3:2",
                "description": app_config.featured_image_prompt_template.format(
                    theme=article_title,
                    topic=article_title,
                    metric=article_angle
                )
            },
            {
                "purpose": "content",
                "aspect_ratio": "4:3",
                "description": app_config.content_image_prompt_template.format(
                    theme=article_title,
                    topic=article_title,
                    metric=article_angle
                )
            },
            {
                "purpose": "content2",
                "aspect_ratio": "4:3",
                "description": getattr(app_config, 'content2_image_prompt_template', app_config.content_image_prompt_template).format(
                    theme=article_title,
                    topic=article_title,
                    metric=article_angle
                )
            },
            {
                "purpose": "content3",
                "aspect_ratio": "4:3",
                "description": getattr(app_config, 'content3_image_prompt_template', app_config.content_image_prompt_template).format(
                    theme=article_title,
                    topic=article_title,
                    metric=article_angle
                )
            },
            {
                "purpose": "content4",
                "aspect_ratio": "4:3",
                "description": getattr(app_config, 'content4_image_prompt_template', app_config.content_image_prompt_template).format(
                    theme=article_title,
                    topic=article_title,
                    metric=article_angle
                )
            }
        ]

        # Generate images with Replicate (parallel)
        replicate_urls = await _generate_with_replicate(prompts)
        activity.logger.info(f"🔍 Replicate URLs generated: {replicate_urls}")

        # Upload to Cloudinary with transformations (parallel)
        cloudinary_urls = await _upload_to_cloudinary(replicate_urls, article_id)
        activity.logger.info(f"🔍 Cloudinary URLs after upload: {cloudinary_urls}")

        activity.logger.info(f"✅ Generated {len(cloudinary_urls)} images successfully")
        return cloudinary_urls

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        activity.logger.error(f"❌ Image generation failed: {e}")
        activity.logger.error(f"Full traceback:\n{error_trace}")
        return {"hero": None, "featured": None, "content": None, "content2": None, "content3": None, "content4": None}


async def _generate_with_replicate(prompts: List[Dict]) -> Dict[str, str]:
    """Generate images using Replicate Ideogram V3 Turbo"""
    activity.logger.info(f"🎨 Generating {len(prompts)} images with Replicate...")

    results = {}
    for prompt in prompts:
        purpose = prompt["purpose"]
        activity.logger.info(f"   Generating {purpose} image ({prompt['aspect_ratio']})...")

        try:
            # Direct call to replicate.run without asyncio.to_thread
            output = replicate.run(
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
            results[purpose] = url

        except Exception as e:
            activity.logger.error(f"   ❌ Failed to generate {purpose}: {e}")
            import traceback
            activity.logger.error(f"   Traceback: {traceback.format_exc()}")
            results[purpose] = None

    return results


async def _upload_to_cloudinary(image_urls: Dict[str, str], article_id: str) -> Dict[str, str]:
    """Upload images to Cloudinary with responsive transformations"""
    activity.logger.info(f"☁️  Uploading {len(image_urls)} images to Cloudinary...")
    activity.logger.info(f"   Image URLs to upload: {image_urls}")

    # Define responsive transformations
    responsive_transformations = [
        {'width': 600, 'crop': 'scale', 'quality': 'auto:good', 'format': 'auto'},  # Mobile
        {'width': 1200, 'crop': 'scale', 'quality': 'auto:good', 'format': 'auto'},  # Tablet
        {'width': 1920, 'crop': 'scale', 'quality': 'auto:best', 'format': 'auto'},  # Desktop
    ]

    async def upload_single(purpose: str, replicate_url: str) -> tuple[str, str]:
        """Upload single image"""
        try:
            activity.logger.info(f"   Uploading {purpose} to Cloudinary from: {replicate_url[:100]}...")

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
        except Exception as e:
            activity.logger.error(f"   ❌ Failed to upload {purpose} to Cloudinary: {e}")
            import traceback
            activity.logger.error(f"   Traceback: {traceback.format_exc()}")
            return (purpose, None)

    # Upload all in parallel
    try:
        results = await asyncio.gather(*[
            upload_single(purpose, url)
            for purpose, url in image_urls.items()
        ])

        # Filter out None values
        successful_uploads = {k: v for k, v in dict(results) if v is not None}
        activity.logger.info(f"   Cloudinary upload complete: {len(successful_uploads)}/{len(image_urls)} successful")

        return successful_uploads if successful_uploads else {"hero": None, "featured": None, "content": None, "content2": None, "content3": None, "content4": None}
    except Exception as e:
        activity.logger.error(f"   ❌ Cloudinary upload gather failed: {e}")
        return {"hero": None, "featured": None, "content": None, "content2": None, "content3": None, "content4": None}
