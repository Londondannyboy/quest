"""
Video generation activity using Seedance (Replicate) or Gemini.
"""

import os
import replicate
from temporalio import activity
from typing import Dict, Any, Optional

# Quality tier configuration
VIDEO_QUALITY_MODELS = {
    "high": {
        "model": "google/gemini",  # TODO: Update with actual Gemini video model
        "resolution": "720p",
        "cost_per_second": 0.30,  # ~$0.90 for 3s
        "description": "Premium quality with perfect text rendering"
    },
    "medium": {
        "model": "bytedance/seedance-1-pro-fast",
        "resolution": "720p",
        "cost_per_second": 0.025,  # $0.075 for 3s
        "description": "Good quality, balanced cost"
    },
    "low": {
        "model": "bytedance/seedance-1-pro-fast",
        "resolution": "480p",
        "cost_per_second": 0.015,  # $0.045 for 3s
        "description": "Budget friendly, adequate quality"
    }
}


@activity.defn
async def generate_article_video(
    title: str,
    content: str,
    app: str = "placement",
    quality: str = "medium",
    duration: int = 3,
    aspect_ratio: str = "16:9",
    video_model: str = "seedance",
    video_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a video for an article using AI video generation.

    Args:
        title: Article title
        content: Article content (used to generate prompt)
        app: Application name (placement, relocation, etc.)
        quality: Video quality tier (high, medium, low)
        duration: Video duration in seconds (default 3)
        aspect_ratio: Video aspect ratio (default 16:9)
        video_model: Model to use (seedance, wan-2.5)
        video_prompt: Custom prompt (if None, auto-generated)

    Returns:
        Dict with video_url, quality, duration, cost
    """
    activity.logger.info(f"Generating video for article: {title[:50]}...")
    activity.logger.info(f"Model: {video_model}, Quality: {quality}")

    # Get quality configuration
    quality_config = VIDEO_QUALITY_MODELS.get(quality, VIDEO_QUALITY_MODELS["medium"])
    resolution = quality_config["resolution"]

    # Use custom prompt if provided, otherwise generate from content
    if video_prompt and video_prompt.strip():
        prompt = video_prompt.strip()
        activity.logger.info(f"Using custom prompt: {prompt[:100]}...")
    else:
        prompt = generate_video_prompt(title, content, app)
        activity.logger.info(f"Generated prompt: {prompt[:100]}...")

    # Generate video based on selected model
    if video_model == "wan-2.5":
        video_url = await generate_with_wan(prompt, duration, resolution, aspect_ratio)
        actual_model = "wan-video/wan-2.5-t2v"
        # WAN 2.5 has different pricing
        cost = 0.02 * duration  # ~$0.06 for 3s
    elif "gemini" in video_model.lower():
        video_url = await generate_with_gemini(prompt, duration, resolution, aspect_ratio)
        actual_model = "google/gemini"
        cost = quality_config["cost_per_second"] * duration
    else:
        # Default to Seedance
        video_url = await generate_with_seedance(prompt, duration, resolution, aspect_ratio)
        actual_model = "bytedance/seedance-1-pro-fast"
        cost = quality_config["cost_per_second"] * duration

    activity.logger.info(f"Video generated: {video_url}")
    activity.logger.info(f"Model: {actual_model}, Cost: ${cost:.3f}")

    return {
        "video_url": video_url,
        "quality": quality,
        "resolution": resolution,
        "duration": duration,
        "cost": cost,
        "model": actual_model,
        "prompt_used": prompt[:200]  # Return first 200 chars of prompt for debugging
    }


def generate_video_prompt(title: str, content: str, app: str) -> str:
    """
    Generate a video prompt based on article content.

    Creates a cinematic prompt that captures the essence of the article
    without attempting to include text (which AI video models struggle with).
    """
    # App-specific visual themes
    app_themes = {
        "placement": {
            "style": "corporate finance, modern office",
            "elements": "stock charts, business meetings, corporate headquarters",
            "mood": "professional, dynamic, successful"
        },
        "relocation": {
            "style": "travel, international, lifestyle",
            "elements": "cityscapes, airports, modern apartments, diverse cultures",
            "mood": "adventurous, hopeful, cosmopolitan"
        },
        "rainmaker": {
            "style": "sales, technology, growth",
            "elements": "dashboards, team celebrations, deal closings",
            "mood": "energetic, ambitious, winning"
        },
        "chief-of-staff": {
            "style": "executive, strategic, leadership",
            "elements": "boardrooms, strategy sessions, executive offices",
            "mood": "authoritative, organized, visionary"
        }
    }

    theme = app_themes.get(app, app_themes["placement"])

    # Extract key concepts from title
    title_clean = title.lower()

    # Generate contextual prompt
    prompt = f"""Cinematic {theme['style']} scene, {theme['mood']} atmosphere.
{theme['elements']}, natural lighting, shallow depth of field,
smooth camera movement, high production value, 4K quality"""

    # Add title-specific context
    if "visa" in title_clean or "immigration" in title_clean:
        prompt += ", passport stamps, international travel, new beginnings"
    elif "startup" in title_clean or "funding" in title_clean:
        prompt += ", startup office, investors meeting, growth charts"
    elif "tax" in title_clean or "finance" in title_clean:
        prompt += ", financial documents, calculator, professional consultation"
    elif "guide" in title_clean or "how to" in title_clean:
        prompt += ", step-by-step process, helpful visual metaphors"

    return prompt


async def generate_with_seedance(
    prompt: str,
    duration: int,
    resolution: str,
    aspect_ratio: str
) -> str:
    """Generate video using Seedance on Replicate."""

    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        raise ValueError("REPLICATE_API_TOKEN not set")

    activity.logger.info(f"Calling Seedance: {resolution}, {duration}s")

    output = replicate.run(
        "bytedance/seedance-1-pro-fast",
        input={
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "camera_fixed": False,  # Allow some camera movement for dynamism
            "fps": 24
        }
    )

    return output


async def generate_with_wan(
    prompt: str,
    duration: int,
    resolution: str,
    aspect_ratio: str
) -> str:
    """Generate video using WAN 2.5 on Replicate.

    WAN 2.5 has better text rendering and longer duration support.
    """

    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        raise ValueError("REPLICATE_API_TOKEN not set")

    # Map resolution to WAN 2.5 size format
    # WAN uses "width*height" format
    size_map = {
        "480p": "832*480",
        "720p": "1280*720",
    }
    size = size_map.get(resolution, "832*480")

    activity.logger.info(f"Calling WAN 2.5: {size}, {duration}s")

    output = replicate.run(
        "wan-video/wan-2.5-t2v",
        input={
            "size": size,
            "prompt": prompt,
            "duration": duration,
            "negative_prompt": "blurry, low quality, distorted, amateur, grainy",
            "enable_prompt_expansion": True
        }
    )

    # WAN returns a FileOutput object, get the URL
    if hasattr(output, 'url'):
        return output.url
    return str(output)


async def generate_with_gemini(
    prompt: str,
    duration: int,
    resolution: str,
    aspect_ratio: str
) -> str:
    """
    Generate video using Google Gemini.

    TODO: Implement when Gemini video API is available/integrated.
    Currently raises NotImplementedError.
    """
    raise NotImplementedError(
        "Gemini video generation not yet implemented. "
        "Use 'medium' or 'low' quality for now."
    )

    # Future implementation:
    # import google.generativeai as genai
    # genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    # ...


@activity.defn
async def get_video_cost_estimate(
    quality: str = "medium",
    duration: int = 3
) -> Dict[str, Any]:
    """
    Get cost estimate for video generation without actually generating.

    Useful for dashboard display and planning.
    """
    quality_config = VIDEO_QUALITY_MODELS.get(quality, VIDEO_QUALITY_MODELS["medium"])
    cost = quality_config["cost_per_second"] * duration

    return {
        "quality": quality,
        "duration": duration,
        "cost": cost,
        "model": quality_config["model"],
        "resolution": quality_config["resolution"],
        "description": quality_config["description"]
    }
