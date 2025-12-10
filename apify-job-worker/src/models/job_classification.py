"""Pydantic AI models for job classification."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
import os

# Configure Pydantic AI Gateway if available
if os.getenv("PYDANTIC_GATEWAY_API_KEY"):
    os.environ["PYDANTIC_AI_GATEWAY_API_KEY"] = os.getenv("PYDANTIC_GATEWAY_API_KEY")


# Classification output models
class JobClassification(BaseModel):
    """Structured classification of a job posting."""

    # Core classification
    employment_type: Literal["fractional", "part_time", "contract", "full_time", "temporary", "freelance"]
    is_fractional: bool = Field(description="True if this is a fractional/part-time/interim executive role")

    # Geographic classification
    country: str = Field(description="Primary country for the job (e.g., 'United Kingdom', 'France')")
    city: Optional[str] = Field(default=None, description="City if specified")
    is_remote: bool = Field(default=False, description="True if fully remote")
    workplace_type: Optional[Literal["remote", "hybrid", "onsite"]] = Field(default=None)

    # Role classification
    category: str = Field(description="Job category (e.g., 'Engineering', 'Finance', 'Marketing', 'Product')")
    seniority_level: Literal["c_suite", "vp", "director", "manager", "senior", "mid", "junior", "entry"]
    role_title: str = Field(description="Normalized role title (e.g., 'Chief Technology Officer', 'VP Engineering')")

    # Company info
    company_name: str
    company_industry: Optional[str] = Field(default=None, description="Industry sector")
    company_size: Optional[Literal["startup", "small", "medium", "large", "enterprise"]] = Field(default=None)

    # Skills and requirements
    required_skills: List[str] = Field(default_factory=list, description="Key technical or domain skills required")
    nice_to_have_skills: List[str] = Field(default_factory=list, description="Optional skills")
    years_experience: Optional[int] = Field(default=None, description="Minimum years of experience")

    # Compensation
    salary_min: Optional[int] = Field(default=None)
    salary_max: Optional[int] = Field(default=None)
    salary_currency: Optional[str] = Field(default="GBP")

    # Confidence and reasoning
    classification_confidence: float = Field(ge=0.0, le=1.0, description="Confidence in classification")
    reasoning: str = Field(description="Brief explanation of classification decisions")

    # Site targeting
    site_tags: List[str] = Field(default_factory=list, description="Which sites should show this job")


# Define the classification agent (initialized when needed)
_job_classifier_agent = None

def get_job_classifier(model_tier: str = "fast") -> Agent:
    """
    Get or create the job classifier agent.

    Args:
        model_tier: Model selection based on requirements:
            - "fast": gemini-2.0-flash (default, cheap, good for basic classification)
            - "thinking": gemini-2.0-flash-thinking (reasoning, moderate cost)
            - "accurate": gemini-2.5-pro (highest accuracy, expensive)
    """
    global _job_classifier_agent
    if _job_classifier_agent is None:
        # Select model based on tier
        model_map = {
            "fast": "gemini-2.0-flash",
            "thinking": "gemini-2.0-flash-thinking",
            "accurate": "gemini-2.5-pro",
        }

        # Allow override via env var, otherwise use tier
        model_name = os.getenv("GOOGLE_MODEL") or model_map.get(model_tier, "gemini-2.0-flash")

        # GeminiModel automatically uses gateway if PYDANTIC_AI_GATEWAY_API_KEY is set
        _job_classifier_agent = Agent(
            GeminiModel(model_name),
            system_prompt="""You are an expert job market analyst specializing in classifying job postings.

Your task is to analyze job postings and extract structured information about:
1. Employment type (fractional, part-time, contract, full-time, etc.)
2. Geographic location (country, city, remote status)
3. Role classification (category, seniority, normalized title)
4. Company information (industry, size)
5. Skills and requirements
6. Compensation details

**Important Guidelines:**

**Fractional Classification:**
- Mark is_fractional=true for ANY fractional/part-time/contract/interim role (not just executives)
- This includes fractional directors, interim managers, part-time specialists, contract engineers, etc.
- Keywords: "fractional", "interim", "part-time", "contract", "0.5 FTE", "2-3 days/week", "reduced hours"
- employment_type should be "fractional", "part_time", or "contract" for these roles
- For scraped results filtered by "fractional OR part-time OR contract OR interim", most should be classified as fractional

**Country Detection:**
- Extract the primary country from the location field
- Common formats: "London, United Kingdom", "Remote, UK", "Berlin, Germany"
- Use full country names, not abbreviations

