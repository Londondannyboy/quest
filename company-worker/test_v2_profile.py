#!/usr/bin/env python3
"""
Test V2 Profile Generation

Tests the new narrative-first profile generation approach.
Fetches research data for an existing company and generates a V2 profile.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any, Dict
from datetime import datetime

from pydantic_ai import Agent
from pydantic import BaseModel, Field


# Inline model definitions to avoid import issues
class ProfileSection(BaseModel):
    """A narrative section of the company profile"""
    title: str
    content: str
    confidence: float = 1.0
    sources: list[str] = []


class CompanyPayload(BaseModel):
    """Simplified, flexible company profile"""
    legal_name: str
    website: str
    domain: str
    slug: str
    company_type: str
    industry: str | None = None
    headquarters_city: str | None = None
    headquarters_country: str | None = None
    founded_year: int | None = None
    employee_range: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    twitter_url: str | None = None
    profile_sections: dict[str, ProfileSection] = {}
    logo_url: str | None = None
    featured_image_url: str | None = None
    research_date: str = ""
    last_updated: str = ""
    confidence_score: float = 1.0
    research_cost: float = 0.0
    data_sources: dict[str, Any] = {}
    sources: list[str] = []
    zep_graph_id: str | None = None
    zep_facts_count: int = 0
    section_count: int = 0
    total_content_length: int = 0


async def fetch_company_research(slug: str) -> Dict[str, Any] | None:
    """Fetch research data from database"""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        print("❌ DATABASE_URL not set")
        return None

    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT payload
            FROM companies
            WHERE slug = %s
            LIMIT 1
        """, (slug,))

        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            return dict(row['payload'])
        return None

    except Exception as e:
        print(f"❌ Database error: {e}")
        return None


def extract_research_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract research data from existing payload for V2 generation"""

    # Build research data structure
    research_dict = {
        "company_name": payload.get("legal_name", "Unknown Company"),
        "domain": payload.get("website", "").replace("https://", "").replace("http://", "").split("/")[0],
        "normalized_url": payload.get("website", ""),
        "jurisdiction": payload.get("headquarters_country", "Unknown"),
        "category": payload.get("company_type", "unknown"),
        "confidence_score": payload.get("confidence_score", 1.0),
        "is_ambiguous": False,
        "ambiguity_signals": payload.get("ambiguity_signals", []),
        "recommendation": "proceed",

        # Data sources
        "website_content": {},
        "news_articles": payload.get("recent_news", []),
        "exa_research": {},
        "zep_context": {},
        "research_date": payload.get("research_date", "")
    }

    # Check if we have data sources metadata
    if "data_sources" in payload:
        ds = payload["data_sources"]

        # Reconstruct website content
        if ds.get("crawl4ai", {}).get("success") or ds.get("firecrawl", {}).get("success"):
            research_dict["website_content"] = {
                "pages": [
                    {
                        "title": "Home Page",
                        "url": payload.get("website", ""),
                        "content": payload.get("description", "") or payload.get("short_description", "")
                    }
                ]
            }

        # Add news articles if available
        if "recent_news" in payload and payload["recent_news"]:
            research_dict["news_articles"] = [
                {
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "snippet": article.get("summary", "")
                }
                for article in payload.get("recent_news", [])[:10]
            ]

    return research_dict


async def generate_v2_profile(research_dict: Dict[str, Any]) -> CompanyPayload:
    """Generate V2 profile using narrative-first approach"""

    print("🤖 Generating V2 profile with AI...")

    # Get AI model from env
    ai_provider = os.getenv("AI_PROVIDER", "google")
    ai_model = os.getenv("AI_MODEL", "gemini-2.0-flash-exp")
    model_string = f"{ai_provider}:{ai_model}"

    print(f"   Using: {model_string}")

    # Create Pydantic AI agent
    company_agent = Agent(
        model_string,
        result_type=CompanyPayload,
        system_prompt="""You are an expert company profiler who creates rich, narrative company profiles.

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

2. **services** (if services/products are described):
   - What they offer
   - Who they serve (clients/customers)
   - How they differentiate
   - Service categories or product lines

3. **team** (if executive/founder info found):
   - Key executives and titles
   - Founder background/story
   - Team expertise and credentials
   - Leadership philosophy

4. **track_record** (if deals/clients/results mentioned):
   - Notable transactions or projects
   - Key clients or partnerships
   - Metrics and results (e.g., "$2B raised", "50+ deals")
   - Awards or recognition

5. **specialization** (if specific focus areas mentioned):
   - Areas of expertise
   - Industry focus
   - Investment preferences (for finance)
   - Niche or positioning

6. **locations** (if multiple offices or geographic presence):
   - Office locations
   - Geographic coverage
   - International presence

7. **news** (if recent developments found):
   - Recent news or press releases
   - Company updates
   - Growth milestones

**Writing Guidelines:**

