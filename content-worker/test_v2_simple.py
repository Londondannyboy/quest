#!/usr/bin/env python3
"""
Simple V2 Profile Generation Test

Tests narrative-first approach with mock data to demonstrate the difference.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from pydantic_ai import Agent
from pydantic import BaseModel


# V2 Models
class ProfileSection(BaseModel):
    title: str
    content: str
    confidence: float = 1.0
    sources: list[str] = []


class CompanyPayload(BaseModel):
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
    profile_sections: dict[str, ProfileSection] = {}
    confidence_score: float = 1.0
    section_count: int = 0
    total_content_length: int = 0


# Mock research data for Thrive Alts
MOCK_RESEARCH = """
COMPANY: Thrive Alternative Investments
DOMAIN: thrivealts.com
URL: https://www.thrivealts.com
CATEGORY: placement_agent

Generate a rich, narrative profile using the information below.
Only create sections where you have substantial, specific content.

======================================================================

===== WEBSITE CONTENT =====

Page: About Us
URL: https://www.thrivealts.com/about
Thrive Alternative Investments is a boutique placement agent specializing in connecting institutional investors with alternative investment managers. Founded in 2015 by industry veterans with over 50 years of combined experience in private markets, Thrive has built a reputation for excellence in capital raising across private equity, venture capital, real estate, and infrastructure funds.

Our team brings deep relationships with institutional investors including pension funds, endowments, foundations, family offices, and sovereign wealth funds across North America, Europe, and Asia. We pride ourselves on providing white-glove service to fund managers seeking to build long-term investor relationships.

Thrive is headquartered in New York City with team members in London and Singapore, enabling us to serve clients across all major time zones. Our global network includes relationships with over 300 institutional investors representing more than $5 trillion in assets under management.

Page: Services
URL: https://www.thrivealts.com/services
We provide comprehensive capital raising services including:

• Investor Identification & Targeting: Leveraging our proprietary database and decades of relationships to identify the right institutional investors for your fund strategy
• Fundraising Strategy: Developing customized marketing materials, pitch decks, and positioning strategies that resonate with institutional investors
• Roadshow Management: Coordinating investor meetings, managing due diligence processes, and facilitating negotiations
• Closing Support: Assisting with legal documentation, subscription processes, and ongoing investor relations

Our team specializes in first-time funds, emerging managers, and established managers looking to expand their investor base. We typically work on a success-based fee structure aligned with our clients' fundraising goals.

======================================================================

===== NEWS ARTICLES =====

1. Thrive Alternative Investments Expands to Asia Pacific
   URL: https://www.privateequitywire.com/thrive-expands-apac
   Thrive Alternative Investments announced the opening of a Singapore office to better serve the growing demand from Asian institutional investors. The firm has hired former Blackstone executive James Chen to lead Asia Pacific business development.

2. Alternative Investment Placement Agents See Record Year
   URL: https://www.institutionalinvestor.com/placement-agents-2024
   Boutique placement agents like Thrive Alternative Investments are experiencing record fundraising activity as institutional investors increase alternative allocations. Thrive reportedly facilitated over $2 billion in commitments across 15 funds in 2024.

3. How Thrive Alternative Investments Built a $5B Placement Firm
   URL: https://www.pitchbook.com/news/thrive-profile
   Founded by Sarah Johnson and Michael Roberts, former executives at Goldman Sachs and Credit Suisse respectively, Thrive has carved out a niche serving emerging alternative asset managers. The firm has facilitated capital for over 40 fund managers since inception, with a focus on ESG-aligned and impact investment strategies.

======================================================================

===== RESEARCH QUALITY =====
Confidence Score: 0.90
Is Ambiguous: False
Recommendation: proceed
"""


async def generate_v2_profile() -> CompanyPayload:
    """Generate V2 profile using narrative approach"""

    print("🤖 Generating V2 Profile with AI...")

    company_agent = Agent(
        'gemini-2.0-flash-exp',
        result_type=CompanyPayload,
        system_prompt="""You are an expert company profiler who creates rich, narrative company profiles.

Your goal: Generate comprehensive, readable profiles using whatever information is available.

===== STRUCTURED DATA (extract if clearly stated) =====

Extract these ONLY if explicitly mentioned:
- industry, headquarters_city, headquarters_country, founded_year, employee_range
- Only extract what's explicitly stated. Don't guess.

