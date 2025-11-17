"""
Flux API Client for Direct BFL Integration

Supports Flux Kontext Pro and Max models for sequential image generation
with context chaining. Used for generating narrative-driven article images.

API Docs: https://docs.bfl.ai/
"""

import httpx
import asyncio
import cloudinary
import cloudinary.uploader
from temporalio import activity
from typing import Dict, Any, Optional, Literal
from enum import Enum

from src.utils.config import config


class FluxModel(str, Enum):
    """Available Flux models"""
    KONTEXT_PRO = "flux-kontext-pro"
    KONTEXT_MAX = "flux-kontext-max"
    PRO_ULTRA = "flux-pro-1.1-ultra"
    PRO = "flux-pro-1.1"


class FluxRegion(str, Enum):
    """Regional endpoints for lower latency"""
    GLOBAL = "https://api.bfl.ai/v1"
    EU = "https://api.eu.bfl.ai/v1"  # Prefer for European deployments
    US = "https://api.us.bfl.ai/v1"


class FluxAPIClient:
    """
    Client for Black Forest Labs Flux API.

    Handles:
    - Image generation with Kontext Pro/Max
    - Context chaining (image-to-image sequential generation)
    - Async polling for results
    - Cloudinary upload
    """

    def __init__(
        self,
        api_key: str,
        region: FluxRegion = FluxRegion.EU,
        timeout: int = 120
    ):
        """
        Initialize Flux API client.

        Args:
            api_key: BFL API key
            region: Regional endpoint (EU for lower latency from Europe)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = region.value
        self.timeout = timeout

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "x-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

    async def generate_image(
        self,
        prompt: str,
        model: FluxModel = FluxModel.KONTEXT_PRO,
        context_image_url: Optional[str] = None,
        aspect_ratio: str = "16:9",
        seed: Optional[int] = None,
        output_format: Literal["jpeg", "png"] = "jpeg",
        prompt_upsampling: bool = False,
        safety_tolerance: int = 2
    ) -> Dict[str, Any]:
        """
        Generate image with Flux Kontext.

        This is the core method for sequential storytelling:
        1. First image: No context_image_url (generates from prompt only)
        2. Subsequent images: Pass previous image URL as context_image_url

        Args:
            prompt: Text description following Kontext prompting guide
            model: Kontext Pro (faster) or Max (higher quality)
            context_image_url: URL of previous image for consistency (optional)
            aspect_ratio: Image dimensions (16:9, 4:3, 1:1, etc.)
            seed: For reproducibility (optional)
            output_format: jpeg (smaller) or png (higher quality)
            prompt_upsampling: Auto-enhance prompt (usually not needed)
            safety_tolerance: 0-6 scale, higher = less restrictive

        Returns:
            Dict with image_url, job_id, cost_estimate
        """
        endpoint = f"{self.base_url}/{model.value}"

        # Build request payload
        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "safety_tolerance": safety_tolerance,
            "prompt_upsampling": prompt_upsampling
        }

        # Add context image if provided (for sequential generation)
        if context_image_url:
            payload["input_image"] = context_image_url

        # Add seed if provided
        if seed is not None:
            payload["seed"] = seed

        activity.logger.info(
            f"Generating with {model.value}, context={'yes' if context_image_url else 'no'}"
        )
        activity.logger.info(f"Prompt: {prompt[:100]}...")

        try:
            # Submit generation request
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()

            data = response.json()

            job_id = data.get("id")
            polling_url = data.get("polling_url")

            if not job_id or not polling_url:
                raise ValueError("Missing id or polling_url in response")

            activity.logger.info(f"Job submitted: {job_id}")

            # Poll for completion
            image_url = await self._poll_for_result(polling_url)

            activity.logger.info(f"Image generated: {image_url}")

            return {
                "image_url": image_url,
                "job_id": job_id,
                "model": model.value,
                "success": True
            }

        except httpx.HTTPStatusError as e:
            activity.logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "image_url": None,
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            activity.logger.error(f"Generation failed: {e}")
            return {
                "image_url": None,
                "success": False,
                "error": str(e)
            }

    async def _poll_for_result(
        self,
        polling_url: str,
        poll_interval: int = 2,
        max_attempts: int = 60
    ) -> str:
        """
        Poll for generation result.

        Args:
            polling_url: Unique URL for this job
            poll_interval: Seconds between polls
            max_attempts: Max polling attempts (60 attempts × 2s = 2min timeout)

        Returns:
            Image URL

        Raises:
            TimeoutError: If max_attempts exceeded
            ValueError: If generation failed
        """
        for attempt in range(max_attempts):
            try:
                response = await self.client.get(polling_url)
                response.raise_for_status()

                data = response.json()
                status = data.get("status")

                if status == "Ready":
                    # Success!
                    result = data.get("result", {})
                    image_url = result.get("sample")

                    if not image_url:
                        raise ValueError("No image URL in Ready response")

                    return image_url

                elif status in ["Error", "Failed"]:
                    error_msg = data.get("error", "Unknown error")
                    raise ValueError(f"Generation failed: {error_msg}")

                # Still processing, wait and retry
                activity.logger.info(f"Status: {status}, attempt {attempt + 1}/{max_attempts}")
                await asyncio.sleep(poll_interval)

            except httpx.HTTPStatusError as e:
                activity.logger.error(f"Polling error: {e}")
                await asyncio.sleep(poll_interval)

        raise TimeoutError(f"Image generation timed out after {max_attempts} attempts")

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


@activity.defn
async def generate_flux_image(
    prompt: str,
    context_image_url: Optional[str] = None,
    aspect_ratio: str = "16:9",
    model: str = "kontext-pro",
    cloudinary_folder: str = "quest-images",
    cloudinary_public_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate image using Flux Kontext and upload to Cloudinary.

    This is the primary activity for sequential image generation.

    Args:
        prompt: Image generation prompt (follow Kontext prompting guide)
        context_image_url: Previous image URL for sequential consistency
        aspect_ratio: Image dimensions
        model: "kontext-pro" (faster) or "kontext-max" (better quality)
        cloudinary_folder: Folder for uploaded image
        cloudinary_public_id: Public ID (optional, auto-generated if None)

    Returns:
        Dict with cloudinary_url, flux_job_id, cost
    """
    activity.logger.info(
        f"Generating Flux image with model={model}, "
        f"context={'yes' if context_image_url else 'no'}"
    )

    # Validate configuration
    if not config.FLUX_API_KEY:
        activity.logger.error("FLUX_API_KEY not configured")
        return {
            "cloudinary_url": None,
            "success": False,
            "error": "FLUX_API_KEY not configured"
        }

    if not config.CLOUDINARY_URL:
        activity.logger.error("CLOUDINARY_URL not configured")
        return {
            "cloudinary_url": None,
            "success": False,
            "error": "CLOUDINARY_URL not configured"
        }

    # Map model string to enum
    model_map = {
        "kontext-pro": FluxModel.KONTEXT_PRO,
        "kontext-max": FluxModel.KONTEXT_MAX,
        "pro-ultra": FluxModel.PRO_ULTRA,
        "pro": FluxModel.PRO
    }

    flux_model = model_map.get(model, FluxModel.KONTEXT_PRO)

    try:
        # Initialize Flux client
        client = FluxAPIClient(
            api_key=config.FLUX_API_KEY,
            region=FluxRegion.EU  # Europe region for lower latency
        )

        # Generate image
        result = await client.generate_image(
            prompt=prompt,
            model=flux_model,
            context_image_url=context_image_url,
            aspect_ratio=aspect_ratio,
            output_format="jpeg",  # Smaller file size
            safety_tolerance=2
        )

        await client.close()

        if not result.get("success"):
            return {
                "cloudinary_url": None,
                "success": False,
                "error": result.get("error", "Unknown Flux API error")
            }

        flux_image_url = result["image_url"]
        job_id = result["job_id"]

        activity.logger.info(f"Flux image generated, uploading to Cloudinary...")

        # Upload to Cloudinary
        cloudinary.config(cloudinary_url=config.CLOUDINARY_URL)

        upload_result = cloudinary.uploader.upload(
            flux_image_url,
            folder=cloudinary_folder,
            public_id=cloudinary_public_id,
            overwrite=True,
            resource_type="image"
        )

        cloudinary_url = upload_result.get("secure_url")

        activity.logger.info(f"Uploaded to Cloudinary: {cloudinary_url}")

        # Estimate cost based on model
        # Note: Actual pricing from BFL docs (placeholder values)
        cost_map = {
            FluxModel.KONTEXT_PRO: 0.04,  # Estimate
            FluxModel.KONTEXT_MAX: 0.10,  # Estimate
            FluxModel.PRO_ULTRA: 0.055,
            FluxModel.PRO: 0.04
        }

        return {
            "cloudinary_url": cloudinary_url,
            "flux_image_url": flux_image_url,
            "flux_job_id": job_id,
            "cloudinary_public_id": upload_result.get("public_id"),
            "cost": cost_map.get(flux_model, 0.04),
            "model": model,
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"Flux image generation failed: {e}")
        return {
            "cloudinary_url": None,
            "success": False,
            "error": str(e)
        }
