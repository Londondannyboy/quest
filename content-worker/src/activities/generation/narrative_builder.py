"""
DEPRECATED: 3-Act Narrative Builder

This module is DEPRECATED - superseded by 4-act workflow in ArticleCreationWorkflow.

The 4-act structure (12 seconds = 4 acts × 3 seconds) in generate_four_act_article
provides better video/article alignment through four_act_visual_hint in each section.

DO NOT USE THIS MODULE for new development.
Kept for backwards compatibility only.

---

Original description:
3-Act Narrative Builder for Video-First Storytelling

Every story has stakes. Someone wins, someone loses. That's engagement.

This activity takes curated research and builds a 3-act narrative structure
that drives BOTH the video generation AND the article structure.

NARRATIVE TEMPLATES:
- ASPIRATIONAL: Dream → Path → Reality (visas, lifestyle, opportunities)
- NEWS/DEALS: Event → Impact → Winners/Losers (acquisitions, funding, market moves)
- COMPANY: Origin → Solution → Verdict (profiles, case studies)
- GUIDE: Problem → Process → Outcome (how-tos, tutorials)
"""
import warnings
warnings.warn(
    "narrative_builder.py is DEPRECATED. Use 4-act workflow (generate_four_act_article) instead.",
    DeprecationWarning
)

from temporalio import activity
from typing import Dict, Any, List, Optional
import anthropic
import json

from src.utils.config import config
from src.config.app_config import APP_CONFIGS


# ============================================================================
# NARRATIVE TEMPLATES
# ============================================================================

NARRATIVE_TEMPLATES = {
    "aspirational": {
        "name": "Aspirational Journey",
        "description": "From desire to achievement - perfect for visas, relocations, lifestyle content",
        "acts": [
            {
                "number": 1,
                "title": "The Dream",
                "focus": "What does the reader want? Paint the desire, the frustration with status quo",
                "visual_style": "Grey, confined, longing expression, current situation shown as limiting",
                "example_visual": "Professional at desk in grey city, rain on window, dreaming expression"
            },
            {
                "number": 2,
                "title": "The Path",
                "focus": "How do they get there? The process, requirements, steps to take",
                "visual_style": "Warm, hopeful, documents/planning visible, confidence building",
                "example_visual": "Same person reviewing documents in sunlit room, smile emerging"
            },
            {
                "number": 3,
                "title": "The Reality",
                "focus": "What does success look like? Living the dream, the payoff",
                "visual_style": "Golden hour, achievement, lifestyle benefits visible, contentment",
                "example_visual": "Happy professional at seaside cafe, laptop open, Mediterranean sunset"
            }
        ],
        "tone": "Inspiring, personal, transformative",
        "article_types": ["guide", "visa", "relocation", "lifestyle", "opportunity"]
    },

    "news_deals": {
        "name": "News & Deals",
        "description": "Breaking news with impact analysis - for acquisitions, funding, market events",
        "acts": [
            {
                "number": 1,
                "title": "The Event",
                "focus": "What happened? The headline, the core news",
                "visual_style": "Dynamic, newsworthy, action shot of the event or key players",
                "example_visual": "Modern boardroom, handshake, deal being struck, confident executives"
            },
            {
                "number": 2,
                "title": "The Impact",
                "focus": "What does it mean? Analysis, ripple effects, who's affected",
                "visual_style": "Analysis mode, multiple perspectives, cause-and-effect visual",
                "example_visual": "Market visualization, teams reacting, data on screens showing change"
            },
            {
                "number": 3,
                "title": "Winners & Losers",
                "focus": "Who benefits? Who's at risk? The stakes made clear",
                "visual_style": "Contrast between winning/losing positions, clear outcomes",
                "example_visual": "Split visual: celebrating team vs. concerned competitors"
            }
        ],
        "tone": "Analytical, authoritative, balanced with clear stakes",
        "article_types": ["news", "deal", "acquisition", "funding", "pe_news", "market"]
    },

    "company_profile": {
        "name": "Company Profile",
        "description": "Origin to impact story - for company profiles, case studies",
        "acts": [
            {
                "number": 1,
                "title": "The Origin",
                "focus": "What problem did they see? Why did they start?",
                "visual_style": "Founding moment, garage/early office, problem visualization",
                "example_visual": "Founders in early workspace, whiteboard with problem, determination"
            },
            {
                "number": 2,
                "title": "The Solution",
                "focus": "What did they build? How does it work?",
                "visual_style": "Product in action, modern office, team collaboration, growth",
                "example_visual": "Modern HQ, product demo, diverse team working, innovation"
            },
            {
                "number": 3,
                "title": "The Verdict",
                "focus": "Who benefits? Market position, competitive landscape",
                "visual_style": "Impact visualization, market presence, future potential",
                "example_visual": "Global reach visualization, customer success, market leadership"
            }
        ],
        "tone": "Investigative, balanced, forward-looking",
        "article_types": ["company", "profile", "startup", "case_study"]
    },

    "guide": {
        "name": "How-To Guide",
        "description": "Problem to solution journey - for tutorials, processes, how-tos",
        "acts": [
            {
                "number": 1,
                "title": "The Problem",
                "focus": "What challenge are we solving? Why does it matter?",
                "visual_style": "Frustration, confusion, the problem clearly visualized",
                "example_visual": "Person facing complex challenge, overwhelmed expression"
            },
            {
                "number": 2,
                "title": "The Process",
                "focus": "Step-by-step solution, the method, the approach",
                "visual_style": "Organized steps, tools laid out, methodical progress",
                "example_visual": "Clear workspace, step visualization, focused execution"
            },
            {
                "number": 3,
                "title": "The Outcome",
                "focus": "Success state, results achieved, benefits realized",
                "visual_style": "Achievement, satisfaction, tangible results visible",
                "example_visual": "Completed project, satisfied expression, measurable success"
            }
        ],
        "tone": "Practical, clear, encouraging",
        "article_types": ["tutorial", "howto", "process", "guide"]
    }
}


