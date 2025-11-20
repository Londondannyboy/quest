"""
Article Section Analysis Activity

Extracts H2 sections from markdown content and analyzes narrative structure
for sequential image generation with Flux Kontext.

Auto-decides optimal image placement (3-5 images) based on:
- Article length and structure
- Sentiment shifts (provocative moments)
- Narrative flow and pacing
"""

import re
from typing import Dict, Any, List
from temporalio import activity

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.utils.config import config


class Section(BaseModel):
    """Article section with metadata"""
    index: int = Field(description="Section index (0-based)")
    title: str = Field(description="H2 heading text")
    content: str = Field(description="Section content (without heading)")
    word_count: int = Field(description="Word count of section")
    sentiment: str = Field(
        description="Overall sentiment: positive, negative, neutral, tense, celebratory, somber, distressed, optimistic"
    )
    sentiment_intensity: float = Field(
        description="Sentiment strength 0-1, higher = more intense emotion"
    )
    business_context: str = Field(
        description="Business context: layoffs, acquisition, deal, growth, crisis, restructuring, success, expansion, etc."
    )
    visual_tone: str = Field(
        description="Appropriate visual tone: professional-optimistic, somber-serious, tense-uncertain, celebratory, analytical-neutral"
    )
    visual_moment: str = Field(
        description="Visual description for image generation, matching the tone and context (e.g., 'somber boardroom for layoffs', 'celebratory handshake for acquisition')"
    )
    should_generate_image: bool = Field(
        default=False,
        description="Whether this section should get an image"
    )


class ArticleAnalysis(BaseModel):
    """Complete article structure analysis"""
    sections: List[Section] = Field(description="All H2 sections")
    total_word_count: int = Field(description="Total article word count")
    recommended_image_count: int = Field(
        description="Recommended number of content images (3-5)",
        ge=3,
        le=5
    )
    narrative_arc: str = Field(
        description="Overall story arc: problem-solution, chronological, comparative, guide, crisis-resolution, etc."
    )

    # Overall + 3-stage sentiment analysis
    overall_sentiment: str = Field(
        description="Overall sentiment of the entire article: positive, negative, mixed, analytical, etc."
    )

    opening_sentiment: str = Field(
        description="Opening stage sentiment and context (first 1-2 sections) - sets the tone"
    )
    middle_sentiment: str = Field(
        description="Middle/transition sentiment (core sections) - where story develops or shifts"
    )
    climax_sentiment: str = Field(
        description="Climax/resolution sentiment (peak moment or conclusion) - how it ends"
    )

    # Business context awareness
    primary_business_context: str = Field(
        description="Primary business context of article: layoffs, acquisition, IPO, expansion, crisis, success, etc."
    )

    key_sentiment_shifts: List[int] = Field(
        description="Section indexes where major sentiment shifts occur (max 3 for the 3 stages)"
    )


def extract_h2_sections(markdown_content: str) -> List[Dict[str, Any]]:
    """
    Parse markdown content into H2 sections.

    Args:
        markdown_content: Full article markdown

    Returns:
        List of dicts with title and content for each section
    """
    # Split on H2 headings (## Heading)
    # Regex: match ## at start of line, capture heading text
    pattern = r'^##\s+(.+?)$'

    # Split content while preserving headings
    splits = re.split(pattern, markdown_content, flags=re.MULTILINE)

    sections = []

    # First element is intro (before first H2)
    if splits[0].strip():
        sections.append({
            "title": "Introduction",
            "content": splits[0].strip()
        })

    # Process H2 sections (pairs of heading + content)
    for i in range(1, len(splits), 2):
        if i + 1 < len(splits):
            title = splits[i].strip()
            content = splits[i + 1].strip()

            # Skip empty sections
            if content:
                sections.append({
                    "title": title,
                    "content": content
                })

    return sections


def count_words(text: str) -> int:
    """Simple word counter"""
    return len(text.split())


