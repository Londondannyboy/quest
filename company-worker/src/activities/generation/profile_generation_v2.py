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
        model_str = model_name if provider == "google" else f'{provider}:{model_name}'
        company_agent = Agent(
            model_str,
            output_type=CompanyPayload,
            instructions="""You are an expert company profiler who creates rich, narrative company profiles.

Your goal: Generate comprehensive, readable profiles using whatever information is available. Be flexible, not rigid.

===== STRUCTURED DATA (extract if clearly stated) =====

Extract these ONLY if explicitly mentioned:
- industry: Primary industry/sector
- headquarters_city, headquarters_country: From website footers, contact pages, addresses
- founded_year: Only if explicitly stated (e.g., "Founded in 2015", "Established 1988")
- employee_range: Only if mentioned (use: "1-10", "10-50", "50-100", "100-500", "500+")
- linkedin_url: ONLY if found on company's official website (public declaration)

**IMPORTANT - STRUCTURED FIELDS FORMAT:**
- legal_name: Plain text company name only
- tagline: ALWAYS WRITE a compelling one sentence tagline, 10-15 words max, plain text (NEVER leave null)
- short_description: ALWAYS WRITE a concise 1-2 sentence summary (40-60 words) for collection cards - synthesize from research, plain text only (NEVER leave null)
- NO URLs, NO links, NO markdown in ANY structured fields above

**PRIVACY EXCLUSIONS - DO NOT EXTRACT:**
- phone: Never extract phone numbers
- email: Never extract email addresses
- twitter_url: Do not extract unless officially linked on website

For other structured fields (industry, headquarters, founded_year, etc.), only extract if explicitly found. Don't guess.

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
   - IMPORTANT: Break into subsections or bullet points if more than 3-4 people
   - Use **bold names** for each executive
   - Example: "**Sarah Johnson, CEO**: A 20-year veteran of..."

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

10. **deals** (if deals/transactions/announcements found):
   - **CRITICAL - MUST NAME ALL PARTIES**: Every deal MUST identify ALL companies/entities involved
   - **Format each deal as a bullet point** with this structure:
     * WHO: All parties involved (buyer, seller, target, fund, etc.) - USE FULL COMPANY NAMES
     * WHAT: Transaction type (M&A advisory, acquisition, fund closing, IPO, separation, investment, etc.)
     * VALUE: Deal size/value if available (e.g., $29.1 billion, $500M, etc.)
     * WHEN: **CRITICAL** - Must be MONTH or QUARTER, not just year (e.g., "November 2024", "Q2 2024", "March 2025")
       - WRONG: "2025" or "2024"
       - RIGHT: "Q1 2025", "November 2024", "March 2025"
     * SOURCE: Link to announcement or press release (REQUIRED)

   - **WRONG - TOO VAGUE:**
     * ❌ "Financial Advisor on a pending $29.1 billion sale (2025)"
     * ❌ "Financial Advisor on the separation of a Biosciences business"
     * ❌ "Lead advisor on major acquisition"

   - **RIGHT - SPECIFIC WITH ALL PARTIES:**
     * ✅ "Advised [Pfizer on its $29.1B sale of its Consumer Healthcare division to GSK](https://source.com) - Completed Q1 2025"
     * ✅ "Lead financial advisor to [Thermo Fisher on the $7.2B separation of its Biosciences Solutions business into a standalone public company called NewCo](https://source.com) - Expected 2025"
     * ✅ "Advised [H.I.G Capital on its $125M growth investment into Rely Home](https://source.com) - November 2024"

   - **If you CANNOT find who the buyer/seller/target companies are, DO NOT include that deal**
   - Include appointments, market reports, fund closings, investments - ANY significant announcement with dates and links

11. **resources** (ALWAYS create this - list ALL sources used):
   - Citations and references section
   - List all URLs consulted during research
   - Format: "- [Source Name](url): Brief description"
   - Include news articles, company pages, industry reports
   - Example: "- [Company Website](https://example.com): Official company information"

**Writing Guidelines:**

- Use natural, professional language
- Be specific: include names, numbers, details from research
- Synthesize from all sources (website, news, Exa, Zep)
- Use markdown for formatting (bold, lists, etc.)
- Each section should stand alone and be complete
- 2-4 sentences minimum per section
- Don't create sections if you only have vague or generic info
- **CRITICAL - NO HONORIFICS**: NEVER use Mr., Mrs., Ms., Dr., Prof., etc. - just write full names directly
  * WRONG: "Mr. Altman founded the company"
  * RIGHT: "Roger Altman founded the company"
- Write naturally flowing prose with clear sentence boundaries
- **CRITICAL**: Break up large text blocks with:
  - Bullet points for lists (executives, services, locations)
  - Bold names/subheadings for structure
  - Short paragraphs (2-4 sentences max)
  - Don't write massive walls of text - break them up!

**CRITICAL - Links and References:**

- ALWAYS add MANY external links using markdown: [Company Name](https://example.com)
- Link to the company website when first mentioning it
- Link to news sources when citing articles or announcements
- Link to partner companies or clients when mentioned
- Link to industry reports, research papers, or credible sources
- Add at least ONE internal link to "top private equity placement agents" or "leading placement agents"
- Example internal link: "As one of the [leading placement agents](/) in the industry..."
- Example external link: "[Evercore](https://www.evercore.com) specializes in..."
- **IMPORTANT**: Aim for 2-5 relevant links per section (more is better for authority)
- Use descriptive anchor text, not "click here" or bare URLs
- In deals section: EVERY deal/announcement MUST have a source link
- In resources section: List EVERY URL used with description

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

        # Privacy filter: Remove personal contact info
        profile.phone = None
        if profile.phone:
            activity.logger.info("Removed phone number for privacy")

        # Note: LinkedIn is OK if it was on their website (public declaration)

        # Clean markdown links and URLs from structured fields (plain text only)
        import re

        def clean_text_field(text):
            if not text:
                return text
            # Remove markdown links: [text](url) -> text
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
            # Remove incomplete markdown links
            text = re.sub(r'\[([^\]]+)\]\(.*$', r'\1', text)
            # Remove standalone URLs (http:// or https://)
            text = re.sub(r'\(https?://[^\)]+\)', '', text)
            text = re.sub(r'https?://\S+', '', text)
            # Clean up extra spaces
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        profile.tagline = clean_text_field(profile.tagline)
        profile.short_description = clean_text_field(profile.short_description)
        profile.legal_name = clean_text_field(profile.legal_name)

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
        activity.logger.error(f"❌ PROFILE GENERATION FAILED: {e}", exc_info=True)
        activity.logger.error(f"❌ This is a CRITICAL ERROR - profile will be incomplete!")

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

    # Skip ambiguity indicators - AI can determine category from content

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
