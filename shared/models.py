"""
Pydantic models for Quest content generation system

All data structures used across workflows, agents, and activities.
"""

from datetime import datetime
from typing import List, Optional, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# ARTICLE MODELS
# ============================================================================

class ArticleRequest(BaseModel):
    """Initial request to trigger article generation workflow"""
    topic: str = Field(..., description="Topic to generate article about", min_length=3)
    app: str = Field(default="placement", description="App/site: placement, relocation, etc.")
    target_word_count: int = Field(default=1500, ge=300, le=5000)
    auto_approve: bool = Field(default=True, description="Skip manual approval")


class StoryCandidate(BaseModel):
    """A candidate story for article generation"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique story ID")
    title: str = Field(..., description="Proposed article title", min_length=10)
    angle: str = Field(..., description="Unique angle or perspective", min_length=20)
    relevance_score: float = Field(..., description="Relevance score (0-10)", ge=0.0, le=10.0)
    justification: str = Field(..., description="Why this story is relevant", min_length=30)
    is_duplicate: bool = Field(default=False, description="Whether story exists in KB")
    source_urls: List[str] = Field(default_factory=list, description="Real source URLs")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is properly formatted"""
        return v.strip()


class ArticleBrief(BaseModel):
    """Approved story brief for research and generation"""
    story_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., description="Article title")
    angle: str = Field(..., description="Article angle/perspective")
    target_word_count: int = Field(default=1500, ge=300, le=5000)
    source_urls: List[str] = Field(default_factory=list, description="Source URLs for research")
    approved_by: str = Field(default="system", description="Who approved this brief")
    approved_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# RESEARCH MODELS
# ============================================================================

class Source(BaseModel):
    """A source for article research"""
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Source article title")
    content: str = Field(default="", description="Extracted content")
    author: Optional[str] = Field(default=None, description="Article author")
    published_date: Optional[datetime] = Field(default=None, description="Publication date")
    credibility_score: float = Field(default=7.0, ge=0.0, le=10.0)
    access_date: datetime = Field(default_factory=datetime.utcnow)


class Citation(BaseModel):
    """A citation within an article"""
    source_url: Optional[str] = Field(default=None, description="URL being cited")
    source_title: Optional[str] = Field(default=None, description="Title of source")
    quote: Optional[str] = Field(default=None, description="Direct quote if applicable")
    context: str = Field(default="", description="Context where citation is used")
    citation_number: int = Field(default=1, ge=1)


class Entity(BaseModel):
    """An entity extracted from research"""
    name: str = Field(..., description="Entity name")
    entity_type: str = Field(..., description="Type: person, organization, technology, etc.")
    description: Optional[str] = Field(default=None, description="Entity description")
    relevance: float = Field(default=5.0, ge=0.0, le=10.0)


class ResearchBrief(BaseModel):
    """Compiled research for article generation"""
    sources: List[Source] = Field(..., description="Research sources")
    citations: List[Citation] = Field(default_factory=list, description="Prepared citations")
    entities: List[Entity] = Field(default_factory=list, description="Extracted entities")
    key_findings: List[str] = Field(default_factory=list, description="Key findings from research")
    research_summary: str = Field(default="", description="Summary of research")


# ============================================================================
# ARTICLE OUTPUT
# ============================================================================

class Article(BaseModel):
    """Final article output"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., description="Article title")
    slug: str = Field(..., description="URL-friendly slug")
    content: str = Field(..., description="Full article content (markdown)")
    excerpt: str = Field(default="", description="Article excerpt/summary")

    # Multi-app support
    app: str = Field(default="placement", description="App/site: placement, relocation, etc.")

    # Metadata
    word_count: int = Field(default=0)
    citation_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Status
    status: str = Field(default="published")
    published_at: Optional[datetime] = Field(default=None)

    # Optional fields
    keywords: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)

    # Knowledge base
    zep_graph_id: Optional[str] = Field(default=None)
    neon_saved: bool = Field(default=False)


# ============================================================================
# NEWS SEARCH MODELS
# ============================================================================

class SearchNewsInput(BaseModel):
    """Input for news search (Serper)"""
    keyword: str = Field(..., description="Search keyword")
    location: str = Field(default="UK", description="Geographic location")
    language: str = Field(default="en", description="Language code")
    num_results: int = Field(default=5, ge=1, le=20)


class NewsSearchOutput(BaseModel):
    """Output from news search"""
    news_items: List[dict] = Field(default_factory=list)
    total_results: int = Field(default=0)
    search_time: float = Field(default=0.0)
