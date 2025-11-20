"""
Article Content Generation - Simplest Possible

Just get the AI to write the article. That's it.
"""

from temporalio import activity
from typing import Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from slugify import slugify

from src.utils.config import config


class ArticleOutput(BaseModel):
    """Just the article content - nothing else."""
    article: str = Field(description="The complete article in markdown format")


@activity.defn
async def generate_article_content(
    topic: str,
    article_type: str,
    app: str,
    research_context: Dict[str, Any],
    target_word_count: int = 1500
) -> Dict[str, Any]:
    """Generate article content using Pydantic AI."""
    activity.logger.info(f"Generating {article_type} article: {topic}")

    try:
        provider, model_name = config.get_ai_model()
        activity.logger.info(f"Using AI: {provider}:{model_name}")

        # Simplest possible agent - just output one string
        # pydantic_ai just wants the model name for Google
        model_str = model_name if provider == "google" else f'{provider}:{model_name}'
        agent = Agent(
            model_str,
            output_type=ArticleOutput,
            system_prompt=f"""You are an expert journalist. Write a {target_word_count}-word {article_type} article for the {app} industry.

Output your article in markdown format with:
- A title on the first line (no # prefix)
- Sections using ## headings
- Professional, engaging prose
- Facts and figures from the research

Just write the article. Nothing else."""
        )

        # Build simple prompt
        prompt = build_prompt(topic, research_context)

        # Generate
        result = await agent.run(prompt)
        article_text = result.output.article

        # Parse title from first line
        lines = article_text.strip().split('\n')
        title = lines[0].strip().lstrip('#').strip() if lines else topic
        content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else article_text

        # Generate metadata
        slug = slugify(title, max_length=100)
        word_count = len(content.split())

        # Extract first paragraph as excerpt
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
        excerpt = paragraphs[0][:200] if paragraphs else f"Article about {topic}"

        activity.logger.info(f"Article generated: {word_count} words")

        return {
            "article": {
                "title": title,
                "slug": slug,
                "content": content,
                "excerpt": excerpt,
                "app": app,
                "article_type": article_type,
                "meta_description": excerpt[:160],
                "tags": [],
                "word_count": word_count,
                "reading_time_minutes": max(1, word_count // 200),
                "section_count": content.count('## '),
                "featured_image_url": None,
                "hero_image_url": None,
                "image_count": 0,
                "author": "Quest Editorial Team",
                "status": "draft",
                "confidence_score": 1.0
            },
            "cost": 0.02,
            "model_used": f"{provider}:{model_name}",
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"FAILED: {e}", exc_info=True)

        slug = slugify(topic, max_length=100)
        return {
            "article": {
                "title": topic,
                "slug": slug,
                "content": f"## {topic}\n\nArticle generation failed: {e}",
                "excerpt": f"Article about {topic}.",
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
            },
            "cost": 0.0,
            "model_used": "fallback",
            "success": False,
            "error": str(e)
        }


def build_prompt(topic: str, research_context: Dict[str, Any]) -> str:
    """Build prompt with research."""
    parts = [f"Write an article about: {topic}\n"]

    # Add all research
    news = research_context.get("news_articles", [])
    if news:
        parts.append("\n=== NEWS ===")
        for a in news[:10]:
            parts.append(f"\n{a.get('title', '')}")
            parts.append(f"URL: {a.get('url', '')}")
            if a.get('snippet'):
                parts.append(a['snippet'])

    crawled = research_context.get("crawled_pages", [])
    if crawled:
        parts.append("\n=== SOURCES ===")
        for p in crawled[:5]:
            parts.append(f"\n{p.get('title', '')}")
            content = p.get('content', '')[:2000]
            if content:
                parts.append(content)

    exa = research_context.get("exa_results", [])
    if exa:
        parts.append("\n=== RESEARCH ===")
        for r in exa[:5]:
            parts.append(f"\n{r.get('title', '')}")
            content = r.get('content', '') or r.get('text', '')
            if content:
                parts.append(content[:2000])

    return '\n'.join(parts)
