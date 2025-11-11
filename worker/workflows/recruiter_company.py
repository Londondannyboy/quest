"""
Recruiter Company Workflow

Dedicated workflow for creating company profiles for chiefofstaff.quest
Focused on Executive Assistant and Chief of Staff recruitment agencies.
"""

from datetime import timedelta
from typing import Optional
from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class RecruiterCompanyWorkflow:
    """
    Workflow for creating recruiter company profiles for Chief of Staff

    This workflow:
    - Scrapes company website
    - Searches for recent company news
    - Extracts structured company information
    - Processes company logo
    - Validates and formats company profile
    - Saves to database with company_type='executive_assistant_recruiters'
    """

    def __init__(self) -> None:
        self.company_data: Optional[dict] = None

    @workflow.run
    async def run(
        self,
        company_name: str,
        company_website: str,
        auto_approve: bool = True
    ) -> dict:
        """
        Run the recruiter company workflow

        Args:
            company_name: Name of the recruitment agency
            company_website: Company website URL
            auto_approve: If True, skip manual approval

        Returns:
            Complete company profile dict
        """
        company_type = "executive_assistant_recruiters"
        company_id = str(workflow.uuid4())[:8]

        workflow.logger.info(f"🚀 Recruiter Company workflow started")
        workflow.logger.info(f"   Company: {company_name}")
        workflow.logger.info(f"   Website: {company_website}")
        workflow.logger.info(f"   Company ID: {company_id}")

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
        # STAGE 2: SEARCH COMPANY NEWS
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📰 STAGE 2: SEARCH COMPANY NEWS")
        workflow.logger.info("=" * 60)

        news_items = await workflow.execute_activity(
            "search_company_news",
            args=[company_name, 5],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"✅ Found {len(news_items)} news articles")

        # =====================================================================
        # STAGE 3: EXTRACT COMPANY INFORMATION
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🔍 STAGE 3: EXTRACT COMPANY INFO")
        workflow.logger.info("=" * 60)

        company_data = await workflow.execute_activity(
            "extract_company_info",
            args=[company_name, website_content, news_items, company_type],
            start_to_close_timeout=timedelta(minutes=3),
            retry_policy=retry_policy,
        )

        company_data['id'] = company_id
        company_data['company_type'] = company_type

        workflow.logger.info(f"✅ Extracted company information")

        # =====================================================================
        # STAGE 4: VALIDATE COMPANY DATA
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📊 STAGE 4: VALIDATE DATA")
        workflow.logger.info("=" * 60)

        validation_result = await workflow.execute_activity(
            "validate_company_data",
            args=[company_data, company_type],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        completeness = validation_result.get("overall_score", 0)
        meets_threshold = validation_result.get("meets_threshold", False)

        workflow.logger.info(f"✅ Data completeness: {completeness:.1%}")
        workflow.logger.info(f"   Meets threshold: {meets_threshold}")

        company_data['validation'] = validation_result

        # =====================================================================
        # STAGE 5: EXTRACT AND PROCESS LOGO
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🎨 STAGE 5: PROCESS COMPANY LOGO")
        workflow.logger.info("=" * 60)

        # First, try to extract logo from website
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

        # Process logo (upload to Cloudinary, optionally stylize, or generate fallback)
        logo_data = await workflow.execute_activity(
            "process_company_logo",
            args=[logo_url, company_name, company_id, company_type, False],  # stylize=False for recruiters
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        company_data['logo'] = logo_data
        workflow.logger.info(f"✅ Logo processed: {logo_data.get('logo_source', 'unknown')}")

        # =====================================================================
        # STAGE 6: FORMAT COMPANY PROFILE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("📝 STAGE 6: FORMAT PROFILE")
        workflow.logger.info("=" * 60)

        formatted_profile = await workflow.execute_activity(
            "format_company_profile",
            args=[company_data, company_type],
            start_to_close_timeout=timedelta(minutes=3),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"✅ Formatted profile with {len(formatted_profile.get('profile_sections', []))} sections")

        # =====================================================================
        # STAGE 7: SAVE TO DATABASE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("💾 STAGE 7: SAVE TO DATABASE")
        workflow.logger.info("=" * 60)

        saved = await workflow.execute_activity(
            "save_company_profile",
            formatted_profile,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        if saved:
            workflow.logger.info(f"✅ Company profile saved (type: {company_type})")
        else:
            workflow.logger.error("❌ Failed to save company profile")

        formatted_profile['saved'] = saved

        # =====================================================================
        # WORKFLOW COMPLETE
        # =====================================================================
        workflow.logger.info("=" * 60)
        workflow.logger.info("🎉 RECRUITER COMPANY WORKFLOW COMPLETE")
        workflow.logger.info("=" * 60)

        workflow.logger.info(f"   Company: {formatted_profile.get('company_name', 'Unknown')}")
        workflow.logger.info(f"   Completeness: {completeness:.1%}")
        workflow.logger.info(f"   Logo: {logo_data.get('logo_source', 'none')}")
        workflow.logger.info(f"   Saved: {saved}")
        workflow.logger.info("=" * 60)

        return formatted_profile

    @workflow.query
    def get_status(self) -> dict:
        """Query the current workflow status"""
        return {
            "company_data": self.company_data
        }