- Use natural, professional language
- Be specific: include names, numbers, details from research
- Synthesize from all sources
- Use markdown for formatting (bold, lists, etc.)
- Each section should stand alone and be complete
- 2-4 sentences minimum per section
- Don't create sections if you only have vague or generic info

===== REMEMBER =====

- Quality over quantity
- Only create sections where you have real information
- Better to have 3 great sections than 7 weak ones
- Synthesize and write naturally
- Professional tone, specific details

Your output must follow the CompanyPayload schema."""
    )

    # Build context
    context = build_context(research_dict)

    # Generate profile
    result = await company_agent.run(context)
    profile = result.data

    # Calculate metrics
    profile.section_count = len(profile.profile_sections)
    profile.total_content_length = sum(
        len(section.content)
        for section in profile.profile_sections.values()
    )

    return profile


def build_context(research_dict: Dict[str, Any]) -> str:
    """Build context string for AI"""
    lines = [
        f"COMPANY: {research_dict['company_name']}",
        f"DOMAIN: {research_dict['domain']}",
        f"URL: {research_dict['normalized_url']}",
        f"CATEGORY: {research_dict['category']}",
        "",
        "Generate a rich, narrative profile using the information below.",
        "Only create sections where you have substantial, specific content.",
        "",
        "=" * 70,
        ""
    ]

    # Website content
    if research_dict.get("website_content", {}).get("pages"):
        lines.append("===== WEBSITE CONTENT =====\n")
        for page in research_dict["website_content"]["pages"]:
            lines.append(f"Page: {page.get('title', 'Unknown')}")
            lines.append(f"URL: {page.get('url', '')}")
            lines.append(f"{page.get('content', '')}")
            lines.append("")
        lines.append("=" * 70 + "\n")

    # News articles
    if research_dict.get("news_articles"):
        lines.append("===== NEWS ARTICLES =====\n")
        for i, article in enumerate(research_dict["news_articles"][:10], 1):
            lines.append(f"{i}. {article.get('title', '')}")
            lines.append(f"   URL: {article.get('url', '')}")
            lines.append(f"   {article.get('snippet', '')}")
            lines.append("")
        lines.append("=" * 70 + "\n")

    return "\n".join(lines)


def print_profile(profile: CompanyPayload):
    """Pretty print the generated profile"""

    print("\n" + "=" * 80)
    print("📄 V2 PROFILE GENERATED")
    print("=" * 80)

    print(f"\n🏢 {profile.legal_name}")
    print(f"🌐 {profile.website}")
    print(f"📂 Type: {profile.company_type}")

    if profile.industry:
        print(f"🏭 Industry: {profile.industry}")

    if profile.headquarters_city:
        print(f"📍 Location: {profile.headquarters_city}, {profile.headquarters_country}")

    if profile.founded_year:
        print(f"📅 Founded: {profile.founded_year}")

    if profile.employee_range:
        print(f"👥 Employees: {profile.employee_range}")

    print(f"\n📊 Metrics:")
    print(f"   Sections: {profile.section_count}")
    print(f"   Content Length: {profile.total_content_length:,} characters")
    print(f"   Confidence: {profile.confidence_score:.2%}")

    print(f"\n📝 Narrative Sections:")
    print("-" * 80)

    for key, section in profile.profile_sections.items():
        print(f"\n## {section.title}")
        print(f"   Confidence: {section.confidence:.2%}")
        print()
        # Wrap content at 80 chars
        content = section.content
        for line in content.split('\n'):
            if line:
                print(f"   {line}")
            else:
                print()

        if section.sources:
            print(f"\n   Sources:")
            for source in section.sources:
                print(f"   - {source}")

    print("\n" + "=" * 80)


async def main():
    """Test V2 profile generation"""

    print("🧪 Testing V2 Profile Generation")
    print("=" * 80)

    # Company to test
    slug = "thrivealts"
    print(f"\n📋 Testing with: {slug}")

    # Check environment
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL not set")
        print("   Run: export DATABASE_URL='...'")
        return

    # Fetch existing company data
    print(f"\n🔍 Fetching existing data from database...")
    payload = await fetch_company_research(slug)

    if not payload:
        print(f"❌ Company '{slug}' not found in database")
        return

    print("✅ Found company data")

    # Extract research data
    print("\n📦 Extracting research data...")
    research_dict = extract_research_data(payload)
    print(f"   Company: {research_dict['company_name']}")
    print(f"   Domain: {research_dict['domain']}")
    print(f"   News articles: {len(research_dict.get('news_articles', []))}")

    # Generate V2 profile
    print()
    profile = await generate_v2_profile(research_dict)

    # Print results
    print_profile(profile)

    # Save to file
    output_file = f"test_v2_output_{slug}.json"
    with open(output_file, 'w') as f:
        json.dump(profile.model_dump(), f, indent=2)

    print(f"\n💾 Full JSON saved to: {output_file}")

    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
