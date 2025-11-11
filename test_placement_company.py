#!/usr/bin/env python3
"""
Test script for PlacementCompanyWorkflow

Creates a company profile for a placement agent/financial services firm.
"""

import asyncio
import os
from temporalio.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_placement_company():
    """Test the placement company workflow"""

    # Get Temporal configuration
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    print("🧪 Testing Placement Company Workflow")
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

    # Test company - KKR (well-known private equity firm)
    test_company = {
        "company_name": "KKR & Co.",
        "company_website": "https://www.kkr.com",
    }

    print(f"Creating profile for: {test_company['company_name']}")
    print(f"Website: {test_company['company_website']}")
    print("\n🚀 Starting workflow...\n")

    # Start workflow
    workflow_id = f"placement-company-test-{asyncio.get_event_loop().time()}"

    result = await client.execute_workflow(
        "PlacementCompanyWorkflow",
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

    # Profile info
    print(f"\nProfile:")
    print(f"  Title: {result.get('profile_title', 'N/A')}")
    print(f"  Sections: {len(result.get('profile_sections', []))}")
    print(f"  Tags: {', '.join(result.get('profile_tags', []))}")

    # Save status
    print(f"\nSaved to Database: {result.get('saved', False)}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_placement_company())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
