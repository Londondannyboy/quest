"""
Flux Image Generation via Replicate

Uses Replicate API for Flux Kontext Pro/Max models with context chaining.
Supports sequential image generation for narrative-driven article images.
"""

import replicate
import cloudinary
import cloudinary.uploader
from temporalio import activity
from typing import Dict, Any, Optional

from src.utils.config import config


# Replicate model IDs for Flux Kontext
FLUX_MODELS = {
    "kontext-pro": "black-forest-labs/flux-kontext-pro",
    "kontext-max": "black-forest-labs/flux-kontext-max",
    "schnell": "black-forest-labs/flux-schnell",
    "pro": "black-forest-labs/flux-pro"
}


@activity.defn
async def generate_flux_image(
    prompt: str,
    context_image_url: Optional[str] = None,
    aspect_ratio: str = "16:9",
    model: str = "kontext-pro",
    cloudinary_folder: str = "quest-articles",
    cloudinary_public_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate image using Flux via Replicate, upload to Cloudinary.

    Supports context chaining for sequential storytelling:
    - First image: No context_image_url
    - Subsequent images: Pass previous image URL as context

    Args:
        prompt: Image generation prompt
        context_image_url: Previous image URL for context (Kontext Pro/Max only)
        aspect_ratio: Image dimensions (16:9, 4:3, 1:1, etc.)
        model: kontext-pro, kontext-max, schnell, or pro
        cloudinary_folder: Cloudinary folder for upload
        cloudinary_public_id: Custom public ID (optional)

    Returns:
        Dict with cloudinary_url, cost, success
    """
    activity.logger.info(f"Generating {model} image: {prompt[:100]}...")

    if not config.REPLICATE_API_TOKEN:
        activity.logger.error("REPLICATE_API_TOKEN not configured")
        return {
            "cloudinary_url": None,
            "cost": 0.0,
            "success": False,
            "error": "REPLICATE_API_TOKEN not configured"
        }

    if not config.CLOUDINARY_URL:
        activity.logger.error("CLOUDINARY_URL not configured")
        return {
            "cloudinary_url": None,
            "cost": 0.0,
            "success": False,
            "error": "CLOUDINARY_URL not configured"
        }

    try:
        # Configure Cloudinary
        cloudinary.config(cloudinary_url=config.CLOUDINARY_URL)

        # Get Replicate model ID
        model_id = FLUX_MODELS.get(model, FLUX_MODELS["kontext-pro"])

        # Build input based on model type
        if model in ["kontext-pro", "kontext-max"]:
            # Kontext models support context images
            input_params = {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "output_format": "jpg",
                "safety_tolerance": 2
            }

            # Add context image if provided
            if context_image_url:
                input_params["input_image"] = context_image_url
                activity.logger.info(f"Using context image: {context_image_url[:50]}...")

        else:
            # Standard Flux models (schnell, pro)
            # Convert aspect ratio to dimensions
            dimensions = {
                "16:9": (1344, 768),
                "4:3": (1024, 768),
                "1:1": (1024, 1024),
                "3:4": (768, 1024),
                "9:16": (768, 1344),
                "1200:630": (1200, 630)
            }
            width, height = dimensions.get(aspect_ratio, (1344, 768))

            input_params = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "num_outputs": 1
            }

            if model == "schnell":
                input_params["num_inference_steps"] = 4
                input_params["guidance_scale"] = 0

        # Generate image via Replicate
        activity.logger.info(f"Calling Replicate model: {model_id}")

        output = replicate.run(model_id, input=input_params)

        # Get image URL from output
        if isinstance(output, list) and len(output) > 0:
            image_url = str(output[0])
        elif hasattr(output, 'url'):
            image_url = str(output.url)
        else:
            image_url = str(output)

        activity.logger.info(f"Image generated: {image_url[:80]}...")

        # Upload to Cloudinary for persistence
        upload_params = {
            "folder": cloudinary_folder,
            "overwrite": True,
            "resource_type": "image"
        }

        if cloudinary_public_id:
            upload_params["public_id"] = cloudinary_public_id

        upload_result = cloudinary.uploader.upload(image_url, **upload_params)

        cloudinary_url = upload_result.get("secure_url")

        activity.logger.info(f"Uploaded to Cloudinary: {cloudinary_url}")

        # Estimate cost based on model
        cost_map = {
            "kontext-pro": 0.025,
            "kontext-max": 0.05,
            "schnell": 0.003,
            "pro": 0.055
        }

        return {
            "cloudinary_url": cloudinary_url,
            "cloudinary_public_id": upload_result.get("public_id"),
            "replicate_model": model_id,
            "cost": cost_map.get(model, 0.025),
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"Image generation failed: {e}")
        return {
            "cloudinary_url": None,
            "cost": 0.0,
            "success": False,
            "error": str(e)
        }