===== NARRATIVE SECTIONS (create only if you have substantial content) =====

1. **overview** (ALWAYS create): 2-4 paragraphs about what the company does
2. **services** (if described): What they offer, who they serve
3. **team** (if mentioned): Key executives, leadership
4. **track_record** (if deals/results mentioned): Notable transactions, metrics
5. **locations** (if multiple offices): Geographic presence
6. **specialization** (if focus areas mentioned): Areas of expertise

**Rules:**
- Professional tone, specific details
- Use markdown formatting
- 2-4 sentences minimum per section
- Only create sections with real, meaningful content

Your output must follow the CompanyPayload schema."""
    )

    result = await company_agent.run(MOCK_RESEARCH)
    profile = result.data

    # Calculate metrics
    profile.section_count = len(profile.profile_sections)
    profile.total_content_length = sum(
        len(section.content)
        for section in profile.profile_sections.values()
    )

    return profile


def print_comparison():
    """Print V1 vs V2 comparison"""

    print("\n" + "=" * 80)
    print("📊 V1 vs V2 COMPARISON")
    print("=" * 80)

    print("\n❌ V1 APPROACH (Current - Structured Extraction):")
    print("-" * 80)

    v1_example = {
        "legal_name": "Thrive Alternative Investments",
        "tagline": None,
        "description": None,
        "headquarters": None,
        "founded_year": None,
        "employees": None,
        "executives": [],
        "services": [],
        "notable_deals": [],
        "data_completeness_score": 29.4
    }

    print(json.dumps(v1_example, indent=2))
    print("\n⚠️  Problems:")
    print("   • 50+ NULL fields")
    print("   • 29.4% completeness")
    print("   • Rigid structure doesn't match scraped data")
    print("   • Frontend has to handle all the NULLs")

    print("\n\n✅ V2 APPROACH (New - Narrative-First):")
    print("-" * 80)
    print("Generating with AI... (see output below)")


def print_profile(profile: CompanyPayload):
    """Pretty print the V2 profile"""

    print("\n" + "=" * 80)
    print("📄 V2 PROFILE OUTPUT")
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

    print(f"\n📊 V2 Metrics:")
    print(f"   • Sections Generated: {profile.section_count}")
    print(f"   • Total Content: {profile.total_content_length:,} characters")
    print(f"   • Confidence: {profile.confidence_score:.0%}")
    print(f"   • NULL Fields Displayed: 0 ✅")

    print(f"\n📝 Narrative Sections (Only What Exists!):")
    print("-" * 80)

    for key, section in profile.profile_sections.items():
        print(f"\n## {section.title}")
        print(f"Confidence: {section.confidence:.0%}")
        print()

        # Print content with wrapping
        for line in section.content.split('\n'):
            if line.strip():
                print(f"{line}")
            else:
                print()

        if section.sources:
            print(f"\nSources:")
            for source in section.sources[:3]:
                print(f"  • {source}")

    print("\n" + "=" * 80)

    print("\n✅ V2 Benefits:")
    print("   • No NULL fields on display")
    print("   • Rich, readable content (2-4 paragraphs per section)")
    print("   • Flexible structure (adapts to available data)")
    print("   • Better user experience")
    print("   • Simpler frontend rendering")

    print("\n💡 Frontend Rendering:")
    print("""
    {/* Simple, dynamic rendering - no NULL handling! */}
    {Object.entries(profile_sections).map(([key, section]) => (
      <Section key={key}>
        <h2>{section.title}</h2>
        <Markdown>{section.content}</Markdown>
      </Section>
    ))}
    """)


async def main():
    """Run V2 test"""

    print("🧪 Testing V2 Narrative-First Profile Generation")
    print("=" * 80)
    print("\nCompany: Thrive Alternative Investments")
    print("Data: Mock research data (website content + news articles)")

    # Show comparison
    print_comparison()

    # Generate V2 profile
    profile = await generate_v2_profile()

    # Print results
    print_profile(profile)

    # Save JSON
    output_file = "test_v2_output.json"
    with open(output_file, 'w') as f:
        json.dump(profile.model_dump(), f, indent=2)

    print(f"\n💾 Full JSON saved to: {output_file}")
    print("\n✅ Test Complete!")


if __name__ == "__main__":
    asyncio.run(main())
