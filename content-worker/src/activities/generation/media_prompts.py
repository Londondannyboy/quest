"""
Media Prompt Generation - Separate activities for video and images

Split into two dedicated activities for cleaner separation:
- generate_video_prompt: Focused on video, model-aware (Seedance/WAN)
- generate_image_prompts: Focused on images, can match video style
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
        "optimal_length": "60-100 words",
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
        "optimal_length": "80-120 words",
        "tips": [
            "Can include single-word text like 'Quest' branding",
            "Emphasize depth: foreground/background layers",
            "Film terminology works well: Kodak Portra, anamorphic",
            "Parallax and depth effects are a strength",
        ]
    }
}


@activity.defn
async def generate_video_prompt(
    title: str,
    topic: str,
    app: str,
    video_model: str = "seedance",
    seed_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a focused video prompt optimized for the target model.

    Called BEFORE video generation. Model-aware prompt engineering.

    Args:
        title: Article title
        topic: Original topic/subject
        app: Application (relocation, placement, etc.)
        video_model: Target model (seedance, wan-2.5)
        seed_hint: Optional user-provided hint to incorporate (e.g., "Cyprus beach sunset")

    Returns:
        {
            "prompt": str,  # The video prompt (60-120 words)
            "model": str,   # Model it was optimized for
            "success": bool,
            "cost": float
        }
    """
    activity.logger.info(f"Generating video prompt for: {title[:50]}...")
    activity.logger.info(f"Target model: {video_model}")
    if seed_hint:
        activity.logger.info(f"User seed hint: {seed_hint}")

    # Get app config for styling
    app_config = APP_CONFIGS.get(app)
    if app_config:
        media_style = app_config.media_style
        media_style_details = app_config.media_style_details
    else:
        media_style = "Cinematic, professional, high production value"
        media_style_details = "High quality, visually compelling imagery."

    # Get model-specific guidance
    model_info = VIDEO_MODEL_GUIDANCE.get(video_model, VIDEO_MODEL_GUIDANCE["seedance"])

    system_prompt = f"""You are a video prompt engineer specializing in AI video generation.

TARGET MODEL: {video_model}
MODEL STRENGTHS: {model_info['strengths']}
MODEL WEAKNESSES: {model_info['weaknesses']}
OPTIMAL PROMPT LENGTH: {model_info['optimal_length']}

MODEL-SPECIFIC TIPS:
{chr(10).join(f"- {tip}" for tip in model_info['tips'])}

APP STYLE: {media_style}
DETAILS: {media_style_details}

PROMPT FORMULA:
[Subject + Action] + [Environment + Lighting] + [Camera Movement] + [Color/Mood]

CAMERA LANGUAGE:
- Push/Dolly: "camera pushes in slowly", "dolly out to reveal"
- Tracking: "camera follows closely", "tracks alongside"
- Orbital: "orbits smoothly around subject"
- Crane: "crane up dramatically"

MOTION IS ESSENTIAL:
- Always include movement adverbs: "slowly", "gently", "dramatically"
- Sequential actions: "opens laptop, sips coffee, looks up and smiles"
- Describe what's HAPPENING, not static scenes

Return ONLY the prompt text, no JSON, no explanation, no quotes around it."""

    # Build user prompt, incorporating seed hint if provided
    seed_section = ""
    if seed_hint:
        seed_section = f"""
USER'S CREATIVE DIRECTION:
The user wants the video to focus on: "{seed_hint}"
Incorporate this direction into your cinematic prompt while adding:
- Professional camera movements
- Cinematic lighting and atmosphere
- Motion and action (not static scenes)
- App-appropriate styling
"""

    user_prompt = f"""Create a {model_info['optimal_length']} cinematic video prompt for:

TITLE: {title}
TOPIC: {topic}
{seed_section}
The prompt should capture the essence of this topic with:
- Specific visual elements related to "{topic}"
- Clear camera movement and motion
- Cinematic lighting and color grading
- Professional, engaging atmosphere

{"CRITICAL: Absolutely NO text, words, or typography - the model cannot render text." if video_model == "seedance" else "You may include single-word branding like 'Quest' if appropriate."}

Write the prompt now:"""

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        prompt = message.content[0].text.strip()

        # Remove any accidental quotes around the prompt
        if prompt.startswith('"') and prompt.endswith('"'):
            prompt = prompt[1:-1]
        if prompt.startswith("'") and prompt.endswith("'"):
            prompt = prompt[1:-1]

        # Calculate cost (Haiku pricing)
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        cost = (input_tokens * 0.0008 + output_tokens * 0.004) / 1000

        activity.logger.info(f"Generated video prompt: {len(prompt)} chars")
        activity.logger.info(f"Prompt preview: {prompt[:100]}...")

        return {
            "prompt": prompt,
            "model": video_model,
            "success": True,
            "cost": cost
        }

    except Exception as e:
        activity.logger.error(f"Video prompt generation failed: {e}")
        return {
            "prompt": "",
            "model": video_model,
            "success": False,
            "error": str(e),
            "cost": 0
        }


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

    Called AFTER video generation (if video exists) so images match the video's style.

    Args:
        title: Article title
        topic: Original topic/subject
        app: Application (relocation, placement, etc.)
        num_prompts: Number of image prompts to generate (default 4)
        video_gif_url: Optional GIF URL from video for style reference
        video_style_description: Optional description of video's visual style

    Returns:
        {
            "prompts": List[str],  # Image prompts
            "matched_video_style": bool,  # Whether style matching was applied
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
        media_style = "Cinematic, professional, high production value"
        media_style_details = "High quality, visually compelling imagery."

    # Style matching context
    style_context = ""
    if video_style_description:
        style_context = f"""
IMPORTANT - MATCH VIDEO STYLE:
The article has a hero video with this visual style:
"{video_style_description}"

Your image prompts should maintain visual consistency with this style:
- Similar color grading and lighting
- Complementary compositions
- Consistent mood and atmosphere
- Same level of professionalism
"""
    elif video_gif_url:
        style_context = """
IMPORTANT - STYLE CONSISTENCY:
The article has a hero video. While you can't see it, ensure your image prompts:
- Use professional, cinematic quality
- Maintain consistent mood throughout
- Complement rather than clash with video content
"""

    system_prompt = f"""You are an image prompt engineer for AI image generation (Flux Kontext Pro).

APP STYLE: {media_style}
DETAILS: {media_style_details}
{style_context}

IMAGE PROMPT GUIDELINES:
1. Each prompt should be 40-80 words
2. Include specific visual details and composition
3. Vary perspectives: close-up, wide, overhead, environmental
4. Describe lighting and atmosphere
5. NO text or typography - purely visual

OUTPUT FORMAT (JSON):
{{
  "prompts": [
    "First image prompt...",
    "Second image prompt...",
    "Third image prompt...",
    "Fourth image prompt..."
  ]
}}

Return ONLY valid JSON, no markdown or explanations."""

    user_prompt = f"""Create {num_prompts} varied image prompts for this article:

TITLE: {title}
TOPIC: {topic}

Each prompt should:
- Cover a different aspect or angle of the topic
- Be specific to "{topic}" with real locations/details
- Use varied compositions (close-up, wide, environmental, aerial)
- Have professional, publication-ready quality

Generate the prompts now:"""

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1500,
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
        activity.logger.error(f"Raw response: {response_text[:500]}")
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


# ============================================================================
# DEPRECATED - Keep for backwards compatibility, will be removed later
# ============================================================================

@activity.defn
async def generate_video_prompt_from_article(
    article: Dict[str, Any],
    app: str,
    video_model: str = "seedance"
) -> Dict[str, Any]:
    """
    Generate a 4-act video prompt from article's structured sections.

    ARTICLE-FIRST APPROACH: The article is written first with 4 sections,
    each with a visual_hint. This activity combines those hints with the
    app's media_style to create a unified 4-act video prompt.

    Args:
        article: Article dict containing structured_sections with visual_hints
        app: Application (relocation, placement, etc.)
        video_model: Target model (seedance or wan-2.5)

    Returns:
        {
            "prompt": str,  # The 4-act video prompt (400-500 words total)
            "model": str,
            "success": bool,
            "cost": float
        }
    """
    activity.logger.info(f"Generating 4-act video prompt from article: {article.get('title', 'Untitled')[:50]}...")

    # Get structured sections from article
    sections = article.get("structured_sections", [])

    if not sections:
        activity.logger.warning("No structured sections found - falling back to legacy prompt generation")
        return await generate_video_prompt(
            article.get("title", ""),
            article.get("title", ""),
            app,
            video_model
        )

    # Get app config for styling
    app_config = APP_CONFIGS.get(app)
    if app_config:
        media_style = app_config.media_style
        media_style_details = app_config.media_style_details
    else:
        media_style = "Cinematic, professional, high production value"
        media_style_details = "High quality, visually compelling imagery."

    # Get model-specific guidance
    model_info = VIDEO_MODEL_GUIDANCE.get(video_model, VIDEO_MODEL_GUIDANCE["seedance"])

    # Build the 4-act prompt from visual hints
    act_prompts = []
    for i, section in enumerate(sections[:4]):
        act_num = i + 1
        visual_hint = section.get("visual_hint", "")
        title = section.get("title", f"Section {act_num}")

        if visual_hint:
            act_prompts.append(f"ACT {act_num} ({act_num * 3 - 3}s-{act_num * 3}s): {title}\n{visual_hint}")
        else:
            # Fallback: generate from title
            act_prompts.append(f"ACT {act_num} ({act_num * 3 - 3}s-{act_num * 3}s): {title}\n[Visual representation of: {title}]")

    acts_text = "\n\n".join(act_prompts)

    # Build the combined prompt
    no_text_rule = "CRITICAL: Absolutely NO text, NO words, NO letters, NO typography anywhere in ANY frame. Purely visual storytelling."

    prompt = f"""{no_text_rule}

STYLE: {media_style}
{media_style_details}

VIDEO STRUCTURE: 12 seconds, 4 acts of 3 seconds each.

{acts_text}

{no_text_rule}"""

    activity.logger.info(f"Generated 4-act video prompt: {len(prompt)} chars")
    activity.logger.info(f"Acts included: {len([s for s in sections[:4] if s.get('visual_hint')])}/4 with visual hints")

    return {
        "prompt": prompt,
        "model": video_model,
        "acts": len(sections[:4]),
        "success": True,
        "cost": 0  # No API call needed - just combining existing visual hints
    }


@activity.defn
async def generate_media_prompts(
    title: str,
    topic: str,
    app: str,
    num_image_prompts: int = 4
) -> Dict[str, Any]:
    """
    DEPRECATED: Use generate_video_prompt and generate_image_prompts separately.

    Kept for backwards compatibility with existing workflows.
    """
    activity.logger.warning("generate_media_prompts is DEPRECATED - use generate_video_prompt and generate_image_prompts")

    # Call the new separated functions
    video_result = await generate_video_prompt(title, topic, app, "seedance")
    image_result = await generate_image_prompts(title, topic, app, num_image_prompts)

    return {
        "video_prompt": video_result.get("prompt", ""),
        "image_prompts": image_result.get("prompts", []),
        "success": video_result.get("success", False) and image_result.get("success", False),
        "cost": video_result.get("cost", 0) + image_result.get("cost", 0)
    }
