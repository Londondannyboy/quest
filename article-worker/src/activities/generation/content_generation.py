"""
Article Content Generation

Generate comprehensive articles using AI with research data.
"""

from __future__ import annotations
from temporalio import activity
from typing import Dict, Any
from pydantic_ai import Agent

from src.models.article_payload import ArticlePayload, ArticleSection
from src.utils.config import config


@activity.defn
async def generate_article_content(research_data: dict) -> dict:
    """
    Generate article content from research data using Pydantic AI.

    Args:
        research_data: Combined research data with news, exa, crawl, zep context

    Returns:
        Dict with article payload and cost
    """
    activity.logger.info(f"Generating article: {research_data.get('topic')}")

    try:
        # Get AI model configuration
        provider, model_name = config.get_ai_model()
        activity.logger.info(f"Using AI provider: {provider}:{model_name}")

        # Create Pydantic AI agent for article generation
        article_agent = Agent(
            f'{provider}:{model_name}',
            output_type=ArticlePayload,
            instructions="""You are an expert business journalist who writes comprehensive, well-researched articles.

Your goal: Create professional, informative articles using all available research data.

===== ARTICLE STRUCTURE =====

Your article must include:

1. **Title** (H1):
   - Clear, compelling, SEO-friendly
   - 50-70 characters
   - Include primary keyword if possible
   - Example: "Digital Nomad Visa Greece: Complete Guide for 2025"

2. **Subtitle** (optional):
   - Supporting context or hook
   - 80-100 characters
   - Example: "Everything you need to know about relocating to Greece"

3. **Excerpt**:
   - Concise 1-2 sentence summary
   - 40-60 words
   - Captures main value proposition
   - Plain text, no markdown

4. **Content** (Markdown format):
   - Opening paragraph: Hook + context + thesis
   - Well-structured body with H2 sections
   - Clear, professional writing
   - Include specific facts, numbers, dates from research
   - Link to authoritative sources using markdown: [Source Name](url)
   - Conclude with actionable takeaways

5. **Sections** (H2 headings):
   - Break content into 4-8 logical sections
   - Each section has:
     * index: Section number (0-based)
     * title: H2 heading text
     * content: Section content (2-4 paragraphs)
     * word_count: Words in this section
   - Sections should flow naturally and build on each other

===== WRITING GUIDELINES =====

**Tone & Style:**
- Professional but accessible
- Authoritative and well-researched
- Use active voice
- Avoid jargon unless explained
- Write for educated general audience

**Content Quality:**
- Use specific details from research (dates, numbers, names)
- Cite sources inline with markdown links: [Company Name](url)
- Include 8-15 external links to research sources
- Balance depth with readability
- No fluff or generic statements

**Structure:**
- 2-4 sentence paragraphs (avoid walls of text)
- Use bullet points for lists
- Bold key terms and concepts
- Clear hierarchical structure (H2 sections only, no H3)

**SEO:**
- Include target keywords naturally
- Front-load important information
- Use semantic variations of keywords
- Create descriptive meta_description (150-160 chars)
- Generate 5-10 relevant tags

===== RESEARCH INTEGRATION =====

You have access to:
- News articles (Serper)
- Deep research (Exa)
- Crawled content (Crawl4AI)
- Knowledge graph context (Zep)

**Use all sources:**
- Synthesize information across sources
- Cite specific articles and sources
- Include dates and concrete details
- Link to original sources
- Identify contradictions or gaps

===== WORD COUNT =====

Target word count is specified in research_data. Distribute words across sections:
- 500-800 words: 3-5 sections
- 800-1500 words: 5-7 sections
- 1500-3000 words: 6-10 sections

===== META DESCRIPTION =====

Create compelling meta_description:
- 150-160 characters exactly
- Include primary keyword
- Call to action or value prop
- Plain text, no markdown

===== TAGS =====

Generate 5-10 relevant tags:
- Mix of broad and specific
- Include location if relevant
- Include industry/category
- Use lowercase with hyphens
- Example: ["digital-nomad", "greece", "visa", "relocation", "remote-work"]

===== CRITICAL RULES =====

1. **NO placeholders**: Every field must have real content
2. **Use research**: Don't make up facts, use provided data
3. **Link sources**: Add markdown links to research URLs
4. **Professional quality**: Publication-ready content
5. **Match format**: Respect article_format (article, guide, analysis)
6. **Target audience**: Write for the specified app context

===== OUTPUT REQUIREMENTS =====

Return ArticlePayload with:
- Populated title, subtitle, excerpt, content, sections
- Accurate word_count and reading_time_minutes
- SEO-optimized meta_description and tags
- All content fields filled (no NULLs)
- Professional, publication-ready quality

Remember: You are writing for real publication. Quality matters."""
        )

        # Build context from research data
        context = build_article_context(research_data)

        # Generate article
        result = await article_agent.run(context)
        article = result.output

        # Ensure app and format are set
        article.app = research_data.get("app", "placement")
        article.article_format = research_data.get("article_format", "article")

        activity.logger.info(
            f"Article generated: {article.word_count} words, "
            f"{len(article.sections)} sections, "
            f"reading time: {article.reading_time_minutes}min"
        )

        return {
            "article": article.model_dump(),
            "cost": estimate_ai_cost(provider, model_name, article.word_count),
            "model_used": f"{provider}:{model_name}",
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"❌ ARTICLE GENERATION FAILED: {e}", exc_info=True)

        # Return minimal fallback
        topic = research_data.get("topic", "Article")
        return {
            "article": {
                "title": topic,
                "subtitle": None,
                "slug": topic.lower().replace(" ", "-"),
                "content": f"# {topic}\n\nArticle content generation failed. Please try again.",
                "excerpt": f"Article about {topic}",
                "sections": [],
                "word_count": 50,
                "reading_time_minutes": 1,
                "meta_description": f"Article about {topic}",
                "tags": [],
                "target_keywords": [],
                "mentioned_companies": [],
                "app": research_data.get("app", "placement"),
                "article_format": research_data.get("article_format", "article")
            },
            "cost": 0.0,
            "model_used": "fallback",
            "success": False,
            "error": str(e)
        }


