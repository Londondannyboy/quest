"""
Article Payload Model - Stripped to Essentials

Simple model for AI generation. Only 8 core fields required.
Image fields populated by image generation activity.
Entities extracted by Zep sync activity.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ArticlePayload(BaseModel):
    """
    Essential article payload for AI generation.

    AI generates: title, slug, content, excerpt, app, article_type, meta_description, tags
    Everything else has defaults or is populated by other activities.
    """

    # ===== CORE (AI must generate these) =====
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

    # ===== VISUAL ASSETS (Populated by image generation activity) =====
    # Featured (1200x630 - social sharing)
    featured_image_url: Optional[str] = Field(default=None)
    featured_image_alt: Optional[str] = Field(default=None)
    featured_image_title: Optional[str] = Field(default=None)
    featured_image_description: Optional[str] = Field(default=None)

    # Hero (16:9 - article header)
    hero_image_url: Optional[str] = Field(default=None)
    hero_image_alt: Optional[str] = Field(default=None)
    hero_image_title: Optional[str] = Field(default=None)
    hero_image_description: Optional[str] = Field(default=None)

    # Hero Video (optional)
    hero_video_url: Optional[str] = Field(default=None)
    hero_video_title: Optional[str] = Field(default=None)
    hero_video_description: Optional[str] = Field(default=None)

    # Content Images 1-3 (4:3 - in-article)
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

    # Image count
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

    # ===== QUALITY METRICS =====
    word_count: int = Field(default=0)
    reading_time_minutes: int = Field(default=1)
    section_count: int = Field(default=0)

    # ===== ZEP INTEGRATION =====
    zep_graph_id: Optional[str] = Field(default=None)

    confidence_score: float = Field(default=1.0)
