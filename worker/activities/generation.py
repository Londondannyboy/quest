"""
Article Generation Activities

AI-powered article writing using Gemini.
"""

import os
import json
import re
from typing import Dict, Any
from temporalio import activity
import google.generativeai as genai
import ulid

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def create_slug(title: str) -> str:
    """Create URL-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = slug.strip('-')
    return slug[:50]


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

    try:
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

        # Create generation prompt
        prompt = f"""Write a professional, data-driven article about: {brief.get('title')}

Angle: {brief.get('angle')}
Target word count: {brief.get('target_word_count', 1500)} words

Key entities: {entities_text}

Key findings:
{key_findings}

Research sources:
{sources_text[:10000]}

Requirements:
- Professional, authoritative tone
- Clear section structure with H2/H3 headers
- Include anchor links in headings: ## <a id="section-slug"></a>Section Title
- Use inline markdown hyperlinks for citations: [Source](url)
- Target {brief.get('target_word_count', 1500)} words
- SEO-optimized title (<60 chars, action verbs)

Return ONLY a JSON object:
{{
  "title": "Article Title (max 60 chars, use action verbs)",
  "slug": "url-friendly-slug",
  "content": "# Title\\n\\n## <a id='intro'></a>Introduction\\n\\nFull article content...",
  "excerpt": "Brief summary (150-160 chars)",
  "keywords": ["keyword1", "keyword2"],
  "word_count": 1500
}}

CRITICAL:
- content must be a single markdown string
- Include ALL required JSON fields
- Use inline citations: [Source Title](url)"""

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

        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        article_data = json.loads(content)

        # Generate article ID (ULID - time-sortable)
        article_id = str(ulid.new())

        # Ensure required fields
        article_data["id"] = article_id
        article_data["app"] = app
        article_data["created_at"] = None  # Will be set by database
        article_data["published_at"] = None
        article_data["status"] = "published"

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

        activity.logger.info(f"✅ Article generated successfully")
        activity.logger.info(f"   Title: {article_data.get('title', '')[:50]}")
        activity.logger.info(f"   Words: {article_data.get('word_count', 0)}")
        activity.logger.info(f"   Citations: {len(citations)}")
        activity.logger.info(f"   App: {app}")

        return article_data

    except Exception as e:
        activity.logger.error(f"❌ Article generation failed: {e}")

        # Return minimal fallback article
        return {
            "id": str(ulid.new()),
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
