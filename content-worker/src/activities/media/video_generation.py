"""
Video generation activity using Seedance (Replicate) or Gemini.
"""

import os
import replicate
from temporalio import activity
from typing import Dict, Any, Optional

# Quality tier configuration
# Default is 12 seconds (4 acts × 3 seconds) for 4-act video structure
VIDEO_QUALITY_MODELS = {
    "high": {
        "model": "google/gemini",  # TODO: Update with actual Gemini video model
        "resolution": "720p",
        "cost_per_second": 0.30,  # ~$3.60 for 12s
        "default_duration": 12,
        "description": "Premium quality with perfect text rendering"
    },
    "medium": {
        "model": "bytedance/seedance-1-pro-fast",
        "resolution": "720p",
        "cost_per_second": 0.025,  # $0.30 for 12s
        "default_duration": 12,
        "description": "Good quality, balanced cost - 4-act structure"
    },
    "low": {
        "model": "bytedance/seedance-1-pro-fast",
        "resolution": "720p",  # Upgraded from 480p for better quality
        "cost_per_second": 0.025,  # $0.30 for 12s (720p pricing)
        "default_duration": 12,
        "description": "Good quality 720p, 4-act structure - recommended"
    }
}

# 4-ACT VIDEO CONFIGURATION
# Each act is 3 seconds, total 12 seconds
# Act timestamps for thumbnail extraction
FOUR_ACT_CONFIG = {
    "duration": 12,
    "acts": 4,
    "act_duration": 3,
    "act_timestamps": {
        "act_1": {"start": 0, "mid": 1.5, "end": 3},
        "act_2": {"start": 3, "mid": 4.5, "end": 6},
        "act_3": {"start": 6, "mid": 7.5, "end": 9},
        "act_4": {"start": 9, "mid": 10.5, "end": 12}
    },
    "thumbnail_times": {
        "sections": [1.5, 4.5, 7.5, 10.5],  # Mid-point of each act
        "faq": [1.0, 4.0, 7.0, 10.0],  # Slightly offset for variety
        "hero": 10.5,  # Final act - resolution/payoff
        "backgrounds": [10.0, 5.0]
    }
}