def build_article_context(research_data: dict) -> str:
    """
    Build comprehensive context string for AI article generation.

    Args:
        research_data: Research data dict

    Returns:
        Formatted context string optimized for article generation
    """
    lines = [
        f"TOPIC: {research_data.get('topic')}",
        f"APP CONTEXT: {research_data.get('app')}",
        f"TARGET WORD COUNT: {research_data.get('target_word_count', 1500)}",
        f"ARTICLE FORMAT: {research_data.get('article_format', 'article')}",
        ""
    ]

    if research_data.get('jurisdiction'):
        lines.append(f"JURISDICTION: {research_data['jurisdiction']}")
        lines.append("")

    if research_data.get('article_angle'):
        lines.append(f"EDITORIAL ANGLE: {research_data['article_angle']}")
        lines.append("")

    if research_data.get('target_keywords'):
        lines.append(f"TARGET KEYWORDS: {', '.join(research_data['target_keywords'])}")
        lines.append("")

    lines.extend([
        "Generate a comprehensive article using the research below.",
        "",
        "=" * 70,
        ""
    ])

    # News articles
    news_articles = research_data.get("news_articles", [])
    if news_articles:
        lines.append("===== NEWS ARTICLES (Serper) =====\n")
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

    # Exa research
    exa_research = research_data.get("exa_research", {})
    exa_results = exa_research.get("results", [])
    if exa_results:
        lines.append("===== EXA RESEARCH (High-Quality Sources) =====\n")
        for i, result in enumerate(exa_results[:10], 1):
            title = result.get('title', 'Untitled')
            url = result.get('url', '')
            content = result.get('content', '')
            score = result.get('score', 0.0)

            lines.append(f"{i}. {title} (relevance: {score:.2f})")
            lines.append(f"   URL: {url}")
            if content:
                lines.append(f"   {content[:2000]}")
            lines.append("")
        lines.append("=" * 70 + "\n")

    # Crawled news content
    news_crawl_pages = research_data.get("news_crawl_pages", [])
    if news_crawl_pages:
        lines.append("===== CRAWLED NEWS CONTENT (Crawl4AI) =====\n")
        for i, page in enumerate(news_crawl_pages[:8], 1):
            title = page.get('title', 'Untitled')
            url = page.get('url', '')
            content = page.get('content', '')

            lines.append(f"{i}. {title}")
            lines.append(f"   URL: {url}")
            if content:
                lines.append(f"   {content[:3000]}")
            lines.append("")
        lines.append("=" * 70 + "\n")

    # Authoritative crawled pages
    auth_crawl_pages = research_data.get("auth_crawl_pages", [])
    if auth_crawl_pages:
        lines.append("===== AUTHORITATIVE SOURCES (Crawl4AI) =====\n")
        for i, page in enumerate(auth_crawl_pages[:5], 1):
            title = page.get('title', 'Untitled')
            url = page.get('url', '')
            content = page.get('content', '')

            lines.append(f"{i}. {title}")
            lines.append(f"   URL: {url}")
            if content:
                lines.append(f"   {content[:3000]}")
            lines.append("")
        lines.append("=" * 70 + "\n")

    # Zep context
    zep_context = research_data.get("zep_context", {})
    if zep_context:
        related_companies = zep_context.get("related_companies", [])
        related_articles = zep_context.get("related_articles", [])

        if related_companies or related_articles:
            lines.append("===== EXISTING KNOWLEDGE (Zep) =====\n")

            if related_companies:
                lines.append("Related Companies:")
                for company in related_companies[:10]:
                    lines.append(f"- {company.get('name', '')}")
                lines.append("")

            if related_articles:
                lines.append("Related Articles:")
                for article in related_articles[:10]:
                    lines.append(f"- {article.get('name', '')}")
                lines.append("")

            lines.append("=" * 70 + "\n")

    context = "\n".join(lines)

    # Truncate if too long
    max_length = 80000
    if len(context) > max_length:
        context = context[:max_length] + "\n\n[... content truncated ...]"

    return context


def estimate_ai_cost(provider: str, model: str, word_count: int) -> float:
    """
    Estimate AI generation cost based on provider and output length.

    Args:
        provider: AI provider
        model: Model name
        word_count: Generated word count

    Returns:
        Estimated cost in USD
    """
    # Base costs per request + per-word multiplier
    if provider == "anthropic":
        base = 0.02
        per_word = 0.00002  # Claude is more expensive but better quality
    elif provider == "google":
        base = 0.01
        per_word = 0.00001  # Gemini is cost-effective
    elif provider == "openai":
        base = 0.015
        per_word = 0.000015
    else:
        base = 0.015
        per_word = 0.000015

    return base + (word_count * per_word)
