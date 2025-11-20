"""
Article Content Generation

Generates comprehensive articles using AI with rich research context.
"""

from temporalio import activity
from typing import Dict, Any
from pydantic_ai import Agent

from src.models.article import ArticlePayload
from src.utils.config import config


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
        Dict with article (ArticlePayload), cost, model_used
    """
    activity.logger.info(f"Generating {article_type} article: {topic}")

    try:
        # Get AI model configuration
        provider, model_name = config.get_ai_model()
        activity.logger.info(f"Using AI: {provider}:{model_name}")

        # Create article generation agent
        article_agent = Agent(
            f'{provider}:{model_name}',
            output_type=ArticlePayload,
            instructions=get_article_instructions(article_type, app, target_word_count)
        )

        # Build context for AI
        context = build_article_context(topic, article_type, research_context, target_word_count)

        # Generate article
        result = await article_agent.run(context)
        article = result.output

        # Calculate quality metrics
        article.word_count = len(article.content.split())
        article.reading_time_minutes = max(1, article.word_count // 200)  # ~200 wpm

        # Count H2 sections in content
        article.section_count = article.content.count('## ')

        activity.logger.info(
            f"Article generated: {article.word_count} words, "
            f"{article.section_count} sections"
        )

        return {
            "article": article.model_dump(),
            "cost": estimate_ai_cost(provider, model_name),
            "model_used": f"{provider}:{model_name}",
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"ARTICLE GENERATION FAILED: {e}", exc_info=True)

        # Return minimal article on error
        minimal_article = ArticlePayload(
            title=topic,
            slug=topic.lower().replace(" ", "-")[:50],
            content=f"## Introduction\n\nArticle about {topic} is currently being researched.",
            excerpt=f"Information about {topic}.",
            app=app,
            article_type=article_type,
            meta_description=f"Article about {topic}.",
            tags=[],
            word_count=10,
            reading_time_minutes=1
        )

        return {
            "article": minimal_article.model_dump(),
            "cost": 0.0,
            "model_used": "fallback",
            "success": False,
            "error": str(e)
        }


def get_article_instructions(article_type: str, app: str, target_word_count: int) -> str:
    """
    Get AI instructions based on article type.

    Args:
        article_type: news, guide, comparison
        app: Application context
        target_word_count: Target length

    Returns:
        System prompt for AI
    """
    base_instructions = f"""You are an expert journalist writing engaging, narrative articles for the {app} industry.

Write a compelling article that tells a story. Make it interesting, insightful, and well-researched.

**TARGET LENGTH**: ~{target_word_count} words

===== OUTPUT FIELDS =====

Generate these 8 fields:

1. **title**: Compelling headline
2. **slug**: URL version, lowercase with hyphens (e.g. "goldman-sachs-acquires-ai-startup")
3. **content**: Full article in markdown - THIS IS THE MAIN OUTPUT
4. **excerpt**: 1-2 sentence teaser
5. **meta_description**: SEO summary, 150-160 chars
6. **tags**: List of 5-8 relevant keywords
7. **app**: "{app}"
8. **article_type**: "{article_type}"

===== WRITING THE ARTICLE =====

Write naturally flowing content in markdown:
- Use ## for section headings (no H1 - title is separate)
- Write engaging prose that tells the story
- Include specific facts, figures, quotes from your research
- Link to sources: [Company Name](url)
- Be specific - use names, numbers, dates
- Cite sources with inline links

The article should read like quality journalism - informative, engaging, well-sourced.

"""

    # Type-specific guidance
    type_guidance = {
        "news": """
**NEWS ARTICLE**: Write like a news story.
- Lead with who/what/when/where/why
- Include background and context
- Cover deal/event details
- Discuss market implications
- Professional, objective tone
""",
        "guide": """
**GUIDE ARTICLE**: Write like a helpful guide.
- Explain what it is and who it's for
- Cover key concepts and requirements
- Provide step-by-step process
- Include tips and best practices
- Helpful, instructive tone
""",
        "comparison": """
