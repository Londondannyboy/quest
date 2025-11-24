"""
Article Image Generation from Prompts

Simple activity that generates images from prompts extracted from article content.
Uses Replicate for Flux Kontext Pro → Cloudinary for storage.
"""

import replicate
import cloudinary
import cloudinary.uploader
from temporalio import activity
from typing import Dict, Any, List

from src.utils.config import config


# Base style for consistency
BASE_STYLE = (
    "Semi-cartoon illustration style, stylized NOT photorealistic. "
    "Clean lines, professional but approachable, digital art aesthetic. "
    "Corporate navy blue, charcoal gray, tech blue accents. "
    "IMPORTANT: Include specific visual elements from the prompt context."
)

# Visual progression hints for sequential storytelling
PROGRESSION_HINTS = [
    "Opening scene establishing the context",
    "Development scene showing action or change",
    "Resolution or implication scene"
]


@activity.defn
async def generate_article_images_from_prompts(
    slug: str,
    featured_prompt: str,
    section_prompts: List[str],
    app: str = "placement"
) -> Dict[str, Any]:
    """
    Generate article images from prompts using Replicate → Cloudinary.

    Args:
        slug: Article slug for naming images
        featured_prompt: Prompt for featured/hero image
        section_prompts: List of prompts for section images
        app: App context for styling

    Returns:
        Dict with featured_image_url, section_images list, costs
    """
    activity.logger.info(f"Generating images for article: {slug}")
    activity.logger.info(f"Featured prompt: {featured_prompt[:100]}...")
    activity.logger.info(f"Section prompts: {len(section_prompts)}")

    result = {
        "featured_image_url": None,
        "section_images": [],
        "images_generated": 0,
        "total_cost": 0.0,
        "errors": []
    }

    if not config.REPLICATE_API_TOKEN:
        activity.logger.error("REPLICATE_API_TOKEN not configured")
        result["errors"].append("REPLICATE_API_TOKEN not configured")
        return result

    if not config.CLOUDINARY_URL:
        activity.logger.error("CLOUDINARY_URL not configured")
        result["errors"].append("CLOUDINARY_URL not configured")
        return result

    try:
        # Configure Cloudinary
        cloudinary.config(cloudinary_url=config.CLOUDINARY_URL)

        folder = f"quest-articles/{slug}"

        # Step 1: Generate featured image
        activity.logger.info("Generating featured image...")

        featured_full_prompt = f"{featured_prompt}. Style: {BASE_STYLE}"

        featured_output = replicate.run(
            "black-forest-labs/flux-kontext-pro",
            input={
                "prompt": featured_full_prompt,
                "aspect_ratio": "16:9",
                "output_format": "jpg",
                "safety_tolerance": 2
            }
        )

        # Get URL from output
        if isinstance(featured_output, list) and len(featured_output) > 0:
            featured_temp_url = str(featured_output[0])
        elif hasattr(featured_output, 'url'):
            featured_temp_url = str(featured_output.url)
        else:
            featured_temp_url = str(featured_output)

        activity.logger.info(f"Featured image generated: {featured_temp_url[:80]}...")

        # Upload to Cloudinary
        featured_upload = cloudinary.uploader.upload(
            featured_temp_url,
            folder=folder,
            public_id=f"{slug}-featured",
            overwrite=True,
            resource_type="image"
        )

        result["featured_image_url"] = featured_upload.get("secure_url")
        result["featured_image_alt"] = f"{slug} - Featured image"
        result["featured_image_title"] = "Featured Image"
        result["featured_image_description"] = featured_prompt
        result["images_generated"] += 1
        result["total_cost"] += 0.025

        activity.logger.info(f"Featured uploaded: {result['featured_image_url']}")

        # Step 2: Generate section images with context and visual progression
        for i, prompt in enumerate(section_prompts, start=1):
            activity.logger.info(f"Generating section image {i}/{len(section_prompts)}...")

            # Add progression hint for visual storytelling
            progression_idx = min(i - 1, len(PROGRESSION_HINTS) - 1)
            progression = PROGRESSION_HINTS[progression_idx]

            # Build contextual prompt emphasizing story elements
            section_full_prompt = (
                f"{prompt}. "
                f"Visual narrative: {progression}. "
                f"Style: {BASE_STYLE} "
                f"Each image should show DIFFERENT scene/angle/moment while maintaining visual coherence. "
                f"Include specific visual elements mentioned in the prompt (golf course, boardroom, etc)."
            )

            # Use featured image as context for visual consistency
            section_output = replicate.run(
                "black-forest-labs/flux-kontext-pro",
                input={
                    "prompt": section_full_prompt,
                    "input_image": result["featured_image_url"],  # Context from featured
                    "aspect_ratio": "16:9",
                    "output_format": "jpg",
                    "safety_tolerance": 2
                }
            )

            # Get URL from output
            if isinstance(section_output, list) and len(section_output) > 0:
                section_temp_url = str(section_output[0])
            elif hasattr(section_output, 'url'):
                section_temp_url = str(section_output.url)
            else:
                section_temp_url = str(section_output)

            activity.logger.info(f"Section {i} generated: {section_temp_url[:80]}...")

            # Upload to Cloudinary
            section_upload = cloudinary.uploader.upload(
                section_temp_url,
                folder=folder,
                public_id=f"{slug}-section-{i}",
                overwrite=True,
                resource_type="image"
            )

            section_url = section_upload.get("secure_url")

            result["section_images"].append({
                "url": section_url,
                "alt": f"Section {i} - {prompt[:50]}..." if len(prompt) > 50 else f"Section {i} - {prompt}",
                "title": f"Section {i} Image",
                "description": prompt,
                "cloudinary_id": section_upload.get("public_id")
            })
            result["images_generated"] += 1
            result["total_cost"] += 0.025

            activity.logger.info(f"Section {i} uploaded: {section_url}")

        activity.logger.info(
            f"Image generation complete: {result['images_generated']} images, "
            f"${result['total_cost']:.3f}"
        )

        return result

    except Exception as e:
        activity.logger.error(f"Image generation failed: {e}")
        result["errors"].append(str(e))
        return result
