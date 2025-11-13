"""
Quest Worker - Temporal Python Worker

Executes NewsroomWorkflow for content generation across multiple apps.

Updated: 2025-11-12 v2 - Force TRULY clean rebuild (Railway bytecode cache issue)
"""

import asyncio
import os
import sys

from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import workflows (relative imports for Railway deployment)
from workflows.newsroom import NewsroomWorkflow
from workflows.placement import PlacementWorkflow
from workflows.relocation import RelocationWorkflow
from workflows.chiefofstaff import ChiefOfStaffWorkflow
from workflows.gtm import GTMWorkflow
from workflows.article_workflow import ArticleWorkflow
from workflows.placement_company import PlacementCompanyWorkflow
from workflows.relocation_company import RelocationCompanyWorkflow
from workflows.recruiter_company import RecruiterCompanyWorkflow
from workflows.smart_company import SmartCompanyWorkflow

# Import all activities
from activities import (
    # Database
    save_to_neon,

    # Research
    search_news_serper,
    deep_scrape_sources,
    extract_entities_from_news,
    extract_entities_citations,
    calculate_quality_score,
    sync_to_zep,  # Legacy

    # Zep Graph
    check_zep_coverage,
    sync_article_to_zep,
    sync_company_to_zep,
    extract_facts_to_zep,

    # Generation
    generate_article,

    # Images - Original (multi-app with config)
    generate_article_images,
    insert_images_into_content,
)

from activities.database import save_company_profile
from activities.duplicate_check import check_for_duplicates

# Import new dedicated image activities
from activities.images_placement import generate_placement_images
from activities.images_relocation import generate_relocation_images
from activities.images_chiefofstaff import generate_chiefofstaff_images
from activities.images_gtm import generate_gtm_images

# Import company profile activities
from activities.company import (
    scrape_company_website,
    search_company_news,
    extract_company_info,
    validate_company_data,
    format_company_profile,
    extract_company_logo,
    process_company_logo,
)

# Import company classification activity
from activities.classify_company import classify_company_type

# Import Exa research activities
from activities.exa_research import (
    exa_research_topic,
    exa_find_similar,
    deep_research_with_firecrawl,
    extract_research_insights,
)


async def main():
    """Start the Temporal worker"""

    # Get Temporal configuration from environment
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "quest-content-queue")

    print("🔧 Quest Worker Configuration:")
    print(f"   Temporal Address: {temporal_address}")
    print(f"   Namespace: {temporal_namespace}")
    print(f"   Task Queue: {task_queue}")
    print(f"   API Key: {'✅ Set' if temporal_api_key else '❌ Not set'}")

    # Validate required environment variables
    required_vars = [
        "DATABASE_URL",
        "GOOGLE_API_KEY",
        "SERPER_API_KEY",
        "EXA_API_KEY",  # Required for ArticleWorkflow
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please set them in .env file or environment")
        sys.exit(1)

    print("✅ All required environment variables present")

    # Connect to Temporal Cloud
    print(f"\n🔗 Connecting to Temporal Cloud...")

    try:
        if temporal_api_key:
            # Connect to Temporal Cloud with API key and TLS
            client = await Client.connect(
                temporal_address,
                namespace=temporal_namespace,
                api_key=temporal_api_key,
                tls=True,  # Enable TLS for Temporal Cloud
            )
        else:
            # Connect to local Temporal (no API key, no TLS)
            client = await Client.connect(
                temporal_address,
                namespace=temporal_namespace,
            )

        print("✅ Connected to Temporal")

    except Exception as e:
        print(f"❌ Failed to connect to Temporal: {e}")
        sys.exit(1)

    # Create worker with all workflows and activities
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            NewsroomWorkflow,
            PlacementWorkflow,
            RelocationWorkflow,
            ChiefOfStaffWorkflow,
            GTMWorkflow,
            ArticleWorkflow,
            PlacementCompanyWorkflow,
            RelocationCompanyWorkflow,
            RecruiterCompanyWorkflow,
            SmartCompanyWorkflow,
        ],
        activities=[
            # Database
            save_to_neon,
            save_company_profile,
            check_for_duplicates,

            # Research
            search_news_serper,
            deep_scrape_sources,
            extract_entities_from_news,
            extract_entities_citations,
            calculate_quality_score,
            sync_to_zep,  # Legacy

            # Exa Research
            exa_research_topic,
            exa_find_similar,
            deep_research_with_firecrawl,
            extract_research_insights,

            # Zep Graph
            check_zep_coverage,
            sync_article_to_zep,
            sync_company_to_zep,
            extract_facts_to_zep,

            # Generation
            generate_article,

            # Images - Original (multi-app with config)
            generate_article_images,
            insert_images_into_content,

            # Images - Dedicated per app (simple, no config)
            generate_placement_images,
            generate_relocation_images,
            generate_chiefofstaff_images,
            generate_gtm_images,

            # Company Profile Activities
            scrape_company_website,
            search_company_news,
            extract_company_info,
            validate_company_data,
            format_company_profile,
            extract_company_logo,
            process_company_logo,
            classify_company_type,
        ],
    )

    print("\n" + "=" * 60)
    print("🚀 Quest Worker Started Successfully!")
    print("=" * 60)
    print(f"   Task Queue: {task_queue}")
    print("=" * 60)
    print("\n📋 Registered Workflows:")
    print("   Articles:")
    print("     - NewsroomWorkflow (multi-app news)")
    print("     - ArticleWorkflow (direct research)")
    print("     - PlacementWorkflow (dedicated)")
    print("     - RelocationWorkflow (dedicated)")
    print("     - ChiefOfStaffWorkflow (dedicated)")
    print("   Companies:")
    print("     - PlacementCompanyWorkflow (company profiles)")
    print("     - RelocationCompanyWorkflow (company profiles)")
    print("     - RecruiterCompanyWorkflow (company profiles)")
    print("     - SmartCompanyWorkflow (auto-detect company type)")
    print("\n📋 Registered Activities:")
    print("   Database:")
    print("     - save_to_neon")
    print("     - save_company_profile")
    print("   Research:")
    print("     - search_news_serper")
    print("     - deep_scrape_sources")
    print("     - extract_entities_from_news")
    print("     - extract_entities_citations")
    print("     - calculate_quality_score")
    print("   Exa Research:")
    print("     - exa_research_topic")
    print("     - exa_find_similar")
    print("     - deep_research_with_firecrawl")
    print("     - extract_research_insights")
    print("   Zep Graph:")
    print("     - check_zep_coverage")
    print("     - sync_article_to_zep")
    print("     - sync_company_to_zep")
    print("     - extract_facts_to_zep")
    print("   Generation:")
    print("     - generate_article")
    print("   Images:")
    print("     - generate_article_images (original multi-app)")
    print("     - generate_placement_images (dedicated)")
    print("     - generate_relocation_images (dedicated)")
    print("     - generate_chiefofstaff_images (dedicated)")
    print("   Company Profiles:")
    print("     - scrape_company_website")
    print("     - search_company_news")
    print("     - extract_company_info")
    print("     - validate_company_data")
    print("     - format_company_profile")
    print("     - extract_company_logo")
    print("     - process_company_logo")
    print("     - classify_company_type (AI auto-detection)")
    print("\n✅ Worker is ready to process workflows...")
    print("   Press Ctrl+C to stop\n")

    # Run worker (blocks until interrupted)
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Worker crashed: {e}")
        sys.exit(1)
