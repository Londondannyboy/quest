"""
Media Prompt Generation - Separate step after article generation

Generates clean, focused video and image prompts based on article title/topic.
Much more reliable than extracting from article content.
"""

from temporalio import activity
from typing import Dict, Any, List
import anthropic

from src.utils.config import config
from src.config.app_config import APP_CONFIGS


@activity.defn
async def generate_media_prompts(
    title: str,
    topic: str,
    app: str,
    num_image_prompts: int = 4
) -> Dict[str, Any]:
    """
    Generate video and image prompts for an article.

    Called AFTER article generation as a separate step.
    Returns clean prompts ready for video/image generation.

    Args:
        title: Article title
        topic: Original topic/subject
        app: Application (relocation, placement, etc.)
        num_image_prompts: Number of section image prompts to generate (default 4)

    Returns:
        {
            "video_prompt": str,  # FEATURED/hero video prompt (80-120 words)
            "image_prompts": List[str],  # Section image prompts
            "success": bool,
            "cost": float
        }
    """
    activity.logger.info(f"Generating media prompts for: {title}")

    # Get app config for styling
    app_config = APP_CONFIGS.get(app)
    if app_config:
        media_style = app_config.media_style
        media_style_details = app_config.media_style_details
    else:
        media_style = "Cinematic, professional, high production value"
        media_style_details = "High quality, visually compelling imagery."

    system_prompt = f"""You are a visual storytelling expert creating prompts for AI video and image generation.

APP STYLE: {media_style}
DETAILS: {media_style_details}

Generate prompts that are:
1. SPECIFIC to the topic and location (not generic)
2. Cinematic with clear camera movements and lighting
3. 80-120 words each (optimal for video models)
4. Varied in perspective and composition

PROMPT FORMULA:
[Subject + Description] + [Scene + Environment] + [Motion + Action] + [Camera Movement] + [Aesthetic/Style]

CAMERA LANGUAGE:
- Push/Dolly: "camera pushes in slowly", "dolly out to reveal"
- Pan/Tilt: "pan left across scene", "tilt up to sky"
- Tracking: "camera follows closely", "tracks alongside subject"
- Orbital: "orbits smoothly around subject"
- Crane: "crane up dramatically"

MOTION DESCRIPTORS:
- Always include movement: "slowly", "gently", "dramatically"
- Sequential actions: "opens laptop, takes sip of coffee, looks up and smiles"
- Describe what's happening, not static scenes

LIGHTING & COLOR:
- "golden hour warm light", "soft morning glow"
- "teal-and-orange color grade", "warm amber tones"
- "shallow depth of field", "cinematic widescreen"

OUTPUT FORMAT (JSON):
{{
  "video_prompt": "Your 80-120 word cinematic prompt for hero video...",
  "image_prompts": [
    "Section 1 prompt...",
    "Section 2 prompt...",
    "Section 3 prompt...",
    "Section 4 prompt..."
  ]
}}

Return ONLY valid JSON, no markdown or explanations."""

    user_prompt = f"""Generate media prompts for this article:

TITLE: {title}
TOPIC: {topic}

Create:
1. ONE video_prompt (80-120 words) - the defining visual moment, cinematic and dynamic
2. {num_image_prompts} image_prompts - varied perspectives covering different aspects

Make prompts SPECIFIC to "{topic}" - include real locations, cultural details, and relevant imagery."""

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        # Use Haiku for speed and cost - this is a simple structured task
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        response_text = message.content[0].text.strip()

        # Parse JSON response
        import json

        # Clean up response if it has markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        result = json.loads(response_text)

        video_prompt = result.get("video_prompt", "")
        image_prompts = result.get("image_prompts", [])

        # Calculate cost (Haiku pricing)
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        cost = (input_tokens * 0.0008 + output_tokens * 0.004) / 1000

        activity.logger.info(f"Generated video prompt: {len(video_prompt)} chars")
        activity.logger.info(f"Generated {len(image_prompts)} image prompts")

        return {
            "video_prompt": video_prompt,
            "image_prompts": image_prompts,
            "success": True,
            "cost": cost
        }

    except json.JSONDecodeError as e:
        activity.logger.error(f"Failed to parse JSON response: {e}")
        activity.logger.error(f"Raw response: {response_text[:500]}")
        return {
            "video_prompt": "",
            "image_prompts": [],
            "success": False,
            "error": f"JSON parse error: {e}",
            "cost": 0
        }
    except Exception as e:
        activity.logger.error(f"Media prompt generation failed: {e}")
        return {
            "video_prompt": "",
            "image_prompts": [],
            "success": False,
            "error": str(e),
            "cost": 0
        }
