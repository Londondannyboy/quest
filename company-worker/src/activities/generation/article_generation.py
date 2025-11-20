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
        article.section_count = len(article.article_sections)
        article.word_count = len(article.content.split())
        article.reading_time_minutes = max(1, article.word_count // 200)  # ~200 wpm
        article.company_mention_count = len(article.mentioned_companies)

        activity.logger.info(
            f"Article generated: {article.section_count} sections, "
            f"{article.word_count} words, "
            f"{article.company_mention_count} companies"
        )

        return {
            "article": article.model_dump(),
            "cost": estimate_ai_cost(provider, model_name),
            "model_used": f"{provider}:{model_name}",
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"❌ ARTICLE GENERATION FAILED: {e}", exc_info=True)

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
            reading_time_minutes=1,
            section_count=0
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
        article_type: news, guide, comparison, analysis
        app: Application context
        target_word_count: Target length

    Returns:
        System prompt for AI
    """
    base_instructions = f"""You are an expert journalist writing engaging, narrative articles for the {app} industry.

Write a compelling article that tells a story. This is for humans to read - make it interesting, insightful, and well-researched.

**TARGET LENGTH**: ~{target_word_count} words

===== REQUIRED FIELDS (use these EXACT names) =====

You MUST provide these fields with these EXACT names:

1. **title** (string): Compelling headline
2. **slug** (string): URL version, lowercase with hyphens, e.g. "goldman-sachs-makes-bold-ai-bet"
3. **content** (string): Full article in markdown - this is the main output
4. **excerpt** (string): 1-2 sentence teaser, plain text
5. **meta_description** (string): SEO summary, 150-160 chars, plain text
6. **tags** (list of strings): 5-8 relevant keywords
7. **app** (string): "{app}"
8. **article_type** (string): "{article_type}"

===== COMPANY MENTIONS (use this EXACT structure) =====

**mentioned_companies** (list): For every company mentioned:
```json
[
  {{"name": "Company Name", "relevance_score": 0.9, "is_primary": true}},
  {{"name": "Another Co", "relevance_score": 0.5, "is_primary": false}}
]
```

===== ARTICLE SECTIONS (use this EXACT structure) =====

**article_sections** (dict): Organize your content:
```json
{{
  "introduction": {{
    "title": "Introduction",
    "content": "The markdown content...",
    "sources": ["https://source1.com"]
  }},
  "deal_details": {{
    "title": "Deal Details",
    "content": "More content...",
    "sources": ["https://source2.com"]
  }}
}}
```

===== WRITING THE ARTICLE =====

Write naturally flowing content using markdown:
- Use ## for section headings (no H1 - title is separate)
- Write engaging prose that tells the story
- Include specific facts, figures, quotes from your research
- Link to sources: [Company Name](url)

The article should read like quality journalism - informative, engaging, well-sourced.

===== LEAVE THESE AS DEFAULTS =====

Don't set: image fields, word_count, reading_time_minutes, section_count, company_mention_count, research_date, research_cost, data_sources, status, published_at, author, zep_graph_id, confidence_score.

"""

    # Type-specific instructions
    type_instructions = {
        "news": """
**NEWS ARTICLE STRUCTURE**:

1. **Introduction** (H2)
   - Lead paragraph with who, what, when, where, why
   - Key facts and figures
   - Context and background

2. **Background** (H2)
   - Company/entity background
   - Historical context
   - Previous related news

3. **Deal/Event Details** (H2)
   - Specific details of the news
   - Terms, conditions, timeline
   - Key parties involved

4. **Market Implications** (H2)
   - Impact on industry
   - Competitive landscape
   - Future outlook

5. **Expert Commentary** (H2) - Optional
   - Quotes from research
   - Expert analysis
   - Market reaction

**TONE**: Professional, objective, news-worthy
**IMAGERY**: Match sentiment to news (somber for layoffs, celebratory for acquisitions)
""",
        "guide": """
**GUIDE ARTICLE STRUCTURE**:

1. **Introduction** (H2)
   - What is this about?
   - Who is it for?
   - Why is it important?

2. **Overview** (H2)
   - Comprehensive explanation
   - Key concepts
   - Important considerations

3. **Requirements** (H2) - If applicable
   - Eligibility criteria
   - Documentation needed
   - Prerequisites

4. **Step-by-Step Process** (H2)
   - Numbered steps
   - Detailed instructions
   - Timeline and costs

5. **Tips & Best Practices** (H2)
   - Practical advice
   - Common mistakes
   - Pro tips

6. **Resources** (H2)
   - Useful links
   - Further reading
   - Contact information

**TONE**: Helpful, instructive, practical
**IMAGERY**: Optimistic, aspirational (for visas/relocation), professional (for business guides)
""",
        "comparison": """
**COMPARISON ARTICLE STRUCTURE**:

1. **Introduction** (H2)
   - What are we comparing?
   - Why this comparison matters
   - Methodology overview

2. **Comparison Criteria** (H2)
   - Key factors being compared
   - How we evaluated
   - Data sources

3. **Top Options** (H2)
   - Detailed analysis of each option
   - Use H3 for each item
   - Include pros/cons
   - Specific data points

4. **Comparison Table** (H2) - Optional
   - Side-by-side comparison
   - Key metrics
   - Pricing/features

5. **How to Choose** (H2)
   - Decision framework
   - Who each option is best for
   - Final recommendations

**TONE**: Analytical, balanced, objective
**IMAGERY**: Analytical (charts, comparisons, professional settings)
"""
    }

    article_specific = type_instructions.get(article_type, type_instructions["news"])

    return base_instructions + "\n" + article_specific + f"""

**QUALITY JOURNALISM**:
- Be specific - use names, numbers, facts from research
- Cite sources with links
- Write for smart readers who want insight
- Tell the story, don't just list facts

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
        "Generate a comprehensive article using the information below.",
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
                # Include substantial content (up to 3000 chars per page)
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
            content = result.get('content', '') or result.get('text', '')  # Exa uses 'content'
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
    max_length = 80000  # Large context for comprehensive articles
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
        "google": 0.015,     # Gemini 2.5 Flash
        "openai": 0.025,     # GPT-4o-mini
        "anthropic": 0.035,  # Claude Sonnet
    }

    return cost_map.get(provider, 0.015)
