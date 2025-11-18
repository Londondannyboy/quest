"""
Article Payload Model

Comprehensive data structure for article content, metadata, and analytics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ArticleSection(BaseModel):
    """
    A section of the article (H2 heading with content).

    Used for sentiment analysis and contextual image generation.
    """
    index: int = Field(description="Section index (0-based)")
    title: str = Field(description="Section title (H2 heading)")
    content: str = Field(description="Section content (markdown)")
    word_count: int = Field(description="Word count of this section")

    # Sentiment analysis (for contextual images)
    sentiment: Optional[str] = Field(
        default=None,
        description="Sentiment: positive, negative, neutral, tense, optimistic, etc."
    )
    sentiment_intensity: Optional[float] = Field(
        default=None,
        description="Sentiment intensity (0-1)",
        ge=0.0,
        le=1.0
    )
    business_context: Optional[str] = Field(
        default=None,
        description="Business context: layoffs, acquisition, deal, growth, innovation, etc."
    )
    visual_tone: Optional[str] = Field(
        default=None,
        description="Visual tone for image: professional-optimistic, somber-serious, dynamic-energetic, etc."
    )
    visual_moment: Optional[str] = Field(
        default=None,
        description="Description of visual moment to capture in image"
    )
    should_generate_image: bool = Field(
        default=False,
        description="Whether this section should get a contextual image"
    )
    image_index: Optional[int] = Field(
        default=None,
        description="Index of content image (1-5) assigned to this section"
    )


class CompanyMention(BaseModel):
    """
    A company mentioned in the article.
    """
    company_id: Optional[str] = Field(default=None, description="Company ID if matched to database")
    name: str = Field(description="Company name as mentioned in article")
    relevance_score: float = Field(
        default=0.5,
        description="Relevance score (0-1)",
        ge=0.0,
        le=1.0
    )
    mention_count: int = Field(default=1, description="Number of times mentioned")
    is_primary: bool = Field(default=False, description="Is this the primary company focus?")


class ArticlePayload(BaseModel):
    """
    Complete article data structure.

    Includes content, metadata, SEO, images, and analytics.
    """

    # ===== CORE CONTENT (Always present) =====
    title: str = Field(description="Article title (H1)")
    subtitle: Optional[str] = Field(
        default=None,
        description="Article subtitle or deck"
    )
    slug: str = Field(description="URL-friendly slug")
    content: str = Field(description="Full article content (markdown)")
    excerpt: str = Field(description="Short summary (1-2 sentences, 40-60 words)")

    # ===== SECTIONS (For analysis and images) =====
    sections: list[ArticleSection] = Field(
        default_factory=list,
        description="Article sections (H2 headings with content)"
    )

    # ===== CLASSIFICATION =====
    app: str = Field(
        description="App context: placement, relocation, chief-of-staff, gtm, newsroom"
    )
    article_format: str = Field(
        default="article",
        description="Article format: article, listicle, guide, analysis"
    )
    article_angle: Optional[str] = Field(
        default=None,
        description="Editorial angle or perspective"
    )
    primary_category: Optional[str] = Field(
        default=None,
        description="Primary content category"
    )

    # ===== SEO =====
    meta_description: str = Field(description="SEO meta description (150-160 chars)")
    tags: list[str] = Field(
        default_factory=list,
        description="Article tags for categorization and search"
    )
    target_keywords: list[str] = Field(
        default_factory=list,
        description="Target SEO keywords"
    )

    # ===== METRICS =====
    word_count: int = Field(description="Total word count")
    reading_time_minutes: int = Field(description="Estimated reading time in minutes")

    # ===== COMPANY RELATIONSHIPS =====
    mentioned_companies: list[CompanyMention] = Field(
        default_factory=list,
        description="Companies mentioned in the article"
    )

    # ===== VISUAL ASSETS (Sequential Images - Flux Kontext) =====

    # Featured Image (Social sharing, 1200x630)
    featured_image_url: Optional[str] = Field(default=None, description="Social sharing image")
    featured_image_alt: Optional[str] = Field(default=None)
    featured_image_description: Optional[str] = Field(default=None)
    featured_image_title: Optional[str] = Field(default=None)

    # Hero Image (Article header, 16:9)
    hero_image_url: Optional[str] = Field(default=None, description="Article header image")
    hero_image_alt: Optional[str] = Field(default=None)
    hero_image_description: Optional[str] = Field(default=None)
    hero_image_title: Optional[str] = Field(default=None)

    # Content Images 1-5 (Contextual section images, 4:3 or 1:1)
    content_image1_url: Optional[str] = Field(default=None, description="First contextual section image")
    content_image1_alt: Optional[str] = Field(default=None)
    content_image1_description: Optional[str] = Field(default=None)
    content_image1_title: Optional[str] = Field(default=None)

    content_image2_url: Optional[str] = Field(default=None, description="Second contextual section image")
    content_image2_alt: Optional[str] = Field(default=None)
    content_image2_description: Optional[str] = Field(default=None)
    content_image2_title: Optional[str] = Field(default=None)

    content_image3_url: Optional[str] = Field(default=None, description="Third contextual section image")
    content_image3_alt: Optional[str] = Field(default=None)
    content_image3_description: Optional[str] = Field(default=None)
    content_image3_title: Optional[str] = Field(default=None)

    content_image4_url: Optional[str] = Field(default=None, description="Fourth contextual section image")
    content_image4_alt: Optional[str] = Field(default=None)
    content_image4_description: Optional[str] = Field(default=None)
    content_image4_title: Optional[str] = Field(default=None)

    content_image5_url: Optional[str] = Field(default=None, description="Fifth contextual section image")
    content_image5_alt: Optional[str] = Field(default=None)
    content_image5_description: Optional[str] = Field(default=None)
    content_image5_title: Optional[str] = Field(default=None)

    # ===== EDITORIAL =====
    author: Optional[str] = Field(default=None, description="Article author")
    status: str = Field(
        default="draft",
        description="Publication status: draft, published, archived"
    )
    published_at: Optional[str] = Field(
        default=None,
        description="ISO datetime when published"
    )

    # ===== RESEARCH METADATA =====
    research_date: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO datetime when research was performed"
    )
    last_updated: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO datetime of last update"
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

    news_sources: list[str] = Field(
        default_factory=list,
        description="News article URLs used in research"
    )

    authoritative_sources: list[str] = Field(
        default_factory=list,
        description="Authoritative website URLs crawled"
    )

    all_sources: list[str] = Field(
        default_factory=list,
        description="All source URLs used in research"
    )

    # ===== ZEP INTEGRATION =====
    zep_graph_id: Optional[str] = Field(
        default=None,
        description="Zep graph episode or entity ID"
    )
    zep_facts_count: int = Field(
        default=0,
        description="Number of facts extracted to Zep"
    )

    # ===== QUALITY METRICS =====
    completeness_score: float = Field(
        default=0.0,
        description="Article completeness score (0-100)",
        ge=0.0,
        le=100.0
    )
    readability_score: Optional[float] = Field(
        default=None,
        description="Readability score (e.g., Flesch Reading Ease)"
    )
    confidence_score: float = Field(
        default=1.0,
        description="Overall research confidence (0-1)",
        ge=0.0,
        le=1.0
    )

    # Content analysis
    section_count: int = Field(default=0, description="Number of H2 sections")
    image_count: int = Field(default=0, description="Number of images generated")
    company_mention_count: int = Field(default=0, description="Number of companies mentioned")

    # Narrative structure
    narrative_arc: Optional[str] = Field(
        default=None,
        description="Narrative arc: problem-solution, chronological, thematic, etc."
    )
    overall_sentiment: Optional[str] = Field(
        default=None,
        description="Overall article sentiment"
    )
    opening_sentiment: Optional[str] = Field(default=None, description="Opening section sentiment")
    middle_sentiment: Optional[str] = Field(default=None, description="Middle section sentiment")
    climax_sentiment: Optional[str] = Field(default=None, description="Climax section sentiment")
    primary_business_context: Optional[str] = Field(
        default=None,
        description="Primary business context of the article"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Rise of AI in Recruitment: How Placement Agencies Are Adapting",
                "subtitle": "Technology is transforming the hiring landscape for finance and legal professionals",
                "slug": "rise-of-ai-recruitment-placement-agencies-adapting",
                "excerpt": "As artificial intelligence reshapes the recruitment industry, placement agencies are rapidly adopting new technologies to stay competitive. This article explores the latest trends and strategies.",
                "content": "## Introduction\n\nThe recruitment industry is experiencing a technological revolution...",
                "word_count": 2150,
                "reading_time_minutes": 11,
                "app": "placement",
                "article_format": "article",
                "primary_category": "Technology",
                "meta_description": "Discover how AI is transforming recruitment and what placement agencies are doing to adapt to the changing landscape.",
                "tags": ["AI", "Recruitment", "Placement Agencies", "HR Technology"],
                "author": "Quest Editorial Team",
                "status": "published",
                "published_at": "2025-01-15T10:00:00Z",
                "mentioned_companies": [
                    {
                        "company_id": "comp_123",
                        "name": "Evercore",
                        "relevance_score": 0.9,
                        "mention_count": 3,
                        "is_primary": True
                    }
                ],
                "completeness_score": 92.5,
                "confidence_score": 0.88,
                "research_cost": 0.25
            }
        }
