"""
Zep Entity Extraction Activity

Extract structured entities from content for Zep knowledge graph population.

Supports extraction of:
- Company profiles: Deals, People
- Job articles: Jobs, Skills, Locations
- Relocation articles: Locations, Countries
"""

from temporalio import activity
from typing import Dict, Any, List
import json

from src.utils.config import config


@activity.defn
async def extract_entities_from_v2_profile(
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract structured entities from V2 narrative sections using LLM.

    Args:
        payload: V2 CompanyPayload as dict

    Returns:
        Dict with:
        - deals: List of Deal entities
        - people: List of Person entities
        - success: bool
    """
    activity.logger.info("Extracting entities from V2 profile")

    try:
        # Import here to avoid circular dependencies
        import google.generativeai as genai
        from pydantic_ai import Agent
        from pydantic import BaseModel, Field

        # Configure Gemini
        genai.configure(api_key=config.GOOGLE_API_KEY)

        # Extract narrative sections
        profile_sections = payload.get("profile_sections", {})
        track_record = profile_sections.get("track_record", {}).get("content", "")
        team = profile_sections.get("team", {}).get("content", "")
        overview = profile_sections.get("overview", {}).get("content", "")
        services = profile_sections.get("services", {}).get("content", "")

        # Combine relevant sections
        narrative = f"""
OVERVIEW:
{overview}

SERVICES:
{services}

TRACK RECORD:
{track_record}

TEAM:
{team}
"""

        activity.logger.info(f"Narrative length: {len(narrative)} chars")

        # Define extraction schema
        class Deal(BaseModel):
            name: str = Field(description="Deal name or description")
            deal_type: str = Field(description="Type: M&A, capital_raising, IPO, advisory, relocation_contract, etc.")
            value: str = Field(description="Deal value (e.g., '$7.4B', '€500M', 'Undisclosed')")
            date: str = Field(description="Deal date or timeframe (e.g., '2024', 'Q1 2023', 'March 2024')")
            sector: str = Field(description="Industry sector (e.g., 'Technology', 'Healthcare', 'Real Estate')")
            parties: List[str] = Field(description="Companies or entities involved in the deal")

        class Person(BaseModel):
            name: str = Field(description="Person's full name")
            role: str = Field(description="Job title or role")
            company: str = Field(description="Associated company name")

        class ExtractedEntities(BaseModel):
            deals: List[Deal] = Field(description="List of deals extracted from narrative")
            people: List[Person] = Field(description="List of key people extracted from narrative")

        # Create extraction agent
        agent = Agent(
            model="gemini-1.5-flash",
            result_type=ExtractedEntities,
            system_prompt="""You are an expert at extracting structured entities from company narratives.

Extract ALL deals and key people mentioned in the text.

For deals:
- Include transaction name, type, value, date, sector, and parties involved
- If value is not mentioned, use "Undisclosed"
- Extract as many deals as you can find
- Be thorough - even brief mentions count

For people:
- Include executives, founders, key team members
- Extract their full name, role, and company
- Focus on senior leadership and notable individuals

Return comprehensive results. Empty lists are okay if nothing is found."""
        )

        # Run extraction
        activity.logger.info("Running LLM extraction...")
        result = await agent.run(narrative)
        extracted = result.data

        activity.logger.info(
            f"Extracted {len(extracted.deals)} deals and {len(extracted.people)} people"
        )

        # Convert to dicts
        deals_list = [
            {
                "name": deal.name,
                "deal_type": deal.deal_type,
                "value": deal.value,
                "date": deal.date,
                "sector": deal.sector,
                "parties": deal.parties
            }
            for deal in extracted.deals
        ]

        people_list = [
            {
                "name": person.name,
                "role": person.role,
                "company": person.company
            }
            for person in extracted.people
        ]

        # Log sample
        if deals_list:
            activity.logger.info(f"Sample deal: {deals_list[0].get('name', 'N/A')}")
        if people_list:
            activity.logger.info(f"Sample person: {people_list[0].get('name', 'N/A')}")

        return {
            "deals": deals_list,
            "people": people_list,
            "success": True,
            "total_deals": len(deals_list),
            "total_people": len(people_list)
        }

    except Exception as e:
        activity.logger.error(f"Entity extraction failed: {e}")
        return {
            "deals": [],
            "people": [],
            "success": False,
            "error": str(e)
        }


@activity.defn
async def extract_entities_from_article(
    content: str,
    article_type: str,
    app: str
) -> Dict[str, Any]:
    """
    Extract structured entities from article content using LLM.

    Extracts different entities based on app context:
    - jobs/placement: Jobs, Skills, Locations, Companies
    - relocation: Locations, Countries, Companies
    - placement/finance: Deals, People, Companies

    Args:
        content: Article content (markdown)
        article_type: Type of article (news, guide, comparison)
        app: App context (placement, relocation, jobs, etc.)

    Returns:
        Dict with extracted entities by type
    """
    activity.logger.info(f"Extracting entities from {app} article ({article_type})")

    try:
        import google.generativeai as genai
        from pydantic_ai import Agent
        from pydantic import BaseModel, Field

        genai.configure(api_key=config.GOOGLE_API_KEY)

        # Define all entity schemas
        class JobMention(BaseModel):
            title: str = Field(description="Job title")
            company: str = Field(description="Company offering the job", default="")
            location: str = Field(description="Job location (city, country)", default="")
            seniority: str = Field(description="Seniority level (junior/mid/senior/executive)", default="")
            employment_type: str = Field(description="Employment type (full-time/contract/part-time)", default="")

        class SkillMention(BaseModel):
            name: str = Field(description="Skill name (e.g., 'Python', 'Financial Modeling')")
            category: str = Field(description="Category: technical, soft, domain, language", default="technical")
            is_essential: bool = Field(description="Whether this is an essential/required skill", default=True)

        class LocationMention(BaseModel):
            city: str = Field(description="City name")
            country: str = Field(description="Country name", default="")
            region: str = Field(description="Region/state if mentioned", default="")
            context: str = Field(description="Context: job_location, relocation_destination, company_hq", default="")

        class CountryMention(BaseModel):
            name: str = Field(description="Country name")
            visa_info: str = Field(description="Any visa/work permit info mentioned", default="")
            relocation_context: str = Field(description="Relocation-relevant context mentioned", default="")

        class CompanyMention(BaseModel):
            name: str = Field(description="Company name")
            context: str = Field(description="Context: hiring, headquartered, mentioned", default="mentioned")

        # Choose extraction schema based on app
        if app in ["jobs", "recruiter", "chief-of-staff", "fractional-jobs"]:
            class JobsArticleEntities(BaseModel):
                jobs: List[JobMention] = Field(description="Job positions mentioned", default=[])
                skills: List[SkillMention] = Field(description="Skills mentioned", default=[])
                locations: List[LocationMention] = Field(description="Locations mentioned", default=[])
                companies: List[CompanyMention] = Field(description="Companies mentioned", default=[])

            result_type = JobsArticleEntities
            system_prompt = """Extract job-related entities from this article.

For jobs: Extract any job positions, roles, or career opportunities mentioned.
For skills: Extract technical skills, soft skills, and domain expertise mentioned.
For locations: Extract cities and regions mentioned as job locations or company bases.
For companies: Extract company names mentioned as employers or in hiring context.

Be thorough - even brief mentions count. Empty lists are okay if nothing found."""

        elif app == "relocation":
            class RelocationArticleEntities(BaseModel):
                locations: List[LocationMention] = Field(description="Cities/regions for relocation", default=[])
                countries: List[CountryMention] = Field(description="Countries with relocation info", default=[])
                companies: List[CompanyMention] = Field(description="Companies mentioned", default=[])

            result_type = RelocationArticleEntities
            system_prompt = """Extract relocation-related entities from this article.

For locations: Extract cities and regions mentioned as relocation destinations.
For countries: Extract countries with any visa, tax, or relocation info mentioned.
For companies: Extract companies mentioned (employers, relocation services, etc.).

Be thorough - even brief mentions count. Empty lists are okay if nothing found."""

        else:  # placement, pe_news, finance
            class FinanceArticleEntities(BaseModel):
                deals: List[dict] = Field(description="Deals/transactions mentioned", default=[])
                people: List[dict] = Field(description="Key people mentioned", default=[])
                companies: List[CompanyMention] = Field(description="Companies mentioned", default=[])

            result_type = FinanceArticleEntities
            system_prompt = """Extract finance-related entities from this article.

For deals: Extract M&A transactions, capital raises, IPOs mentioned.
For people: Extract executives, founders, key individuals.
For companies: Extract financial institutions, firms mentioned.

Be thorough - even brief mentions count. Empty lists are okay if nothing found."""

        # Create extraction agent
        agent = Agent(
            model="gemini-1.5-flash",
            result_type=result_type,
            system_prompt=system_prompt
        )

        # Run extraction (truncate content to avoid token limits)
        truncated_content = content[:15000] if len(content) > 15000 else content
        activity.logger.info(f"Running extraction on {len(truncated_content)} chars...")

        result = await agent.run(truncated_content)
        extracted = result.data

        # Convert to dict format
        entities = {}
        for field_name in extracted.model_fields:
            field_value = getattr(extracted, field_name)
            if isinstance(field_value, list):
                entities[field_name] = [
                    item.model_dump() if hasattr(item, 'model_dump') else item
                    for item in field_value
                ]
            else:
                entities[field_name] = field_value

        # Log summary
        for entity_type, items in entities.items():
            if items:
                activity.logger.info(f"  Extracted {len(items)} {entity_type}")

        return {
            "entities": entities,
            "app": app,
            "article_type": article_type,
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"Article entity extraction failed: {e}")
        return {
            "entities": {},
            "app": app,
            "article_type": article_type,
            "success": False,
            "error": str(e)
        }
