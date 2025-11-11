#!/usr/bin/env python3
"""
Test script for Campbell Lutyens - Placement Company Profile

Creates a company profile for Campbell Lutyens on placement.news
"""

import asyncio
import os
from temporalio.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_campbell_lutyens():
    """Create profile for Campbell Lutyens"""

    # Get Temporal configuration
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    print("🧪 Creating Company Profile: Campbell Lutyens")
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

    # Campbell Lutyens details
    company_name = "Campbell Lutyens"
    company_website = "https://campbell-lutyens.com/"

    print(f"Creating profile for: {company_name}")
    print(f"Website: {company_website}")
    print("\n🚀 Starting PlacementCompanyWorkflow...\n")

    # Start workflow with unique timestamp-based ID
    import time
    workflow_id = f"campbell-lutyens-{int(time.time())}"

    result = await client.execute_workflow(
        "PlacementCompanyWorkflow",
        args=[
            company_name,
            company_website,
            True,  # auto_approve
        ],
        id=workflow_id,
        task_queue=task_queue,
    )

    print("\n" + "=" * 60)
    print("✅ COMPANY PROFILE CREATED")
    print("=" * 60)

    print(f"\n📋 Company Details:")
    print(f"  ID: {result.get('id')}")
    print(f"  Name: {result.get('company_name')}")
    print(f"  Type: {result.get('company_type')}")
    print(f"  Industry: {result.get('industry')}")
    print(f"  Website: {result.get('website')}")
    print(f"  HQ Location: {result.get('headquarters_location')}")

    # Description
    description = result.get('description', '')
    if description:
        print(f"\n📝 Description:")
        print(f"  {description}")

    # Key services
    key_services = result.get('key_services', [])
    if key_services:
        print(f"\n💼 Key Services:")
        for service in key_services:
            print(f"  • {service}")

    # Specializations
    specializations = result.get('specializations', [])
    if specializations:
        print(f"\n🎯 Specializations:")
        for spec in specializations:
            print(f"  • {spec}")

    # Validation info
    validation = result.get('validation', {})
    completeness = validation.get('overall_score', 0)
    meets_threshold = validation.get('meets_threshold', False)

    print(f"\n✅ Validation:")
    print(f"  Overall Score: {completeness:.1%}")
    print(f"  Meets Threshold: {'✅ Yes' if meets_threshold else '❌ No'}")
    print(f"  Required Fields Present: {len(validation.get('present_required_fields', []))}/{len(validation.get('present_required_fields', [])) + len(validation.get('missing_required_fields', []))}")

    if validation.get('missing_required_fields'):
        print(f"  Missing Fields: {', '.join(validation.get('missing_required_fields', []))}")

    # Logo info
    logo = result.get('logo', {})
    print(f"\n🎨 Logo:")
    print(f"  Source: {logo.get('logo_source', 'none')}")
    if logo.get('original_logo_url'):
        print(f"  URL: {logo.get('original_logo_url')}")
    elif logo.get('fallback_image_url'):
        print(f"  Fallback URL: {logo.get('fallback_image_url')}")

    # Profile info
    profile_title = result.get('profile_title', 'N/A')
    profile_sections = result.get('profile_sections', [])
    profile_tags = result.get('profile_tags', [])

    print(f"\n📄 Profile:")
    print(f"  Title: {profile_title}")
    print(f"  Sections: {len(profile_sections)}")

    if profile_sections:
        print(f"\n  📑 Section Headings:")
        for section in profile_sections:
            print(f"    • {section.get('heading', 'Untitled')}")

    if profile_tags:
        print(f"\n  🏷️  Tags: {', '.join(profile_tags)}")

    # Summary
    profile_summary = result.get('profile_summary', '')
    if profile_summary:
        print(f"\n💡 Summary:")
        print(f"  {profile_summary}")

    # Save status
    saved = result.get('saved', False)
    print(f"\n💾 Database Status: {'✅ Saved' if saved else '❌ Not Saved'}")

    # Data sources
    data_sources = result.get('data_sources', {})
    if data_sources:
        print(f"\n📊 Data Sources:")
        print(f"  Website Scraped: {'✅' if data_sources.get('website_scraped') else '❌'}")
        print(f"  News Articles: {data_sources.get('news_articles', 0)}")

    print("\n" + "=" * 60)
    print("🎉 Profile creation complete for Campbell Lutyens!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_campbell_lutyens())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
