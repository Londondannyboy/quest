"""
Image Generation Activities

Placeholder for image generation using Replicate + Cloudinary.
To be implemented in Phase 2.
"""

from temporalio import activity
from typing import Dict, Any


@activity.defn(name="generate_article_images")
async def generate_article_images(
    article_id: str,
    article_title: str,
    article_angle: str
) -> Dict[str, str]:
    """
    Generate images for article (placeholder)

    Args:
        article_id: Article ID for linking
        article_title: Article title for context
        article_angle: Article angle for image generation

    Returns:
        Dict with image URLs (hero, content, featured)
    """
    activity.logger.info(f"🎨 Image generation placeholder for: {article_title[:50]}")
    activity.logger.info("   To be implemented with Replicate + Cloudinary")

    # Return empty - images will be added in Phase 2
    return {
        "hero": None,
        "content": None,
        "featured": None
    }
