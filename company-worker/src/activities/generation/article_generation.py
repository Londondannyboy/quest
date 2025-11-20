"""
Article Content Generation

Generates comprehensive articles using AI with rich research context.
Uses simple Pydantic model for AI output, then builds full payload.
"""

from temporalio import activity
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from slugify import slugify

from src.utils.config import config


# ============================================================================
# SIMPLE PYDANTIC MODEL FOR AI OUTPUT
# ============================================================================

class ArticleContentOutput(BaseModel):
    """Simple AI-generated article - just the core content."""
    title: str = Field(description="Compelling article headline")
    summary: str = Field(description="Article summary/excerpt (2-3 sentences)")
    content: str = Field(description="Full article content in markdown with ## headings")
    meta_description: str = Field(description="SEO meta description (150-160 chars)")
    tags: List[str] = Field(default_factory=list, description="5-8 relevant keywords")


# ============================================================================
# ARTICLE GENERATION ACTIVITY
# ============================================================================

@activity.defn
async def generate_article_content(
    topic: str,
    article_type: str,
    app: str,
    research_context: Dict[str, Any],
    target_word_count: int = 1500
) -> Dict[str, Any]:
    """
    Generate article content using Pydantic AI.

    Args:
        topic: Article topic/title
        article_type: Type (news, guide, comparison)
        app: Application context (placement, relocation, etc.)
        research_context: Dict with news, crawled_content, exa_results
        target_word_count: Target article length

    Returns:
        Dict with article payload, cost, model_used
    """
    activity.logger.info(f"Generating {article_type} article: {topic}")

    try:
        # Get AI model configuration
        provider, model_name = config.get_ai_model()
        activity.logger.info(f"Using AI: {provider}:{model_name}")

        # Create agent with simple output model
        agent = Agent(
            model=f'{provider}:{model_name}',
            result_type=ArticleContentOutput,
            system_prompt=get_system_prompt(article_type, app, target_word_count)
        )

        # Build context prompt
        prompt = build_prompt(topic, article_type, research_context, target_word_count)

        # Generate article
        result = await agent.run(prompt)
        article_output = result.data

        # Generate slug
        slug = slugify(article_output.title, max_length=100)

        # Calculate metrics
        word_count = len(article_output.content.split())
        section_count = article_output.content.count('## ')
        reading_time = max(1, word_count // 200)

        activity.logger.info(
            f"Article generated: {word_count} words, {section_count} sections"
        )

        # Build full payload
        payload = {
            "title": article_output.title,
            "slug": slug,
            "content": article_output.content,
            "excerpt": article_output.summary,
            "app": app,
            "article_type": article_type,
            "meta_description": article_output.meta_description,
            "tags": article_output.tags,

            # Metrics
            "word_count": word_count,
            "reading_time_minutes": reading_time,
            "section_count": section_count,

            # Image placeholders (populated by image generation)
            "featured_image_url": None,
            "featured_image_alt": None,
            "hero_image_url": None,
            "hero_image_alt": None,
            "content_image_1_url": None,
            "content_image_2_url": None,
            "content_image_3_url": None,
            "image_count": 0,

            # Metadata
            "author": "Quest Editorial Team",
            "status": "draft",
            "confidence_score": 1.0
        }

        return {
            "article": payload,
            "cost": estimate_ai_cost(provider, model_name),
            "model_used": f"{provider}:{model_name}",
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"ARTICLE GENERATION FAILED: {e}", exc_info=True)

        # Return minimal article on error
        slug = slugify(topic, max_length=100)

        payload = {
            "title": topic,
            "slug": slug,
            "content": f"## Introduction\n\nArticle about {topic} is currently being researched.",
            "excerpt": f"Information about {topic}.",
            "app": app,
            "article_type": article_type,
            "meta_description": f"Article about {topic}.",
            "tags": [],
            "word_count": 10,
            "reading_time_minutes": 1,
            "section_count": 1,
            "featured_image_url": None,
            "hero_image_url": None,
            "image_count": 0,
            "author": "Quest Editorial Team",
            "status": "draft",
            "confidence_score": 0.0
        }

        return {
            "article": payload,
            "cost": 0.0,
            "model_used": "fallback",
            "success": False,
            "error": str(e)
        }


def get_system_prompt(article_type: str, app: str, target_word_count: int) -> str:
    """Get system prompt for article generation."""

    type_guidance = {
        "news": "Write a news article with the most important information first (inverted pyramid). Keep it factual and cite sources.",
        "guide": "Write a helpful guide that explains concepts clearly with step-by-step instructions where appropriate.",
        "comparison": "Write an analytical comparison examining options objectively with pros/cons and recommendations."
    }

    guidance = type_guidance.get(article_type, type_guidance["news"])

    return f"""You are an expert journalist writing for a professional audience in the {app} industry.

Article Type: {article_type.upper()}
Target Length: ~{target_word_count} words
Guidance: {guidance}

Write a compelling, well-structured article from the research provided.

Guidelines:
- Write in third person, professional journalistic tone
- Lead with the most newsworthy/important information
- Include specific numbers, dates, and names when available
- Attribute information to sources with inline links [Source](url)
- Use markdown ## headings to structure content
- Write engaging prose that tells a story

Your output should have:
- title: Compelling headline
- summary: 2-3 sentence excerpt
- content: Full article in markdown (the main output)
- meta_description: SEO description (150-160 chars)
- tags: List of 5-8 keywords"""


def build_prompt(
    topic: str,
    article_type: str,
    research_context: Dict[str, Any],
    target_word_count: int
) -> str:
    """Build the prompt with all research context."""

    parts = [
        f"TOPIC: {topic}",
        f"TYPE: {article_type}",
        f"TARGET: ~{target_word_count} words",
        "",
        "Write a comprehensive article using this research:",
        "=" * 60
    ]

    # News articles from Serper
    news = research_context.get("news_articles", [])
    if news:
        parts.append("\n=== NEWS ARTICLES ===")
        for i, article in enumerate(news[:15], 1):
            parts.append(f"\n{i}. {article.get('title', 'Untitled')}")
            if article.get('date'):
                parts.append(f"   Date: {article['date']}")
            parts.append(f"   URL: {article.get('url', '')}")
            if article.get('snippet'):
                parts.append(f"   {article['snippet']}")

    # Crawled content
    crawled = research_context.get("crawled_pages", [])
    if crawled:
        parts.append("\n=== CRAWLED CONTENT ===")
        for i, page in enumerate(crawled[:10], 1):
            parts.append(f"\n{i}. {page.get('title', 'Untitled')}")
            parts.append(f"   URL: {page.get('url', '')}")
            content = page.get('content', '')
            if content:
                parts.append(content[:3000])

    # Exa research
    exa = research_context.get("exa_results", [])
    if exa:
        parts.append("\n=== EXA DEEP RESEARCH ===")
        for i, result in enumerate(exa[:5], 1):
            parts.append(f"\n{i}. {result.get('title', 'Untitled')}")
            parts.append(f"   URL: {result.get('url', '')}")
            content = result.get('content', '') or result.get('text', '')
            if content:
                parts.append(content[:2000])

    # Zep context
    zep = research_context.get("zep_context", {})
    if zep.get("articles") or zep.get("deals"):
        parts.append("\n=== EXISTING KNOWLEDGE ===")
        if zep.get("articles"):
            parts.append("Related Articles:")
            for a in zep["articles"][:5]:
                parts.append(f"- {a.get('name', '')}")
        if zep.get("deals"):
            parts.append("Related Deals:")
            for d in zep["deals"][:5]:
                parts.append(f"- {d.get('name', '')}")

    prompt = "\n".join(parts)

    # Truncate if too long
    if len(prompt) > 80000:
        prompt = prompt[:80000] + "\n\n[truncated]"

    return prompt


def estimate_ai_cost(provider: str, model: str) -> float:
    """Estimate AI generation cost."""
    costs = {
        "google": 0.015,
        "openai": 0.025,
        "anthropic": 0.035,
    }
    return costs.get(provider, 0.015)
