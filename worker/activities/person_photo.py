"""
Person Photo Extraction Activity

Identifies and extracts person photos from scraped news articles.
"""

import os
from typing import List, Dict, Any, Optional
from temporalio import activity
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


@activity.defn(name="extract_person_photo")
async def extract_person_photo(
    scraped_sources: List[Dict[str, Any]],
    article_theme: str
) -> Optional[Dict[str, str]]:
    """
    Extract person photo from news articles if the article is about a person

    Uses Gemini Vision to analyze images and determine if they show a person
    relevant to the article's subject (e.g., new chief of staff appointment)

    Args:
        scraped_sources: List of scraped articles with images
        article_theme: Main theme/angle of the article

    Returns:
        Dict with person_photo_url, source_name, source_url, person_name
        or None if no relevant person photo found
    """
    activity.logger.info(f"👤 Extracting person photo from {len(scraped_sources)} sources")

    # Check if article theme suggests it's about a person
    person_keywords = [
        "appoint", "hire", "join", "promote", "name",
        "new", "chief of staff", "executive", "leader"
    ]

    is_person_focused = any(keyword in article_theme.lower() for keyword in person_keywords)

    if not is_person_focused:
        activity.logger.info("   Article doesn't appear to be person-focused, skipping photo extraction")
        return None

    activity.logger.info("   Article appears person-focused, analyzing images...")

    # Analyze images from each source
    for source in scraped_sources:
        images = source.get("images", [])
        source_url = source.get("url", "")
        source_title = source.get("title", "")

        if not images:
            continue

        activity.logger.info(f"   Checking {len(images)} images from {source_url[:50]}...")

        # Analyze first few images (usually the lead image is most relevant)
        for img_url in images[:3]:
            try:
                # Use Gemini to analyze if image is a professional headshot/portrait
                model = genai.GenerativeModel("gemini-2.0-flash-exp")

                analysis_prompt = f"""Analyze this image and determine:
1. Does it show a professional headshot or portrait of a person? (not a group photo, stock image, or logo)
2. If yes, estimate the person's role/position based on context
3. Is this likely the subject of a news article about an executive appointment?

Respond with JSON only:
{{
  "is_person_photo": true/false,
  "photo_type": "headshot" or "portrait" or "group" or "other",
  "appears_professional": true/false,
  "likely_subject": true/false,
  "confidence": "high" or "medium" or "low"
}}"""

                response = model.generate_content([analysis_prompt, {"mime_type": "image/jpeg", "data": img_url}])

                # Parse response (simplified - in production would need better parsing)
                result_text = response.text.strip()

                activity.logger.info(f"      Image analysis: {result_text[:100]}...")

                # If this looks like a relevant person photo, return it
                if '"is_person_photo": true' in result_text and '"likely_subject": true' in result_text:
                    activity.logger.info(f"   ✅ Found person photo: {img_url[:60]}...")

                    return {
                        "person_photo_url": img_url,
                        "source_name": source_title,
                        "source_url": source_url,
                        "person_name": None,  # Could extract from article text
                        "attribution": f"Photo: {source_title}"
                    }

            except Exception as e:
                activity.logger.warning(f"      Failed to analyze image: {e}")
                continue

    activity.logger.info("   No relevant person photo found")
    return None