**COMPARISON ARTICLE**: Write like an analytical comparison.
- Explain what's being compared and why
- Define comparison criteria
- Analyze each option with pros/cons
- Provide decision framework
- Analytical, balanced tone
"""
    }

    guidance = type_guidance.get(article_type, type_guidance["news"])

    return base_instructions + guidance + """

Write an article that people will actually want to read.
"""


def build_article_context(
    topic: str,
    article_type: str,
    research_context: Dict[str, Any],
    target_word_count: int
) -> str:
    """
    Build comprehensive context string for AI generation.

    Args:
        topic: Article topic
        article_type: Article type
        research_context: Research data
        target_word_count: Target length

    Returns:
        Formatted context string
    """
    lines = [
        f"TOPIC: {topic}",
        f"TYPE: {article_type}",
        f"TARGET LENGTH: ~{target_word_count} words",
        "",
        "Write a comprehensive article using the research below.",
        "",
        "=" * 70,
        ""
    ]

    # News articles from Serper
    news_articles = research_context.get("news_articles", [])
    if news_articles:
        lines.append("===== NEWS ARTICLES =====\n")
        for i, article in enumerate(news_articles[:15], 1):
            title = article.get('title', 'Untitled')
            url = article.get('url', '')
            snippet = article.get('snippet', '')
            date = article.get('date', '')

            lines.append(f"{i}. {title}")
            if date:
                lines.append(f"   Date: {date}")
            lines.append(f"   URL: {url}")
            if snippet:
                lines.append(f"   {snippet}")
            lines.append("")
        lines.append("=" * 70 + "\n")

    # Crawled full content from discovered URLs
    crawled_pages = research_context.get("crawled_pages", [])
    if crawled_pages:
        lines.append("===== FULL CONTENT FROM CRAWLED SOURCES =====\n")
        for i, page in enumerate(crawled_pages[:10], 1):
            url = page.get('url', '')
            title = page.get('title', 'Untitled')
            content = page.get('content', '')

            lines.append(f"{i}. {title}")
            lines.append(f"   URL: {url}")
            if content:
                lines.append(f"{content[:3000]}")
            lines.append("")
        lines.append("=" * 70 + "\n")

    # Exa research (high-quality sources)
    exa_results = research_context.get("exa_results", [])
    if exa_results:
        lines.append("===== EXA DEEP RESEARCH =====\n")
        for i, result in enumerate(exa_results[:5], 1):
            title = result.get('title', 'Untitled')
            url = result.get('url', '')
            content = result.get('content', '') or result.get('text', '')
            score = result.get('score', 0.0)

            lines.append(f"{i}. {title} (relevance: {score:.2f})")
            lines.append(f"   URL: {url}")
            if content:
                lines.append(f"{content[:2000]}")
            lines.append("")
        lines.append("=" * 70 + "\n")

    # Zep context (existing knowledge)
    zep_context = research_context.get("zep_context", {})
    if zep_context.get("articles") or zep_context.get("deals"):
        lines.append("===== EXISTING KNOWLEDGE (ZEP) =====\n")

        if zep_context.get("articles"):
            lines.append("Related Articles:")
            for article in zep_context["articles"][:5]:
                lines.append(f"- {article.get('name', '')}")
            lines.append("")

        if zep_context.get("deals"):
            lines.append("Related Deals:")
            for deal in zep_context["deals"][:5]:
                lines.append(f"- {deal.get('name', '')}")
            lines.append("")

        lines.append("=" * 70 + "\n")

    context = "\n".join(lines)

    # Truncate if too long
    max_length = 80000
    if len(context) > max_length:
        context = context[:max_length] + "\n\n[... content truncated ...]"

    return context


def estimate_ai_cost(provider: str, model: str) -> float:
    """
    Estimate AI generation cost.

    Args:
        provider: AI provider
        model: Model name

    Returns:
        Estimated cost in USD
    """
    cost_map = {
        "google": 0.015,
        "openai": 0.025,
        "anthropic": 0.035,
    }

    return cost_map.get(provider, 0.015)
