"""
Company Profile Generation Activity

Uses Pydantic AI to generate structured company profiles from research data.
"""

from temporalio import activity
from typing import Dict, Any
from pydantic_ai import Agent

from src.models.payload import CompanyPayload
from src.models.research import ResearchData
from src.utils.config import config


@activity.defn
async def generate_company_profile(
    research_data_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate comprehensive company profile using Pydantic AI.

    Uses Gemini 2.5 (or configured AI provider) to synthesize all
    research into a structured CompanyPayload.

    Args:
        research_data_dict: ResearchData as dict

    Returns:
        Dict with profile (CompanyPayload), cost, model_used
    """
    activity.logger.info("Generating company profile with Pydantic AI")

    # Convert dict back to ResearchData
    research = ResearchData(**research_data_dict)

    try:
        # Get AI model configuration
        provider, model_name = config.get_ai_model()
        activity.logger.info(f"Using AI provider: {provider}:{model_name}")

        # Create Pydantic AI agent
        company_agent = Agent(
            f'{provider}:{model_name}',
            result_type=CompanyPayload,
            system_prompt="""You are an expert company profiler.

Your task is to generate comprehensive, accurate company profiles based on research data.

IMPORTANT RULES:
1. Only include information you are confident about
2. Leave fields as null/empty if no reliable data found
3. Use Zep context to enrich deals and relationships
4. Extract hero_stats prominently (employees, founded_year, etc.)
5. Focus on factual information, not marketing fluff
6. For lists (services, clients, etc.), extract concrete examples
7. For notable_deals, include name, date, amount, parties involved
8. Calculate data_completeness_score honestly based on filled fields

QUALITY STANDARDS:
- Descriptions should be 2-3 paragraphs, professional tone
- Taglines should be 1 sentence, clear and descriptive
- All numbers should be formatted properly
- All dates should be ISO format or year only
- URLs should be complete and valid

Your output must strictly follow the CompanyPayload schema."""
        )

        # Build context for AI
        context = build_research_context(research)

        # Generate profile
        result = await company_agent.run(context)

        profile = result.data

        activity.logger.info(
            f"Profile generated: completeness={profile.data_completeness_score}, "
            f"confidence={profile.confidence_score}"
        )

        return {
            "profile": profile.model_dump(),
            "cost": estimate_ai_cost(provider, model_name),
            "model_used": f"{provider}:{model_name}",
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"Profile generation failed: {e}")

        # Return minimal profile on error
        minimal_profile = CompanyPayload(
            legal_name=research.company_name,
            website=research.normalized_url,
            headquarters_country=research.jurisdiction,
            company_type=research.category,
            research_date=research_data_dict.get("research_date", ""),
            confidence_score=research.confidence_score,
            ambiguity_signals=research.ambiguity_signals,
            data_completeness_score=10.0
        )

        return {
            "profile": minimal_profile.model_dump(),
            "cost": 0.0,
            "model_used": "fallback",
            "success": False,
            "error": str(e)
        }


def build_research_context(research: ResearchData) -> str:
    """
    Build comprehensive context string for AI generation.

    Args:
        research: ResearchData object

    Returns:
        Formatted context string
    """
    lines = [
        f"COMPANY: {research.company_name}",
        f"DOMAIN: {research.domain}",
        f"URL: {research.normalized_url}",
        f"JURISDICTION: {research.jurisdiction}",
        f"CATEGORY: {research.category}",
        "",
        "=" * 60,
        ""
    ]

    # News articles
    if research.news_articles:
        lines.append("NEWS ARTICLES:")
        for i, article in enumerate(research.news_articles[:10], 1):
            lines.append(f"\n{i}. {article.get('title', '')}")
            lines.append(f"   URL: {article.get('url', '')}")
            snippet = article.get('snippet', '')
            if snippet:
                lines.append(f"   {snippet[:200]}")
        lines.append("\n" + "=" * 60 + "\n")

    # Website content
    if research.website_content:
        pages = research.website_content.get("pages", [])
        if pages:
            lines.append("WEBSITE CONTENT:")
            for page in pages[:5]:
                lines.append(f"\nPage: {page.get('title', 'Unknown')}")
                lines.append(f"URL: {page.get('url', '')}")
                content = page.get('content', '')
                if content:
                    lines.append(f"{content[:1000]}")
            lines.append("\n" + "=" * 60 + "\n")

    # Exa research
    if research.exa_research:
        results = research.exa_research.get("results", [])
        if results:
            lines.append("EXA RESEARCH:")
            for i, result in enumerate(results[:5], 1):
                lines.append(f"\n{i}. {result.get('title', '')}")
                lines.append(f"   Score: {result.get('score', 0.0):.2f}")
                content = result.get('content', '')
                if content:
                    lines.append(f"   {content[:500]}")
            lines.append("\n" + "=" * 60 + "\n")

    # Zep context (existing coverage)
    if research.zep_context:
        articles = research.zep_context.get("articles", [])
        deals = research.zep_context.get("deals", [])

        if articles or deals:
            lines.append("EXISTING COVERAGE IN ZEP:")

            if articles:
                lines.append("\nArticles:")
                for article in articles[:5]:
                    lines.append(f"- {article.get('name', '')}")

            if deals:
                lines.append("\nDeals:")
                for deal in deals[:5]:
                    lines.append(f"- {deal.get('name', '')}")

            lines.append("\n" + "=" * 60 + "\n")

    # Research metadata
    lines.extend([
        "RESEARCH METADATA:",
        f"Confidence: {research.confidence_score:.2f}",
        f"Ambiguous: {research.is_ambiguous}",
        f"Recommendation: {research.recommendation}"
    ])

    if research.ambiguity_signals:
        lines.append("\nAmbiguity Signals:")
        for signal in research.ambiguity_signals:
            lines.append(f"- {signal}")

    context = "\n".join(lines)

    # Truncate if too long (AI context limits)
    max_length = 50000  # ~50k chars for context
    if len(context) > max_length:
        context = context[:max_length] + "\n\n[... truncated for length ...]"

    return context


def estimate_ai_cost(provider: str, model: str) -> float:
    """
    Estimate AI generation cost.

    Args:
        provider: AI provider (google, openai, anthropic)
        model: Model name

    Returns:
        Estimated cost in USD
    """
    # Rough estimates per request
    cost_map = {
        "google": 0.01,      # Gemini 2.5 Flash
        "openai": 0.02,      # GPT-4o-mini
        "anthropic": 0.03,   # Claude Sonnet
    }

    return cost_map.get(provider, 0.01)
