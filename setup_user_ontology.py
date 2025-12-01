#!/usr/bin/env python3
"""
Setup User Ontology in ZEP

Applies the user ontology (entity types + edge types) to the 'users' graph.

Usage:
    python setup_user_ontology.py
    python setup_user_ontology.py --dry-run  # Preview without applying
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

load_dotenv()

# Add gateway to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gateway'))

ZEP_API_KEY = os.getenv("ZEP_API_KEY")
ZEP_USERS_GRAPH_ID = os.getenv("ZEP_GRAPH_ID_USERS", "users")


async def main(dry_run: bool = False):
    print("=" * 60)
    print("ZEP User Ontology Setup")
    print("=" * 60)
    print()

    if not ZEP_API_KEY:
        print("ERROR: ZEP_API_KEY not set")
        sys.exit(1)

    # Import ontology
    try:
        from models.user_ontology import (
            get_user_ontology_config,
            USER_ENTITY_TYPES,
            USER_EDGE_TYPES_CONFIG,
            ZEP_USER_ONTOLOGY_AVAILABLE
        )
    except ImportError as e:
        print(f"ERROR: Failed to import user ontology: {e}")
        sys.exit(1)

    if not ZEP_USER_ONTOLOGY_AVAILABLE:
        print("ERROR: zep-cloud package not available")
        sys.exit(1)

    # Print ontology summary
    print("ENTITY TYPES (10 max):")
    for name, model in USER_ENTITY_TYPES.items():
        fields = [f for f in model.model_fields.keys() if f not in ['name']]
        print(f"  {name}: {', '.join(fields[:5])}")
    print()

    print("EDGE TYPES (10 max):")
    for name, config in USER_EDGE_TYPES_CONFIG.items():
        print(f"  {name}: {config['source']} → {config['target']}")
    print()

    if dry_run:
        print("DRY RUN - Not applying to ZEP")
        return

    # Get ontology config
    ontology_config = get_user_ontology_config()

    # Apply to ZEP
    print(f"Applying ontology to graph '{ZEP_USERS_GRAPH_ID}'...")

    from zep_cloud.client import AsyncZep
    client = AsyncZep(api_key=ZEP_API_KEY)

    try:
        # Ensure graph exists
        try:
            await client.graph.create(
                graph_id=ZEP_USERS_GRAPH_ID,
                name="User Profiles",
                description="Knowledge graph of user profiles, goals, and preferences across Quest apps"
            )
            print(f"  Created graph '{ZEP_USERS_GRAPH_ID}'")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"  Graph '{ZEP_USERS_GRAPH_ID}' already exists")
            else:
                print(f"  Warning creating graph: {e}")

        # Apply ontology
        await client.graph.set_ontology(
            entities=ontology_config["entities"],
            edges=ontology_config["edges"],
            graph_ids=[ZEP_USERS_GRAPH_ID]
        )

        print(f"  Ontology applied to '{ZEP_USERS_GRAPH_ID}'")
        print()
        print("SUCCESS!")
        print()
        print("The 'users' graph now has:")
        print(f"  - {len(USER_ENTITY_TYPES)} entity types")
        print(f"  - {len(USER_EDGE_TYPES_CONFIG)} edge types")
        print()
        print("Entity types: User, Destination, Origin, CareerProfile, Organization,")
        print("              Goal, Motivation, FamilyUnit, FinancialProfile, Preference")
        print()
        print("Edge types: INTERESTED_IN, LOCATED_IN, HAS_CAREER, EMPLOYED_BY,")
        print("            REPRESENTS, HAS_GOAL, MOTIVATED_BY, HAS_FAMILY,")
        print("            HAS_FINANCES, PREFERS")

    except Exception as e:
        print(f"ERROR applying ontology: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup user ontology in ZEP")
    parser.add_argument("--dry-run", action="store_true", help="Preview without applying")
    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run))
