"""
Company Classification Activity

Uses AI to analyze website content and classify company type.
"""

import os
import json
from temporalio import activity
import google.generativeai as genai


@activity.defn
async def classify_company_type(company_name: str, website_content: str) -> dict:
    """
    Classify company type using AI analysis of website content

    Args:
        company_name: Name of the company
        website_content: Scraped website content

    Returns:
        dict with company_type, confidence, reasoning
    """
    activity.logger.info(f"🤖 Classifying company type for: {company_name}")

    # Configure Gemini
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    genai.configure(api_key=api_key)

    # Truncate content if too long (keep first 10k chars for classification)
    content_sample = website_content[:10000] if len(website_content) > 10000 else website_content

    classification_prompt = f"""Analyze this company's website content and classify what type of company it is.

Company Name: {company_name}

Website Content:
{content_sample}

Based on this content, classify the company into ONE of these categories:

1. **recruiter** - Executive Assistant, Chief of Staff, PA, or administrative recruitment agencies
   Examples: Bain & Gray, Tiger Recruitment, Office Angels, Pertemps
   Keywords: "executive assistant", "EA recruitment", "Chief of Staff", "PA jobs", "administrative", "personal assistant", "office manager recruitment"
   IMPORTANT: These companies help people find JOBS as assistants/administrators

2. **placement** - Private equity placement agents, fund placement, capital raising advisors
   Examples: Campbell Lutyens, Evercore, Lazard, Park Hill Group
   Keywords: "placement agent", "private equity", "fund placement", "capital raising", "fundraising", "GP stakes", "secondary transactions", "fund advisory", "capital advisory"
   IMPORTANT: These companies help funds/investors raise CAPITAL, NOT recruit people. "Fund placement" means placing capital with investors, NOT placing people in jobs.

3. **relocation** - Relocation services, immigration, visa support, moving services
   Examples: Santa Fe Relocation, Crown Relocations, Sirva
   Keywords: "relocation", "immigration", "visa", "moving", "expat", "international assignment", "global mobility"
   IMPORTANT: These companies help people/families move to new countries

CRITICAL DISTINCTION:
- If the company mentions "fund placement", "capital raising", "private equity", "secondary advisory", "GP capital advisory" → This is **placement** (financial services), NOT recruiter
- If the company mentions "executive assistant", "EA jobs", "administrative roles", "PA placement" → This is **recruiter**
- "Placement" in financial context means placing CAPITAL/FUNDS, not placing PEOPLE

Return your analysis as JSON:
{{
  "company_type": "recruiter|placement|relocation",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of why this classification was chosen (2-3 sentences)"
}}

Be very confident in your classification. Analyze the services offered, client types, job listings, and language used.
"""

    try:
        # Use Gemini for classification
        model = genai.GenerativeModel('gemini-1.5-flash')

        response = model.generate_content(
            classification_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,  # Low temperature for consistent classification
                max_output_tokens=500,
            )
        )

        response_text = response.text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text

        # Parse classification result
        result = json.loads(json_str)

        company_type = result.get("company_type", "recruiter")
        confidence = float(result.get("confidence", 0.5))
        reasoning = result.get("reasoning", "")

        # Validate company_type
        valid_types = ["recruiter", "placement", "relocation"]
        if company_type not in valid_types:
            activity.logger.warning(f"Invalid type '{company_type}', defaulting to 'recruiter'")
            company_type = "recruiter"
            confidence = 0.5

        activity.logger.info(f"✅ Classification complete:")
        activity.logger.info(f"   Type: {company_type}")
        activity.logger.info(f"   Confidence: {confidence:.1%}")
        activity.logger.info(f"   Reasoning: {reasoning[:100]}...")

        # Confidence threshold check
        if confidence < 0.8:
            activity.logger.warning(f"⚠️  Low confidence classification ({confidence:.1%})")
            activity.logger.warning(f"   Detected type: {company_type}")
            activity.logger.warning(f"   Defaulting to 'placement' for safety")

            # For low confidence, default to placement (most common type)
            # This prevents misclassification when signals are unclear
            return {
                "company_type": "placement",
                "confidence": confidence,
                "reasoning": f"Low confidence ({confidence:.1%}). Original: {company_type}. {reasoning}"
            }

        return {
            "company_type": company_type,
            "confidence": confidence,
            "reasoning": reasoning
        }

    except json.JSONDecodeError as e:
        activity.logger.error(f"Failed to parse AI response as JSON: {e}")
        activity.logger.error(f"Response was: {response_text[:200]}...")

        # Fallback: Try to detect type from keywords in response
        response_lower = response_text.lower()
        if "placement" in response_lower or "private equity" in response_lower:
            return {
                "company_type": "placement",
                "confidence": 0.6,
                "reasoning": "Detected placement-related keywords in AI response"
            }
        elif "relocation" in response_lower or "immigration" in response_lower:
            return {
                "company_type": "relocation",
                "confidence": 0.6,
                "reasoning": "Detected relocation-related keywords in AI response"
            }
        else:
            return {
                "company_type": "recruiter",
                "confidence": 0.5,
                "reasoning": "Defaulted to recruiter after parsing failure"
            }

    except Exception as e:
        activity.logger.error(f"Classification error: {e}")

        # Safe fallback
        return {
            "company_type": "recruiter",
            "confidence": 0.3,
            "reasoning": f"Classification failed, defaulting to recruiter. Error: {str(e)[:100]}"
        }
