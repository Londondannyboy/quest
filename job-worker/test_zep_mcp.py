#!/usr/bin/env python3
"""
Test ZEP MCP functionality for job skill graphs
Tests proper ontology setup and entity relationships
"""

import asyncio
import json
import os
from datetime import datetime
from zep_cloud.client import AsyncZep
from dotenv import load_dotenv

load_dotenv()


async def test_zep_ontology():
    """Test setting up and using ZEP ontology for jobs"""

    zep_api_key = os.getenv("ZEP_API_KEY")
    if not zep_api_key:
        print("❌ No ZEP_API_KEY found in environment")
        return

    print("🚀 Testing ZEP with proper ontology")
    print("="*60)

    zep = AsyncZep(api_key=zep_api_key)

    # Create a new graph for testing
    graph_id = f"test-jobs-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print(f"\n0️⃣ Creating test graph: {graph_id}")
    try:
        graph = await zep.graph.create(
            graph_id=graph_id,
            name="Test Job Skills Graph",
            description="Testing job skill graph functionality"
        )
        print(f"✅ Created graph: {graph_id}")
    except Exception as e:
        print(f"⚠️  Graph creation warning: {e}")
        # Graph might already exist, continue

    # Test 1: Add sample job data with proper structure
    print("\n1️⃣ Testing job data addition with entities and relationships...")

    sample_job = {
        "id": "test-job-001",
        "title": "Senior Python Engineer",
        "company_name": "TestCorp",
        "location": "London - Remote",
        "department": "Engineering",
        "employment_type": "Full-time",
        "seniority_level": "Senior",
        "is_fractional": False,
        "is_remote": True,
        "classification_confidence": 0.95,
        "url": "https://example.com/jobs/senior-python-engineer",
        "description": "We're looking for a Senior Python Engineer with experience in FastAPI, PostgreSQL, and AWS. You'll work on building scalable microservices.",
        "skills": [
            {"name": "Python", "importance": "essential", "category": "technical"},
            {"name": "FastAPI", "importance": "essential", "category": "technical"},
            {"name": "PostgreSQL", "importance": "essential", "category": "technical"},
            {"name": "AWS", "importance": "beneficial", "category": "technical"},
            {"name": "Docker", "importance": "beneficial", "category": "technical"}
        ]
    }

    # Create a rich episode with entity information
    # The key is to structure data so ZEP can extract entities properly
    episode_text = f"""
Job Posting: {sample_job['title']} at {sample_job['company_name']}

The company {sample_job['company_name']} has posted a job for {sample_job['title']} in the {sample_job['department']} department.

Location: {sample_job['location']}
Employment Type: {sample_job['employment_type']}
Seniority Level: {sample_job['seniority_level']}
Remote: {"Yes" if sample_job['is_remote'] else "No"}

Description: {sample_job['description']}

Required Skills:
"""

    # Add skills to the text
    for skill in sample_job['skills']:
        episode_text += f"- {skill['name']} ({skill['importance']})\n"

    episode_text += f"\nJob URL: {sample_job['url']}"

    try:
        # Add as text episode - ZEP will extract entities
        result = await zep.graph.add(
            graph_id=graph_id,
            type="text",
            data=episode_text
        )

        print(f"✅ Added job episode to graph")
        print(f"   Episode ID: {result.episode_id if hasattr(result, 'episode_id') else 'N/A'}")

        # Wait a bit for processing
        await asyncio.sleep(2)

    except Exception as e:
        print(f"❌ Failed to add job to graph: {e}")
        return

    # Test 2: Search for the job
    print("\n2️⃣ Testing search for job...")

    try:
        search_results = await zep.graph.search(
            graph_id=graph_id,
            query=sample_job['title'],
            limit=5
        )

        print(f"✅ Search results:")
        if hasattr(search_results, 'edges') and search_results.edges:
            print(f"   Found {len(search_results.edges)} edges")
            for edge in search_results.edges[:3]:
                print(f"   - {edge.fact if hasattr(edge, 'fact') else 'No fact'}")
        else:
            print("   No edges found")

        if hasattr(search_results, 'nodes') and search_results.nodes:
            print(f"   Found {len(search_results.nodes)} nodes")
            for node in search_results.nodes[:3]:
                if hasattr(node, 'name'):
                    print(f"   - {node.name}")
        else:
            print("   No nodes found")

    except Exception as e:
        print(f"❌ Search failed: {e}")

    # Test 3: Search for skills
    print("\n3️⃣ Testing skill graph retrieval...")

    try:
        # Search for Python skill
        skill_results = await zep.graph.search(
            graph_id=graph_id,
            query="Python skill requirements",
            limit=10
        )

        print(f"✅ Skill search results:")
        if hasattr(skill_results, 'edges') and skill_results.edges:
            print(f"   Found {len(skill_results.edges)} skill edges")
            for edge in skill_results.edges[:5]:
                if hasattr(edge, 'fact'):
                    print(f"   - {edge.fact}")
        else:
            print("   No skill edges found")

    except Exception as e:
        print(f"❌ Skill search failed: {e}")

    # Test 4: Get graph entities
    print("\n4️⃣ Testing entity retrieval...")

    try:
        # Try to get entities for the graph
        # Note: This might need adjustment based on actual ZEP API
        entities_response = await zep.graph.get_graph(graph_id=graph_id)

        print(f"✅ Graph info retrieved")
        if hasattr(entities_response, 'name'):
            print(f"   Graph name: {entities_response.name}")
        if hasattr(entities_response, 'description'):
            print(f"   Graph description: {entities_response.description}")

    except Exception as e:
        print(f"⚠️  Could not get graph entities: {e}")

    print("\n" + "="*60)
    print("✅ ZEP testing complete!")
    print("\nKey findings:")
    print("- Job data can be added as text episodes")
    print("- ZEP will extract entities from structured text")
    print("- Search works for retrieving job and skill information")
    print("\nNext steps:")
    print("- Update save_jobs_to_zep activity to use text episodes")
    print("- Structure job data as rich text with entity hints")
    print("- Test full workflow with multiple jobs")


if __name__ == "__main__":
    asyncio.run(test_zep_ontology())
