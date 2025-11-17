"""
Company Payload Model V2 - Narrative-First Approach

Simplified model that stores:
1. Essential structured data (for search/filtering)
2. Dynamic narrative sections (only exist if data supports them)

This eliminates NULL fields and provides richer, more flexible profiles.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ProfileSection(BaseModel):
    """
    A narrative section of the company profile.

    Only created when substantial information is available for that section.
    """
    title: str = Field(description="Section title (e.g., 'Overview', 'Services')")
    content: str = Field(description="Rich narrative content (markdown supported)")
    confidence: float = Field(
        default=1.0,
        description="Confidence in this section's accuracy (0-1)",
        ge=0.0,
        le=1.0
    )
    sources: list[str] = Field(
        default_factory=list,
        description="URLs or sources supporting this section"
    )


class CompanyPayload(BaseModel):
    """
    Simplified, flexible company profile.

    Narrative-first approach: Only show what exists, no NULL fields on display.
    """

    # ===== ESSENTIAL STRUCTURED (Always present) =====
    legal_name: str = Field(description="Company legal name")
    website: str = Field(description="Company website URL")
    domain: str = Field(description="Domain name (e.g., 'thrivealts.com')")
    slug: str = Field(description="URL-friendly slug")
    company_type: str = Field(
        description="Company type: placement_agent, relocation_provider, etc."
    )

    # ===== OPTIONAL STRUCTURED (Only if clearly available) =====
    industry: str | None = Field(
        default=None,
        description="Primary industry or sector"
    )

    headquarters_city: str | None = Field(
        default=None,
        description="Headquarters city"
    )

    headquarters_country: str | None = Field(
        default=None,
        description="Headquarters country"
    )

    founded_year: int | None = Field(
        default=None,
        description="Year founded (only if explicitly mentioned)"
    )

    employee_range: str | None = Field(
        default=None,
        description="Employee count range: '1-10', '10-50', '50-100', '100-500', '500+'"
    )

    # ===== CONTACT (Optional) =====
    phone: str | None = Field(default=None, description="Primary phone number")
    linkedin_url: str | None = Field(default=None, description="LinkedIn URL")
    twitter_url: str | None = Field(default=None, description="Twitter/X URL")

    # ===== NARRATIVE SECTIONS (Dynamic - only exist if data supports them) =====
    profile_sections: dict[str, ProfileSection] = Field(
        default_factory=dict,
        description="""
        Dynamic narrative sections. Common sections:
        - overview: Always present, 2-4 paragraphs about the company
        - services: Services/products offered, who they serve
        - team: Key executives, founders, team expertise
        - track_record: Notable deals, clients, results
        - locations: Office locations and geographic presence
        - technology: Tech stack, platforms, tools
        - news: Recent developments and updates
        - specialization: Areas of expertise or focus
        - clients: Key clients and partnerships
        - awards: Awards, recognition, achievements

        Only create sections with meaningful content (2+ sentences).
        """
    )

    # ===== VISUAL ASSETS =====
    logo_url: str | None = Field(
        default=None,
        description="Company logo URL (Cloudinary or other CDN)"
    )

    featured_image_url: str | None = Field(
        default=None,
        description="Featured/hero image URL (AI-generated or scraped)"
    )

    # ===== METADATA =====
    research_date: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO datetime when research was performed"
    )

    last_updated: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO datetime of last update"
    )

    confidence_score: float = Field(
        default=1.0,
        description="Overall research confidence (0-1)",
        ge=0.0,
        le=1.0
    )

    research_cost: float = Field(
        default=0.0,
        description="Total research cost in USD"
    )

    data_sources: dict[str, Any] = Field(
        default_factory=lambda: {
            "serper": {"articles": 0, "cost": 0.0},
            "crawl4ai": {"pages": 0, "success": False},
            "firecrawl": {"pages": 0, "cost": 0.0},
            "exa": {"results": 0, "cost": 0.0},
        },
        description="Breakdown of data sources used"
    )

    sources: list[str] = Field(
        default_factory=list,
        description="All source URLs used in research"
    )

    # ===== ZEP INTEGRATION =====
    zep_graph_id: str | None = Field(
        default=None,
        description="Zep graph episode or entity ID"
    )

    zep_facts_count: int = Field(
        default=0,
        description="Number of facts extracted to Zep"
    )

    # ===== QUALITY METRICS =====
    section_count: int = Field(
        default=0,
        description="Number of profile sections generated"
    )

    total_content_length: int = Field(
        default=0,
        description="Total character count of all narrative sections"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "legal_name": "Thrive Alternative Investments",
                "website": "https://www.thrivealts.com",
                "domain": "thrivealts.com",
                "slug": "thrivealts",
                "company_type": "placement_agent",
                "industry": "Financial Services",
                "headquarters_city": "New York",
                "headquarters_country": "United States",
                "founded_year": 2015,
                "employee_range": "10-50",
                "profile_sections": {
                    "overview": {
                        "title": "Overview",
                        "content": "Thrive Alternative Investments is a specialized placement agent focused on connecting institutional investors with alternative investment opportunities. With deep expertise in private equity, venture capital, and real estate funds, Thrive provides comprehensive capital raising services to fund managers and investment firms.\n\nThe firm leverages its extensive network of institutional investors, family offices, and high-net-worth individuals to facilitate successful fundraising campaigns. Thrive's team brings decades of combined experience in financial services, with particular strength in navigating complex regulatory environments and structuring investor relationships.",
                        "confidence": 0.9,
                        "sources": ["https://www.thrivealts.com/about", "https://www.thrivealts.com/services"]
                    },
                    "services": {
                        "title": "Services",
                        "content": "Thrive offers end-to-end capital raising services including investor identification, pitch deck development, roadshow coordination, and closing support. The firm specializes in fund formations, secondary transactions, and co-investment opportunities across alternative asset classes.",
                        "confidence": 0.85,
                        "sources": ["https://www.thrivealts.com/services"]
                    },
                    "track_record": {
                        "title": "Track Record",
                        "content": "The firm has facilitated over $2 billion in capital commitments across 50+ transactions, working with both emerging and established fund managers. Thrive maintains relationships with 200+ institutional investors globally.",
                        "confidence": 0.7,
                        "sources": ["https://www.linkedin.com/company/thrive-alts"]
                    }
                },
                "confidence_score": 0.85,
                "section_count": 3,
                "zep_graph_id": "episode_123",
                "research_cost": 0.18
            }
        }