def select_template(article_type: str, topic: str, app: str) -> Dict[str, Any]:
    """
    Select the best narrative template based on article type, topic, and app.
    """
    topic_lower = topic.lower()
    type_lower = article_type.lower() if article_type else ""

    # Visa/relocation content -> aspirational
    if any(kw in topic_lower for kw in ["visa", "nomad", "relocat", "move to", "live in", "expat"]):
        return NARRATIVE_TEMPLATES["aspirational"]

    # News/deals content
    if any(kw in topic_lower for kw in ["acqui", "funding", "raise", "deal", "buyout", "merger"]):
        return NARRATIVE_TEMPLATES["news_deals"]

    if any(kw in type_lower for kw in ["news", "deal", "acquisition"]):
        return NARRATIVE_TEMPLATES["news_deals"]

    # App-based selection
    if app in ["relocation"]:
        return NARRATIVE_TEMPLATES["aspirational"]
    if app in ["pe_news", "placement"]:
        return NARRATIVE_TEMPLATES["news_deals"]

    # Company profiles
    if any(kw in topic_lower for kw in ["company", "startup", "profile", "founded"]):
        return NARRATIVE_TEMPLATES["company_profile"]

    # Guide content
    if any(kw in topic_lower for kw in ["how to", "guide", "tutorial", "step", "process"]):
        return NARRATIVE_TEMPLATES["guide"]

    # Default based on article type
    if "guide" in type_lower:
        return NARRATIVE_TEMPLATES["guide"]
    if "news" in type_lower:
        return NARRATIVE_TEMPLATES["news_deals"]

    # Ultimate fallback: aspirational (most engaging)
    return NARRATIVE_TEMPLATES["aspirational"]


