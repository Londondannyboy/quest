"""
Smart Company Workflow

Universal workflow that auto-detects company type and creates appropriate profile.
Just provide a URL - AI figures out if it's a recruiter, placement agent, or relocation company.
"""

from datetime import timedelta
from typing import Optional
from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class SmartCompanyWorkflow:
    """
    Universal company profile workflow with auto-detection

    This workflow:
    - Scrapes company website
    - Uses AI to classify company type (recruiter/placement/relocation)
    - Searches for recent company news
    - Extracts structured company information with type-specific prompts
    - Processes company logo
    - Validates and formats company profile
    - Saves to database with correct company_type
    """

    def __init__(self) -> None:
        self.company_data: Optional[dict] = None
        self.detected_type: Optional[str] = None

    @workflow.run
    async def run(
        self,
        company_name: str,
        company_website: str,
        auto_approve: bool = True
    ) -> dict:
        """
        Run the smart company workflow with auto-detection

        Args:
            company_name: Name of the company
            company_website: Company website URL
            auto_approve: If True, skip manual approval

        Returns:
            Complete company profile dict with detected type
        """
        company_id = str(workflow.uuid4())[:8]

        workflow.logger.info(f"🚀 Smart Company workflow started")
        workflow.logger.info(f"   Company: {company_name}")
        workflow.logger.info(f"   Website: {company_website}")
        workflow.logger.info(f"   Company ID: {company_id}")
        workflow.logger.info(f"   Mode: AUTO-DETECT")

        # Configure retry policy
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )

        # =====================================================================
        # STAGE 1: SCRAPE COMPANY WEBSITE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🌐 STAGE 1: SCRAPE COMPANY WEBSITE")
        workflow.logger.info("=" * 60)

        website_data = await workflow.execute_activity(
            "scrape_company_website",
            company_website,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        website_content = website_data.get("content", "")
        workflow.logger.info(f"✅ Scraped {len(website_content)} characters from website")

        # =====================================================================
        # STAGE 2: AI CLASSIFICATION - DETECT COMPANY TYPE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🤖 STAGE 2: AI CLASSIFICATION")
        workflow.logger.info("=" * 60)

        classification = await workflow.execute_activity(
            "classify_company_type",
            args=[company_name, website_content],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        detected_type = classification.get("company_type")
        confidence = classification.get("confidence", 0)
        reasoning = classification.get("reasoning", "")

        self.detected_type = detected_type

        workflow.logger.info(f"✅ Detected Type: {detected_type}")
        workflow.logger.info(f"   Confidence: {confidence:.1%}")
        workflow.logger.info(f"   Reasoning: {reasoning[:100]}...")

        # Map detected type to database company_type
        type_mapping = {
            "recruiter": "executive_assistant_recruiters",
            "placement": "placement_agent",
            "relocation": "relocation_company",
        }

        db_company_type = type_mapping.get(detected_type, "executive_assistant_recruiters")

        # =====================================================================
        # STAGE 3: SEARCH COMPANY NEWS
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📰 STAGE 3: SEARCH COMPANY NEWS")
        workflow.logger.info("=" * 60)

        news_items = await workflow.execute_activity(
            "search_company_news",
            args=[company_name, 5],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"✅ Found {len(news_items)} news articles")

        # =====================================================================
        # STAGE 4: EXTRACT COMPANY INFORMATION (TYPE-AWARE)
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🔍 STAGE 4: EXTRACT COMPANY INFO")
        workflow.logger.info(f"   Using {detected_type}-specific extraction")
        workflow.logger.info("=" * 60)

        company_data = await workflow.execute_activity(
            "extract_company_info",
            args=[company_name, website_content, news_items, db_company_type],
            start_to_close_timeout=timedelta(minutes=3),
            retry_policy=retry_policy,
        )

        company_data['id'] = company_id
        company_data['company_type'] = db_company_type
        company_data['detected_type'] = detected_type
        company_data['detection_confidence'] = confidence

        workflow.logger.info(f"✅ Extracted company information")

        # =====================================================================
        # STAGE 5: VALIDATE COMPANY DATA
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📊 STAGE 5: VALIDATE DATA")
        workflow.logger.info("=" * 60)

        validation_result = await workflow.execute_activity(
            "validate_company_data",
            args=[company_data, db_company_type],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        completeness = validation_result.get("overall_score", 0)
        meets_threshold = validation_result.get("meets_threshold", False)

        workflow.logger.info(f"✅ Data completeness: {completeness:.1%}")
        workflow.logger.info(f"   Meets threshold: {meets_threshold}")

        company_data['validation'] = validation_result

        # =====================================================================
        # STAGE 6: EXTRACT AND PROCESS LOGO
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🎨 STAGE 6: PROCESS COMPANY LOGO")
        workflow.logger.info("=" * 60)

        # Extract logo from website
        logo_url = await workflow.execute_activity(
            "extract_company_logo",
            args=[company_website, company_name],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        if logo_url:
            workflow.logger.info(f"✅ Found logo: {logo_url[:60]}...")
        else:
            workflow.logger.info(f"ℹ️  No logo found, will use fallback")

        # Process logo (upload to Cloudinary or generate fallback)
        logo_data = await workflow.execute_activity(
            "process_company_logo",
            args=[logo_url, company_name, company_id, db_company_type, False],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        company_data['logo'] = logo_data
        workflow.logger.info(f"✅ Logo processed: {logo_data.get('logo_source', 'unknown')}")

        # =====================================================================
        # STAGE 7: FORMAT COMPANY PROFILE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📝 STAGE 7: FORMAT PROFILE")
        workflow.logger.info("=" * 60)

        formatted_profile = await workflow.execute_activity(
            "format_company_profile",
            args=[company_data, db_company_type],
            start_to_close_timeout=timedelta(minutes=3),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"✅ Formatted profile with {len(formatted_profile.get('profile_sections', []))} sections")

        # =====================================================================
        # STAGE 8: SAVE TO DATABASE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("💾 STAGE 8: SAVE TO DATABASE")
        workflow.logger.info("=" * 60)

        saved = await workflow.execute_activity(
            "save_company_profile",
            formatted_profile,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        if saved:
            workflow.logger.info(f"✅ Company profile saved")
            workflow.logger.info(f"   Type: {db_company_type}")
            workflow.logger.info(f"   Detected as: {detected_type}")
        else:
            workflow.logger.error("❌ Failed to save company profile")

        formatted_profile['saved'] = saved

        # =====================================================================
        # WORKFLOW COMPLETE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🎉 SMART COMPANY WORKFLOW COMPLETE")
        workflow.logger.info("=" * 60)

        workflow.logger.info(f"   Company: {formatted_profile.get('company_name', 'Unknown')}")
        workflow.logger.info(f"   Detected Type: {detected_type} ({confidence:.1%} confidence)")
        workflow.logger.info(f"   Database Type: {db_company_type}")
        workflow.logger.info(f"   Completeness: {completeness:.1%}")
        workflow.logger.info(f"   Logo: {logo_data.get('logo_source', 'none')}")
        workflow.logger.info(f"   Saved: {saved}")
        workflow.logger.info("=" * 60)

        return formatted_profile

    @workflow.query
    def get_status(self) -> dict:
        """Query the current workflow status"""
        return {
            "company_data": self.company_data,
            "detected_type": self.detected_type
        }
