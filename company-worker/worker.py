"""
Company Worker - Temporal Python Worker

Executes CompanyCreationWorkflow for comprehensive company profiling.
"""

import asyncio
import os
import sys

from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import workflow
from src.workflows.company_creation import CompanyCreationWorkflow

# Import all activities
from src.activities.normalize import (
    normalize_company_url,
    check_company_exists,
)

from src.activities.research.serper import (
    fetch_company_news,
    fetch_targeted_research,
    serper_httpx_deep_articles,  # Deep article crawling with httpx
)

from src.activities.research.crawl import (
    httpx_crawl,
    firecrawl_crawl,  # Keep for backward compatibility
    firecrawl_httpx_discover,  # Intelligent URL discovery with Firecrawl + httpx
)

from src.activities.research.crawl4ai_service import (
    crawl4ai_service_crawl,  # External Railway Crawl4AI microservice (browser automation)
)

from src.activities.research.exa import (
    exa_research_company,
    exa_find_similar_companies,
)

from src.activities.research.ambiguity import (
    check_research_ambiguity,
    validate_company_match,
)

from src.activities.validation.link_validator import (
    playwright_url_cleanse,
    playwright_clean_links,
)

from src.activities.media.logo_extraction import (
    extract_and_process_logo,
)

from src.activities.media.replicate_images import (
    generate_company_featured_image,
    generate_placeholder_image,
)

from src.activities.media.flux_api_client import (
    generate_flux_image,
)

from src.activities.media.sequential_images import (
    generate_sequential_article_images,
    generate_company_contextual_images,
)

from src.activities.articles.analyze_sections import (
    analyze_article_sections,
)

from src.activities.generation.profile_generation import (
    generate_company_profile,
)

from src.activities.generation.profile_generation_v2 import (
    generate_company_profile_v2,
)

from src.activities.generation.completeness import (
    calculate_completeness_score,
    get_missing_fields,
    suggest_improvements,
)

from src.activities.storage.neon_database import (
    save_company_to_neon,
    update_company_metadata,
    get_company_by_id,
)

from src.activities.storage.zep_integration import (
    query_zep_for_context,
    sync_company_to_zep,
    create_zep_summary,
    sync_v2_profile_to_zep_graph,
)

from src.activities.storage.zep_entity_extraction import (
    extract_entities_from_v2_profile,
)

from src.activities.storage.zep_graph_visual import (
    fetch_company_graph_data,
)

# Articles activities re-enabled
from src.activities.articles.fetch_related import (
    fetch_related_articles,
    link_article_to_company,
    get_article_timeline,
)

from src.utils.config import config


