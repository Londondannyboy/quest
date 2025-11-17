"""
Company Profile Generation V2 - Narrative-First

Generates flexible, narrative company profiles that only include sections
where substantial information is available. No NULL fields, no forced structure.
"""

from __future__ import annotations

from temporalio import activity
from typing import Dict, Any
from pydantic_ai import Agent

from src.models.payload_v2 import CompanyPayload, ProfileSection
from src.models.research import ResearchData
from src.utils.config import config


@activity.defn
async def generate_company_profile_v2(
    research_data_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate narrative company profile using Pydantic AI.

    Uses flexible, narrative-first approach: only creates sections where
    meaningful content can be generated from research data.

    Args:
        research_data_dict: ResearchData as dict

    Returns:
        Dict with profile (CompanyPayload), cost, model_used
    """
    activity.logger.info("Generating narrative company profile (V2)")

    # Convert dict back to ResearchData
    research = ResearchData(**research_data_dict)

    try:
        # Get AI model configuration
        provider, model_name = config.get_ai_model()
        activity.logger.info(f"Using AI provider: {provider}:{model_name}")

        # Create Pydantic AI agent
        company_agent = Agent(
            f'{provider}:{model_name}',
            output_type=CompanyPayload,
            instructions="""You are an expert company profiler who creates rich, narrative company profiles.

Your goal: Generate comprehensive, readable profiles using whatever information is available. Be flexible, not rigid.

===== STRUCTURED DATA (extract if clearly stated) =====

Extract these ONLY if explicitly mentioned:
- industry: Primary industry/sector
- headquarters_city, headquarters_country: From website footers, contact pages, addresses
- founded_year: Only if explicitly stated (e.g., "Founded in 2015", "Established 1988")
- employee_range: Only if mentioned (use: "1-10", "10-50", "50-100", "100-500", "500+")
- phone, linkedin_url, twitter_url: Extract if found

If not found, leave as null. Don't guess or infer these structured fields.

===== NARRATIVE SECTIONS (create only if you have substantial content) =====

Generate rich narrative sections using markdown. Only create sections where you have 2+ sentences of meaningful content.

**Standard Sections:**

1. **overview** (ALWAYS create this):
   - 2-4 paragraphs describing what the company does
   - Synthesize from website content, news, research
   - Focus on: business model, value proposition, target market
   - Professional, comprehensive tone
   - Example: "Thrive Alternative Investments is a specialized placement agent..."

2. **services** (if services/products are described):
   - What they offer
   - Who they serve (clients/customers)
   - How they differentiate
   - Service categories or product lines
   - Example: "The firm provides end-to-end capital raising services..."

3. **team** (if executive/founder info found):
   - Key executives and titles
   - Founder background/story
   - Team expertise and credentials
   - Leadership philosophy
   - Example: "Led by CEO Sarah Johnson, a 20-year veteran of..."

4. **track_record** (if deals/clients/results mentioned):
   - Notable transactions or projects
   - Key clients or partnerships
   - Metrics and results (e.g., "$2B raised", "50+ deals")
   - Awards or recognition
   - Example: "The firm has facilitated over $2B in capital..."

5. **locations** (if multiple offices or geographic presence):
   - Office locations
   - Geographic coverage
   - International presence
   - Example: "With offices in New York, London, and Singapore..."

6. **specialization** (if specific focus areas mentioned):
   - Areas of expertise
   - Industry focus
   - Investment preferences (for finance)
   - Niche or positioning
   - Example: "Specializes in emerging markets and impact investments..."

7. **technology** (if tech stack/platform mentioned):
   - Technology approach
   - Platforms or tools used
   - Innovation or R&D
   - Example: "Built on a proprietary matching platform..."

8. **news** (if recent developments found):
   - Recent news or press releases
   - Company updates
   - Growth milestones
   - Example: "Recently announced expansion into European markets..."

9. **clients** (if client info available):
   - Key clients or customer segments
   - Case studies or testimonials
   - Example: "Serves leading institutional investors including..."

**Writing Guidelines:**

- Use natural, professional language
- Be specific: include names, numbers, details from research
- Synthesize from all sources (website, news, Exa, Zep)
- Use markdown for formatting (bold, lists, etc.)
- Each section should stand alone and be complete
- 2-4 sentences minimum per section
- Don't create sections if you only have vague or generic info

**CRITICAL - Links and References:**

- ALWAYS add external links using markdown: [Company Name](https://example.com)
- Link to the company website when first mentioning it
- Link to news sources when citing articles or announcements
- Link to partner companies or clients when mentioned
- Add at least ONE internal link to "top private equity placement agents" or "leading placement agents"
- Example internal link: "As one of the [leading placement agents](/) in the industry..."
- Example external link: "[Evercore](https://www.evercore.com) specializes in..."
- Every section should have 1-3 relevant links where appropriate
- Use descriptive anchor text, not "click here" or bare URLs

**Content Quality:**

✅ Good: "Thrive Alternative Investments specializes in connecting institutional investors with alternative asset managers. The firm focuses on private equity, venture capital, and real estate funds, providing comprehensive capital raising services including investor identification, roadshow coordination, and closing support."

❌ Bad: "This company provides financial services." (too vague, too short)

✅ Good: "Led by Managing Partner John Smith, formerly a senior executive at Goldman Sachs with 25 years in alternative investments."

❌ Bad: "The company has a leadership team." (too generic)

===== SOURCE ATTRIBUTION =====

For each section, note the sources (URLs) that provided the information. This builds credibility.

===== OUTPUT STRUCTURE =====

Return a CompanyPayload with:
- Populated structured fields (only if clearly found)
- profile_sections dict with only meaningful sections
- confidence_score (0-1) based on source quality
- sources list with all URLs used

===== REMEMBER =====

- Quality over quantity
- Only create sections where you have real information
- Better to have 3 great sections than 7 weak ones
- Synthesize and write naturally
- Professional tone, specific details

Your output must follow the CompanyPayload schema."""
        )

        # Build context for AI
        context = build_research_context(research)

        # Generate profile
        result = await company_agent.run(context)

        profile = result.output

        # Calculate quality metrics
        profile.section_count = len(profile.profile_sections)
        profile.total_content_length = sum(
            len(section.content)
            for section in profile.profile_sections.values()
        )

        activity.logger.info(
            f"Profile generated: {profile.section_count} sections, "
            f"{profile.total_content_length} chars, "
            f"confidence={profile.confidence_score:.2f}"
        )

        return {
            "profile": profile.model_dump(),
            "cost": estimate_ai_cost(provider, model_name),
            "model_used": f"{provider}:{model_name}",
            "success": True,
            "section_count": profile.section_count
        }

    except Exception as e:
        activity.logger.error(f"Profile generation failed: {e}")

        # Return minimal profile on error
        minimal_profile = CompanyPayload(
            legal_name=research.company_name,
            website=research.normalized_url,
            domain=research.domain,
            slug=research.company_name.lower().replace(" ", "-"),
            company_type=research.category,
            headquarters_country=research.jurisdiction,
            research_date=research_data_dict.get("research_date", ""),
            confidence_score=research.confidence_score,
            profile_sections={
                "overview": ProfileSection(
                    title="Overview",
                    content=f"{research.company_name} is a company in the {research.category} sector. Limited information is currently available.",
                    confidence=0.3
                )
            }
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
        Formatted context string optimized for narrative generation
    """
    lines = [
        f"COMPANY: {research.company_name}",
        f"DOMAIN: {research.domain}",
        f"URL: {research.normalized_url}",
        f"JURISDICTION: {research.jurisdiction}",
        f"CATEGORY: {research.category}",
        "",
        "Generate a rich, narrative profile using the information below.",
        "Only create sections where you have substantial, specific content.",
        "",
        "=" * 70,
        ""
    ]

    # Website content (primary source)
    if research.website_content:
        pages = research.website_content.get("pages", [])
        if pages:
            lines.append("===== WEBSITE CONTENT =====\n")
            for page in pages[:5]:  # Top 5 pages
                title = page.get('title', 'Untitled')
                url = page.get('url', '')
                content = page.get('content', '')

                lines.append(f"Page: {title}")
                lines.append(f"URL: {url}")
                if content:
                    # Include more content for narrative generation
                    lines.append(f"{content[:2000]}")
                lines.append("")
            lines.append("=" * 70 + "\n")

    # News articles
    if research.news_articles:
        lines.append("===== NEWS ARTICLES =====\n")
        for i, article in enumerate(research.news_articles[:10], 1):
            title = article.get('title', 'Untitled')
            url = article.get('url', '')
            snippet = article.get('snippet', '')

            lines.append(f"{i}. {title}")
            lines.append(f"   URL: {url}")
            if snippet:
                lines.append(f"   {snippet}")
            lines.append("")
        lines.append("=" * 70 + "\n")

    # Exa research (high-quality sources)
    if research.exa_research:
        results = research.exa_research.get("results", [])
        if results:
            lines.append("===== EXA RESEARCH (HIGH-QUALITY SOURCES) =====\n")
            for i, result in enumerate(results[:5], 1):
                title = result.get('title', 'Untitled')
                score = result.get('score', 0.0)
                content = result.get('content', '')

                lines.append(f"{i}. {title} (relevance: {score:.2f})")
                if content:
                    lines.append(f"{content[:1500]}")
                lines.append("")
            lines.append("=" * 70 + "\n")

    # Zep context (existing knowledge)
    if research.zep_context:
        articles = research.zep_context.get("articles", [])
        deals = research.zep_context.get("deals", [])

        if articles or deals:
            lines.append("===== EXISTING KNOWLEDGE (ZEP) =====\n")

            if articles:
                lines.append("Related Articles:")
                for article in articles[:5]:
                    lines.append(f"- {article.get('name', '')}")
                lines.append("")

            if deals:
                lines.append("Related Deals:")
                for deal in deals[:5]:
                    lines.append(f"- {deal.get('name', '')}")
                lines.append("")

            lines.append("=" * 70 + "\n")

    # Research quality indicators
    lines.extend([
        "===== RESEARCH QUALITY =====",
        f"Confidence Score: {research.confidence_score:.2f}",
        f"Is Ambiguous: {research.is_ambiguous}",
        f"Recommendation: {research.recommendation}",
        ""
    ])

    if research.ambiguity_signals:
        lines.append("Ambiguity Signals:")
        for signal in research.ambiguity_signals:
            lines.append(f"- {signal}")
        lines.append("")

    context = "\n".join(lines)

    # Truncate if too long (AI context limits)
    max_length = 60000  # More room for narrative generation
    if len(context) > max_length:
        context = context[:max_length] + "\n\n[... content truncated ...]"

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
    # Rough estimates per request (narrative generation uses more tokens)
    cost_map = {
        "google": 0.015,     # Gemini 2.5 Flash (slightly more for longer output)
        "openai": 0.025,     # GPT-4o-mini
        "anthropic": 0.035,  # Claude Sonnet
    }

    return cost_map.get(provider, 0.015)
