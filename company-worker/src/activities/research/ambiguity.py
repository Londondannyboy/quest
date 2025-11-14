"""
Ambiguity Check Activity

Assess research quality and confidence to determine if re-scrape is needed.
"""

from temporalio import activity
from typing import Dict, Any


# Category keywords for validation
CATEGORY_KEYWORDS = {
    "placement_agent": [
        "private equity", "capital raising", "fundraising",
        "placement", "fund", "investment", "lp", "gp"
    ],
    "relocation_provider": [
        "relocation", "mobility", "moving", "expatriate",
        "assignment", "transfer", "immigration", "visa"
    ],
    "recruiter": [
        "recruitment", "hiring", "talent", "executive search",
        "headhunter", "staffing", "employment"
    ],
}


@activity.defn
async def check_research_ambiguity(
    news_data: Dict[str, Any],
    website_data: Dict[str, Any],
    exa_data: Dict[str, Any],
    category: str
) -> Dict[str, Any]:
    """
    Check if research has ambiguity issues.

    Confidence factors:
    1. Category keywords present in content (30%)
    2. Exa confidence scores (20%)
    3. News article count (20%)
    4. Website content quality (20%)
    5. Consistency across sources (10%)

    Args:
        news_data: News search results
        website_data: Website scraping results
        exa_data: Exa research results
        category: Company category

    Returns:
        Dict with is_ambiguous, confidence, signals, recommendation
    """
    activity.logger.info("Checking research ambiguity")

    confidence = 1.0
    signals = []

    # ===== CHECK 1: Category keywords in news (30%) =====
    keywords = CATEGORY_KEYWORDS.get(category, [])
    news_articles = news_data.get("articles", [])

    if news_articles:
        # Check if any article contains category keywords
        keyword_found = False
        for article in news_articles:
            text = (
                article.get("title", "") + " " +
                article.get("snippet", "")
            ).lower()

            if any(kw in text for kw in keywords):
                keyword_found = True
                break

        if not keyword_found:
            confidence -= 0.3
            signals.append(
                f"No '{category}' keywords found in news articles"
            )
    else:
        confidence -= 0.2
        signals.append("No news articles found")

    # ===== CHECK 2: Exa confidence (20%) =====
    exa_summary = exa_data.get("summary", {})
    exa_avg_score = exa_summary.get("avg_score", 0.0)

    if exa_avg_score < 0.5:
        confidence -= 0.2
        signals.append(f"Low Exa confidence score: {exa_avg_score:.2f}")
    elif exa_avg_score < 0.7:
        confidence -= 0.1
        signals.append(f"Medium Exa confidence score: {exa_avg_score:.2f}")

    # ===== CHECK 3: News article count (20%) =====
    news_count = len(news_articles)

    if news_count == 0:
        confidence -= 0.2
        signals.append("Zero news articles found")
    elif news_count < 3:
        confidence -= 0.1
        signals.append(f"Only {news_count} news articles found")

    # ===== CHECK 4: Website content quality (20%) =====
    pages = website_data.get("pages", [])

    if not pages:
        confidence -= 0.2
        signals.append("No website content scraped")
    elif len(pages) < 2:
        confidence -= 0.1
        signals.append("Limited website content")

    # Check if website has category keywords
    if pages:
        website_text = " ".join(
            page.get("content", "").lower()
            for page in pages
        )

        if not any(kw in website_text for kw in keywords):
            confidence -= 0.1
            signals.append("No category keywords on website")

    # ===== CHECK 5: Consistency (10%) =====
    # Check if company name appears consistently
    exa_results = exa_data.get("results", [])
    if exa_results:
        # Check if Exa results are relevant
        relevant_count = sum(
            1 for r in exa_results
            if r.get("score", 0.0) > 0.6
        )

        if relevant_count == 0:
            confidence -= 0.1
            signals.append("No highly relevant Exa results")

    # ===== DETERMINE OUTCOME =====
    is_ambiguous = len(signals) > 0
    recommendation = "proceed"

    if confidence < 0.5:
        recommendation = "manual_review"
        signals.append("Confidence too low - manual review needed")
    elif confidence < 0.7:
        recommendation = "rescrape"
        signals.append("Consider re-scraping with refined queries")

    activity.logger.info(
        f"Ambiguity check complete: confidence={confidence:.2f}, "
        f"signals={len(signals)}, recommendation={recommendation}"
    )

    return {
        "is_ambiguous": is_ambiguous,
        "confidence": confidence,
        "signals": signals,
        "recommendation": recommendation
    }


@activity.defn
async def validate_company_match(
    company_name: str,
    domain: str,
    research_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate that researched data matches the target company.

    This prevents mixing up companies with similar names.

    Args:
        company_name: Expected company name
        domain: Expected domain
        research_data: All research data

    Returns:
        Dict with is_match, confidence, issues
    """
    activity.logger.info(f"Validating company match for {company_name}")

    is_match = True
    confidence = 1.0
    issues = []

    # Check 1: Domain appears in news URLs
    news_articles = research_data.get("news_articles", [])
    domain_in_news = any(
        domain in article.get("url", "")
        for article in news_articles
    )

    if not domain_in_news and len(news_articles) > 0:
        confidence -= 0.2
        issues.append("Domain not found in any news URLs")

    # Check 2: Company name in Exa results
    exa_results = research_data.get("exa_research", {}).get("results", [])
    name_in_exa = any(
        company_name.lower() in result.get("title", "").lower()
        for result in exa_results
    )

    if not name_in_exa and len(exa_results) > 0:
        confidence -= 0.2
        issues.append("Company name not in Exa results titles")

    # Check 3: Website content mentions company name
    website_pages = research_data.get("website_content", {}).get("pages", [])
    name_on_website = any(
        company_name.lower() in page.get("content", "").lower()
        for page in website_pages
    )

    if not name_on_website and len(website_pages) > 0:
        confidence -= 0.3
        issues.append("Company name not found on website content")

    # Determine match
    if confidence < 0.5:
        is_match = False
        issues.append("Low confidence - possible wrong company")

    activity.logger.info(
        f"Validation complete: is_match={is_match}, confidence={confidence:.2f}"
    )

    return {
        "is_match": is_match,
        "confidence": confidence,
        "issues": issues
    }
