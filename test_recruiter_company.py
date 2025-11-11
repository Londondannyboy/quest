#!/usr/bin/env python3
"""
Test script for RecruiterCompanyWorkflow

Creates a company profile for executive assistant/chief of staff recruiters.

Usage:
    python test_recruiter_company.py
    python test_recruiter_company.py --company "Bain & Gray" --website "https://www.bainandgray.com"
"""

import asyncio
import os
import sys
from temporalio.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_recruiter_company(company_name: str = None, company_website: str = None):
    """Test the recruiter company workflow"""

    # Get Temporal configuration
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    print("🧪 Testing Recruiter Company Workflow")
    print("=" * 60)
    print(f"Temporal Address: {temporal_address}")
    print(f"Namespace: {temporal_namespace}")
    print(f"Task Queue: {task_queue}")
    print("=" * 60)

    # Connect to Temporal
    if temporal_api_key:
        client = await Client.connect(
            temporal_address,
            namespace=temporal_namespace,
            api_key=temporal_api_key,
            tls=True,
        )
    else:
        client = await Client.connect(
            temporal_address,
            namespace=temporal_namespace,
        )

    print("✅ Connected to Temporal\n")

    # Test company - default to Bain & Gray or use provided
    test_company = {
        "company_name": company_name or "Bain & Gray",
        "company_website": company_website or "https://www.bainandgray.com",
    }

    print(f"Creating profile for: {test_company['company_name']}")
    print(f"Website: {test_company['company_website']}")
    print("\n🚀 Starting workflow...\n")

    # Start workflow
    workflow_id = f"recruiter-company-test-{asyncio.get_event_loop().time()}"

    result = await client.execute_workflow(
        "RecruiterCompanyWorkflow",
        args=[
            test_company["company_name"],
            test_company["company_website"],
            True,  # auto_approve
        ],
        id=workflow_id,
        task_queue=task_queue,
    )

    print("\n" + "=" * 60)
    print("✅ WORKFLOW COMPLETED")
    print("=" * 60)

    print(f"\nCompany ID: {result.get('id')}")
    print(f"Company Name: {result.get('company_name')}")
    print(f"Company Type: {result.get('company_type')}")
    print(f"Industry: {result.get('industry')}")
    print(f"Website: {result.get('website')}")
    print(f"Phone: {result.get('phone', 'N/A')}")
    print(f"Headquarters: {result.get('headquarters', 'N/A')}")
    print(f"Description: {result.get('description', '')[:200]}...")

    # Validation info
    validation = result.get('validation', {})
    print(f"\nValidation:")
    print(f"  Completeness: {validation.get('overall_score', 0):.1%}")
    print(f"  Meets Threshold: {validation.get('meets_threshold', False)}")

    # Logo info
    logo = result.get('logo', {})
    print(f"\nLogo:")
    print(f"  Source: {logo.get('logo_source', 'none')}")
    if logo.get('original_logo_url'):
        print(f"  URL: {logo.get('original_logo_url')[:80]}...")

    # Specializations
    specializations = result.get('specializations', [])
    if specializations:
        print(f"\nSpecializations:")
        for spec in specializations:
            print(f"  - {spec}")

    # Profile info
    print(f"\nProfile:")
    print(f"  Title: {result.get('profile_title', 'N/A')}")
    print(f"  Sections: {len(result.get('profile_sections', []))}")
    print(f"  Tags: {', '.join(result.get('profile_tags', []))}")

    # Save status
    print(f"\nSaved to Database: {result.get('saved', False)}")

    if result.get('saved'):
        print(f"\n🎉 Company available at:")
        slug = result.get('slug', result.get('company_name', '').lower().replace(' ', '-').replace('&', 'and'))
        print(f"   https://chiefofstaff.quest/companies/{slug}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Parse command line arguments
    company_name = None
    company_website = None

    for i, arg in enumerate(sys.argv):
        if arg == "--company" and i + 1 < len(sys.argv):
            company_name = sys.argv[i + 1]
        elif arg == "--website" and i + 1 < len(sys.argv):
            company_website = sys.argv[i + 1]

    try:
        asyncio.run(test_recruiter_company(company_name, company_website))
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
