"""
Company Payload Model

Complete company data structure based on Crunchbase + PitchBook analysis.
Stored as JSONB in Neon PostgreSQL.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class CompanyPayload(BaseModel):
    """
    Complete company profile data structure.

    This is the comprehensive payload stored in the database.
    60+ fields covering all aspects of a company profile.

    Based on competitive intelligence from Crunchbase and PitchBook.
    """

    # ===== HERO STATS (Display prominently) =====
    hero_stats: dict[str, Any] = Field(
        default_factory=lambda: {
            "employees": None,              # "60" or "1,000-5,000"
            "founded_year": None,           # 1988
            "serviced_companies": None,     # 72
            "serviced_deals": None,         # 20
            "serviced_investors": None,     # 172
            "countries_served": None,       # 45
        },
        description="Key metrics for hero section display"
    )

    # ===== BASIC INFO =====
    legal_name: str | None = Field(
        default=None,
        description="Official legal company name"
    )

    also_known_as: list[str] = Field(
        default_factory=list,
        description="Alternative names, DBA names"
    )

    tagline: str | None = Field(
        default=None,
        description="One-line company tagline"
    )

    description: str | None = Field(
        default=None,
        description="Full company description (2-3 paragraphs)"
    )

    short_description: str | None = Field(
        default=None,
        description="Short description (1-2 sentences)"
    )

    # ===== CLASSIFICATION =====
    industry: str | None = Field(
        default=None,
        description="Primary industry"
    )

    sub_industries: list[str] = Field(
        default_factory=list,
        description="Sub-industries and sectors"
    )

    service_type: str | None = Field(
        default=None,
        description="Type of services provided"
    )

    company_type: str | None = Field(
        default=None,
        description="Company type (placement_agent, relocation_provider, etc.)"
    )

    operating_status: str = Field(
        default="Active",
        description="Operating status: Active, Acquired, Closed, etc."
    )

    # ===== LOCATION =====
    headquarters: str | None = Field(
        default=None,
        description="Full headquarters address"
    )

    headquarters_city: str | None = Field(
        default=None,
        description="HQ city"
    )

    headquarters_country: str | None = Field(
        default=None,
        description="HQ country"
    )

    office_locations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of office locations with city, country, address"
    )

    # ===== CONTACT =====
    phone: str | None = Field(
        default=None,
        description="Primary phone number"
    )

    website: str | None = Field(
        default=None,
        description="Company website URL"
    )

    linkedin_url: str | None = Field(
        default=None,
        description="LinkedIn company page URL"
    )

    twitter_url: str | None = Field(
        default=None,
        description="Twitter/X profile URL"
    )

    # ===== PEOPLE =====
    headcount: str | None = Field(
        default=None,
        description="Employee count or range"
    )

    executives: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Executive team with name, title, bio"
    )

    founders: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Founders with name, background"
    )

    board_members: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Board members"
    )

    # ===== SERVICES =====
    services: list[str] = Field(
        default_factory=list,
        description="List of services offered"
    )

    specializations: list[str] = Field(
        default_factory=list,
        description="Areas of specialization"
    )

    services_to_companies: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Services offered to companies"
    )

    services_to_investors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Services offered to investors"
    )

    # ===== DEALS =====
    total_deals: int | None = Field(
        default=None,
        description="Total number of deals completed"
    )

    notable_deals: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Notable deals with deal name, date, amount, parties"
    )

    # ===== CLIENTS =====
    total_clients: int | None = Field(
        default=None,
        description="Total number of clients served"
    )

    key_clients: list[str] = Field(
        default_factory=list,
        description="List of key client names"
    )

    # ===== PREFERENCES (For Placement Agents) =====
    investment_preferences: dict[str, Any] | None = Field(
        default=None,
        description="Investment preferences: sectors, stage, geography, etc."
    )

    # ===== COMPETITORS =====
    competitors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Competitor companies with name, comparison"
    )

    # ===== GROWTH =====
    growth_metrics: dict[str, Any] | None = Field(
        default=None,
        description="Growth metrics: YoY revenue, employee growth, etc."
    )

    # ===== FINANCIAL =====
    financial_data: dict[str, Any] | None = Field(
        default=None,
        description="Financial information: funding, revenue, valuation"
    )

    # ===== NEWS & ACTIVITY =====
    recent_news: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Recent news articles with title, url, date, summary"
    )

    press_releases: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Press releases"
    )

    # ===== AWARDS =====
    awards: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Awards and recognitions with name, year, organization"
    )

    # ===== SUB-ORGANIZATIONS =====
    subsidiaries: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Subsidiary companies"
    )

    parent_company: str | None = Field(
        default=None,
        description="Parent company name if applicable"
    )

    # ===== RESEARCH METADATA =====
    research_quality: str = Field(
        default="standard",
        description="Research quality level: quick, standard, deep"
    )

    research_cost: float = Field(
        default=0.04,
        description="Total cost of research in USD"
    )

    research_date: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO datetime when research was performed"
    )

    sources: list[str] = Field(
        default_factory=list,
        description="List of source URLs used in research"
    )

    data_sources: dict[str, Any] = Field(
        default_factory=lambda: {
            "serper": {"articles": 0, "cost": 0.0, "queries": 0},
            "crawl4ai": {"pages": 0, "success": False},
            "firecrawl": {"pages": 0, "cost": 0.0, "success": False},
            "exa": {"results": 0, "cost": 0.0, "research_id": None},
        },
        description="Detailed breakdown of what each data source contributed"
    )

    data_completeness_score: float | None = Field(
        default=None,
        description="Data completeness score (0-100)",
        ge=0.0,
        le=100.0
    )

    last_verified: str | None = Field(
        default=None,
        description="ISO datetime of last verification"
    )

    confidence_score: float = Field(
        default=1.0,
        description="Research confidence score (0-1)",
        ge=0.0,
        le=1.0
    )

    ambiguity_signals: list[str] = Field(
        default_factory=list,
        description="List of ambiguity signals detected during research"
    )

    # ===== ZEPGRAPH =====
    zep_graph_id: str | None = Field(
        default=None,
        description="Zep graph node ID"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "legal_name": "Evercore Inc.",
                "hero_stats": {
                    "employees": "1,800",
                    "founded_year": 1995,
                    "serviced_deals": 450,
                    "countries_served": 15
                },
                "tagline": "Premier global independent investment banking advisory firm",
                "headquarters_city": "New York",
                "headquarters_country": "United States",
                "industry": "Investment Banking",
                "company_type": "placement_agent",
                "data_completeness_score": 85.5,
                "confidence_score": 0.92
            }
        }
