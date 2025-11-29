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

# Import workflows
from src.workflows.company_creation import CompanyCreationWorkflow
from src.workflows.article_creation import ArticleCreationWorkflow
from src.workflows.news_creation import NewsCreationWorkflow
from src.workflows.country_guide_creation import CountryGuideCreationWorkflow
from src.workflows.segment_video_workflow import SegmentVideoWorkflow
from src.workflows.crawl_url_workflow import CrawlUrlWorkflow
from src.workflows.cluster_article_workflow import ClusterArticleWorkflow
from src.workflows.topic_cluster_workflow import TopicClusterWorkflow
# NarrativeArticleCreationWorkflow removed - superseded by 4-act workflow in ArticleCreationWorkflow

# Import all activities
from src.activities.normalize import (
    normalize_company_url,
    check_company_exists,
)

from src.activities.research.serper import (
    fetch_company_news,
    serper_news_search,
    serper_article_search,
    fetch_targeted_research,
    serper_httpx_deep_articles,  # Deep article crawling with httpx
    serper_scrape_url,  # Single URL scrape via Serper API
)

from src.activities.research.dataforseo import (
    dataforseo_news_search,
    dataforseo_serp_search,
    dataforseo_keyword_research,
    dataforseo_keyword_difficulty,
    dataforseo_related_keywords,  # Keyword cluster discovery (first step in research)
    research_country_seo_keywords,  # Country guide SEO research
)

from src.activities.research.news_assessment import (
    assess_news_batch,
)

from src.activities.research.crawl import (
    httpx_crawl,
    # firecrawl_crawl,  # Disabled - out of credit
    # firecrawl_httpx_discover,  # Disabled - out of credit
)

from src.activities.research.crawl4ai_service import (
    crawl4ai_service_crawl,  # External Railway Crawl4AI microservice (browser automation)
    crawl4ai_batch_crawl,  # Batch crawl multiple URLs at once
    prefilter_urls_by_relevancy,  # Pre-filter URLs by topic relevancy before crawling
)

from src.activities.research.exa import (
    exa_research_company,
    exa_research_topic,
    exa_find_similar_companies,
)

from src.activities.research.reddit import (
    reddit_search_expat_content,  # Reddit JSON API for expat voices
)

from src.activities.research.ambiguity import (
    check_research_ambiguity,
    validate_company_match,
)

