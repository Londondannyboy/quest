"""
FRESH VIDEO GENERATION - NO LEGACY VALIDATION

Simple activity: prompt → Seedance → video URL
No checks for "ACT 1", no structured prompt validation
Just generate the damn video!
"""

import os
import replicate
from temporalio import activity
from typing import Dict, Any


@activity.defn
async def generate_video_simple(
    prompt: str,
    duration: int = 12,
    resolution: str = "720p",
    aspect_ratio: str = "16:9",
) -> Dict[str, Any]:
    """
    Generate video with Seedance. ZERO validation logic.

    Takes a prompt, generates a video, returns URL. That's it.

    Args:
        prompt: Video generation prompt (no validation!)
        duration: Video length in seconds (default 12)
        resolution: Video resolution (default 720p)
        aspect_ratio: Aspect ratio (default 16:9)

    Returns:
        Dict with video_url, cost, duration
    """
    import time

    activity.logger.info(f"🎬 Generating {duration}s video at {resolution}")
    activity.logger.info(f"📝 Prompt ({len(prompt)} chars): {prompt[:100]}...")

    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        raise ValueError("REPLICATE_API_TOKEN not set")

    # Just send it to Seedance - no validation!
    client = replicate.Client(api_token=replicate_token)
    prediction = client.predictions.create(
        version="bytedance/seedance-1-pro-fast",
        input={
            "prompt": prompt.strip(),
            "duration": duration,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "camera_fixed": False,
            "fps": 24
        }
    )

    activity.logger.info(f"✅ Prediction created: {prediction.id}")

    # Poll with heartbeats
    max_wait = 300  # 5 minutes
    poll_interval = 5
    elapsed = 0

    while elapsed < max_wait:
        prediction.reload()
        activity.heartbeat(f"Status: {prediction.status}, elapsed: {elapsed}s")

        if prediction.status == "succeeded":
            video_url = prediction.output
            cost = 0.025 * duration  # $0.30 for 12s
            activity.logger.info(f"✅ Video generated after {elapsed}s: {video_url[:50]}...")
            activity.logger.info(f"💰 Cost: ${cost:.3f}")

            return {
                "video_url": video_url,
                "duration": duration,
                "cost": cost,
                "model": "bytedance/seedance-1-pro-fast",
                "resolution": resolution
            }

        elif prediction.status == "failed":
            raise RuntimeError(f"Seedance failed: {prediction.error}")

        elif prediction.status == "canceled":
            raise RuntimeError("Seedance canceled")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Seedance timed out after {max_wait}s")
