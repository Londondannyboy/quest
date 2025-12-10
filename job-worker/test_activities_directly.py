#!/usr/bin/env python3
"""
Test activities directly without Temporal to verify the fix
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import activities
from src.activities.classification import save_jobs_to_zep
from src.activities.zep_retrieval import get_job_skill_graph


async def test_save_and_retrieve():
    """Test saving jobs to ZEP and retrieving skill graphs"""

    print("🧪 Testing ZEP Activities Directly")
    print("="*60)

    # Sample classified jobs (simulating what comes from classification)
    sample_jobs = [
        {
            "url": "https://example.com/jobs/senior-python-1",
            "title": "Senior Python Engineer",
            "company_name": "TechStartup",
            "location": "London - Remote",
            "department": "Engineering",
            "employment_type": "Full-time",
            "seniority_level": "Senior",
            "is_fractional": False,
            "is_remote": True,
            "classification_confidence": 0.92,
            "description": "Join our team building scalable microservices with Python, FastAPI, and PostgreSQL. Work with AWS, Docker, and Kubernetes.",
            "skills": [
                {"name": "Python", "importance": "essential", "category": "technical"},
                {"name": "FastAPI", "importance": "essential", "category": "technical"},
                {"name": "PostgreSQL", "importance": "essential", "category": "technical"},
                {"name": "AWS", "importance": "beneficial", "category": "technical"},
                {"name": "Docker", "importance": "beneficial", "category": "technical"},
            ]
        },
        {
            "url": "https://example.com/jobs/fullstack-2",
            "title": "Full Stack Developer",
            "company_name": "ProductCo",
            "location": "Paris - Hybrid",
            "department": "Engineering",
            "employment_type": "Full-time",
            "seniority_level": "Mid-level",
            "is_fractional": True,
            "is_remote": False,
            "classification_confidence": 0.88,
            "description": "Build modern web applications with React, TypeScript, and Node.js. 20-30 hours per week.",
            "skills": [
                {"name": "React", "importance": "essential", "category": "technical"},
                {"name": "TypeScript", "importance": "essential", "category": "technical"},
                {"name": "Node.js", "importance": "essential", "category": "technical"},
                {"name": "PostgreSQL", "importance": "beneficial", "category": "technical"},
            ]
        },
        {
            "url": "https://example.com/jobs/devops-3",
            "title": "DevOps Engineer",
            "company_name": "CloudServices",
            "location": "Amsterdam - Remote",
            "department": "Infrastructure",
            "employment_type": "Contract",
            "seniority_level": "Senior",
            "is_fractional": True,
            "is_remote": True,
            "classification_confidence": 0.95,
            "description": "Manage cloud infrastructure and CI/CD pipelines. Kubernetes, AWS, Terraform experience required.",
            "skills": [
                {"name": "Kubernetes", "importance": "essential", "category": "technical"},
                {"name": "AWS", "importance": "essential", "category": "technical"},
                {"name": "Terraform", "importance": "essential", "category": "technical"},
                {"name": "Docker", "importance": "essential", "category": "technical"},
                {"name": "Python", "importance": "beneficial", "category": "technical"},
            ]
        }
    ]

    print(f"\n1️⃣ Testing save_jobs_to_zep with {len(sample_jobs)} jobs...")
    print("-" * 60)

    try:
        # Call the activity directly
        result = await save_jobs_to_zep(sample_jobs)

        print(f"\n✅ Save result:")
        print(f"   Jobs saved to graph: {result.get('jobs_saved_to_graph', 0)}")
        print(f"   Skipped duplicates: {result.get('skipped_duplicates', 0)}")

        if result.get('error'):
            print(f"   ⚠️  Error: {result['error']}")

        if result.get('jobs_saved_to_graph', 0) > 0:
            print(f"\n   ✨ SUCCESS! {result['jobs_saved_to_graph']} jobs saved to ZEP!")
        else:
            print(f"\n   ❌ FAILED! No jobs were saved to ZEP")
            print(f"   Check ZEP_API_KEY and graph configuration")

    except Exception as e:
        print(f"\n❌ Save failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return

    # Wait a bit for ZEP to process
    print("\n⏳ Waiting 5 seconds for ZEP to process...")
    await asyncio.sleep(5)

    # Test retrieval
    print(f"\n2️⃣ Testing get_job_skill_graph...")
    print("-" * 60)

    try:
        # Use the first job's URL as ID
        test_job_id = sample_jobs[0]["url"]

        result = await get_job_skill_graph(test_job_id)

        print(f"\n✅ Retrieval result:")
        print(f"   Job ID: {result.get('job_id')}")
        print(f"   Skills found: {result.get('total_skills', 0)}")
        print(f"   Related jobs: {result.get('total_related', 0)}")

        if result.get('skills'):
            print(f"\n   Skills:")
            for skill in result['skills'][:5]:
                print(f"     - {skill}")

        if result.get('related_jobs'):
            print(f"\n   Related jobs:")
            for job in result['related_jobs'][:3]:
                print(f"     - {job}")

    except Exception as e:
        print(f"\n❌ Retrieval failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("✅ Direct activity test complete!")
    print("\n📊 Summary:")
    print("   - save_jobs_to_zep: Uses text episodes with entity hints")
    print("   - ZEP extracts: Companies, Jobs, Skills, Locations")
    print("   - get_job_skill_graph: Retrieves related skills and jobs")
    print("\n💡 Next: Test full Temporal workflow with real scraper")


if __name__ == "__main__":
    asyncio.run(test_save_and_retrieve())
