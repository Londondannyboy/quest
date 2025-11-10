"""
Article Generation Activities

AI-powered article writing using Gemini.
"""

import os
import json
import re
import uuid
from datetime import datetime
from typing import Dict, Any
from temporalio import activity
import google.generativeai as genai

# Import config - using relative import to avoid circular dependency
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_app_config

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def create_slug(title: str) -> str:
    """Create URL-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = slug.strip('-')
    return slug[:50]


def extract_and_parse_json(text: str) -> dict:
    """
    Robustly extract and parse JSON from LLM response.

    Tries multiple extraction methods and fixes common JSON errors.
    """
    # Method 1: Try to find JSON between code blocks
    if "```json" in text:
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            json_text = match.group(1).strip()
        else:
            json_text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            json_text = match.group(1).strip()
        else:
            json_text = text.split("```")[1].split("```")[0].strip()
    else:
        # Method 2: Try to find JSON by looking for { ... }
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_text = match.group(0)
        else:
            json_text = text.strip()

    # Fix common JSON errors
    # Remove trailing commas before } or ]
    json_text = re.sub(r',\s*}', '}', json_text)
    json_text = re.sub(r',\s*]', ']', json_text)

    # Try parsing
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        # Log the problematic JSON for debugging
        activity.logger.error(f"JSON parse error at position {e.pos}: {e.msg}")
        activity.logger.error(f"Problematic JSON (first 500 chars): {json_text[:500]}")
        raise


@activity.defn(name="generate_article")
async def generate_article(
    brief: Dict[str, Any],
    research_brief: Dict[str, Any],
    app: str = "placement"
) -> Dict[str, Any]:
    """
    Generate complete article using Gemini

    Args:
        brief: ArticleBrief dict with title, angle, target_word_count
        research_brief: ResearchBrief dict with sources, citations, entities
        app: Application/site identifier

    Returns:
        Article dict with title, slug, content, etc.
    """
    activity.logger.info(f"✍️  Generating article: {brief.get('title', 'Unknown')}")
    activity.logger.info(f"   App: {app}")

    try:
        # Load app-specific configuration
        app_config = get_app_config(app)
        activity.logger.info(f"   Using config for: {app_config.display_name}")

        # Determine target word count from config
        min_words, max_words = app_config.word_count_range
        target_words = brief.get('target_word_count', (min_words + max_words) // 2)

        # Clamp to app's allowed range
        target_words = max(min_words, min(target_words, max_words))

        # Prepare research context
        sources_text = "\n\n".join([
            f"Source {i+1}: {s.get('title', 'Unknown')}\n{s.get('content', '')[:2000]}"
            for i, s in enumerate(research_brief.get('sources', []))
        ])

        entities_text = ", ".join([
            e.get('name', '') for e in research_brief.get('entities', [])
        ])

        key_findings = "\n".join([
            f"- {finding}" for finding in research_brief.get('key_findings', [])
        ])

        # Format app-specific writing guidelines
        guidelines_text = "\n".join([
            f"- {guideline}" for guideline in app_config.writing_guidelines
        ])

        # Format app-specific content requirements
        requirements_text = "\n".join([
            f"- {req}" for req in app_config.content_requirements
        ])

        # Format preferred sources
        sources_list = ", ".join(app_config.preferred_sources[:5])  # First 5 for brevity

        # Create app-specific generation prompt
        prompt = f"""Write an article for {app_config.display_name} about: {brief.get('title')}

