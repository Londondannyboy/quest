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


def _guess_node_type(edge_name: str, entity_name: str) -> str:
    """
    Infer node type from edge relationship and entity name.

    Args:
        edge_name: Edge type (e.g., WORKS_AT, ADVISED_ON)
        entity_name: Entity name extracted from fact

    Returns:
        Node type: company, person, deal, or entity
    """
    edge_name_lower = edge_name.lower()
    entity_name_lower = entity_name.lower()

    # Check edge type patterns
    if "works_at" in edge_name_lower or "employed_by" in edge_name_lower:
        # WORKS_AT edges: source is person, target is company
        return "person"

    if "advised_on" in edge_name_lower or "facilitated" in edge_name_lower:
        # ADVISED_ON edges: source is company, target is deal
        if "deal" in edge_name_lower or "transaction" in edge_name_lower:
            return "deal"
        return "company"

    # Check entity name patterns
    if any(word in entity_name_lower for word in ["deal", "transaction", "acquisition", "merger", "ipo"]):
        return "deal"

    if any(word in entity_name_lower for word in ["mr", "ms", "dr", "ceo", "cfo", "president", "director"]):
        return "person"

    # Check if it's likely a company (has Inc, LLC, Corp, etc.)
    if any(suffix in entity_name_lower for suffix in ["inc", "llc", "corp", "ltd", "group", "partners", "capital"]):
        return "company"

    # Default to generic entity type
    return "entity"


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
        # Strategy: Extract node info from facts since Zep doesn't return node details
        nodes = []
        edges = []
        node_map = {}  # uuid -> node info

        # First pass: Extract all unique entities from edge facts
        if results and hasattr(results, 'edges'):
            for edge in results.edges:
                fact = getattr(edge, 'fact', '')
                edge_name = getattr(edge, 'name', 'RELATED_TO')

                # Get UUIDs
                source_uuid = getattr(edge, 'source_node_uuid', None)
                target_uuid = getattr(edge, 'target_node_uuid', None)

                if not source_uuid or not target_uuid:
                    continue

                # Extract entity names from fact text
                # Facts like "Evercore is an investment banking firm"
                # or "Roger Altman works at Evercore"
                parts = fact.split(' ')

                # Create/update source node
                if source_uuid not in node_map:
                    # Try to extract name from beginning of fact
                    source_name = company_name if company_name.lower() in fact.lower() else parts[0] if parts else "Entity"
                    node_map[source_uuid] = {
                        "id": source_uuid,
                        "label": source_name,
                        "group": _guess_node_type(edge_name, source_name),
                        "title": fact  # Show fact as tooltip
                    }

                # Create/update target node
                if target_uuid not in node_map:
                    # Try to extract name from end of fact
                    target_name = parts[-1] if len(parts) > 2 else "Related"
                    node_map[target_uuid] = {
                        "id": target_uuid,
                        "label": target_name,
                        "group": _guess_node_type(edge_name, target_name),
                        "title": fact
                    }

                # Add edge
                edges.append({
                    "from": source_uuid,
                    "to": target_uuid,
                    "label": edge_name.replace('_', ' ').title(),
                    "title": fact
                })

        # Convert node_map to list
        nodes = list(node_map.values())

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
