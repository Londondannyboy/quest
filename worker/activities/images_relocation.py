"""
Relocation Image Generation Activity

Simple, hardcoded travel/lifestyle imagery.
No config dependencies - just works.
"""

import os
import asyncio
from temporalio import activity
from typing import Dict
import replicate
import cloudinary
import cloudinary.uploader


# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


@activity.defn(name="generate_relocation_images")
async def generate_relocation_images(
    article_id: str,
    article_title: str,
    article_angle: str
) -> Dict[str, str]:
    """
    Generate 6 travel/lifestyle images for Relocation articles

    Simple, hardcoded prompts - no config loading.
    This is the simple approach that worked before.

    Args:
        article_id: Article ID for linking
        article_title: Article title for context
        article_angle: Article angle for image generation

    Returns:
        Dict with Cloudinary URLs for hero, featured, content, content2, content3, content4 images
    """
    activity.logger.info(f"🎨 Generating RELOCATION images: {article_title[:50]}")

    # Check API keys
    if not os.getenv("REPLICATE_API_TOKEN"):
        activity.logger.warning("⚠️  REPLICATE_API_TOKEN not set")
        return {"hero": None, "featured": None, "content": None, "content2": None, "content3": None, "content4": None}

    if not os.getenv("CLOUDINARY_CLOUD_NAME"):
        activity.logger.warning("⚠️  Cloudinary not configured")
        return {"hero": None, "featured": None, "content": None, "content2": None, "content3": None, "content4": None}

    try:
        # Simple, hardcoded prompts - Travel/lifestyle style
        prompts = {
            "hero": f"Vibrant travel photography, {article_title}, lifestyle scene, welcoming atmosphere, professional travel photography, city life, warm natural lighting, diverse people, modern urban environment",
            "featured": f"Travel destination imagery, {article_angle}, aspirational photography, golden hour lighting, cultural authenticity, welcoming atmosphere",
            "content": f"Practical lifestyle scene, {article_title}, authentic photography, real-world scenarios, natural lighting, helpful realistic depiction",
            "content2": f"Community and culture, {article_angle}, local lifestyle photography, welcoming neighborhood atmosphere, authentic daily life scenes",
            "content3": f"Local amenities and services, {article_title}, practical everyday life photography, neighborhood facilities, community resources, helpful visual guide",
            "content4": f"Housing and accommodation, {article_angle}, residential photography, home interiors and exteriors, comfortable living spaces, welcoming environment"
        }

        activity.logger.info("📸 Generating images with Replicate...")

        # Generate all images
        replicate_urls = {}
        for purpose, prompt in prompts.items():
            try:
                activity.logger.info(f"   Generating {purpose} image...")

                output = replicate.run(
                    "ideogram-ai/ideogram-v3-turbo",
                    input={
                        "prompt": prompt,
                        "aspect_ratio": "16:9" if purpose == "hero" else ("3:2" if purpose == "featured" else "4:3"),
                        "magic_prompt_option": "Auto",
                        "style_type": "General"
                    }
                )

                # Handle output
                if isinstance(output, str):
                    url = output
                elif isinstance(output, list) and len(output) > 0:
                    url = str(output[0])
                elif hasattr(output, 'url'):
                    url = output.url
                else:
                    url = str(output)

                activity.logger.info(f"   ✅ Generated {purpose}: {url[:60]}...")
                replicate_urls[purpose] = url

            except Exception as e:
                activity.logger.error(f"   ❌ Failed {purpose}: {e}")
                replicate_urls[purpose] = None

        # Upload to Cloudinary
        activity.logger.info("☁️  Uploading to Cloudinary...")

        cloudinary_urls = {}
        for purpose, url in replicate_urls.items():
            if url:
                try:
                    activity.logger.info(f"   Uploading {purpose}...")

                    result = await asyncio.to_thread(
                        cloudinary.uploader.upload,
                        url,
                        folder="quest-articles",
                        public_id=f"relocation_{purpose}_{article_id}",
                        overwrite=True,
                        resource_type="image"
                    )

                    cloudinary_urls[purpose] = result["secure_url"]
                    activity.logger.info(f"   ✅ Uploaded {purpose}")

                except Exception as e:
                    activity.logger.error(f"   ❌ Upload failed {purpose}: {e}")
                    cloudinary_urls[purpose] = None
            else:
                cloudinary_urls[purpose] = None

        activity.logger.info(f"✅ Relocation images complete: {len([u for u in cloudinary_urls.values() if u])}/6 successful")
        return cloudinary_urls

    except Exception as e:
        import traceback
        activity.logger.error(f"❌ Relocation image generation failed: {e}")
        activity.logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return {"hero": None, "featured": None, "content": None, "content2": None, "content3": None, "content4": None}
