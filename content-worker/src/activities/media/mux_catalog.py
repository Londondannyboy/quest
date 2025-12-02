"""
Mux Asset Catalog & Management Activities

Provides asset querying and cataloging functions using Mux MCP server.
Enables easy discovery of videos by country, mode, and article.
"""

from temporalio import activity
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@activity.defn
async def query_videos_by_country(country_code: str) -> List[Dict[str, Any]]:
    """
    Find all videos for a specific country using MCP.

    Example: query_videos_by_country("SI") → all Slovenia videos

    Args:
        country_code: Two-letter country code (e.g., "SI", "PT", "MT")

    Returns:
        List of video assets with metadata
    """
    activity.logger.info(f"Querying videos for country: {country_code}")

    try:
        # TODO: Implement MCP client call once MCP server is authenticated
        # For now, return placeholder indicating setup is needed
        activity.logger.warning("MCP client not yet configured - returning empty results")
        return []

        # Future implementation:
        # result = await mcp_client.call_tool(
        #     "list_assets",
        #     filter={"passthrough": {"contains": country_code}}
        # )
        # return result.get("data", [])

    except Exception as e:
        activity.logger.error(f"Error querying videos by country: {e}")
        return []


@activity.defn
async def query_videos_by_mode(
    article_mode: str,
    country_code: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find all videos by article_mode (story/guide/yolo/voices).

    Example: query_videos_by_mode("guide", "SI") → all Slovenia GUIDE videos

    Args:
        article_mode: Article mode (story, guide, yolo, voices)
        country_code: Optional country filter

    Returns:
        List of video assets with metadata
    """
    filter_str = article_mode.upper()
    if country_code:
        filter_str = f"{country_code} {filter_str}"

    activity.logger.info(f"Querying videos by mode: {filter_str}")

    try:
        # TODO: Implement MCP client call once MCP server is authenticated
        activity.logger.warning("MCP client not yet configured - returning empty results")
        return []

        # Future implementation:
        # result = await mcp_client.call_tool(
        #     "list_assets",
        #     filter={"passthrough": {"contains": filter_str}}
        # )
        # return result.get("data", [])

    except Exception as e:
        activity.logger.error(f"Error querying videos by mode: {e}")
        return []


@activity.defn
async def query_videos_by_article(article_id: int) -> List[Dict[str, Any]]:
    """
    Find all videos linked to a specific article.

    Example: query_videos_by_article(155) → all videos for article #155

    Args:
        article_id: Article ID to search for

    Returns:
        List of video assets with metadata
    """
    activity.logger.info(f"Querying videos for article: {article_id}")

    try:
        # TODO: Implement MCP client call once MCP server is authenticated
        activity.logger.warning("MCP client not yet configured - returning empty results")
        return []

        # Future implementation:
        # result = await mcp_client.call_tool(
        #     "list_assets",
        #     filter={"passthrough": {"contains": f"id:{article_id}"}}
        # )
        # return result.get("data", [])

    except Exception as e:
        activity.logger.error(f"Error querying videos by article: {e}")
        return []


@activity.defn
async def get_all_videos_summary() -> Dict[str, Any]:
    """
    Get summary statistics of all relocation videos.

    Returns counts by country, mode, and total storage.

    Returns:
        Dictionary with:
        - total_videos: Total count of videos
        - by_country: Count by country
        - by_mode: Count by article mode
        - total_duration: Total video duration in seconds
    """
    activity.logger.info("Generating video summary statistics")

    try:
        # TODO: Implement MCP client call once MCP server is authenticated
        activity.logger.warning("MCP client not yet configured - returning empty summary")
        return {
            "total_videos": 0,
            "by_country": {},
            "by_mode": {},
            "total_duration": 0,
            "note": "MCP client not yet authenticated - configure Mux MCP server first"
        }

        # Future implementation:
        # result = await mcp_client.call_tool("list_assets")
        #
        # # Aggregate by country and mode
        # by_country = {}
        # by_mode = {}
        #
        # for asset in result.get("data", []):
        #     passthrough = asset.get("passthrough", "")
        #     # Parse passthrough format: "Title | MODE | Country | app:relocation"
        #     parts = passthrough.split(" | ")
        #     if len(parts) >= 3:
        #         mode = parts[1].strip().lower()
        #         country = parts[2].strip()
        #
        #         by_country[country] = by_country.get(country, 0) + 1
        #         by_mode[mode] = by_mode.get(mode, 0) + 1
        #
        # return {
        #     "total_videos": len(result.get("data", [])),
        #     "by_country": by_country,
        #     "by_mode": by_mode,
        #     "total_duration": sum(a.get("duration", 0) for a in result.get("data", []))
        # }

    except Exception as e:
        activity.logger.error(f"Error generating video summary: {e}")
        return {
            "total_videos": 0,
            "by_country": {},
            "by_mode": {},
            "total_duration": 0,
            "error": str(e)
        }