PUBLICATION PROFILE:
- Target Audience: {app_config.target_audience}
- Content Focus: {app_config.content_focus}
- Tone & Style: {app_config.tone}
- Brand Voice (DO): {app_config.brand_voice.get('do', 'Professional')}
- Brand Voice (DON'T): {app_config.brand_voice.get('dont', 'Avoid casual language')}

ARTICLE BRIEF:
Angle: {brief.get('angle')}
Target word count: {target_words} words (range: {min_words}-{max_words})

Key entities: {entities_text}

Key findings:
{key_findings}

Research sources:
{sources_text[:10000]}

WRITING GUIDELINES:
{guidelines_text}

CONTENT REQUIREMENTS (Must Include):
{requirements_text}

CITATION REQUIREMENTS:
- Minimum {app_config.min_citations} citations required
- Preferred sources: {sources_list}
- Citation style: {app_config.citation_style}
- Use inline markdown hyperlinks: [Source Title](url)

STRUCTURAL REQUIREMENTS:
- Minimum {app_config.min_sections} major sections
- Section style: {app_config.section_style}
- Include anchor links in headings: ## <a id="section-slug"></a>Section Title
- Clear H2/H3 hierarchy

SEO REQUIREMENTS:
- Title: max 60 chars, action verbs, include primary keyword
- Target {app_config.target_keywords_count} relevant keywords
- SEO Focus: {app_config.seo_focus}
- Excerpt: 150-160 characters, compelling summary

Return ONLY a valid JSON object (no markdown formatting, no explanations):
{{
  "title": "Article Title (max 60 chars, use action verbs)",
  "slug": "url-friendly-slug",
  "content": "# Title\\n\\n## <a id='intro'></a>Introduction\\n\\nFull article content...",
  "excerpt": "Brief summary (150-160 chars)",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "word_count": {target_words}
}}

CRITICAL JSON REQUIREMENTS:
- Output MUST be valid, parseable JSON
- NO trailing commas in arrays or objects
- Escape all quotes inside strings with backslash
- content must be a single markdown string
- Include ALL required JSON fields
- Meet minimum citation requirement ({app_config.min_citations})
- Match the specified tone and brand voice
- Target {target_words} words (±10% acceptable)

EXAMPLE OF VALID JSON:
{{
  "title": "Example Title",
  "slug": "example-title",
  "content": "# Example\\n\\nThis is content with \\"quotes\\" escaped.",
  "excerpt": "Brief summary here",
  "keywords": ["key1", "key2"],
  "word_count": 1500
}}"""

        # Generate with Gemini Pro (better quality than Flash for long content)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4096
            )
        )

        content = response.text

        # Extract and parse JSON robustly
        article_data = extract_and_parse_json(content)

        # Generate article ID (UUID v4)
        article_id = str(uuid.uuid4())

        # Ensure required fields
        article_data["id"] = article_id
        article_data["app"] = app
        article_data["created_at"] = None  # Will be set by database
        article_data["published_at"] = None

        # Initialize metadata with app config tracking
        article_data["metadata"] = {
            "app_config_version": "v1",
            "target_word_count": target_words,
            "word_count_range": list(app_config.word_count_range),
            "min_citations_required": app_config.min_citations,
            "generated_at": datetime.utcnow().isoformat()
        }

        # Calculate word count if not provided
        if "word_count" not in article_data or article_data["word_count"] == 0:
            article_data["word_count"] = len(article_data.get("content", "").split())

        # Generate slug if not provided
        if not article_data.get("slug"):
            article_data["slug"] = create_slug(article_data.get("title", "untitled"))

        # Extract citations from content
        citations = []
        content_text = article_data.get("content", "")
        citation_matches = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content_text)
        for i, (title, url) in enumerate(citation_matches, 1):
            citations.append({
                "source_title": title,
                "source_url": url,
                "citation_number": i
            })

        article_data["citations"] = citations
        article_data["citation_count"] = len(citations)

        # Quality validation against app config
        quality_issues = []
        actual_word_count = article_data.get('word_count', 0)

        # Check word count range
        if actual_word_count < min_words:
            quality_issues.append(f"Below minimum word count ({actual_word_count} < {min_words})")
        elif actual_word_count > max_words:
            quality_issues.append(f"Exceeds maximum word count ({actual_word_count} > {max_words})")

        # Check citation count
        if len(citations) < app_config.min_citations:
            quality_issues.append(f"Insufficient citations ({len(citations)} < {app_config.min_citations})")

        # Set status based on quality checks
        if quality_issues:
            article_data["status"] = "draft"
            article_data["metadata"]["quality_issues"] = quality_issues
            activity.logger.warning(f"⚠️  Article has quality issues - marked as draft")
            for issue in quality_issues:
                activity.logger.warning(f"    - {issue}")
        else:
            article_data["status"] = "published"
            activity.logger.info(f"✅ Article meets quality standards - marked as published")

        activity.logger.info(f"✅ Article generated successfully")
        activity.logger.info(f"   Title: {article_data.get('title', '')[:50]}")
        activity.logger.info(f"   Words: {actual_word_count} (target: {min_words}-{max_words})")
        activity.logger.info(f"   Citations: {len(citations)} (min: {app_config.min_citations})")
        activity.logger.info(f"   Status: {article_data['status']}")
        activity.logger.info(f"   App: {app}")

        return article_data

    except Exception as e:
        activity.logger.error(f"❌ Article generation failed: {e}")

        # Return minimal fallback article
        return {
            "id": str(uuid.uuid4()),
            "title": brief.get('title', 'Article Generation Failed')[:60],
            "slug": create_slug(brief.get('title', 'failed')),
            "content": f"# {brief.get('title')}\n\nArticle generation failed: {str(e)}",
            "excerpt": "Article generation encountered an error",
            "keywords": [],
            "word_count": 0,
            "citation_count": 0,
            "citations": [],
            "app": app,
            "status": "draft"
        }
