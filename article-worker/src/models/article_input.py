"""
Article Input Models

User-provided input for article creation workflow.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ArticleInput(BaseModel):
    """
    User-provided input to trigger article research and creation.

    Requires topic and app - everything else is researched automatically.
    """

    topic: str = Field(
        ...,
        description="Article topic or subject",
        examples=[
            "The rise of AI in recruitment",
            "Top relocation destinations for tech workers in 2025",
            "How placement agencies are adapting to remote work"
        ]
    )

    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Ensure topic is not empty and has minimum length."""
        if not v:
            raise ValueError("Topic cannot be empty")

        v = v.strip()

        if len(v) < 5:
            raise ValueError("Topic must be at least 5 characters")

        return v

    app: str = Field(
        ...,
        description="App context (placement, relocation, chief-of-staff, etc.)",
        examples=["placement", "relocation", "chief-of-staff", "gtm", "newsroom"]
    )

    # Optional parameters
    target_word_count: int = Field(
        default=1500,
        description="Target word count for the article",
        ge=500,
        le=5000
    )

    article_format: str = Field(
        default="article",
        description="Article format type",
        pattern="^(article|listicle|guide|analysis)$"
    )

    jurisdiction: Optional[str] = Field(
        default=None,
        description="Primary jurisdiction for geo-targeted research (UK, US, SG, EU, etc.)"
    )

    num_research_sources: int = Field(
        default=10,
        description="Number of research sources to crawl",
        ge=3,
        le=20
    )

    deep_crawl_enabled: bool = Field(
        default=True,
        description="Enable deep crawling of authoritative sites"
    )

    skip_zep_sync: bool = Field(
        default=False,
        description="Skip syncing to Zep knowledge graph"
    )

    generate_images: bool = Field(
        default=True,
        description="Generate contextual images for the article"
    )

    auto_publish: bool = Field(
        default=False,
        description="Automatically publish the article (vs draft status)"
    )

    # SEO settings
    target_keywords: Optional[list[str]] = Field(
        default=None,
        description="Target SEO keywords to include"
    )

    meta_description: Optional[str] = Field(
        default=None,
        description="Override auto-generated meta description"
    )

    # Editorial
    author: Optional[str] = Field(
        default=None,
        description="Article author name"
    )

    article_angle: Optional[str] = Field(
        default=None,
        description="Editorial angle or perspective"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "The rise of AI in recruitment: How placement agencies are adapting",
                "app": "placement",
                "target_word_count": 2000,
                "article_format": "article",
                "jurisdiction": "UK",
                "num_research_sources": 10,
                "deep_crawl_enabled": True,
                "generate_images": True,
                "auto_publish": False,
                "target_keywords": ["AI recruitment", "placement agencies", "hiring technology"],
                "author": "Quest Editorial Team",
                "article_angle": "Industry transformation"
            }
        }
