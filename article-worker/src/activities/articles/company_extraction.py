"""
Company Mention Extraction

Extract company mentions from article content using NER.
"""

from __future__ import annotations
from temporalio import activity
import re


@activity.defn
async def extract_company_mentions(
    content: str,
    related_companies: list[dict]
) -> dict:
    """
    Extract company mentions from article content.

    Args:
        content: Article content (markdown)
        related_companies: Related companies from Zep context

    Returns:
        Dict with companies list
    """
    activity.logger.info("Extracting company mentions")
    
    # TODO: Implement NER-based company extraction
    # For now, return empty list
    
    return {"companies": []}


@activity.defn
async def calculate_article_completeness(payload: dict) -> float:
    """Calculate article completeness score (0-100)."""
    
    # Basic completeness calculation
    score = 0.0
    
    # Title (10 points)
    if payload.get("title"):
        score += 10
    
    # Content (30 points)
    word_count = payload.get("word_count", 0)
    if word_count >= 500:
        score += 30
    elif word_count >= 300:
        score += 20
    elif word_count > 0:
        score += 10
    
    # Sections (15 points)
    sections = payload.get("sections", [])
    if len(sections) >= 3:
        score += 15
    elif len(sections) > 0:
        score += 10
    
    # Images (20 points)
    if payload.get("featured_image_url"):
        score += 10
    if payload.get("hero_image_url"):
        score += 10
    
    # Meta/SEO (15 points)
    if payload.get("meta_description"):
        score += 5
    if payload.get("tags") and len(payload["tags"]) > 0:
        score += 5
    if payload.get("excerpt"):
        score += 5
    
    # Companies (10 points)
    if payload.get("mentioned_companies") and len(payload["mentioned_companies"]) > 0:
        score += 10
    
    activity.logger.info(f"Completeness score: {score}%")
    
    return score
