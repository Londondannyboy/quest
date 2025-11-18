"""
Initialize Zep Knowledge Graph Ontology

One-time script to set up custom entity and edge types for:
- finance-knowledge graph (placement app)
- relocation graph (relocation app)

Run with: python scripts/init_zep_ontology.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from zep_cloud.client import AsyncZep
try:
    from zep_cloud.external_clients.ontology import EntityModel, EntityText, EntityInt
except ImportError:
    # Fallback for different zep_cloud versions
    from zep_cloud.ontology import EntityModel, EntityText, EntityInt
from pydantic import Field

load_dotenv()

# Zep Configuration
ZEP_API_KEY = os.getenv("ZEP_API_KEY")

# Entity Type Definitions using Pydantic EntityModel
class Company(EntityModel):
    """Company entity for financial services firms, investment banks, etc."""
    domain: EntityText = Field(description="Company domain (e.g., evercore.com)")
    industry: EntityText = Field(description="Primary industry or sector")
    headquarters_city: EntityText = Field(description="Headquarters city location")
    headquarters_country: EntityText = Field(description="Headquarters country")
    founded_year: EntityInt = Field(description="Year the company was founded")
    employee_range: EntityText = Field(description="Employee count range")
    company_type: EntityText = Field(description="Type: placement_agent, investment_bank, etc.")


class Deal(EntityModel):
    """Deal entity for transactions, M&A, capital raises, etc."""
    deal_type: EntityText = Field(description="Type: M&A, capital_raising, IPO, etc.")
    value: EntityText = Field(description="Deal value (e.g., '$7.4B', '€500M')")
    date: EntityText = Field(description="Deal date or timeframe")
    status: EntityText = Field(description="Status: completed, announced, pending")
    sector: EntityText = Field(description="Industry sector of the deal")


class Person(EntityModel):
    """Person entity for executives, key people, board members."""
    role: EntityText = Field(description="Job title or role (e.g., 'CEO', 'Managing Director')")
    company: EntityText = Field(description="Associated company name")
    linkedin: EntityText = Field(description="LinkedIn profile URL")


# Legacy dictionary definitions (for reference only - not used)
COMPANY_ENTITY = {
    "name": "Company",
    "description": "Financial services firms, investment banks, placement agents, advisory firms, relocation providers",
    "properties": {
        "domain": {
            "type": "string",
            "description": "Company domain (e.g., evercore.com)"
        },
        "industry": {
            "type": "string",
            "description": "Primary industry or sector"
        },
        "headquarters_city": {
            "type": "string",
            "description": "Headquarters city location"
        },
        "headquarters_country": {
            "type": "string",
            "description": "Headquarters country"
        },
        "founded_year": {
            "type": "integer",
            "description": "Year the company was founded"
        },
        "employee_range": {
            "type": "string",
            "description": "Employee count range"
        },
        "company_type": {
            "type": "string",
            "description": "Type: placement_agent, investment_bank, relocation_provider, etc."
        }
    }
}

DEAL_ENTITY = {
    "name": "Deal",
    "description": "Transactions, M&A deals, capital raises, IPOs, advisory mandates",
    "properties": {
        "deal_type": {
            "type": "string",
            "description": "Type: M&A, capital_raising, IPO, advisory, etc."
        },
        "value": {
            "type": "string",
            "description": "Deal value (e.g., '$7.4B', '€500M')"
        },
        "date": {
            "type": "string",
            "description": "Deal date or timeframe (e.g., '2024-Q1', 'March 2024')"
        },
        "status": {
            "type": "string",
            "description": "Status: completed, announced, pending, etc."
        },
        "sector": {
            "type": "string",
            "description": "Industry sector of the deal"
        }
    }
}

PERSON_ENTITY = {
    "name": "Person",
    "description": "Executives, key people, board members, advisors",
    "properties": {
        "role": {
            "type": "string",
            "description": "Job title or role (e.g., 'CEO', 'Managing Director')"
        },
        "company": {
            "type": "string",
            "description": "Associated company name"
        },
        "linkedin": {
            "type": "string",
            "description": "LinkedIn profile URL"
        }
    }
}

# Edge Type Definitions (Relationships)
ADVISED_ON = {
    "name": "ADVISED_ON",
    "description": "Company advised on a deal or transaction",
    "from_entity": "Company",
    "to_entity": "Deal"
}

WORKS_AT = {
    "name": "WORKS_AT",
    "description": "Person works at or is employed by a company",
    "from_entity": "Person",
    "to_entity": "Company"
}

INVESTED_IN = {
    "name": "INVESTED_IN",
    "description": "Company invested in another company (equity stake, acquisition, etc.)",
    "from_entity": "Company",
    "to_entity": "Company"
}

PARTNERED_WITH = {
    "name": "PARTNERED_WITH",
    "description": "Companies have a partnership or strategic relationship",
    "from_entity": "Company",
    "to_entity": "Company"
}

COMPETED_WITH = {
    "name": "COMPETED_WITH",
    "description": "Companies competed on the same deal or mandate",
    "from_entity": "Company",
    "to_entity": "Company"
}

# Graphs to initialize
GRAPHS = [
    {
        "id": "finance-knowledge",
        "description": "Financial services knowledge graph (placement, banking, advisory)"
    },
    {
        "id": "relocation",
        "description": "Relocation services knowledge graph"
    }
]


async def set_project_ontology(client: AsyncZep):
    """
    Set project-level ontology (applies to all graphs).

    Args:
        client: AsyncZep client
    """
    print(f"\n{'='*60}")
    print("Setting Project-Level Ontology")
    print(f"{'='*60}")

    try:
        # Build entities dictionary using Pydantic models
        entities = {
            "Company": Company,
            "Deal": Deal,
            "Person": Person
        }

        # Build edges dictionary
        # Note: Edges might need to be defined differently - for now, just pass empty dict
        # The SDK might not require edges to be defined upfront
        edges = {}

        print("\n📋 Setting custom ontology (project-level)...")

        # Set ontology at project level (no graph_id parameter)
        await client.graph.set_ontology(
            entities=entities,
            edges=edges
        )

        print("✅ Ontology set successfully!")
        print(f"   - Entity types: {len(entities)}")
        print(f"   - Edge types: {len(edges)}")

        # Print entity types
        print("\n📊 Entity Types:")
        for name, entity_class in entities.items():
            print(f"   • {name}: {entity_class.__doc__ or 'No description'}")

        # Print edge types (if any)
        if edges:
            print("\n🔗 Edge Types:")
            for name, edge in edges.items():
                print(f"   • {name}: {edge.get('from_entity', '?')} → {edge.get('to_entity', '?')}")
        else:
            print("\n🔗 Edge Types: (None defined - edges can be created dynamically)")

        return True

    except Exception as e:
        print(f"❌ Failed to set ontology: {e}")
        return False


async def create_graph(client: AsyncZep, graph_id: str, description: str):
    """
    Create a knowledge graph (uses project ontology).

    Args:
        client: AsyncZep client
        graph_id: Graph ID to create
        description: Graph description
    """
    print(f"\n{'='*60}")
    print(f"Creating graph: {graph_id}")
    print(f"Description: {description}")
    print(f"{'='*60}")

    try:
        # Create graph (will use project ontology)
        await client.graph.create(
            graph_id=graph_id,
            name=description
        )

        print(f"✅ Graph '{graph_id}' created successfully!")
        return True

    except Exception as e:
        # Graph might already exist
        if "already exists" in str(e).lower() or "409" in str(e):
            print(f"ℹ️  Graph '{graph_id}' already exists")
            return True
        else:
            print(f"❌ Failed to create graph '{graph_id}': {e}")
            return False


async def main():
    """Initialize all Zep graphs with custom ontology."""

    print("\n" + "="*60)
    print("🚀 ZEP KNOWLEDGE GRAPH ONTOLOGY INITIALIZATION")
    print("="*60)

    # Validate API key
    if not ZEP_API_KEY:
        print("\n❌ ERROR: ZEP_API_KEY not found in environment variables")
        print("   Please set ZEP_API_KEY in your .env file")
        return

    print(f"\n🔑 Using Zep API Key: {ZEP_API_KEY[:20]}...")

    # Initialize client
    client = AsyncZep(api_key=ZEP_API_KEY)

    # Step 1: Set project-level ontology
    ontology_success = await set_project_ontology(client)

    if not ontology_success:
        print("\n❌ Failed to set ontology. Cannot proceed with graph creation.")
        return

    # Step 2: Create graphs (they will use the project ontology)
    results = []
    for graph in GRAPHS:
        success = await create_graph(
            client,
            graph["id"],
            graph["description"]
        )
        results.append((graph["id"], success))

    # Summary
    print("\n" + "="*60)
    print("📊 INITIALIZATION SUMMARY")
    print("="*60)

    print(f"{'✅ SUCCESS' if ontology_success else '❌ FAILED'}: Project Ontology")
    for graph_id, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: Graph '{graph_id}'")

    all_success = ontology_success and all(success for _, success in results)

    if all_success:
        print("\n🎉 All graphs initialized successfully!")
        print("\n📝 Next Steps:")
        print("   1. Graphs are ready to receive structured entities")
        print("   2. Deploy updated company-worker with entity extraction")
        print("   3. Create companies via dashboard - entities will sync to Zep")
    else:
        print("\n⚠️  Some graphs failed to initialize. Check errors above.")

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
