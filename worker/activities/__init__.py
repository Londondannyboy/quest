"""
Quest Worker Activities

All Temporal activities for workflows.
"""

from .database import save_to_neon, calculate_metadata
from .research import (
    search_news_serper,
    deep_scrape_sources,
    extract_entities_from_news,
    extract_entities_citations,
    calculate_quality_score,
    sync_to_zep,  # Legacy placeholder - use zep_activities instead
)
from .generation import generate_article
from .images import generate_article_images
from .insert_images import insert_images_into_content
from .zep_activities import (
    check_zep_coverage,
    sync_article_to_zep,
    extract_facts_to_zep,
)

__all__ = [
    # Database
    "save_to_neon",
    "calculate_metadata",

    # Research
    "search_news_serper",
    "deep_scrape_sources",
    "extract_entities_from_news",
    "extract_entities_citations",
    "calculate_quality_score",
    "sync_to_zep",  # Legacy

    # Zep Graph
    "check_zep_coverage",
    "sync_article_to_zep",
    "extract_facts_to_zep",

    # Generation
    "generate_article",

    # Images
    "generate_article_images",
    "insert_images_into_content",
]
