from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from ..models.job import Company, ScrapingResult


@workflow.defn
class JobScrapingWorkflow:
    """Master workflow that orchestrates all job scraping"""

    @workflow.run
    async def run(self, companies: list[dict] | None = None) -> dict:
        """
        Run job scraping for all configured companies.

        Args:
            companies: Optional list of specific companies to scrape.
                      If None, fetches all active companies from database.
        """
        # Get companies to scrape
        if companies is None:
            companies = await workflow.execute_activity(
                "get_companies_to_scrape",
                start_to_close_timeout=timedelta(seconds=30),
            )

        results = []
        child_workflows = []

        # Group companies by board type
        companies_by_type: dict[str, list] = {}
        for company in companies:
            board_type = company.get("board_type", "unknown")
            if board_type not in companies_by_type:
                companies_by_type[board_type] = []
            companies_by_type[board_type].append(company)

        # Launch child workflows for each scraper type
        for board_type, type_companies in companies_by_type.items():
            workflow_name = f"{board_type.title()}ScraperWorkflow"

            for company in type_companies:
                child_handle = await workflow.start_child_workflow(
                    workflow_name,
                    company,
                    id=f"scrape-{company['name'].lower().replace(' ', '-')}-{workflow.now().isoformat()}",
                    retry_policy=RetryPolicy(
                        maximum_attempts=3,
                        initial_interval=timedelta(seconds=10),
                    ),
                )
                child_workflows.append((company["name"], child_handle))

        # Wait for all child workflows to complete
        for company_name, handle in child_workflows:
            try:
                result = await handle
                results.append(result)
            except Exception as e:
                results.append({
                    "company_name": company_name,
                    "jobs_found": 0,
                    "jobs_added": 0,
                    "jobs_updated": 0,
                    "errors": [str(e)],
                    "duration_seconds": 0,
                })

        # Update graphs with all new data
        await workflow.execute_activity(
            "update_job_graphs",
            results,
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Calculate company trends
        await workflow.execute_activity(
            "calculate_company_trends",
            [r["company_name"] for r in results if r.get("jobs_added", 0) > 0],
            start_to_close_timeout=timedelta(minutes=2),
        )

        return {
            "total_companies": len(companies),
            "total_jobs_found": sum(r.get("jobs_found", 0) for r in results),
            "total_jobs_added": sum(r.get("jobs_added", 0) for r in results),
            "results": results,
        }
