#!/usr/bin/env python3
"""
Complete ZEP test with multiple jobs and skill graph retrieval
"""

import asyncio
import os
from datetime import datetime
from zep_cloud.client import AsyncZep
from dotenv import load_dotenv

load_dotenv()


async def test_complete_workflow():
    """Test complete workflow with multiple jobs"""

    zep_api_key = os.getenv("ZEP_API_KEY")
    if not zep_api_key:
        print("❌ No ZEP_API_KEY found in environment")
        return

    print("🚀 Testing Complete ZEP Workflow")
    print("="*60)

    zep = AsyncZep(api_key=zep_api_key)

    # Create a new graph
    graph_id = f"fractional-jobs-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print(f"\n📝 Creating graph: {graph_id}")
    try:
        await zep.graph.create(
            graph_id=graph_id,
            name="Fractional Jobs Graph",
            description="Job postings with skill requirements for fractional.quest"
        )
        print(f"✅ Created graph")
    except Exception as e:
        print(f"⚠️  Graph creation: {e}")

    # Sample jobs with different skills
    sample_jobs = [
        {
            "title": "Senior Python Engineer",
            "company": "TechCorp",
            "location": "London - Remote",
            "skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
            "description": "Build scalable microservices with Python and FastAPI"
        },
        {
            "title": "React Developer",
            "company": "DigitalAgency",
            "location": "Paris - Hybrid",
            "skills": ["React", "TypeScript", "Node.js", "PostgreSQL"],
            "description": "Develop modern web applications with React and TypeScript"
        },
        {
            "title": "Full Stack Engineer",
            "company": "StartupCo",
            "location": "Berlin - Remote",
            "skills": ["Python", "React", "TypeScript", "AWS", "Kubernetes"],
            "description": "Work across the full stack building products from frontend to backend"
        },
        {
            "title": "DevOps Engineer",
            "company": "CloudServices",
            "location": "Amsterdam - Remote",
            "skills": ["Kubernetes", "Docker", "AWS", "Terraform", "Python"],
            "description": "Manage cloud infrastructure and deployment pipelines"
        },
        {
            "title": "Data Engineer",
            "company": "DataCorp",
            "location": "Stockholm - Hybrid",
            "skills": ["Python", "SQL", "PostgreSQL", "Airflow", "AWS"],
            "description": "Build and maintain data pipelines and warehouses"
        }
    ]

    print(f"\n1️⃣ Adding {len(sample_jobs)} jobs to graph...")
    for i, job in enumerate(sample_jobs, 1):
        episode_text = f"""
Job: {job['title']} at {job['company']}
Location: {job['location']}

{job['description']}

Required Skills: {', '.join(job['skills'])}

This is a fractional opportunity for experienced professionals.
"""

        try:
            result = await zep.graph.add(
                graph_id=graph_id,
                type="text",
                data=episode_text
            )
            print(f"  ✅ {i}. Added: {job['title']} at {job['company']}")
        except Exception as e:
            print(f"  ❌ {i}. Failed: {e}")

        # Small delay between additions
        await asyncio.sleep(0.5)

    # Wait for processing
    print("\n⏳ Waiting 10 seconds for ZEP to process and extract entities...")
    await asyncio.sleep(10)

    # Test searches
    print("\n2️⃣ Testing searches...")

    # Search for Python jobs
    print("\n  🔍 Searching for Python jobs:")
    try:
        results = await zep.graph.search(
            graph_id=graph_id,
            query="Python engineer jobs",
            limit=10
        )

        if hasattr(results, 'edges') and results.edges:
            print(f"    Found {len(results.edges)} edges")
            for edge in results.edges[:3]:
                if hasattr(edge, 'fact'):
                    print(f"    - {edge.fact}")
        if hasattr(results, 'nodes') and results.nodes:
            print(f"    Found {len(results.nodes)} nodes")
            for node in results.nodes[:3]:
                print(f"    - {node.name if hasattr(node, 'name') else node}")
    except Exception as e:
        print(f"    ❌ Search failed: {e}")

    # Search for skills
    print("\n  🔍 Searching for AWS skills:")
    try:
        results = await zep.graph.search(
            graph_id=graph_id,
            query="AWS cloud skills required",
            limit=10
        )

        if hasattr(results, 'edges') and results.edges:
            print(f"    Found {len(results.edges)} edges")
            for edge in results.edges[:3]:
                if hasattr(edge, 'fact'):
                    print(f"    - {edge.fact}")
        if hasattr(results, 'nodes') and results.nodes:
            print(f"    Found {len(results.nodes)} nodes")
    except Exception as e:
        print(f"    ❌ Search failed: {e}")

    # Search for React jobs
    print("\n  🔍 Searching for React jobs:")
    try:
        results = await zep.graph.search(
            graph_id=graph_id,
            query="React TypeScript developer",
            limit=10
        )

        if hasattr(results, 'edges') and results.edges:
            print(f"    Found {len(results.edges)} edges")
            for edge in results.edges[:3]:
                if hasattr(edge, 'fact'):
                    print(f"    - {edge.fact}")
        if hasattr(results, 'nodes') and results.nodes:
            print(f"    Found {len(results.nodes)} nodes")
    except Exception as e:
        print(f"    ❌ Search failed: {e}")

    print("\n" + "="*60)
    print("✅ Complete workflow test finished!")
    print(f"\nGraph ID: {graph_id}")
    print("\n📊 Summary:")
    print(f"  - Created graph: {graph_id}")
    print(f"  - Added {len(sample_jobs)} jobs with skills")
    print(f"  - Tested search for jobs and skills")
    print("\n💡 This demonstrates:")
    print("  - ZEP can extract entities from text episodes")
    print("  - Multiple jobs can be added to build a knowledge graph")
    print("  - Skill relationships are automatically created")
    print("  - Search retrieves relevant job and skill information")


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