**Category Classification:**
- Engineering: Software, DevOps, Infrastructure, Data Engineering
- Product: Product Management, Product Design, UX/UI
- Finance: CFO, Finance Manager, Accounting, FP&A
- Marketing: CMO, Growth, Content, Brand
- Operations: COO, Operations Manager, Supply Chain
- Sales: CRO, Sales Director, Business Development
- HR: CHRO, People Operations, Talent
- Executive: CEO, General Manager, Chief of Staff

**Seniority Levels:**
- c_suite: CEO, CTO, CFO, CMO, COO, CHRO, CRO, etc.
- vp: VP, Vice President
- director: Director level
- manager: Manager, Lead
- senior/mid/junior: IC roles

**Site Tags:**
- Add "fractional-jobs" for fractional roles
- Add "startup-jobs" if startup/early-stage company
- Add "remote-jobs" if fully remote

**Confidence Scoring:**
- 0.9-1.0: Very clear, explicit information
- 0.7-0.9: Clear implications, good confidence
- 0.5-0.7: Some uncertainty, needs review
- <0.5: Low confidence, flag for manual review

Be thorough but conservative with confidence scores."""
        )
    return _job_classifier_agent


# Example usage function
async def classify_job(
    job_title: str,
    job_description: str,
    company_name: str,
    location: str,
    employment_type: Optional[str] = None,
    seniority_level: Optional[str] = None,
) -> JobClassification:
    """
    Classify a job using Pydantic AI.

    Args:
        job_title: Job title
        job_description: Full job description
        company_name: Company name
        location: Job location
        employment_type: Optional pre-classified employment type
        seniority_level: Optional pre-classified seniority

    Returns:
        JobClassification with all structured fields
    """
    # Quick keyword check for fractional roles - if keywords present, it's definitely fractional
    combined_text = f"{job_title} {job_description}".lower()
    fractional_keywords = ["fractional", "part-time", "part time", "contract", "interim", "0.5 fte", "2-3 days", "3 days a week"]
    has_fractional_keyword = any(keyword in combined_text for keyword in fractional_keywords)

    # Build prompt with all available context
    prompt = f"""Classify this job posting and return a JSON object with these fields:
- employment_type: "fractional", "part_time", "contract", "full_time", "temporary", or "freelance"
- is_fractional: boolean (true for ANY fractional/part-time/contract/interim role, not just executives)
- country: full country name (e.g., "United Kingdom")
- city: city name if available, otherwise null
- is_remote: boolean
- workplace_type: "remote", "hybrid", "onsite", or null
- category: job category (e.g., "Engineering", "Finance", "Marketing", "Product")
- seniority_level: "c_suite", "vp", "director", "manager", "senior", "mid", "junior", or "entry"
- role_title: normalized role title (e.g., "Chief Technology Officer")
- company_name: company name
- company_industry: industry sector or null
- company_size: "startup", "small", "medium", "large", "enterprise", or null
- required_skills: array of key skills
- nice_to_have_skills: array of optional skills
- years_experience: minimum years or null
- salary_min, salary_max: numbers or null
- salary_currency: currency code (e.g., "GBP") or null
- classification_confidence: float 0-1
- reasoning: brief explanation
- site_tags: array of tags (e.g., ["fractional-jobs"])

**Job Title:** {job_title}
**Company:** {company_name}
**Location:** {location}
{f'**Listed Employment Type:** {employment_type}' if employment_type else ''}
{f'**Listed Seniority:** {seniority_level}' if seniority_level else ''}

**Job Description:**
{job_description[:3000]}"""

    classifier = get_job_classifier()
    result = await classifier.run(prompt)

    # The result.output contains the string response
    # Parse it as JSON and convert to JobClassification
    import json
    response_text = result.output

    # Try to extract JSON from the response
    if isinstance(response_text, str):
        # If it's wrapped in markdown code blocks, extract it
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        data_dict = json.loads(response_text)
    else:
        data_dict = response_text

    classification = JobClassification(**data_dict)

    # Override fractional classification if we found explicit keywords
    if has_fractional_keyword and not classification.is_fractional:
        classification.is_fractional = True
        classification.employment_type = "fractional"
        classification.classification_confidence = max(0.95, classification.classification_confidence)
        classification.reasoning = f"Keyword-based detection: Found fractional keywords in title/description. {classification.reasoning}"
        if "fractional-jobs" not in classification.site_tags:
            classification.site_tags = [*classification.site_tags, "fractional-jobs"]

    return classification
