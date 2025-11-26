"""
Media Prompt Generation - 4-Act Video & Image Prompts

PRIMARY ACTIVITIES:
- generate_four_act_video_prompt: 4-act video from article sections
- generate_image_prompts: Contextual images matching article/video style
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
import anthropic

from src.utils.config import config
from src.config.app_config import APP_CONFIGS


# Model-specific knowledge for video prompt optimization
VIDEO_MODEL_GUIDANCE = {
    "seedance": {
        "strengths": "Fast, good motion, cinematic quality",
        "weaknesses": "Cannot render text at all - completely ignore any text requests",
        "optimal_length": "60-100 words per act",
        "char_limit": 2000,
        "tips": [
            "Use degree adverbs for motion: slowly, gently, dramatically",
            "Sequential actions work well: 'opens laptop, takes sip, looks up'",
            "Avoid any text, words, or typography - purely visual",
            "Camera movements: dolly, pan, track, orbit",
        ]
    },
    "wan-2.5": {
        "strengths": "Better text rendering (single words only), excellent depth/parallax",
        "weaknesses": "Slower, struggles with multiple words",
        "optimal_length": "80-120 words per act",
        "char_limit": 2500,
        "tips": [
            "Can include single-word text like 'Quest' branding",
            "Emphasize depth: foreground/background layers",
            "Film terminology works well: Kodak Portra, anamorphic",
            "Parallax and depth effects are a strength",
        ]
    }
}


# ============================================================================
# PRIMARY: 4-ACT VIDEO PROMPT
# ============================================================================

@activity.defn
async def generate_four_act_video_prompt(
    article: Dict[str, Any],
    app: str,
    video_model: str = "seedance"
) -> Dict[str, Any]:
    """
    Generate a 4-act video prompt from article's structured sections.

    4-ACT FRAMEWORK:
    - Article written FIRST with 4 sections
    - Each section has a visual_hint (80-120 words, cinematic)
    - This activity combines hints into unified 4-act video prompt
    - 12 seconds total = 4 acts × 3 seconds each

    Args:
        article: Article dict containing four_act_content with visual_hints per act
        app: Application (relocation, placement, pe_news)
        video_model: Target model (seedance or wan-2.5)

    Returns:
        {
            "prompt": str,  # The 4-act video prompt
            "model": str,
            "acts": int,
            "success": bool,
            "was_truncated": bool,
            "cost": float
        }
    """
    activity.logger.info(f"Generating 4-act video prompt: {article.get('title', 'Untitled')[:50]}...")

    # Get structured sections from article
    sections = article.get("four_act_content", [])

    if not sections:
        activity.logger.error("No four_act_content found in article - cannot generate 4-act prompt")
        return {
            "prompt": "",
            "model": video_model,
            "acts": 0,
            "success": False,
            "error": "No four_act_content in article",
            "cost": 0
        }

    # Get app config for styling
    app_config = APP_CONFIGS.get(app)
    if app_config:
        media_style = app_config.media_style
        media_style_details = app_config.media_style_details
        no_text_rule = app_config.article_theme.video_prompt_template.no_text_rule
    else:
        media_style = "Cinematic, professional, high production value"
        media_style_details = "High quality, visually compelling imagery."
        no_text_rule = "CRITICAL: NO text, words, letters, numbers anywhere. Purely visual."

    # Get model limits
    model_info = VIDEO_MODEL_GUIDANCE.get(video_model, VIDEO_MODEL_GUIDANCE["seedance"])
    char_limit = model_info.get("char_limit", 2000)

    # Build the 4-act prompt from visual hints
    act_prompts = []
    for i, section in enumerate(sections[:4]):
        act_num = i + 1
        visual_hint = section.get("visual_hint", "")
        title = section.get("title", f"Section {act_num}")

        # Calculate timing: 3 seconds per act
        start_time = (act_num - 1) * 3
        end_time = act_num * 3

        if visual_hint:
            act_prompts.append(f"ACT {act_num} ({start_time}s-{end_time}s): {title}\n{visual_hint}")
        else:
            activity.logger.warning(f"Section {act_num} has no visual_hint")
            act_prompts.append(f"ACT {act_num} ({start_time}s-{end_time}s): {title}\n[Cinematic visual for: {title}]")

    acts_text = "\n\n".join(act_prompts)

    # Build the combined prompt
    prompt = f"""{no_text_rule}

