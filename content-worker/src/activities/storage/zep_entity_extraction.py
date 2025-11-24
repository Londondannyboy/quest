"""
Zep Entity Extraction Activity

Extract structured entities (deals, people) from V2 narrative payload
for Zep knowledge graph population.
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
