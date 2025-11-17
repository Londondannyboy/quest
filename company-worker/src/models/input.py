"""
Company Input Models

User-provided input for company creation workflow.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CompanyInput(BaseModel):
    """
    User-provided input to trigger company research and creation.

    Only 4 required fields - everything else is researched automatically.
    """

    url: str = Field(
        ...,
        description="Company website URL or domain",
        examples=["https://evercore.com", "evercore.com"]
    )

    @field_validator('url')
    @classmethod
    def normalize_url(cls, v: str) -> str:
        """Normalize URL to ensure it has https:// scheme."""
        if not v:
            raise ValueError("URL cannot be empty")

        # Remove any whitespace
        v = v.strip()

        # If it already has a scheme, return as-is
        if v.startswith(('http://', 'https://')):
            return v

        # Add https:// to plain domains
        return f"https://{v}"

    category: str = Field(
        ...,
        description="Company category/type",
        examples=["placement_agent", "relocation_provider", "recruiter"]
    )

    jurisdiction: str = Field(
        ...,
        description="Primary jurisdiction for geo-targeted research",
        examples=["UK", "US", "SG", "EU"]
    )

    app: str = Field(
        default="relocation",
        description="App context (placement, relocation, etc.)"
    )

    force_update: bool = Field(
        default=False,
        description="Force re-research of existing company"
    )

    # Optional overrides
    company_name: str | None = Field(
        default=None,
        description="Override auto-detected company name"
    )

    research_depth: str = Field(
        default="standard",
        description="Research depth: quick, standard, deep",
        pattern="^(quick|standard|deep)$"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://evercore.com",
                "category": "placement_agent",
                "jurisdiction": "US",
                "app": "placement",
                "force_update": False,
                "research_depth": "standard"
            }
        }
