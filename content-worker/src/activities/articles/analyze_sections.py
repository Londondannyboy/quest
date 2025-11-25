"""
Article Section Analysis Activity

Extracts H2 sections from markdown/HTML content and analyzes narrative structure
for sequential image generation with Flux Kontext.

Uses direct Anthropic SDK to avoid pydantic_ai validation issues.
"""

import re
import json
from typing import Dict, Any, List
from temporalio import activity
import anthropic

from src.utils.config import config


def extract_sections(content: str) -> List[Dict[str, Any]]:
    """
    Parse content into sections (supports both markdown ## and HTML h2).
    """
    sections = []

    # Try HTML h2 tags first
    h2_pattern = r'<h2[^>]*>(.*?)</h2>'
    h2_matches = list(re.finditer(h2_pattern, content, re.DOTALL | re.IGNORECASE))

    if h2_matches:
        # HTML format - split by h2 tags
        for i, match in enumerate(h2_matches):
            title = re.sub(r'<[^>]+>', '', match.group(1)).strip()

            # Get content between this h2 and next h2 (or end)
            start = match.end()
            end = h2_matches[i + 1].start() if i + 1 < len(h2_matches) else len(content)
            section_content = content[start:end].strip()

            if section_content:
                sections.append({
                    "title": title,
                    "content": section_content
                })
    else:
        # Try markdown ## format
        pattern = r'^##\s+(.+?)$'
        splits = re.split(pattern, content, flags=re.MULTILINE)

        # First element is intro
        if splits[0].strip():
            sections.append({
                "title": "Introduction",
                "content": splits[0].strip()
            })

        # Process ## sections
        for i in range(1, len(splits), 2):
            if i + 1 < len(splits):
                title = splits[i].strip()
                section_content = splits[i + 1].strip()
                if section_content:
                    sections.append({
                        "title": title,
                        "content": section_content
                    })

    return sections


def count_words(text: str) -> int:
    """Count words, stripping HTML tags."""
    text_only = re.sub(r'<[^>]+>', '', text)
    return len(text_only.split())


@activity.defn
async def analyze_article_sections(
    content: str,
    title: str,
    app: str = "placement"
) -> Dict[str, Any]:
    """
    Analyze article structure for sequential image generation.

    Uses direct Anthropic SDK instead of pydantic_ai to avoid validation issues.
    """
    activity.logger.info(f"Analyzing sections for article: {title}")

    # Extract sections
    raw_sections = extract_sections(content)

    if not raw_sections:
        activity.logger.warning("No sections found, using full content")
        raw_sections = [{"title": title, "content": content}]

    total_words = count_words(content)
    activity.logger.info(f"Found {len(raw_sections)} sections, {total_words} words")

    # Prepare section summaries for AI
    sections_text = "\n\n".join([
        f"## {i+1}. {s['title']}\n{s['content'][:300]}..."
        for i, s in enumerate(raw_sections)
    ])

    try:
        # Use Anthropic SDK directly
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        prompt = f"""Analyze this article for image generation. Return a JSON object.

Article Title: {title}
Total Words: {total_words}
Number of Sections: {len(raw_sections)}

Sections:
{sections_text}

Return this exact JSON structure:
{{
  "sections": [
    {{
      "index": 0,
      "title": "Section title",
      "sentiment": "positive/negative/neutral/tense",
      "sentiment_intensity": 0.7,
      "visual_moment": "Description for image generation matching the tone",
      "should_generate_image": true
    }}
  ],
  "recommended_image_count": 4,
  "narrative_arc": "problem-solution/chronological/guide/etc",
  "key_sentiment_shifts": [1, 3]
}}

Rules:
- Analyze each section's sentiment and tone
- Recommend 3-5 images distributed across the article
- visual_moment should describe an appropriate image for that section
- Match tone to context (somber for layoffs, professional for deals)
- IMPORTANT: visual_moment descriptions must be purely visual - NO text, words, signs, or typography
- Only return valid JSON, no other text"""

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        # Parse JSON from response
        # Find JSON in response (may have markdown code blocks)
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in response")

        # Build result with full section content
        result_sections = []
        for i, raw_section in enumerate(raw_sections):
            # Find matching analysis section
            ai_section = next(
                (s for s in analysis.get("sections", []) if s.get("index") == i),
                None
            )

            result_sections.append({
                "index": i,
                "title": raw_section["title"],
                "content": raw_section["content"],
                "word_count": count_words(raw_section["content"]),
                "sentiment": ai_section.get("sentiment", "neutral") if ai_section else "neutral",
                "sentiment_intensity": ai_section.get("sentiment_intensity", 0.5) if ai_section else 0.5,
                "visual_moment": ai_section.get("visual_moment", f"Professional image for {raw_section['title']}") if ai_section else f"Professional image for {raw_section['title']}",
                "should_generate_image": ai_section.get("should_generate_image", False) if ai_section else False
            })

        result = {
            "sections": result_sections,
            "total_word_count": total_words,
            "recommended_image_count": analysis.get("recommended_image_count", 4),
            "narrative_arc": analysis.get("narrative_arc", "unknown"),
            "key_sentiment_shifts": analysis.get("key_sentiment_shifts", [])
        }

        image_count = sum(1 for s in result_sections if s["should_generate_image"])
        activity.logger.info(f"Analysis complete: {image_count} sections marked for images")

        return result

    except Exception as e:
        activity.logger.error(f"Failed to analyze sections: {e}")

        # Fallback: simple structure with first, middle, last sections getting images
        fallback_sections = []
        image_indices = [0, len(raw_sections) // 2, len(raw_sections) - 1]

        for i, raw_section in enumerate(raw_sections):
            fallback_sections.append({
                "index": i,
                "title": raw_section["title"],
                "content": raw_section["content"],
                "word_count": count_words(raw_section["content"]),
                "sentiment": "neutral",
                "sentiment_intensity": 0.5,
                "visual_moment": f"Professional illustration for {raw_section['title']}",
                "should_generate_image": i in image_indices
            })

        return {
            "sections": fallback_sections,
            "total_word_count": total_words,
            "recommended_image_count": min(3, len(raw_sections)),
            "narrative_arc": "unknown (fallback)",
            "key_sentiment_shifts": []
        }