async def main():
    """Start the Temporal worker"""

    print("=" * 70)
    print("🏢 Company Worker - Starting...")
    print("=" * 70)

    # Display configuration
    print("\n🔧 Configuration:")
    print(f"   Temporal Address: {config.TEMPORAL_ADDRESS}")
    print(f"   Namespace: {config.TEMPORAL_NAMESPACE}")
    print(f"   Task Queue: {config.TEMPORAL_TASK_QUEUE}")
    print(f"   API Key: {'✅ Set' if config.TEMPORAL_API_KEY else '❌ Not set'}")
    print(f"   Environment: {config.ENVIRONMENT}")

    # Validate required environment variables
    missing = config.validate_required()

    if missing:
        print(f"\n❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n   Please set them in .env file or environment")
        sys.exit(1)

    print("\n✅ All required environment variables present")

    # Display service status
    print("\n📊 Service Status:")
    service_config = config.as_dict()
    for key, value in service_config.items():
        if key.startswith("has_"):
            service_name = key.replace("has_", "").upper()
            status = "✅" if value else "❌"
            print(f"   {status} {service_name}")

    # Connect to Temporal
    print(f"\n🔗 Connecting to Temporal Cloud...")

    try:
        if config.TEMPORAL_API_KEY:
            # Temporal Cloud with TLS
            client = await Client.connect(
                config.TEMPORAL_ADDRESS,
                namespace=config.TEMPORAL_NAMESPACE,
                api_key=config.TEMPORAL_API_KEY,
                tls=True,
            )
        else:
            # Local Temporal (development)
            client = await Client.connect(
                config.TEMPORAL_ADDRESS,
                namespace=config.TEMPORAL_NAMESPACE,
            )

        print("✅ Connected to Temporal successfully")

    except Exception as e:
        print(f"❌ Failed to connect to Temporal: {e}")
        sys.exit(1)

    # Create worker with all workflows and activities
    worker = Worker(
        client,
        task_queue=config.TEMPORAL_TASK_QUEUE,
        workflows=[CompanyCreationWorkflow],
        activities=[
            # Normalization
            normalize_company_url,
            check_company_exists,

            # Research
            fetch_company_news,
            fetch_targeted_research,
            serper_httpx_deep_articles,  # Deep article crawling with httpx
            httpx_crawl,
            crawl4ai_service_crawl,  # External Crawl4AI service (browser automation)
            firecrawl_crawl,  # Keep for backward compatibility
            firecrawl_httpx_discover,  # Intelligent URL discovery with Firecrawl + httpx
            exa_research_company,
            exa_find_similar_companies,

            # Ambiguity & Validation
            check_research_ambiguity,
            validate_company_match,
            playwright_url_cleanse,
            playwright_clean_links,

            # Media
            extract_and_process_logo,
            generate_company_featured_image,
            generate_placeholder_image,
            generate_flux_image,
            generate_sequential_article_images,
            generate_company_contextual_images,
            analyze_article_sections,

            # Generation
            generate_company_profile,
            generate_company_profile_v2,
            calculate_completeness_score,
            get_missing_fields,
            suggest_improvements,

            # Database
            save_company_to_neon,
            update_company_metadata,
            get_company_by_id,

            # Zep Integration
            query_zep_for_context,
            sync_company_to_zep,
            create_zep_summary,
            fetch_company_graph_data,

            # Articles (re-enabled)
            fetch_related_articles,
            link_article_to_company,
            get_article_timeline,
        ],
    )

    print("\n" + "=" * 70)
    print("🚀 Company Worker Started Successfully!")
    print("=" * 70)
    print(f"   Task Queue: {config.TEMPORAL_TASK_QUEUE}")
    print(f"   Environment: {config.ENVIRONMENT}")
    print("=" * 70)

    print("\n📋 Registered Workflows:")
    print("   - CompanyCreationWorkflow")

    print("\n📋 Registered Activities:")
    activity_groups = [
        ("Normalization", ["normalize_company_url", "check_company_exists"]),
        ("Research", [
            "fetch_company_news",
            "fetch_targeted_research",
            "serper_crawl4ai_deep_articles",  # NEW
            "crawl4ai_crawl",
            "firecrawl_crawl",
            "firecrawl_crawl4ai_discover_and_scrape",  # NEW
            "exa_research_company",
            "exa_find_similar_companies",
        ]),
        ("Validation", ["check_research_ambiguity", "validate_company_match"]),
        ("Media", [
            "extract_and_process_logo",
            "generate_company_featured_image",
            "generate_placeholder_image",
        ]),
        ("Generation", [
            "generate_company_profile",
            "generate_company_profile_v2",
            "calculate_completeness_score",
            "get_missing_fields",
            "suggest_improvements",
        ]),
        ("Database", [
            "save_company_to_neon",
            "update_company_metadata",
            "get_company_by_id",
        ]),
        ("Zep Integration", [
            "query_zep_for_context",
            "sync_company_to_zep",
            "create_zep_summary",
            "fetch_company_graph_data",
        ]),
        ("Articles", [
            "fetch_related_articles",
            "link_article_to_company",
            "get_article_timeline",
        ]),
    ]

    for group_name, activities in activity_groups:
        print(f"\n   {group_name}:")
        for activity in activities:
            print(f"     - {activity}")

    print("\n✅ Worker is ready to process company creation workflows")
    print("   Press Ctrl+C to stop\n")

    # Run worker (blocks until interrupted)
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Company Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Company Worker crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