@activity.defn
async def generate_four_act_video(
    title: str,
    content: str,
    app: str = "placement",
    quality: str = "low",  # Default to low for cost-effective 4-act videos ($0.18)
    duration: int = 12,  # Default to 12s for 4-act structure
    aspect_ratio: str = "16:9",
    video_model: str = "seedance",
    video_prompt: Optional[str] = None,
    reference_image: Optional[str] = None  # Character reference for visual consistency
) -> Dict[str, Any]:
    """
    Generate a video for an article using AI video generation.

    Default is 12-second 4-act video structure:
    - Act 1 (0-3s): Setup
    - Act 2 (3-6s): Opportunity
    - Act 3 (6-9s): Journey
    - Act 4 (9-12s): Payoff

    Args:
        title: Article title
        content: Article content (used to generate prompt)
        app: Application name (placement, relocation, etc.)
        quality: Video quality tier (high, medium, low) - default low for 4-act
        duration: Video duration in seconds (default 12 for 4-act)
        aspect_ratio: Video aspect ratio (default 16:9)
        video_model: Model to use (seedance, wan-2.5)
        video_prompt: Custom prompt (if None, auto-generated)
        reference_image: URL to reference image for character consistency

    Returns:
        Dict with video_url, quality, duration, cost, four_act_config
    """
    # Get quality config
    quality_config = VIDEO_QUALITY_MODELS.get(quality, VIDEO_QUALITY_MODELS["low"])

    # Determine act structure based on duration
    is_four_act = duration == 12
    act_label = "4 acts" if is_four_act else f"{duration}s single"

    activity.logger.info(f"Generating video for: {title[:50]}...")
    activity.logger.info(f"Model: {video_model}, Quality: {quality}, Duration: {duration}s ({act_label})")
    activity.logger.info(f"✓ Received parameters: app={app}, aspect_ratio={aspect_ratio}")
    activity.logger.info(f"✓ video_prompt: {'PROVIDED' if video_prompt else 'MISSING (will fail for 4-act)'}")

    # Get quality configuration
    quality_config = VIDEO_QUALITY_MODELS.get(quality, VIDEO_QUALITY_MODELS["medium"])
    resolution = quality_config["resolution"]

    # For 12-second 4-act videos: REQUIRE proper 4-act structured prompt
    # No fallback to legacy generate_video_prompt() - fail hard if prompt is missing/invalid
    if is_four_act:
        if not video_prompt or not video_prompt.strip():
            error_msg = (
                "❌ 4-ACT VIDEO FAILED: No structured prompt provided.\n"
                "4-act video REQUIRES a prompt from generate_four_act_video_prompt.\n"
                "ROOT CAUSE: Article likely missing four_act_content or four_act_visual_hint in sections.\n"
                "FIX: Check JSON extraction from Sonnet response. Ensure STRUCTURED DATA section is parsed."
            )
            activity.logger.error(error_msg)
            raise ValueError(error_msg)

        prompt = video_prompt.strip()

        # Validate 4-act structure exists in prompt
        required_acts = ["ACT 1", "ACT 2", "ACT 3", "ACT 4"]
        missing_acts = [act for act in required_acts if act not in prompt]

        if missing_acts:
            error_msg = (
                f"❌ 4-ACT VIDEO FAILED: Malformed prompt - missing {missing_acts}.\n"
                f"Prompt must contain ACT 1, ACT 2, ACT 3, ACT 4 structure.\n"
                f"ROOT CAUSE: generate_four_act_video_prompt didn't extract all 4 sections.\n"
                f"Received: {prompt[:300]}..."
            )
            activity.logger.error(error_msg)
            raise ValueError(error_msg)

        activity.logger.info(f"✓ 4-act prompt validated: all 4 acts present")
        activity.logger.info(f"4-act prompt: {prompt[:150]}...")
    else:
        # Non-4-act videos (company videos use generate_company_video instead)
        if video_prompt and video_prompt.strip():
            prompt = video_prompt.strip()
            activity.logger.info(f"Using custom prompt: {prompt[:100]}...")
        else:
            raise ValueError(
                f"Video prompt required. For articles use generate_four_act_video with 4-act prompt. "
                f"For companies use generate_company_video."
            )

    # Log reference image if provided
    if reference_image:
        activity.logger.info(f"✓ Reference image provided for character consistency: {reference_image[:60]}...")

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
        # Default to Seedance - pass reference image for character consistency
        video_url = await generate_with_seedance(prompt, duration, resolution, aspect_ratio, reference_image)
        actual_model = "bytedance/seedance-1-pro-fast"
        cost = quality_config["cost_per_second"] * duration

    activity.logger.info(f"Video generated: {video_url}")
    activity.logger.info(f"Model: {actual_model}, Cost: ${cost:.3f}")

    # Include 4-act config for thumbnail extraction
    four_act_config = FOUR_ACT_CONFIG if duration == 12 else None

    return {
        "video_url": video_url,
        "quality": quality,
        "resolution": resolution,
        "duration": duration,
        "cost": cost,
        "model": actual_model,
        "prompt_used": prompt[:200],  # Return first 200 chars of prompt for debugging
        "four_act_config": four_act_config,  # For thumbnail extraction
        "acts": 4 if duration == 12 else 1
    }