STYLE: {media_style}
{media_style_details}

VIDEO STRUCTURE: 12 seconds, 4 acts of 3 seconds each.

{acts_text}

{no_text_rule}"""

    # Enforce character limit
    was_truncated = False
    if len(prompt) > char_limit:
        activity.logger.warning(f"Prompt {len(prompt)} chars exceeds {char_limit} limit - truncating")
        prompt = prompt[:char_limit]
        was_truncated = True

    acts_with_hints = len([s for s in sections[:4] if s.get("visual_hint")])
    activity.logger.info(f"Generated 4-act prompt: {len(prompt)} chars, {acts_with_hints}/4 acts with visual hints")

    return {
        "prompt": prompt,
        "model": video_model,
        "acts": len(sections[:4]),
        "success": True,
        "was_truncated": was_truncated,
        "cost": 0  # No API call - just combining existing visual hints
    }


# ============================================================================
# IMAGE PROMPTS
# ============================================================================

@activity.defn
async def generate_image_prompts(
    title: str,
    topic: str,
    app: str,
    num_prompts: int = 4,
    video_gif_url: Optional[str] = None,
    video_style_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate image prompts, optionally matching video style.

    Can be called after video generation to create style-matched images,
    or independently for image-only articles.

    Args:
        title: Article title
        topic: Original topic
        app: Application context
        num_prompts: Number of image prompts (default 4)
        video_gif_url: Optional GIF URL from video (for style reference)
        video_style_description: Optional description of video style to match

    Returns:
        {
            "prompts": List[str],  # Image prompts
            "matched_video_style": bool,
            "success": bool,
            "cost": float
        }
    """
    activity.logger.info(f"Generating {num_prompts} image prompts for: {title[:50]}...")

    # Get app config for styling
    app_config = APP_CONFIGS.get(app)
    if app_config:
        media_style = app_config.media_style
        media_style_details = app_config.media_style_details
    else:
        media_style = "Professional, high quality imagery"
        media_style_details = "Clean, modern aesthetic."

    # Build style context
    style_context = ""
    if video_style_description:
        style_context = f"""
IMPORTANT: Match this video style for visual consistency:
{video_style_description}
"""
    elif video_gif_url:
        style_context = """
Note: Images should complement the video style (cinematic, warm tones, professional).
"""

    system_prompt = f"""You are an expert at creating image prompts for AI image generation.

APP STYLE: {media_style}
DETAILS: {media_style_details}
{style_context}

Create {num_prompts} distinct image prompts that:
1. Are visually compelling and professional
2. Match the app's aesthetic
3. Each capture a different aspect of the topic
4. Work well as article thumbnails or content images

Return JSON format:
{{"prompts": ["prompt 1", "prompt 2", ...]}}"""

    user_prompt = f"""Create {num_prompts} image prompts for:

TITLE: {title}
TOPIC: {topic}

Each prompt should be 30-50 words, highly visual, and suitable for AI image generation (Flux/DALL-E style).
Focus on different angles: overview, detail, person-focused, abstract/conceptual.

Return only valid JSON."""

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
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
        prompts = result.get("prompts", [])

        # Calculate cost (Haiku pricing)
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        cost = (input_tokens * 0.0008 + output_tokens * 0.004) / 1000

        activity.logger.info(f"Generated {len(prompts)} image prompts")

        return {
            "prompts": prompts,
            "matched_video_style": bool(video_style_description or video_gif_url),
            "success": True,
            "cost": cost
        }

    except json.JSONDecodeError as e:
        activity.logger.error(f"Failed to parse JSON response: {e}")
        return {
            "prompts": [],
            "matched_video_style": False,
            "success": False,
            "error": f"JSON parse error: {e}",
            "cost": 0
        }
    except Exception as e:
        activity.logger.error(f"Image prompt generation failed: {e}")
        return {
            "prompts": [],
            "matched_video_style": False,
            "success": False,
            "error": str(e),
            "cost": 0
        }
