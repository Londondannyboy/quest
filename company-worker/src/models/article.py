"""
Article Payload Model

Structured data for article content, images, and metadata.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CompanyMention(BaseModel):
    """Company mentioned in the article."""
    company_id: Optional[str] = Field(default=None, description="Database company ID if matched")
    name: str = Field(description="Company name as mentioned")
    relevance_score: float = Field(default=0.5, description="Relevance (0-1)")
    mention_count: int = Field(default=1, description="Number of mentions")
    is_primary: bool = Field(default=False, description="Is primary focus?")


class ArticleSection(BaseModel):
    """Article section with sentiment analysis for image generation."""
    index: int = Field(description="Section index (0-based)")
    title: str = Field(description="H2 heading text")
    content: str = Field(description="Section content (markdown)")
    word_count: int = Field(description="Word count")

    # For image generation
    sentiment: Optional[str] = Field(default=None, description="positive, negative, neutral, etc.")
    business_context: Optional[str] = Field(default=None, description="layoffs, acquisition, deal, etc.")
    visual_tone: Optional[str] = Field(default=None, description="professional-optimistic, somber-serious, etc.")
    visual_moment: Optional[str] = Field(default=None, description="Visual description for image")
    should_generate_image: bool = Field(default=False, description="Generate image for this section?")


class ArticlePayload(BaseModel):
    """Complete article data structure."""

    # ===== CORE CONTENT =====
    title: str = Field(description="Article title (H1)")
    subtitle: Optional[str] = Field(default=None, description="Article subtitle")
    slug: str = Field(description="URL-friendly slug")
    content: str = Field(description="Full markdown content")
    excerpt: str = Field(description="Short summary (40-60 words)")

    # ===== SECTIONS =====
    sections: List[ArticleSection] = Field(
        default_factory=list,
        description="Article sections (H2 headings)"
    )

    # ===== CLASSIFICATION =====
    app: str = Field(description="App: placement, relocation, chief-of-staff, etc.")
    article_type: str = Field(description="Type: news, guide, comparison, analysis")
    primary_category: Optional[str] = Field(default=None, description="Content category")

    # ===== SEO =====
    meta_description: str = Field(description="SEO meta description (150-160 chars)")
    tags: List[str] = Field(default_factory=list, description="Article tags")
    target_keywords: List[str] = Field(default_factory=list, description="SEO keywords")

    # ===== METRICS =====
    word_count: int = Field(description="Total word count")
    reading_time_minutes: int = Field(description="Estimated reading time")

    # ===== COMPANY RELATIONSHIPS =====
    mentioned_companies: List[CompanyMention] = Field(
        default_factory=list,
        description="Companies mentioned in article"
    )

    # ===== IMAGES (Sequential - Flux Kontext Pro) =====

    # Featured (1200x630 - social sharing)
    featured_image_url: Optional[str] = Field(default=None)
    featured_image_alt: Optional[str] = Field(default=None)
    featured_image_description: Optional[str] = Field(default=None)
    featured_image_title: Optional[str] = Field(default=None)

    # Hero (16:9 - article header)
    hero_image_url: Optional[str] = Field(default=None)
    hero_image_alt: Optional[str] = Field(default=None)
    hero_image_description: Optional[str] = Field(default=None)
    hero_image_title: Optional[str] = Field(default=None)

    # Content Images 1-5 (4:3 - section images)
    content_image1_url: Optional[str] = Field(default=None)
    content_image1_alt: Optional[str] = Field(default=None)
    content_image1_description: Optional[str] = Field(default=None)
    content_image1_title: Optional[str] = Field(default=None)

    content_image2_url: Optional[str] = Field(default=None)
    content_image2_alt: Optional[str] = Field(default=None)
    content_image2_description: Optional[str] = Field(default=None)
    content_image2_title: Optional[str] = Field(default=None)

    content_image3_url: Optional[str] = Field(default=None)
    content_image3_alt: Optional[str] = Field(default=None)
    content_image3_description: Optional[str] = Field(default=None)
    content_image3_title: Optional[str] = Field(default=None)

    content_image4_url: Optional[str] = Field(default=None)
    content_image4_alt: Optional[str] = Field(default=None)
    content_image4_description: Optional[str] = Field(default=None)
    content_image4_title: Optional[str] = Field(default=None)

    content_image5_url: Optional[str] = Field(default=None)
    content_image5_alt: Optional[str] = Field(default=None)
    content_image5_description: Optional[str] = Field(default=None)
    content_image5_title: Optional[str] = Field(default=None)

    # ===== EDITORIAL =====
    author: Optional[str] = Field(default="Quest Editorial Team")
    status: str = Field(default="draft", description="draft, published, archived")
    published_at: Optional[str] = Field(default=None, description="ISO datetime")

    # ===== RESEARCH METADATA =====
    research_date: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO datetime of research"
    )
    research_cost: float = Field(default=0.0, description="Total cost in USD")

    data_sources: Dict[str, Any] = Field(
        default_factory=lambda: {
            "serper": {"articles": 0, "cost": 0.0},
            "exa": {"results": 0, "cost": 0.0},
            "crawl4ai": {"pages": 0, "cost": 0.0},
            "firecrawl": {"pages": 0, "cost": 0.0}
        },
        description="Data source breakdown"
    )

    news_sources: List[str] = Field(default_factory=list, description="News URLs")
    authoritative_sources: List[str] = Field(default_factory=list, description="Research URLs")
    all_sources: List[str] = Field(default_factory=list, description="All URLs")

    # ===== ZEP INTEGRATION =====
    zep_graph_id: Optional[str] = Field(default=None, description="Zep graph episode ID")
    zep_facts_count: int = Field(default=0, description="Facts extracted to Zep")

    # ===== QUALITY METRICS =====
    completeness_score: float = Field(default=0.0, description="Completeness (0-100)")
    confidence_score: float = Field(default=1.0, description="Research confidence (0-1)")

    # Content analysis
    section_count: int = Field(default=0, description="Number of H2 sections")
    image_count: int = Field(default=0, description="Number of images generated")
    company_mention_count: int = Field(default=0, description="Companies mentioned")

    # Narrative structure (from sentiment analysis)
    narrative_arc: Optional[str] = Field(default=None, description="problem-solution, chronological, etc.")
    overall_sentiment: Optional[str] = Field(default=None, description="Overall sentiment")
    opening_sentiment: Optional[str] = Field(default=None)
    middle_sentiment: Optional[str] = Field(default=None)
    climax_sentiment: Optional[str] = Field(default=None)
    primary_business_context: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Goldman Sachs Acquires AI Startup for $500M",
                "subtitle": "Major investment bank expands tech capabilities",
                "slug": "goldman-sachs-acquires-ai-startup-500m",
                "excerpt": "Goldman Sachs announced today the acquisition of AI startup TechCo for $500M, marking a significant expansion of the bank's technology capabilities.",
                "content": "## Background\n\nGoldman Sachs has been actively...",
                "word_count": 1500,
                "reading_time_minutes": 8,
                "app": "placement",
                "article_type": "news",
                "meta_description": "Goldman Sachs acquires AI startup TechCo for $500M in major tech expansion. Analysis of the deal and market implications.",
                "tags": ["M&A", "Goldman Sachs", "AI", "Tech Acquisition"],
                "mentioned_companies": [
                    {
                        "company_id": "comp_123",
                        "name": "Goldman Sachs",
                        "relevance_score": 1.0,
                        "mention_count": 15,
                        "is_primary": True
                    }
                ],
                "research_cost": 0.22
            }
        }