@activity.defn
async def analyze_article_sections(
    content: str,
    title: str,
    app: str = "placement"
) -> Dict[str, Any]:
    """
    Analyze article structure for sequential image generation.

    This activity:
    1. Extracts H2 sections from markdown
    2. Analyzes sentiment and narrative flow
    3. Identifies provocative moments (sentiment shifts)
    4. Auto-decides which 3-5 sections should get images

    Args:
        content: Full article markdown content
        title: Article title for context
        app: Application context (placement, relocation, etc.)

    Returns:
        ArticleAnalysis dict with sections and image placement recommendations
    """
    activity.logger.info(f"Analyzing sections for article: {title}")

    # Extract raw sections
    raw_sections = extract_h2_sections(content)

    if not raw_sections:
        activity.logger.warning("No H2 sections found, using full content as single section")
        raw_sections = [{
            "title": title,
            "content": content
        }]

    # Count total words
    total_words = count_words(content)

    activity.logger.info(f"Found {len(raw_sections)} sections, {total_words} words total")

    # Prepare section data for AI analysis
    sections_text = "\n\n".join([
        f"## {i+1}. {s['title']}\n{s['content'][:300]}..."  # First 300 chars
        for i, s in enumerate(raw_sections)
    ])

    # Determine app-specific context
    app_context = {
        "placement": "corporate finance, M&A, private equity, executive recruitment - professional, analytical",
        "relocation": "international relocation, lifestyle, travel, cultural adaptation - aspirational, practical",
        "chief-of-staff": "executive leadership, C-suite, strategic operations - authoritative, professional",
        "consultancy": "business consulting, strategy, transformation - analytical, advisory"
    }.get(app, "professional business content")

    # Use AI to analyze narrative structure
    provider, model_name = config.get_ai_model()
    model_str = model_name if provider == "google" else f"{provider}:{model_name}"

    agent = Agent(
        model=model_str,
        result_type=ArticleAnalysis,
        system_prompt=f"""You are an expert content analyst specializing in narrative structure
        and visual storytelling for {app_context} content.

        CRITICAL CONTEXT AWARENESS:
        You MUST detect business context and match visual tone accordingly:

        - LAYOFFS/REDUNDANCIES → Somber, serious imagery (NO smiling executives!)
        - ACQUISITIONS/DEALS → Professional optimism, handshakes, positive but measured
        - DISTRESSED SALES → Tense, uncertain, serious boardroom atmosphere
        - IPO/SUCCESS → Celebratory but professional, achievement moments
        - CRISIS/PROBLEMS → Serious, analytical, problem-solving imagery
        - GROWTH/EXPANSION → Optimistic, forward-looking, professional energy

        3-STAGE SENTIMENT ANALYSIS FOR IMAGES:
        Analyze sentiment at THREE key stages:
        1. OPENING: Sets the tone and context (first section or two)
        2. MIDDLE: Where story develops, transitions, or shifts (core sections)
        3. CLIMAX/RESOLUTION: Peak moment or conclusion (how it ends)

        Also provide OVERALL sentiment of the entire article for context.

        For each section, analyze:
        1. Business context (layoffs, acquisition, deal, crisis, success, etc.)
        2. Appropriate visual tone (somber-serious, professional-optimistic, celebratory, etc.)
        3. Sentiment that MATCHES the context
        4. Visual moment that reflects the REALITY of the situation

        CRITICAL RULES:
        ❌ NO happy/smiling imagery for negative news (layoffs, crisis, failure)
        ❌ NO somber imagery for positive news (success, deals, growth)
        ✅ MATCH tone to reality: layoffs = serious faces, acquisitions = professional handshakes

        For visual moments, be specific AND context-appropriate:
        ❌ "Executive in office" (too generic)
        ❌ "Smiling CEO announcing layoffs" (WRONG TONE!)
        ✅ "Somber boardroom meeting, executives with serious expressions discussing difficult decision"
        ✅ "Professional handshake sealing acquisition deal, confident but measured optimism"

        Recommend 3-5 images, distributed across the 3 stages:
        - 1-2 images for opening stage
        - 1-2 images for middle/transition stage
        - 1-2 images for climax/resolution stage

        This ensures visual coverage of the complete narrative arc.
        """
    )

    # Construct analysis prompt
    prompt = f"""Analyze this article for sequential image generation:

Title: {title}
Total Word Count: {total_words}
Number of Sections: {len(raw_sections)}

Sections:
{sections_text}

For each section, provide:
- Business context (layoffs, acquisition, deal, etc.)
- Sentiment analysis (matching the context)
- Visual tone (somber-serious, professional-optimistic, etc.)
- Visual moment description (for AI image generation, tone-appropriate)
- Whether it should get an image

Then provide:
1. OVERALL SENTIMENT of the entire article
2. THREE-STAGE sentiment analysis:
   - Opening sentiment (first 1-2 sections)
   - Middle sentiment (core sections, transitions)
   - Climax sentiment (conclusion/resolution)
3. Primary business context
4. Recommended number of images (3-5)
5. Which sections should get images (distributed across 3 stages)

Base recommendations on:
- Article length ({total_words} words)
- Number of sections ({len(raw_sections)})
- Narrative complexity
- Sentiment variation across the 3 stages

Return complete analysis with all sections analyzed."""

    try:
        # Run AI analysis
        result = await agent.run(prompt)

        analysis = result.data

        # Ensure we have correct number of sections
        if len(analysis.sections) != len(raw_sections):
            activity.logger.warning(
                f"AI returned {len(analysis.sections)} sections but we have {len(raw_sections)}. Adjusting..."
            )
            # Take first N sections or pad if needed
            if len(analysis.sections) > len(raw_sections):
                analysis.sections = analysis.sections[:len(raw_sections)]

        # Add word counts from raw sections
        for i, section in enumerate(analysis.sections):
            if i < len(raw_sections):
                section.word_count = count_words(raw_sections[i]["content"])
                # Ensure index is set
                section.index = i

        # Convert to dict for return
        result_dict = {
            "sections": [
                {
                    "index": s.index,
                    "title": s.title,
                    "content": raw_sections[s.index]["content"] if s.index < len(raw_sections) else "",
                    "word_count": s.word_count,
                    "sentiment": s.sentiment,
                    "sentiment_intensity": s.sentiment_intensity,
                    "visual_moment": s.visual_moment,
                    "should_generate_image": s.should_generate_image
                }
                for s in analysis.sections
            ],
            "total_word_count": total_words,
            "recommended_image_count": analysis.recommended_image_count,
            "narrative_arc": analysis.narrative_arc,
            "key_sentiment_shifts": analysis.key_sentiment_shifts
        }

        # Count how many images recommended
        image_sections = [s for s in result_dict["sections"] if s["should_generate_image"]]

        activity.logger.info(
            f"Analysis complete: {len(image_sections)} sections marked for images "
            f"(recommended: {analysis.recommended_image_count})"
        )
        activity.logger.info(f"Narrative arc: {analysis.narrative_arc}")
        activity.logger.info(f"Sentiment shifts at sections: {analysis.key_sentiment_shifts}")

        return result_dict

    except Exception as e:
        activity.logger.error(f"Failed to analyze sections: {e}")

        # Fallback: simple structure
        fallback_sections = []
        for i, raw_section in enumerate(raw_sections):
            fallback_sections.append({
                "index": i,
                "title": raw_section["title"],
                "content": raw_section["content"],
                "word_count": count_words(raw_section["content"]),
                "sentiment": "neutral",
                "sentiment_intensity": 0.5,
                "visual_moment": f"Professional illustration representing {raw_section['title']}",
                "should_generate_image": i in [0, len(raw_sections) // 2, len(raw_sections) - 1]  # First, middle, last
            })

        # Calculate recommended images (3-5 based on length)
        if total_words < 800:
            recommended = 3
        elif total_words < 1500:
            recommended = 4
        else:
            recommended = 5

        return {
            "sections": fallback_sections,
            "total_word_count": total_words,
            "recommended_image_count": recommended,
            "narrative_arc": "unknown (fallback mode)",
            "key_sentiment_shifts": []
        }
