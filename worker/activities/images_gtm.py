"""
GTM Image Generation Activity

Executive-focused, sophisticated imagery with "GTM" branding.
Tailored for C-suite and organizational leadership content.
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


@activity.defn(name="generate_gtm_images")
async def generate_gtm_images(
    article_id: str,
    article_title: str,
    article_angle: str
) -> Dict[str, str]:
    """
    Generate 6 executive-focused images for GTM articles

    All images include "GTM" branding in the bottom left corner.
    Sophisticated C-suite aesthetic with professional executive themes.

    Args:
        article_id: Article ID for linking
        article_title: Article title for context
        article_angle: Article angle for image generation

    Returns:
        Dict with Cloudinary URLs for hero, featured, content, content2, content3, content4 images
    """
    activity.logger.info(f"🎨 Generating GTM images: {article_title[:50]}")

    # Check API keys
    if not os.getenv("REPLICATE_API_TOKEN"):
        activity.logger.warning("⚠️  REPLICATE_API_TOKEN not set")
        return {"hero": None, "featured": None, "content": None, "content2": None, "content3": None, "content4": None}

    if not os.getenv("CLOUDINARY_CLOUD_NAME"):
        activity.logger.warning("⚠️  Cloudinary not configured")
        return {"hero": None, "featured": None, "content": None, "content2": None, "content3": None, "content4": None}

    try:
        # Executive-focused prompts with "GTM" branding
        prompts = {
            "hero": f"""Professional executive concept illustration, {article_title}, sophisticated C-suite style,
modern clean design with leadership motifs, executive boardroom aesthetic, high-quality business photography,
refined color palette (deep navy, charcoal, platinum, subtle gold accents), strategic visualization elements,
minimalist sophisticated composition, executive office or modern boardroom background.
IMPORTANT: Include elegant text 'GTM' in bottom left corner in refined sans-serif font, white or light gray color""",

            "featured": f"""Strategic visualization, {article_angle}, clean modern professional design,
executive leadership aesthetic, elegant charts or conceptual diagrams, sophisticated corporate color scheme,
high-contrast executive presentation style, C-suite intelligence aesthetic.
IMPORTANT: Include text 'GTM' in bottom left corner in professional font, clearly visible""",

            "content": f"""Professional executive imagery, {article_title}, sophisticated corporate photography,
modern C-suite environment or executive workspace, refined lighting and composition,
contemporary leadership aesthetic, executives in strategic discussion or modern corporate headquarters.
IMPORTANT: Include text 'GTM' in bottom left corner, white text on subtle dark overlay""",

            "content2": f"""Executive leadership setting, {article_angle}, modern boardroom or executive office,
professional corporate atmosphere, global business leadership imagery, sophisticated meeting environment,
strategic planning aesthetic, high-level organizational setting.
IMPORTANT: Include 'GTM' text in bottom left corner in elegant font""",

            "content3": f"""C-suite collaboration and strategy, {article_title}, professional executive team environment,
modern leadership setting, strategic planning atmosphere, sophisticated corporate space,
organizational effectiveness visualization, refined business aesthetic.
IMPORTANT: Include 'GTM' branding in bottom left corner in professional style""",

            "content4": f"""Executive innovation and organizational leadership, {article_angle}, modern executive workspace,
strategic technology and data visualization, professional leadership environment,
sophisticated organizational setting, contemporary C-suite aesthetic, strategic digital transformation imagery.
IMPORTANT: Include text 'GTM' in bottom left corner, clean professional typography"""
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
                        public_id=f"gtm_{purpose}_{article_id}",
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

        activity.logger.info(f"✅ GTM images complete: {len([u for u in cloudinary_urls.values() if u])}/6 successful")
        return cloudinary_urls

    except Exception as e:
        import traceback
        activity.logger.error(f"❌ GTM image generation failed: {e}")
        activity.logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return {"hero": None, "featured": None, "content": None, "content2": None, "content3": None, "content4": None}
