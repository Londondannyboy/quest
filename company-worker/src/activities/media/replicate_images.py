"""
Replicate Image Generation Activity

Generate featured images for companies using Flux Schnell via Replicate.
"""

import replicate
import cloudinary
import cloudinary.uploader
from temporalio import activity
from typing import Dict, Any

from src.utils.config import config


@activity.defn
async def generate_company_featured_image(
    company_name: str,
    logo_url: str | None,
    country: str,
    founded_year: int | None
) -> Dict[str, Any]:
    """
    Generate featured image for company using Replicate + Flux Schnell.

    Creates a professional business card design featuring:
    - Company logo (if available)
    - Country flag watermark (15% opacity)
    - Modern gradient background
    - Premium corporate aesthetic
    - 1200x630px (perfect for OG images)

    Args:
        company_name: Company name
        logo_url: URL to company logo (optional)
        country: Country name for flag watermark
        founded_year: Year company was founded (optional)

    Returns:
        Dict with url, replicate_id, cost
    """
    activity.logger.info(f"Generating featured image for {company_name}")

    if not config.REPLICATE_API_TOKEN:
        activity.logger.warning("REPLICATE_API_TOKEN not configured")
        return {
            "url": None,
            "replicate_id": None,
            "cost": 0.0,
            "error": "REPLICATE_API_TOKEN not configured"
        }

    if not config.CLOUDINARY_URL:
        activity.logger.warning("CLOUDINARY_URL not configured")
        return {
            "url": None,
            "replicate_id": None,
            "cost": 0.0,
            "error": "CLOUDINARY_URL not configured"
        }

    try:
        # Configure services
        cloudinary.config(cloudinary_url=config.CLOUDINARY_URL)

        # Build prompt
        prompt = build_image_prompt(
            company_name,
            logo_url,
            country,
            founded_year
        )

        activity.logger.info(f"Image prompt: {prompt[:100]}...")

        # Generate with Replicate (Flux Schnell)
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": prompt,
                "width": 1200,
                "height": 630,
                "num_outputs": 1,
                "num_inference_steps": 4,  # Schnell is fast
                "guidance_scale": 0,  # Schnell doesn't use guidance
            }
        )

        # Get image URL
        if isinstance(output, list) and len(output) > 0:
            image_url = output[0]
        else:
            image_url = str(output)

        activity.logger.info(f"Image generated: {image_url}")

        # Upload to Cloudinary for persistence
        upload_result = cloudinary.uploader.upload(
            image_url,
            folder="company-featured",
            public_id=f"{company_name.lower().replace(' ', '-')}-featured",
            overwrite=True,
            resource_type="image"
        )

        final_url = upload_result.get("secure_url")

        activity.logger.info(f"Image uploaded to Cloudinary: {final_url}")

        return {
            "url": final_url,
            "replicate_id": "flux-schnell",
            "cloudinary_id": upload_result.get("public_id"),
            "cost": 0.003,  # Flux Schnell cost per image
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"Image generation failed: {e}")
        return {
            "url": None,
            "replicate_id": None,
            "cost": 0.003,  # Still charged even on error
            "success": False,
            "error": str(e)
        }


def build_image_prompt(
    company_name: str,
    logo_url: str | None,
    country: str,
    founded_year: int | None
) -> str:
    """
    Build prompt for featured image generation.

    Args:
        company_name: Company name
        logo_url: Logo URL (optional)
        country: Country name
        founded_year: Founded year (optional)

    Returns:
        Image generation prompt
    """
    prompt_parts = [
        "Professional business card design",
        f"for {company_name}",
        "clean modern style",
        "premium corporate aesthetic",
        "minimal gradient background in blues and grays",
        "1200x630px aspect ratio",
    ]

    # Add country flag reference
    if country and country != "Unknown":
        prompt_parts.append(
            f"{country} subtle flag watermark in corner (15% opacity)"
        )

    # Add founding year
    if founded_year:
        prompt_parts.append(f"founded {founded_year} text in small elegant font")

    # Add style guidance
    prompt_parts.extend([
        "high quality",
        "photorealistic",
        "professional photography",
        "studio lighting",
        "sharp focus",
        "8k resolution"
    ])

    prompt = ", ".join(prompt_parts)

    return prompt


@activity.defn
async def generate_placeholder_image(
    company_name: str,
    color_scheme: str = "blue"
) -> Dict[str, Any]:
    """
    Generate simple placeholder image (fallback if Replicate fails).

    Uses Cloudinary transformations to create a simple colored background
    with company name text.

    Args:
        company_name: Company name
        color_scheme: Color scheme (blue, green, purple)

    Returns:
        Dict with url, cost
    """
    activity.logger.info(f"Generating placeholder for {company_name}")

    if not config.CLOUDINARY_URL:
        return {
            "url": None,
            "cost": 0.0,
            "error": "CLOUDINARY_URL not configured"
        }

    try:
        cloudinary.config(cloudinary_url=config.CLOUDINARY_URL)

        # Color map
        colors = {
            "blue": "rgb:2c5aa0",
            "green": "rgb:2a9d8f",
            "purple": "rgb:7209b7"
        }

        bg_color = colors.get(color_scheme, colors["blue"])

        # Create placeholder using Cloudinary text overlay
        # This doesn't require uploading an image, just generates URL
        placeholder_url = cloudinary.CloudinaryImage("placeholder").build_url(
            width=1200,
            height=630,
            background=bg_color,
            crop="fill",
            overlay={
                "font_family": "Arial",
                "font_size": 60,
                "font_weight": "bold",
                "text": company_name[:30]
            },
            color="white"
        )

        activity.logger.info("Placeholder generated")

        return {
            "url": placeholder_url,
            "cost": 0.0,
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"Placeholder generation failed: {e}")
        return {
            "url": None,
            "cost": 0.0,
            "success": False,
            "error": str(e)
        }
