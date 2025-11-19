"""
Article Payload Model - Flexible Narrative Approach

Simplified model matching CompanyPayload V2 pattern:
1. Essential structured data (for search/filtering)
2. Dynamic narrative sections (only exist if data supports them)

This eliminates NULL fields and provides richer, more flexible articles.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ArticleSection(BaseModel):
    """
    A section of the article content.

    Only created when substantial information is available.
    """
    title: str = Field(description="Section title (H2 heading)")
    content: str = Field(description="Section content (markdown)")
    sources: list[str] = Field(
        default_factory=list,
        description="URLs supporting this section"
    )


class CompanyMention(BaseModel):
    """Company mentioned in the article."""
    name: str = Field(description="Company name as mentioned")
    relevance_score: float = Field(default=0.5, description="Relevance (0-1)")
    is_primary: bool = Field(default=False, description="Is primary focus?")


class ArticlePayload(BaseModel):
    """
    Simplified, flexible article payload.

    Narrative-first approach matching CompanyPayload V2.
    Only essential fields required - everything else optional.
    """

    # ===== ESSENTIAL (Always present) =====
    title: str = Field(description="Article title")
    slug: str = Field(description="URL-friendly slug")
    content: str = Field(description="Full article content (markdown)")
    excerpt: str = Field(description="Short summary (1-2 sentences)")

    # ===== CLASSIFICATION =====
    app: str = Field(description="App context: placement, relocation, etc.")
    article_type: str = Field(description="Type: news, guide, comparison")

    # ===== SEO =====
    meta_description: str = Field(description="SEO meta description (150-160 chars)")
    tags: list[str] = Field(default_factory=list, description="Article tags")

    # ===== OPTIONAL STRUCTURED =====
    subtitle: Optional[str] = Field(default=None, description="Article subtitle")
    primary_category: Optional[str] = Field(default=None, description="Content category")

    # ===== DYNAMIC SECTIONS (Like company profile_sections) =====
    article_sections: dict[str, ArticleSection] = Field(
        default_factory=dict,
        description="""
        Dynamic article sections. Common sections:
        - introduction: Opening context and key facts
        - background: Historical context and company info
        - details: Deal/event specifics
        - implications: Market impact and analysis
        - outlook: Future implications

        Only create sections with meaningful content.
        """
    )

    # ===== COMPANY RELATIONSHIPS =====
    mentioned_companies: list[CompanyMention] = Field(
        default_factory=list,
        description="Companies mentioned in article"
    )

    # ===== VISUAL ASSETS (Populated by image generation, replaceable by humans) =====
    # Featured (1200x630 - social sharing)
    featured_image_url: Optional[str] = Field(default=None)
    featured_image_alt: Optional[str] = Field(default=None)
    featured_image_title: Optional[str] = Field(default=None)
    featured_image_description: Optional[str] = Field(default=None)

    # Hero (16:9 - article header, can be replaced with video)
    hero_image_url: Optional[str] = Field(default=None)
    hero_image_alt: Optional[str] = Field(default=None)
    hero_image_title: Optional[str] = Field(default=None)
    hero_image_description: Optional[str] = Field(default=None)

    # Hero Video (optional replacement for hero image)
    hero_video_url: Optional[str] = Field(default=None, description="Cloudinary video URL")
    hero_video_title: Optional[str] = Field(default=None)
    hero_video_description: Optional[str] = Field(default=None)

    # Content Images 1-3 (4:3 - in-article contextual)
    content_image_1_url: Optional[str] = Field(default=None)
    content_image_1_alt: Optional[str] = Field(default=None)
    content_image_1_title: Optional[str] = Field(default=None)
    content_image_1_description: Optional[str] = Field(default=None)

    content_image_2_url: Optional[str] = Field(default=None)
    content_image_2_alt: Optional[str] = Field(default=None)
    content_image_2_title: Optional[str] = Field(default=None)
    content_image_2_description: Optional[str] = Field(default=None)

    content_image_3_url: Optional[str] = Field(default=None)
    content_image_3_alt: Optional[str] = Field(default=None)
    content_image_3_title: Optional[str] = Field(default=None)
    content_image_3_description: Optional[str] = Field(default=None)

    # Image count for tracking
    image_count: int = Field(default=0)

    # ===== METADATA =====
    author: Optional[str] = Field(default="Quest Editorial Team")
    status: str = Field(default="draft")
    published_at: Optional[str] = Field(default=None)

    research_date: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )

    research_cost: float = Field(default=0.0)

    data_sources: dict[str, Any] = Field(
        default_factory=lambda: {
            "serper": {"articles": 0, "cost": 0.0},
            "exa": {"results": 0, "cost": 0.0},
            "crawl4ai": {"pages": 0},
            "firecrawl": {"pages": 0}
        }
    )

    sources: list[str] = Field(
        default_factory=list,
        description="All source URLs"
    )

    # ===== QUALITY METRICS =====
    word_count: int = Field(default=0)
    reading_time_minutes: int = Field(default=1)
    section_count: int = Field(default=0)
    company_mention_count: int = Field(default=0)

    # ===== ZEP INTEGRATION =====
    zep_graph_id: Optional[str] = Field(default=None)

    confidence_score: float = Field(default=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Goldman Sachs Acquires AI Startup for $500M",
                "slug": "goldman-sachs-acquires-ai-startup-500m",
                "content": "## Introduction\n\nGoldman Sachs announced today...",
                "excerpt": "Goldman Sachs announced the acquisition of AI startup TechCo for $500M.",
                "app": "placement",
                "article_type": "news",
                "meta_description": "Goldman Sachs acquires AI startup for $500M in major tech expansion.",
                "tags": ["M&A", "Goldman Sachs", "AI"],
                "article_sections": {
                    "introduction": {
                        "title": "Introduction",
                        "content": "Goldman Sachs announced today the acquisition...",
                        "sources": ["https://example.com/news"]
                    },
                    "background": {
                        "title": "Background",
                        "content": "The investment bank has been expanding...",
                        "sources": ["https://example.com/about"]
                    }
                },
                "mentioned_companies": [
                    {
                        "name": "Goldman Sachs",
                        "relevance_score": 1.0,
                        "is_primary": True
                    }
                ],
                "word_count": 1500,
                "section_count": 4
            }
        }
