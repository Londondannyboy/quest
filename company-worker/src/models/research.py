"""
Research Data Models

Intermediate research data structures used during company profiling.
"""

from pydantic import BaseModel, Field
from typing import Any


class ResearchData(BaseModel):
    """
    Aggregated research data from all sources.

    This is the intermediate structure that holds raw research
    before it's synthesized into CompanyPayload.
    """

    # ===== BASIC INFO =====
    normalized_url: str = Field(
        ...,
        description="Normalized company URL"
    )

    domain: str = Field(
        ...,
        description="Company domain (e.g., evercore.com)"
    )

    company_name: str = Field(
        ...,
        description="Company name"
    )

    jurisdiction: str = Field(
        ...,
        description="Primary jurisdiction for research"
    )

    category: str = Field(
        ...,
        description="Company category"
    )

    # ===== RESEARCH SOURCES =====
    news_articles: list[dict[str, Any]] = Field(
        default_factory=list,
        description="News articles from Serper search"
    )

    website_content: dict[str, Any] = Field(
        default_factory=dict,
        description="Scraped website content from Crawl4AI/Firecrawl"
    )

    exa_research: dict[str, Any] = Field(
        default_factory=dict,
        description="Research data from Exa"
    )

    logo_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Logo extraction and processing data"
    )

    zep_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Existing coverage from Zep knowledge graph"
    )

    # ===== CONFIDENCE & QUALITY =====
    confidence_score: float = Field(
        default=1.0,
        description="Overall research confidence (0-1)",
        ge=0.0,
        le=1.0
    )

    ambiguity_signals: list[str] = Field(
        default_factory=list,
        description="List of detected ambiguity signals"
    )

    is_ambiguous: bool = Field(
        default=False,
        description="Whether research has ambiguity issues"
    )

    recommendation: str = Field(
        default="proceed",
        description="Research recommendation: proceed, rescrape, manual_review"
    )

    # ===== COST TRACKING =====
    total_cost: float = Field(
        default=0.0,
        description="Total research cost in USD"
    )

    cost_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Cost breakdown by service"
    )

    # ===== METADATA =====
    research_duration_seconds: float | None = Field(
        default=None,
        description="Total research duration in seconds"
    )

    sources_used: list[str] = Field(
        default_factory=list,
        description="List of services/sources used"
    )

    research_attempts: int = Field(
        default=1,
        description="Number of research attempts"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "normalized_url": "https://evercore.com",
                "domain": "evercore.com",
                "company_name": "Evercore",
                "jurisdiction": "US",
                "category": "placement_agent",
                "news_articles": [
                    {
                        "title": "Evercore Advises on $500M Deal",
                        "url": "https://example.com/news/1",
                        "published_date": "2024-10-15",
                        "snippet": "Evercore acted as exclusive financial advisor..."
                    }
                ],
                "confidence_score": 0.92,
                "is_ambiguous": False,
                "total_cost": 0.06,
                "cost_breakdown": {
                    "serper": 0.02,
                    "exa": 0.04,
                    "crawl4ai": 0.0
                }
            }
        }


class NormalizedURL(BaseModel):
    """Result of URL normalization"""

    normalized_url: str = Field(
        ...,
        description="Clean, normalized URL"
    )

    domain: str = Field(
        ...,
        description="Extracted domain"
    )

    company_name_guess: str = Field(
        ...,
        description="Best guess at company name from domain"
    )

    is_valid: bool = Field(
        default=True,
        description="Whether URL is valid"
    )


class ExistingCompanyCheck(BaseModel):
    """Result of checking if company already exists"""

    exists: bool = Field(
        ...,
        description="Whether company exists in database"
    )

    company_id: str | None = Field(
        default=None,
        description="Database ID if exists"
    )

    slug: str | None = Field(
        default=None,
        description="URL slug if exists"
    )

    needs_update: bool = Field(
        default=False,
        description="Whether existing company needs update"
    )

    last_updated: str | None = Field(
        default=None,
        description="ISO datetime of last update"
    )