@activity.defn
async def build_3_act_narrative(
    topic: str,
    article_type: str,
    app: str,
    curated_research: str,
    title_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    DEPRECATED: Use generate_four_act_article instead.

    This 3-act function is superseded by the 4-act workflow which provides:
    - Better video/article alignment (4 acts × 3 seconds = 12s video)
    - four_act_visual_hint in each section for video generation
    - Integrated article + video prompt generation

    This function is kept for backwards compatibility only.

    Args:
        topic: The article topic
        article_type: Type of article (news, guide, etc.)
        app: Application name (relocation, placement, pe_news)
        curated_research: Pre-curated research content
        title_hint: Optional title suggestion

    Returns:
        {
            "template": str,  # Template name used
            "title": str,  # Generated article title
            "topic": str,  # Original topic
            "acts": [
                {
                    "number": 1,
                    "title": str,  # "The Dream"
                    "visual": str,  # 50-80 word visual description for video
                    "key_points": List[str],  # 3-5 key points for article section
                    "start": float,  # Video timestamp start (0, 3.3, 6.6)
                    "end": float,  # Video timestamp end (3.3, 6.6, 10)
                },
                ...
            ],
            "video_prompt": str,  # Full 10-second video prompt combining all acts
            "preamble_context": str,  # Context for article preamble
            "tone": str,  # Recommended tone
            "success": bool,
            "cost": float
        }
    """
    activity.logger.info(f"Building 3-act narrative for: {topic[:50]}...")
    activity.logger.info(f"Article type: {article_type}, App: {app}")

    # Select appropriate template
    template = select_template(article_type, topic, app)
    activity.logger.info(f"Selected template: {template['name']}")

    # Get app config for styling
    app_config = APP_CONFIGS.get(app)
    media_style = app_config.media_style if app_config else "Cinematic, professional"

    # Build the prompt for Claude
    system_prompt = f"""You are a narrative architect specializing in video-first storytelling.

Your job is to create a 3-ACT NARRATIVE STRUCTURE that will drive both:
1. A 10-second video (divided into 3 acts of ~3.3s each)
2. An article with 3 main sections matching the video acts

TEMPLATE: {template['name']}
DESCRIPTION: {template['description']}
TONE: {template['tone']}

ACT STRUCTURE:
{json.dumps(template['acts'], indent=2)}

VISUAL STYLE GUIDANCE: {media_style}

OUTPUT FORMAT (JSON):
{{
    "title": "Compelling article title (60-90 chars)",
    "acts": [
        {{
            "number": 1,
            "title": "{template['acts'][0]['title']}",
            "visual": "50-80 word cinematic visual description for this act. Include: subject, action, environment, lighting, camera movement, mood. Must be CONTINUOUS with next act for smooth video transition.",
            "key_points": ["Point 1 from research", "Point 2", "Point 3"],
            "section_hook": "Opening sentence for this article section"
        }},
        {{
            "number": 2,
            "title": "{template['acts'][1]['title']}",
            "visual": "50-80 word visual description. TRANSITION smoothly from Act 1. Different scene but connected narrative.",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "section_hook": "Opening sentence for this section"
        }},
        {{
            "number": 3,
            "title": "{template['acts'][2]['title']}",
            "visual": "50-80 word visual description. CONCLUDE the visual journey. Emotional payoff.",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "section_hook": "Opening sentence for this section"
        }}
    ],
    "preamble_context": "2-3 sentences of market context/authority establishment for article intro"
}}

CRITICAL RULES:
1. Visual descriptions must form ONE CONTINUOUS 10-second video
2. Each act's visual MUST smoothly transition to the next
3. Key points MUST come from the research provided
4. Include camera movements (pan, push, track, dolly)
5. Include lighting progression (grey→warm→golden hour works well)
6. NO text/words in visuals - purely cinematic
7. Be SPECIFIC to the topic - not generic"""

    user_prompt = f"""Create a 3-act narrative for:

TOPIC: {topic}
{'TITLE HINT: ' + title_hint if title_hint else ''}

CURATED RESEARCH:
{curated_research[:8000]}

Requirements:
- Extract the most compelling facts from research for key_points
- Create visuals that tell a story specific to "{topic}"
- Ensure smooth visual transitions between acts
- Title should be SEO-friendly and compelling

Generate the narrative JSON now:"""

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        response_text = message.content[0].text.strip()

        # Clean up response if it has markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        result = json.loads(response_text)

        # Add timestamps to acts
        acts = result.get("acts", [])
        timestamps = [(0, 3.3), (3.3, 6.6), (6.6, 10.0)]
        for i, act in enumerate(acts):
            if i < len(timestamps):
                act["start"] = timestamps[i][0]
                act["end"] = timestamps[i][1]

        # Build the combined video prompt
        video_prompt = build_video_prompt_from_acts(acts, template['name'])

        # Calculate cost (Sonnet pricing)
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000

        activity.logger.info(f"Narrative built successfully: {len(acts)} acts")
        activity.logger.info(f"Title: {result.get('title', '')[:60]}...")

        return {
            "template": template['name'],
            "title": result.get("title", ""),
            "topic": topic,
            "acts": acts,
            "video_prompt": video_prompt,
            "preamble_context": result.get("preamble_context", ""),
            "tone": template['tone'],
            "success": True,
            "cost": cost
        }

    except json.JSONDecodeError as e:
        activity.logger.error(f"Failed to parse narrative JSON: {e}")
        activity.logger.error(f"Raw response: {response_text[:500]}")
        return {
            "template": template['name'],
            "title": "",
            "topic": topic,
            "acts": [],
            "video_prompt": "",
            "preamble_context": "",
            "tone": template['tone'],
            "success": False,
            "error": f"JSON parse error: {e}",
            "cost": 0
        }
    except Exception as e:
        activity.logger.error(f"Narrative building failed: {e}")
        return {
            "template": template['name'],
            "title": "",
            "topic": topic,
            "acts": [],
            "video_prompt": "",
            "preamble_context": "",
            "tone": template['tone'],
            "success": False,
            "error": str(e),
            "cost": 0
        }


def build_video_prompt_from_acts(acts: List[Dict], template_name: str) -> str:
    """
    Combine act visuals into a single flowing video prompt.
    """
    if not acts:
        return ""

    # Extract visuals
    visuals = [act.get("visual", "") for act in acts]

    # Build flowing prompt
    prompt_parts = []
    for i, visual in enumerate(visuals):
        prompt_parts.append(visual)
        if i < len(visuals) - 1:
            prompt_parts.append("Scene transitions smoothly to")

    visual_narrative = " ".join(prompt_parts)

    # Add cinematic instructions
    full_prompt = f"""{visual_narrative}

Cinematic {template_name.lower()} narrative, 10-second duration with clear 3-act structure.
Lighting progression from opening mood through transformation to resolution.
Film aesthetic: Kodak Portra 400 color grading, shallow depth of field.
Smooth 1-second dissolve transitions between scenes. Professional quality."""

    return full_prompt


def generate_mux_narrative_urls(playback_id: str, acts: List[Dict]) -> Dict[str, Any]:
    """
    Generate all Mux URLs for a 3-act narrative video.

    Returns URLs for:
    - Full video stream
    - Thumbnails at each act timestamp
    - GIFs for each act (bounded)
    - Storyboard
    """
    image_base = f"https://image.mux.com/{playback_id}"
    stream_base = f"https://stream.mux.com/{playback_id}"

    urls = {
        "stream_url": f"{stream_base}.m3u8",
        "storyboard": f"{image_base}/storyboard.jpg",
        "full_gif": f"{image_base}/animated.gif?start=0&end=10&width=480&fps=15",
        "acts": {}
    }

    for act in acts:
        act_num = act["number"]
        start = act["start"]
        end = act["end"]
        mid = (start + end) / 2

        urls["acts"][f"act_{act_num}"] = {
            "title": act.get("title", f"Act {act_num}"),
            "thumbnail": f"{image_base}/thumbnail.jpg?time={mid}&width=1200",
            "thumbnail_hero": f"{image_base}/thumbnail.jpg?time={mid}&width=1920&height=1080&fit_mode=smartcrop",
            "gif": f"{image_base}/animated.gif?start={start}&end={end}&width=480&fps=15",
            "start": start,
            "end": end
        }

    return urls


def generate_chapter_data(acts: List[Dict]) -> List[Dict]:
    """
    Generate Mux Player chapter data from acts.
    """
    return [
        {
            "startTime": act["start"],
            "endTime": act["end"],
            "value": act.get("title", f"Act {act['number']}")
        }
        for act in acts
    ]
