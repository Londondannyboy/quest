"""
Zep Knowledge Graph Visualization Data

Fetch nodes and edges from Zep for graph visualization.
"""

from temporalio import activity
from typing import Dict, Any, List
from zep_cloud.client import AsyncZep

from src.utils.config import config


def get_graph_id_for_app(app: str) -> str:
    """Map app type to Zep graph ID."""
    graph_mapping = {
        "placement": "finance-knowledge",
        "relocation": "relocation"
    }
    return graph_mapping.get(app, "finance-knowledge")


@activity.defn
async def fetch_company_graph_data(
    company_name: str,
    domain: str,
    app: str = "placement"
) -> Dict[str, Any]:
    """
    Fetch knowledge graph visualization data for a company.

    Returns nodes and edges in format compatible with vis-network:
    {
        "nodes": [{"id": "1", "label": "Company", "group": "company"}, ...],
        "edges": [{"from": "1", "to": "2", "label": "invested_in"}, ...]
    }

    Args:
        company_name: Company name
        domain: Company domain
        app: Application type for graph selection

    Returns:
        Dict with nodes, edges arrays for vis-network
    """
    graph_id = get_graph_id_for_app(app)
    activity.logger.info(f"Fetching graph visualization data for {company_name}")

    if not config.ZEP_API_KEY:
        activity.logger.warning("ZEP_API_KEY not configured")
        return {"nodes": [], "edges": [], "error": "ZEP_API_KEY not configured"}

    try:
        client = AsyncZep(api_key=config.ZEP_API_KEY)

        # Search for company node and its connections
        search_query = f"{company_name} {domain}"

        results = await client.graph.search(
            graph_id=graph_id,
            query=search_query,
            limit=50  # Get up to 50 connected entities
        )

        # Build nodes and edges for visualization
        nodes = []
        edges = []
        node_ids = set()

        # Process search results
        if results and hasattr(results, 'edges'):
            for edge in results.edges:
                # Add source node
                if hasattr(edge, 'source') and edge.source:
                    source_id = str(edge.source.uuid) if hasattr(edge.source, 'uuid') else str(hash(edge.source.name))
                    if source_id not in node_ids:
                        nodes.append({
                            "id": source_id,
                            "label": getattr(edge.source, 'name', 'Unknown'),
                            "group": getattr(edge.source, 'type', 'entity'),
                            "title": getattr(edge.source, 'summary', '')  # Tooltip
                        })
                        node_ids.add(source_id)

                # Add target node
                if hasattr(edge, 'target') and edge.target:
                    target_id = str(edge.target.uuid) if hasattr(edge.target, 'uuid') else str(hash(edge.target.name))
                    if target_id not in node_ids:
                        nodes.append({
                            "id": target_id,
                            "label": getattr(edge.target, 'name', 'Unknown'),
                            "group": getattr(edge.target, 'type', 'entity'),
                            "title": getattr(edge.target, 'summary', '')
                        })
                        node_ids.add(target_id)

                # Add edge
                if hasattr(edge, 'source') and hasattr(edge, 'target'):
                    edges.append({
                        "from": source_id,
                        "to": target_id,
                        "label": getattr(edge, 'fact', ''),
                        "title": getattr(edge, 'fact', '')  # Tooltip
                    })

        activity.logger.info(f"Graph data: {len(nodes)} nodes, {len(edges)} edges")

        return {
            "nodes": nodes,
            "edges": edges,
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"Failed to fetch graph data: {e}")
        return {
            "nodes": [],
            "edges": [],
            "success": False,
            "error": str(e)
        }
