#!/usr/bin/env python3
"""Quick integration test for the Apify Job Worker pipeline."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Ensure GEMINI_API_KEY is set for Pydantic AI
if not os.getenv("GEMINI_API_KEY") and os.getenv("GOOGLE_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

async def test_classification():
    """Test Pydantic AI classification on a sample job."""
    print("\n" + "="*70)
    print("🧪 Testing Pydantic AI Job Classification")
    print("="*70)

    from src.models.job_classification import classify_job

    # Sample job from our Apify scrape
    sample_job = {
        "title": "Fractional CTO (CPG / eCommerce / ex-Big4 Consulting)",
        "description": """We're hiring a senior Fractional CTO with 10–15+ years of experience
        in CPG, eCommerce, or Big-4 consulting. This is a hands-on delivery role working
        2-3 days per week. You'll own the technology roadmap, manage vendors, and drive
        technical delivery for a fast-growing consumer brand.""",
        "company": "NEUROTIC",
        "location": "London Area, United Kingdom",
    }

    print(f"\n📋 Job: {sample_job['title']}")
    print(f"🏢 Company: {sample_job['company']}")
    print(f"📍 Location: {sample_job['location']}")
    print("\n⏳ Classifying with Pydantic AI (Gemini 2.0 Flash)...")

    try:
        classification = await classify_job(
            job_title=sample_job['title'],
            job_description=sample_job['description'],
            company_name=sample_job['company'],
            location=sample_job['location'],
        )

        print("\n✅ Classification Complete!")
        print(f"\n📊 Results:")
        print(f"  Employment Type: {classification.employment_type}")
        print(f"  Is Fractional: {classification.is_fractional}")
        print(f"  Country: {classification.country}")
        print(f"  City: {classification.city or 'N/A'}")
        print(f"  Category: {classification.category}")
        print(f"  Seniority: {classification.seniority_level}")
        print(f"  Normalized Title: {classification.role_title}")
        print(f"  Required Skills: {', '.join(classification.required_skills[:5]) if classification.required_skills else 'None'}")
        print(f"  Site Tags: {', '.join(classification.site_tags)}")
        print(f"  Confidence: {classification.classification_confidence:.2f}")
        print(f"\n💭 Reasoning: {classification.reasoning}")

        return True

    except Exception as e:
        print(f"\n❌ Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_duplicate_check():
    """Test duplicate checking in Neon."""
    print("\n" + "="*70)
    print("🔍 Testing Duplicate Check in Neon")
    print("="*70)

    import asyncpg

    database_url = os.getenv("DATABASE_URL")

    try:
        conn = await asyncpg.connect(database_url)

        # Check for existing jobs
        count = await conn.fetchval(
            """SELECT COUNT(*) FROM jobs j
            JOIN job_boards jb ON j.board_id = jb.id
            WHERE jb.company_name = 'LinkedIn UK (Apify)'
            AND j.is_active = true"""
        )

        print(f"\n✅ Found {count} existing jobs in Neon")

        # Get sample
        if count > 0:
            sample = await conn.fetch(
                """SELECT
                    j.company_name,
                    j.title,
                    j.is_fractional,
                    j.employment_type,
                    j.site_tags
                FROM jobs j
                JOIN job_boards jb ON j.board_id = jb.id
                WHERE jb.company_name = 'LinkedIn UK (Apify)'
                AND j.is_active = true
                ORDER BY j.first_seen_at DESC
                LIMIT 3"""
            )

            print(f"\n📋 Recent jobs:")
            for job in sample:
                print(f"  • {job['company_name']}: {job['title']}")
                print(f"    Fractional: {job['is_fractional']}, Type: {job['employment_type']}")

        await conn.close()
        return True

    except Exception as e:
        print(f"\n❌ Database check failed: {e}")
        return False


async def test_apify_connection():
    """Test Apify API connection."""
    print("\n" + "="*70)
    print("🔌 Testing Apify API Connection")
    print("="*70)

    import httpx

    api_key = os.getenv("APIFY_API_KEY")
    task_id = os.getenv("APIFY_TASK_ID")

    if not api_key or not task_id:
        print("❌ APIFY_API_KEY or APIFY_TASK_ID not set")
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check recent runs
            response = await client.get(
                f"https://api.apify.com/v2/actor-tasks/{task_id.replace('/', '~')}/runs?limit=1",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                runs = data.get("data", {}).get("items", [])

                if runs:
                    last_run = runs[0]
                    print(f"\n✅ Connected to Apify!")
                    print(f"  Last run: {last_run.get('status')}")
                    print(f"  Started: {last_run.get('startedAt', 'N/A')}")
                else:
                    print("\n✅ Connected to Apify (no recent runs)")

                return True
            else:
                print(f"\n❌ Apify API returned {response.status_code}")
                return False

    except Exception as e:
        print(f"\n❌ Apify connection failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🚀 LinkedIn Apify Job Worker - Integration Test")
    print("="*70)

    results = {
        "Apify Connection": await test_apify_connection(),
        "Pydantic AI Classification": await test_classification(),
        "Neon Duplicate Check": await test_duplicate_check(),
    }

    print("\n" + "="*70)
    print("📊 Test Results Summary")
    print("="*70)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All tests passed! Pipeline is ready.")
    else:
        print("\n⚠️  Some tests failed. Check configuration.")

    print("="*70 + "\n")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