from src.activities.validation.link_validator import (
    playwright_url_cleanse,  # Deprecated
    playwright_clean_links,
    playwright_pre_cleanse,  # Phase 4b: Score URLs before article generation
    playwright_post_cleanse,  # Phase 5b: Validate links after article written
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

from src.activities.media.prompt_images import (
    generate_article_images_from_prompts,
)

from src.activities.media.video_generation import (
    generate_four_act_video,  # 4-act 12-second video for articles
    generate_company_video,  # Simple 3s branding video for company profiles
)

from src.activities.media.mux_client import (
    upload_video_to_mux,
    upload_video_file_to_mux,
    delete_mux_asset,
    get_mux_asset_info,
)

from src.activities.articles.analyze_sections import (
    analyze_article_sections,
)

from src.activities.generation.profile_generation_v2 import (
    generate_company_profile_v2,
)

from src.activities.generation.article_generation import (
    generate_four_act_article,  # 4-act article with four_act_content
    generate_narrative_article,  # Legacy 3-act narrative-driven article
    refine_broken_links,  # Phase 5b: Haiku fixes broken links in article
    generate_four_act_video_prompt,  # Assembles video prompt from briefs (simple, no AI fallback)
    generate_four_act_video_prompt_brief,  # NEW: Generates briefs from article AFTER save
)

from src.activities.generation.country_guide_generation import (
    generate_country_guide_content,  # 8-motivation country guide (now with mode: story/guide/yolo)
    extract_country_facts,  # Extract facts for countries.facts JSONB
    generate_country_video_prompt,  # Country-specific 4-act video prompt
    generate_segment_video_prompt,  # Multi-video: hero/family/finance/daily/yolo prompts
    generate_topic_cluster_content,  # SEO-targeted topic cluster articles
)

from src.activities.generation.research_curation import (
    curate_research_sources,
)

# generate_four_act_video_prompt moved to article_generation.py
# generate_image_prompts removed (dead code - thumbnails come from video)

from src.activities.generation.narrative_builder import (
    build_3_act_narrative,  # Video-first 3-act narrative structure
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
    save_article_to_neon,
    get_article_by_slug,
    update_article_four_act_content,  # NEW: Update four_act_content briefs and video_prompt
    save_spawn_candidate,
    # Video tags for cluster architecture
    save_video_tags,
    get_videos_by_cluster,
    get_videos_by_country,
)

from src.activities.storage.neon_countries import (
    save_or_create_country,
    update_country_facts,
    update_country_seo_keywords,
    link_article_to_country,
    publish_country,
    get_country_by_code,
)

from src.activities.storage.neon_articles import (
    get_recent_articles_from_neon,
)

from src.activities.storage.zep_integration import (
    query_zep_for_context,
    sync_company_to_zep,
    create_zep_summary,
    sync_v2_profile_to_zep_graph,
    sync_article_to_zep,
)

from src.activities.storage.zep_entity_extraction import (
    extract_entities_from_v2_profile,
    extract_entities_from_article,  # New: Extract jobs, skills, locations from articles
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
        workflows=[CompanyCreationWorkflow, ArticleCreationWorkflow, NewsCreationWorkflow, CountryGuideCreationWorkflow, SegmentVideoWorkflow, CrawlUrlWorkflow, ClusterArticleWorkflow, TopicClusterWorkflow],
        activities=[
            # Normalization
            normalize_company_url,
            check_company_exists,

            # Research - Serper
            fetch_company_news,
            serper_news_search,  # News search for scheduling/news creation
            serper_article_search,  # Article search for article creation workflow
            fetch_targeted_research,
            serper_httpx_deep_articles,  # Deep article crawling with httpx
            serper_scrape_url,  # Single URL scrape via Serper API (50/50 with crawl4ai)

            # Research - DataForSEO
            dataforseo_news_search,
            dataforseo_serp_search,
            dataforseo_keyword_research,  # SEO keyword research
            dataforseo_keyword_difficulty,  # SEO keyword difficulty analysis
            dataforseo_related_keywords,  # Keyword cluster discovery (first step)
            research_country_seo_keywords,  # Country guide SEO research

            # News Assessment
            assess_news_batch,

            # Research - Other
            httpx_crawl,
            crawl4ai_service_crawl,  # External Crawl4AI service (browser automation)
            crawl4ai_batch_crawl,  # Batch crawl multiple URLs
            prefilter_urls_by_relevancy,  # Pre-filter URLs before crawling
            # firecrawl_crawl,  # Disabled - out of credit
            # firecrawl_httpx_discover,  # Disabled - out of credit
            exa_research_company,
            exa_research_topic,
            exa_find_similar_companies,

            # Reddit
            reddit_search_expat_content,  # Expat voices from Reddit

            # Ambiguity & Validation
            check_research_ambiguity,
            validate_company_match,
            playwright_url_cleanse,  # Deprecated
            playwright_clean_links,
            playwright_pre_cleanse,  # Phase 4b: Score URLs before article gen
            playwright_post_cleanse,  # Phase 5b: Validate links after article

            # Media
            extract_and_process_logo,
            generate_company_featured_image,
            generate_placeholder_image,
            generate_flux_image,
            generate_sequential_article_images,
            generate_company_contextual_images,
            generate_article_images_from_prompts,
            analyze_article_sections,
            # Video
            generate_four_act_video,  # 4-act 12-second video for articles
            generate_company_video,  # Simple 3s branding video for company profiles
            upload_video_to_mux,
            upload_video_file_to_mux,
            delete_mux_asset,
            get_mux_asset_info,

            # Generation
            generate_company_profile_v2,
            generate_four_act_article,  # 4-act article with four_act_content
            generate_narrative_article,  # Legacy 3-act narrative-driven article
            refine_broken_links,  # Phase 5b: Haiku fixes broken links
            generate_four_act_video_prompt,  # Assembles video prompt from briefs (simple)
            generate_four_act_video_prompt_brief,  # NEW: Generates briefs AFTER article save
            build_3_act_narrative,   # New: video-first 3-act narrative structure
            curate_research_sources,
            calculate_completeness_score,
            get_missing_fields,
            suggest_improvements,

            # Database
            save_company_to_neon,
            update_company_metadata,
            get_company_by_id,
            save_article_to_neon,
            get_article_by_slug,
            update_article_four_act_content,  # NEW: Update briefs and video_prompt
            get_recent_articles_from_neon,
            save_spawn_candidate,  # Article spawn candidates
            # Video tags for cluster architecture
            save_video_tags,
            get_videos_by_cluster,
            get_videos_by_country,

            # Country Guide Database
            save_or_create_country,
            update_country_facts,
            update_country_seo_keywords,
            link_article_to_country,
            publish_country,
            get_country_by_code,

            # Country Guide Generation
            generate_country_guide_content,
            extract_country_facts,
            generate_country_video_prompt,
            generate_segment_video_prompt,  # Multi-video: hero/family/finance/daily/yolo
            generate_topic_cluster_content,  # SEO-targeted topic cluster articles

            # Zep Integration
            query_zep_for_context,
            sync_company_to_zep,
            create_zep_summary,
            sync_article_to_zep,
            fetch_company_graph_data,
            extract_entities_from_v2_profile,  # Extract deals/people from company profiles
            extract_entities_from_article,  # Extract jobs/skills/locations from articles

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
    print("   - ArticleCreationWorkflow")
    print("   - NewsCreationWorkflow (Scheduled with intelligent video prompts)")
    print("   - CountryGuideCreationWorkflow (8-motivation country guides)")
    print("   - SegmentVideoWorkflow (Child workflow for segment videos)")
    print("   - ClusterArticleWorkflow (Child workflow for cluster articles)")
    print("   - CrawlUrlWorkflow (Child workflow for individual URL crawls)")
    print("   - TopicClusterWorkflow (SEO-targeted topic cluster articles)")

    print("\n📋 Registered Activities:")
    activity_groups = [
        ("Normalization", ["normalize_company_url", "check_company_exists"]),
        ("Research - Serper", [
            "fetch_company_news",
            "fetch_targeted_research",
            "serper_httpx_deep_articles",
        ]),
        ("Research - DataForSEO", [
            "dataforseo_news_search",
            "dataforseo_serp_search",
        ]),
        ("Research - Other", [
            "httpx_crawl",
            "crawl4ai_service_crawl",
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
            "generate_article_content",
            "curate_research_sources",
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
