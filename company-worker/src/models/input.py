"""
Company Input Models

User-provided input for company creation workflow.
"""

from pydantic import BaseModel, HttpUrl, Field


class CompanyInput(BaseModel):
    """
    User-provided input to trigger company research and creation.

    Only 4 required fields - everything else is researched automatically.
    """

    url: HttpUrl = Field(
        ...,
        description="Company website URL",
        examples=["https://evercore.com"]
    )

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
