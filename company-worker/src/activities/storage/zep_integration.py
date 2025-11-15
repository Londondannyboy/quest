"""
Zep Knowledge Graph Integration

Activities for querying and syncing company data with Zep Cloud.
"""

from temporalio import activity
from typing import Dict, Any
from zep_cloud.client import AsyncZep
from zep_cloud.types import GraphSearchScope

from src.utils.config import config


def get_graph_id_for_app(app: str) -> str:
    """
    Map app type to Zep graph ID.

    Args:
        app: Application type (placement, relocation, etc.)

    Returns:
        Zep graph ID
    """
    graph_mapping = {
        "placement": "finance-knowledge",
        "relocation": "relocation"
    }

    return graph_mapping.get(app, "finance-knowledge")


@activity.defn
async def query_zep_for_context(
    company_name: str,
    domain: str,
    app: str = "placement"  # Default for backward compatibility
) -> Dict[str, Any]:
    """
    Query Zep knowledge graph for existing company coverage.

    This checks if we have articles, deals, or other content
    mentioning this company already.

    Args:
        company_name: Company name
        domain: Company domain
        app: Application type (placement, relocation) for graph selection

    Returns:
        Dict with articles, deals, found_existing_coverage
    """
    graph_id = get_graph_id_for_app(app)
    activity.logger.info(f"Querying Zep graph '{graph_id}' for {company_name} context")

    if not config.ZEP_API_KEY:
        activity.logger.warning("ZEP_API_KEY not configured")
        return {
            "articles": [],
            "deals": [],
            "found_existing_coverage": False,
            "error": "ZEP_API_KEY not configured"
        }

    try:
        client = AsyncZep(api_key=config.ZEP_API_KEY)

        # Search Zep graph using graph_id (organizational knowledge)
        search_query = f"{company_name} {domain}"

        results = await client.graph.search(
            graph_id=graph_id,  # Use app-specific organizational graph
            query=search_query,
            scope=GraphSearchScope.EDGES,  # Search relationships
            limit=20
        )

        # Extract articles and deals from nodes
        articles = extract_articles_from_results(results)
        deals = extract_deals_from_results(results)

        activity.logger.info(
            f"Zep context: {len(articles)} articles, {len(deals)} deals"
        )

        return {
            "articles": articles[:10],
            "deals": deals[:10],
            "found_existing_coverage": len(articles) > 0 or len(deals) > 0,
            "total_nodes": len(results.nodes) if hasattr(results, 'nodes') else 0
        }

    except Exception as e:
        activity.logger.error(f"Zep query failed: {e}")
        return {
            "articles": [],
            "deals": [],
            "found_existing_coverage": False,
            "error": str(e)
        }


@activity.defn
async def sync_company_to_zep(
    company_id: str,
    company_name: str,
    summary: str,
    app: str = "placement"  # Default for backward compatibility
) -> Dict[str, Any]:
    """
    Sync company profile to Zep knowledge graph.

    Creates a company node with key facts condensed to <10k chars.

    Args:
        company_id: Database company ID
        company_name: Company name
        summary: Condensed company summary (<10k chars)
        app: Application type (placement, relocation) for graph selection

    Returns:
        Dict with graph_id, success
    """
    graph_id = get_graph_id_for_app(app)
    activity.logger.info(f"Syncing {company_name} to Zep graph '{graph_id}'")

    if not config.ZEP_API_KEY:
        return {
            "graph_id": None,
            "success": False,
            "error": "ZEP_API_KEY not configured"
        }

    try:
        client = AsyncZep(api_key=config.ZEP_API_KEY)

        # Add company to organizational graph using graph.add
        graph_data = {
            "company_id": company_id,
            "company_name": company_name,
            "summary": summary,
            "type": "company_profile",
            "app": app
        }

        # Add to Zep using app-specific organizational graph
        await client.graph.add(
            graph_id=graph_id,
            data=graph_data
        )

        activity.logger.info(f"Company synced to Zep graph '{graph_id}': {company_name}")

        return {
            "graph_id": graph_id,
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"Zep sync failed: {e}")
        return {
            "graph_id": None,
            "success": False,
            "error": str(e)
        }


@activity.defn
async def create_zep_summary(
    payload: Dict[str, Any],
    zep_context: Dict[str, Any]
) -> str:
    """
    Create condensed summary for Zep storage (<10k chars).

    Args:
        payload: Full CompanyPayload
        zep_context: Existing Zep context

    Returns:
        Condensed summary string
    """
    activity.logger.info("Creating Zep summary")

    # Extract key information
    name = payload.get("legal_name", "Unknown")
    tagline = payload.get("tagline", "")
    description = payload.get("short_description", "")
    hq = payload.get("headquarters", "")
    industry = payload.get("industry", "")
    services = payload.get("services", [])
    notable_deals = payload.get("notable_deals", [])

    # Build summary
    summary_parts = [
        f"Company: {name}",
        f"Tagline: {tagline}" if tagline else "",
        f"Description: {description}" if description else "",
        f"Headquarters: {hq}" if hq else "",
        f"Industry: {industry}" if industry else "",
        f"Services: {', '.join(services[:5])}" if services else "",
    ]

    # Add notable deals
    if notable_deals:
        deals_text = "Notable Deals:\n"
        for deal in notable_deals[:3]:
            deal_name = deal.get("name", "")
            deal_date = deal.get("date", "")
            deals_text += f"- {deal_name} ({deal_date})\n"
        summary_parts.append(deals_text)

    # Add existing coverage context
    existing_articles = zep_context.get("articles", [])
    if existing_articles:
        summary_parts.append(
            f"Previously covered in {len(existing_articles)} articles"
        )

    summary = "\n".join(p for p in summary_parts if p)

    # Truncate to 10k chars
    if len(summary) > 10000:
        summary = summary[:9950] + "... [truncated]"

    activity.logger.info(f"Summary created: {len(summary)} chars")

    return summary


def extract_articles_from_results(results: Any) -> list[Dict[str, Any]]:
    """
    Extract article information from Zep search results.

    Args:
        results: Zep search results

    Returns:
        List of article dicts
    """
    articles = []

    if not hasattr(results, 'nodes'):
        return articles

    for node in results.nodes:
        # Check if node is an article
        node_type = getattr(node, 'type', '')
        if node_type == 'article':
            articles.append({
                "id": getattr(node, 'uuid', ''),
                "name": getattr(node, 'name', ''),
                "summary": getattr(node, 'summary', '')
            })

    return articles


def extract_deals_from_results(results: Any) -> list[Dict[str, Any]]:
    """
    Extract deal information from Zep search results.

    Args:
        results: Zep search results

    Returns:
        List of deal dicts
    """
    deals = []

    if not hasattr(results, 'nodes'):
        return deals

    for node in results.nodes:
        # Check if node is a deal
        node_type = getattr(node, 'type', '')
        if node_type == 'deal':
            deals.append({
                "id": getattr(node, 'uuid', ''),
                "name": getattr(node, 'name', ''),
                "summary": getattr(node, 'summary', '')
            })

    return deals