@activity.defn
async def generate_company_video(
    company_name: str,
    app: str = "placement",
    quality: str = "low",
    duration: int = 3,
    aspect_ratio: str = "16:9",
    video_model: str = "seedance",
    video_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a simple branding video for a company profile.

    Creates a short 3-5 second video focused on company identity/logo.
    NOT a 4-act narrative - just a clean professional visual.

    Args:
        company_name: Company name for branding
        app: Application name (placement, relocation, etc.)
        quality: Video quality tier (high, medium, low)
        duration: Video duration in seconds (default 3s)
        aspect_ratio: Video aspect ratio (default 16:9)
        video_model: Model to use (seedance, wan-2.5)
        video_prompt: Custom prompt (if None, auto-generated)

    Returns:
        Dict with video_url, quality, duration, cost
    """
    activity.logger.info(f"Generating company video for: {company_name}")
    activity.logger.info(f"Model: {video_model}, Quality: {quality}, Duration: {duration}s")

    # Get quality config
    quality_config = VIDEO_QUALITY_MODELS.get(quality, VIDEO_QUALITY_MODELS["low"])
    resolution = quality_config["resolution"]

    # Use custom prompt if provided, otherwise generate simple branding prompt
    if video_prompt and video_prompt.strip():
        prompt = video_prompt.strip()
        activity.logger.info(f"Using custom prompt: {prompt[:100]}...")
    else:
        # Simple company branding prompt
        prompt = f"""Professional corporate identity reveal. Clean modern aesthetic, {company_name} company branding.
Elegant motion graphics, subtle light rays, premium quality feel.
Smooth camera movement, shallow depth of field, high production value.
CRITICAL: NO text, NO words, NO letters - purely visual brand essence."""
        activity.logger.info(f"Generated branding prompt: {prompt[:100]}...")

    # Generate video
    if video_model == "wan-2.5":
        video_url = await generate_with_wan(prompt, duration, resolution, aspect_ratio)
        actual_model = "wan-video/wan-2.5-t2v"
        cost = 0.02 * duration
    else:
        video_url = await generate_with_seedance(prompt, duration, resolution, aspect_ratio)
        actual_model = "bytedance/seedance-1-pro-fast"
        cost = quality_config["cost_per_second"] * duration

    activity.logger.info(f"Company video generated: {video_url}")
    activity.logger.info(f"Model: {actual_model}, Cost: ${cost:.3f}")

    return {
        "video_url": video_url,
        "quality": quality,
        "resolution": resolution,
        "duration": duration,
        "cost": cost,
        "model": actual_model,
        "prompt_used": prompt[:200]
    }


def transform_prompt_for_seedance(prompt: str) -> str:
    """
    Transform a universal prompt for Seedance model.

    For 4-act prompts (already well-crafted): pass through unchanged
    For auto-generated prompts: add motion adverbs and no-text instruction
    """
    # 4-act prompts are already optimized with no_text_rule - don't mangle them
    if "ACT 1" in prompt and "ACT 4" in prompt:
        # Well-crafted 4-act prompt, return as-is
        return prompt.strip()

    # For auto-generated prompts only:
    # Ensure motion adverbs are present
    motion_adverbs = ['slowly', 'gently', 'gradually', 'quickly', 'softly', 'dramatically']
    has_adverb = any(adv in prompt.lower() for adv in motion_adverbs)

    if not has_adverb:
        prompt = prompt.replace('camera ', 'camera moves slowly ')

    # Add no-text instruction for auto-generated prompts
    seedance_prompt = f"{prompt.strip()} CRITICAL: Absolutely NO text, NO words, NO letters, NO typography - purely visual only."

    return seedance_prompt


def transform_prompt_for_wan(prompt: str) -> tuple[str, str]:
    """
    Transform a universal prompt for WAN 2.5 model.

    WAN 2.5 specific optimizations:
    - Supports negative prompts (return as separate parameter)
    - Excels at depth/parallax - add foreground/background hints if missing
    - 80-120 words optimal
    - Film terminology works well (Kodak Portra, anamorphic, etc.)
    - Can handle single-word text like "Quest"

    Returns:
        Tuple of (positive_prompt, negative_prompt)
    """
    # WAN 2.5 negative prompt for quality control
    negative_prompt = "blurry, low quality, distorted, amateur, grainy, shaky, text, watermark, logo, multiple words, sentences"

    # Add depth hint if not present (WAN excels at parallax)
    depth_keywords = ['foreground', 'background', 'depth', 'parallax', 'layers']
    has_depth = any(kw in prompt.lower() for kw in depth_keywords)

    if not has_depth:
        # Add subtle depth instruction
        prompt = f"{prompt.strip()} Subtle depth with foreground elements soft-focused."

    # Add single-word text allowance for Q branding if desired
    wan_prompt = f"{prompt.strip()} Only single-word text like 'Q' is allowed."

    return wan_prompt, negative_prompt


def generate_video_prompt(title: str, content: str, app: str) -> str:
    """
    DEPRECATED: Do not use this function.

    This legacy function generates single-block prompts that don't work with
    the 4-act video framework. Articles MUST use generate_four_act_video_prompt
    to extract structured prompts from article sections.

    For company videos, use generate_company_video instead.

    This function is kept only for backwards compatibility with old tests.
    """
    import warnings
    warnings.warn(
        "generate_video_prompt is DEPRECATED. Use generate_four_act_video_prompt for articles "
        "or generate_company_video for company profiles.",
        DeprecationWarning,
        stacklevel=2
    )
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
        "pe_news": {
            "style": "investment, deal-making, finance",
            "elements": "modern boardroom, handshakes, deal negotiations, growth charts",
            "mood": "ambitious, strategic, triumphant"
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

    # Analyze content sentiment (simple keyword analysis)
    content_lower = content.lower()
    sentiment_keywords = {
        "positive": ["growth", "success", "gain", "profit", "rise", "up", "strong", "opportunity", "expansion"],
        "negative": ["decline", "loss", "down", "challenge", "risk", "fall", "weak", "downturn"],
        "neutral": ["report", "announce", "statement", "update", "change"]
    }

    sentiment = "neutral"
    for category, keywords in sentiment_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            sentiment = category
            break

    # Sentiment-based mood adjustment
    if sentiment == "positive":
        theme_mood = theme['mood'] + ", optimistic, upward momentum"
    elif sentiment == "negative":
        theme_mood = theme['mood'] + ", analytical, problem-solving focus"
    else:
        theme_mood = theme['mood']

    # Extract key concepts from title for context
    title_clean = title.lower()

    # Generate contextual prompt with Q branding
    prompt = f"""Cinematic {theme['style']} scene, {theme_mood} atmosphere.
{theme['elements']}, natural lighting, shallow depth of field,
smooth camera movement, high production value, 4K quality.
Background: kinetic white illuminated "Q" letter in large capital format,
subtly glowing and moving dynamically behind the main action. Q branding
serves as professional backdrop without overwhelming the scene."""

    # Add title-specific context
    if "visa" in title_clean or "immigration" in title_clean:
        prompt += ", passport stamps, international travel, new beginnings"
    elif "startup" in title_clean or "funding" in title_clean:
        prompt += ", startup office, investors meeting, growth charts"
    elif "tax" in title_clean or "finance" in title_clean or "investment" in title_clean or "deal" in title_clean:
        prompt += ", financial documents, calculator, professional consultation, deal negotiation"
    elif "guide" in title_clean or "how to" in title_clean:
        prompt += ", step-by-step process, helpful visual metaphors"
    elif "private equity" in title_clean or "pe " in title_clean:
        prompt += ", investment office, deal closing, acquisition celebration"

    return prompt


async def generate_with_seedance(
    prompt: str,
    duration: int,
    resolution: str,
    aspect_ratio: str,
    reference_image: Optional[str] = None
) -> str:
    """Generate video using Seedance on Replicate with heartbeats.

    Note: Seedance struggles with text rendering - only single words work reliably.
    Uses model-specific prompt transformation for optimal results.

    If reference_image is provided, uses image-to-video mode for character consistency.
    """
    import time

    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        raise ValueError("REPLICATE_API_TOKEN not set")

    # Apply Seedance-specific prompt transformation
    seedance_prompt = transform_prompt_for_seedance(prompt)

    activity.logger.info(f"Calling Seedance: {resolution}, {duration}s")
    activity.logger.info(f"Transformed prompt: {seedance_prompt[:100]}...")

    # Build input parameters
    input_params = {
        "prompt": seedance_prompt,
        "duration": duration,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "camera_fixed": False,
        "fps": 24
    }

    # Add reference image for character consistency (image-to-video mode)
    if reference_image:
        activity.logger.info(f"Using reference image for character consistency")
        input_params["image"] = reference_image

    # Create prediction (non-blocking)
    client = replicate.Client(api_token=replicate_token)
    prediction = client.predictions.create(
        model="bytedance/seedance-1-pro-fast",
        input=input_params
    )

    activity.logger.info(f"Prediction created: {prediction.id}")

    # Poll with heartbeats
    max_wait = 600  # 10 minutes max
    poll_interval = 5  # Check every 5 seconds
    elapsed = 0

    while elapsed < max_wait:
        prediction.reload()
        activity.heartbeat(f"Status: {prediction.status}, elapsed: {elapsed}s")

        if prediction.status == "succeeded":
            activity.logger.info(f"Video generation succeeded after {elapsed}s")
            return prediction.output
        elif prediction.status == "failed":
            raise RuntimeError(f"Seedance generation failed: {prediction.error}")
        elif prediction.status == "canceled":
            raise RuntimeError("Seedance generation was canceled")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Seedance generation timed out after {max_wait}s")


async def generate_with_wan(
    prompt: str,
    duration: int,
    resolution: str,
    aspect_ratio: str
) -> str:
    """Generate video using WAN 2.5 on Replicate with heartbeats.

    WAN 2.5 specific strengths:
    - Excellent depth/parallax effects
    - Supports negative prompts for quality control
    - 80-120 word prompts optimal
    - Film terminology (Kodak Portra, anamorphic) works well
    - Can handle single-word text like "Quest"
    """
    import time

    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        raise ValueError("REPLICATE_API_TOKEN not set")

    # Map resolution to WAN 2.5 size format
    size_map = {
        "480p": "832*480",
        "720p": "1280*720",
    }
    size = size_map.get(resolution, "832*480")

    # Apply WAN 2.5-specific prompt transformation
    wan_prompt, negative_prompt = transform_prompt_for_wan(prompt)

    activity.logger.info(f"Calling WAN 2.5: {size}, {duration}s")
    activity.logger.info(f"Transformed prompt: {wan_prompt[:100]}...")
    activity.logger.info(f"Negative prompt: {negative_prompt[:60]}...")

    # Create prediction (non-blocking)
    # WAN 2.5 version from https://replicate.com/wan-video/wan-2.5-t2v
    client = replicate.Client(api_token=replicate_token)
    prediction = client.predictions.create(
        version="39ca1e5fd0fd12ca1f71bebef447273394a0b2a6feaf3e3f80e42e3c23f85fa2",
        input={
            "size": size,
            "prompt": wan_prompt,
            "duration": duration,
            "negative_prompt": negative_prompt,
            "enable_prompt_expansion": True  # Let WAN expand intent automatically
        }
    )

    activity.logger.info(f"Prediction created: {prediction.id}")

    # Poll with heartbeats
    max_wait = 600  # 10 minutes max
    poll_interval = 5
    elapsed = 0

    while elapsed < max_wait:
        prediction.reload()
        activity.heartbeat(f"Status: {prediction.status}, elapsed: {elapsed}s")

        if prediction.status == "succeeded":
            activity.logger.info(f"WAN video generation succeeded after {elapsed}s")
            output = prediction.output
            # WAN returns a FileOutput object, get the URL
            if hasattr(output, 'url'):
                return output.url
            return str(output)
        elif prediction.status == "failed":
            raise RuntimeError(f"WAN generation failed: {prediction.error}")
        elif prediction.status == "canceled":
            raise RuntimeError("WAN generation was canceled")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"WAN generation timed out after {max_wait}s")


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


@activity.defn
async def generate_sequential_content_videos(
    article_slug: str,
    title: str,
    content: str,
    app: str,
    context_gif_url: str,
    video_prompts: list,
    quality: str = "medium",
    duration: int = 3,
    aspect_ratio: str = "16:9"
) -> Dict[str, Any]:
    """
    Generate sequential content videos using the hero video's GIF as visual context.

    Each video uses the previous video's style for consistency, starting from
    the context GIF. This creates a visually cohesive set of videos that tell
    different parts of the story.

    Args:
        article_slug: Article slug for logging
        title: Article title
        content: Article content for prompt generation
        app: Application name
        context_gif_url: GIF URL from hero video (starting context)
        video_prompts: List of prompts for each video (from section analysis)
        quality: Video quality tier
        duration: Duration per video in seconds
        aspect_ratio: Video aspect ratio

    Returns:
        Dict with video URLs, costs, and metadata
    """
    import time

    activity.logger.info(f"Generating {len(video_prompts)} sequential videos for: {article_slug}")
    activity.logger.info(f"Using context GIF: {context_gif_url[:60]}...")

    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        raise ValueError("REPLICATE_API_TOKEN not set")

    client = replicate.Client(api_token=replicate_token)
    quality_config = VIDEO_QUALITY_MODELS.get(quality, VIDEO_QUALITY_MODELS["medium"])
    resolution = quality_config["resolution"]

    videos = []
    total_cost = 0.0
    current_context = context_gif_url  # Start with the hero video's GIF

    for i, prompt in enumerate(video_prompts[:4]):  # Max 4 content videos
        activity.logger.info(f"Generating video {i+1}/{len(video_prompts)}: {prompt[:60]}...")

        # Apply Seedance-specific prompt transformation
        seedance_prompt = transform_prompt_for_seedance(prompt)
        activity.logger.info(f"Transformed prompt: {seedance_prompt[:80]}...")

        try:
            # Use image-to-video mode with context
            prediction = client.predictions.create(
                model="bytedance/seedance-1-pro-fast",
                input={
                    "prompt": seedance_prompt,
                    "duration": duration,
                    "resolution": resolution,
                    "aspect_ratio": aspect_ratio,
                    "camera_fixed": False,
                    "fps": 24,
                    "image": current_context  # Use previous video's GIF as context!
                }
            )

            activity.logger.info(f"Video {i+1} prediction: {prediction.id}")

            # Poll with heartbeats
            max_wait = 300  # 5 minutes per video
            poll_interval = 5
            elapsed = 0

            while elapsed < max_wait:
                prediction.reload()
                activity.heartbeat(f"Video {i+1}: {prediction.status}, {elapsed}s")

                if prediction.status == "succeeded":
                    video_url = prediction.output
                    cost = quality_config["cost_per_second"] * duration
                    total_cost += cost

                    videos.append({
                        "index": i + 1,
                        "video_url": video_url,
                        "prompt": prompt[:200],
                        "cost": cost
                    })

                    activity.logger.info(f"Video {i+1} generated: {video_url[:60]}...")

                    # Update context for next video (this video's URL will be processed by Mux later)
                    # For now, we keep using the original GIF for consistency
                    # In future, we could extract GIF from each video for true chaining
                    break

                elif prediction.status == "failed":
                    activity.logger.error(f"Video {i+1} failed: {prediction.error}")
                    break
                elif prediction.status == "canceled":
                    activity.logger.error(f"Video {i+1} canceled")
                    break

                time.sleep(poll_interval)
                elapsed += poll_interval
            else:
                activity.logger.error(f"Video {i+1} timed out after {max_wait}s")

        except Exception as e:
            activity.logger.error(f"Video {i+1} generation failed: {e}")
            continue

    activity.logger.info(f"Generated {len(videos)} videos, total cost: ${total_cost:.3f}")

    return {
        "videos": videos,
        "videos_generated": len(videos),
        "total_cost": total_cost,
        "context_gif_used": context_gif_url,
        "model": "bytedance/seedance-1-pro-fast"
    }
