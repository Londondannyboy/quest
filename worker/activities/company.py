"""
Company Activities

Activities for scraping company websites, extracting company information,
and creating standardized company profiles.
"""

import os
import json
import re
import asyncio
from typing import Dict, Any, List, Optional
from temporalio import activity
import httpx
import google.generativeai as genai
import cloudinary
import cloudinary.uploader
from urllib.parse import urljoin, urlparse

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


async def _scrape_with_firecrawl(company_url: str) -> Optional[Dict[str, Any]]:
    """Crawl entire website using Firecrawl API to get About, Team, Contact pages"""
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    if not firecrawl_key:
        return None

    try:
        activity.logger.info("🔥 Firecrawl v2: Starting crawl job...")
        async with httpx.AsyncClient(timeout=180.0) as client:
            # Start crawl job (v2 API)
            response = await client.post(
                "https://api.firecrawl.dev/v2/crawl",
                json={
                    "url": company_url,
                    "sitemap": "include",  # Use sitemap for faster crawling
                    "crawlEntireDomain": False,
                    "limit": 10,  # Crawl up to 10 pages
                    "scrapeOptions": {
                        "onlyMainContent": False,  # Get full content including nav
                        "formats": ["markdown"],
                        "parsers": ["pdf"]  # Parse PDFs too
                    }
                },
                headers={
                    "Authorization": f"Bearer {firecrawl_key}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            data = response.json()

            # Get crawl ID (v2 returns 'id')
            crawl_id = data.get("id")
            if not crawl_id:
                activity.logger.warning("Firecrawl v2: No crawl ID returned")
                return None

            activity.logger.info(f"🔥 Firecrawl v2: Crawl started, ID: {crawl_id}")

            # Poll for completion (max 120 seconds)
            for attempt in range(24):  # 24 attempts * 5 seconds = 120 seconds
                await asyncio.sleep(5)
                status_response = await client.get(
                    f"https://api.firecrawl.dev/v2/crawl/{crawl_id}",
                    headers={"Authorization": f"Bearer {firecrawl_key}"}
                )
                status_response.raise_for_status()
                status_data = status_response.json()

                status = status_data.get("status")
                activity.logger.info(f"🔥 Firecrawl v2: Poll {attempt+1}/24, status: {status}")

                if status == "completed":
                    # v2 API: data is in 'data' field, each page has 'markdown' field
                    pages = status_data.get("data", [])
                    combined_content = "\n\n---PAGE BREAK---\n\n".join([
                        f"PAGE: {page.get('metadata', {}).get('title', 'Unknown')}\nURL: {page.get('metadata', {}).get('url', '')}\n{page.get('markdown', '')}"
                        for page in pages
                    ])

                    if combined_content:
                        activity.logger.info(f"✅ Firecrawl v2: Crawled {len(pages)} pages successfully")
                        return {
                            "source": "firecrawl-v2-crawl",
                            "content": combined_content,
                            "title": pages[0].get("metadata", {}).get("title", "") if pages else "",
                            "char_count": len(combined_content)
                        }
                    break
                elif status in ["failed", "cancelled"]:
                    activity.logger.warning(f"Firecrawl v2 crawl {status}")
                    break

    except Exception as e:
        activity.logger.warning(f"Firecrawl crawl failed: {e}")
    return None


async def _scrape_with_tavily(company_url: str) -> Optional[Dict[str, Any]]:
    """Crawl entire website using Tavily Crawl API"""
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                "https://api.tavily.com/crawl",
                json={
                    "url": company_url,
                    "max_pages": 10,  # Crawl up to 10 pages
                    "extract_mode": "markdown"
                },
                headers={
                    "Content-Type": "application/json",
                    "api-key": tavily_key
                }
            )
            response.raise_for_status()
            data = response.json()
            pages = data.get("pages", [])

            if pages:
                # Combine content from all crawled pages
                combined_content = "\n\n---PAGE BREAK---\n\n".join([
                    f"PAGE: {page.get('title', 'Unknown')}\nURL: {page.get('url', '')}\n{page.get('content', '')}"
                    for page in pages
                ])

                activity.logger.info(f"✅ Tavily: Crawled {len(pages)} pages")
                return {
                    "source": "tavily-crawl",
                    "content": combined_content,
                    "title": pages[0].get("title", "") if pages else "",
                    "char_count": len(combined_content)
                }
    except Exception as e:
        activity.logger.warning(f"Tavily crawl failed: {e}")
    return None


async def _scrape_direct(company_url: str) -> Optional[Dict[str, Any]]:
    """Direct scraping using BeautifulSoup"""
    try:
        from bs4 import BeautifulSoup

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = await client.get(company_url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            main = soup.find('main') or soup.find('article') or soup.find('body')

            if main:
                for element in main.find_all(["script", "style", "nav", "footer", "header"]):
                    element.decompose()

                text = main.get_text(separator=' ', strip=True)
                text = ' '.join(text.split())

                if text:
                    return {
                        "source": "direct",
                        "content": text,
                        "title": soup.title.string if soup.title else "",
                        "char_count": len(text)
                    }
    except Exception as e:
        activity.logger.warning(f"Direct scraping failed: {e}")
    return None


@activity.defn(name="scrape_company_website")
async def scrape_company_website(company_url: str) -> Dict[str, Any]:
    """
    Scrape a company website using multiple services in parallel for guaranteed results

    Args:
        company_url: URL of the company website

    Returns:
        Dict with scraped content and metadata
    """
    activity.logger.info(f"🌐 Scraping company website: {company_url} (parallel: Firecrawl + Tavily + Direct)")

    # Run all scrapers in parallel
    results = await asyncio.gather(
        _scrape_with_firecrawl(company_url),
        _scrape_with_tavily(company_url),
        _scrape_direct(company_url),
        return_exceptions=True
    )

    # Filter out None and exceptions
    valid_results = [r for r in results if r and not isinstance(r, Exception)]

    if not valid_results:
        activity.logger.error(f"❌ All scraping methods failed for {company_url}")
        return {
            "url": company_url,
            "content": "",
            "error": "All scraping methods failed"
        }

    # Log results from each source
    sources_used = [r['source'] for r in valid_results]
    activity.logger.info(f"✅ Successfully scraped from: {', '.join(sources_used)}")

    # Choose the result with the most content
    best_result = max(valid_results, key=lambda x: x['char_count'])

    activity.logger.info(f"📊 Using {best_result['source']} result ({best_result['char_count']} chars)")
    other_sources = [f"{r['source']}={r['char_count']} chars" for r in valid_results if r != best_result]
    activity.logger.info(f"   Other sources: {', '.join(other_sources)}")

    return {
        "url": company_url,
        "content": best_result['content'],
        "title": best_result['title'],
        "error": None,
        "sources_used": sources_used,
        "source_chosen": best_result['source']
    }


@activity.defn(name="search_company_news")
async def search_company_news(company_name: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search for recent news about a company using Serper

    Args:
        company_name: Name of the company to search for
        num_results: Number of news results to return

    Returns:
        List of news items with titles, links, and snippets
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        activity.logger.error("SERPER_API_KEY not set")
        return []

    activity.logger.info(f"📰 Searching news for: {company_name}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://google.serper.dev/news",
                json={
                    "q": f'"{company_name}"',
                    "num": num_results,
                    "tbs": "qdr:m"  # Last month
                },
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            data = response.json()

        news_items = data.get("news", [])
        activity.logger.info(f"✅ Found {len(news_items)} news articles")

        return news_items

    except Exception as e:
        activity.logger.error(f"❌ News search failed: {e}")
        return []


@activity.defn(name="extract_company_info")
async def extract_company_info(
    company_name: str,
    website_content: str,
    news_items: List[Dict[str, Any]],
    company_type: str
) -> Dict[str, Any]:
    """
    Extract structured company information using Gemini

    Args:
        company_name: Name of the company
        website_content: Scraped content from company website
        news_items: Recent news articles about the company
        company_type: Type of company profile (placement_company or relocation_company)

    Returns:
        Structured company data dict
    """
    from config.app_configs import get_company_config

    activity.logger.info(f"🔍 Extracting company info for: {company_name}")

    try:
        # Get company config for this type
        config = get_company_config(company_type)

        # Combine news summaries
        news_context = "\n".join([
            f"- {item.get('title', '')}: {item.get('snippet', '')}"
            for item in news_items[:5]
        ])

        # Build extraction prompt based on company type
        if "placement" in company_type:
            extraction_focus = """Focus on:
- Financial services and deal types (fund placement, secondary advisory, GP capital advisory)
- Notable transactions and deals
- Assets under management (AUM) - total capital raised/placed
- Key leadership in finance/investment
- Market reputation and competitive position
- Specializations (PE, VC, Infrastructure, Private Credit, Real Assets, etc.)
- Geographic focus and office locations

DO NOT include (these are NOT placement agent services):
- Recruitment services, headhunting, or executive search
- Executive Assistant or Chief of Staff placement
- HR staffing or personnel services
- Job boards or career services
- Relocation or immigration services"""
        else:  # relocation
            extraction_focus = """Focus on:
- Relocation and immigration services offered
- Countries and regions served
- Visa types and specializations
- Client reviews and success rates
- Pricing information if available
- Languages supported
- Certifications and credentials

DO NOT include (these are NOT relocation services):
- Fund placement or capital raising services
- Executive recruitment services
- Financial advisory services"""

        extraction_prompt = f"""Extract comprehensive company information for: {company_name}

Company Type: {config.display_name}

{extraction_focus}

Website Content:
{website_content[:8000]}

Recent News:
{news_context}

Required Fields to Extract:
{', '.join(config.required_fields)}

Optional Fields to Extract (if available):
{', '.join(config.optional_fields)}

IMPORTANT - Extract from news:
- Look for PEOPLE'S NAMES and their titles/roles in the "Recent News" section
- Look for founding dates, employee counts, office locations mentioned in news
- Look for phone numbers, email addresses in website content
- News articles often mention partners, executives, heads of departments - extract ALL of them

Return ONLY a JSON object with this exact structure:
{{
  "company_name": "Official company name",
  "website": "Company website URL",
  "description": "Clear, factual 2-3 sentence description",
  "industry": "Specific industry classification",
  "headquarters_location": "City, Country",
  "founded_year": "YYYY or null",
  "employee_count": "number or range or null",
  "key_services": ["service 1", "service 2"],
  "specializations": ["spec 1", "spec 2"],
  "notable_achievements": ["achievement 1", "achievement 2"],
  "key_people": [{{"name": "...", "title": "..."}}, ...],
  "contact_info": {{
    "phone": "..." or null,
    "email": "..." or null,
    "linkedin": "..." or null
  }},
  "additional_data": {{
    // Any other relevant fields based on company type
  }}
}}

Guidelines:
- Be factual and objective
- Use information ONLY from the provided sources (website content and news)
- DO NOT invent, assume, or hallucinate services that are not explicitly mentioned
- If a service or field is not clearly stated in the sources, return null
- Avoid promotional language
- Ensure accuracy over completeness
- When in doubt, return null rather than guessing"""

        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(extraction_prompt)
        content = response.text

        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        company_data = json.loads(content)

        # Add metadata
        company_data['company_type'] = company_type
        company_data['data_sources'] = {
            'website_scraped': bool(website_content),
            'news_articles': len(news_items)
        }

        activity.logger.info(f"✅ Extracted company info for {company_name}")

        return company_data

    except Exception as e:
        activity.logger.error(f"❌ Company info extraction failed: {e}")
        # Return minimal structure
        return {
            "company_name": company_name,
            "website": "",
            "description": "",
            "industry": "",
            "headquarters_location": "",
            "error": str(e),
            "company_type": company_type
        }


@activity.defn(name="validate_company_data")
async def validate_company_data(
    company_data: Dict[str, Any],
    company_type: str
) -> Dict[str, Any]:
    """
    Validate company data completeness and quality

    Args:
        company_data: Extracted company data
        company_type: Type of company profile

    Returns:
        Validation result with score and missing fields
    """
    from config.app_configs import get_company_config

    activity.logger.info("📊 Validating company data")

    try:
        config = get_company_config(company_type)

        # Check required fields
        required_fields = config.required_fields
        missing_required = []
        present_required = []

        for field in required_fields:
            value = company_data.get(field)
            if value and value != "" and value != "null" and value is not None:
                present_required.append(field)
            else:
                missing_required.append(field)

        # Calculate completeness score
        required_completeness = len(present_required) / len(required_fields) if required_fields else 1.0

        # Check optional fields
        optional_fields = config.optional_fields
        present_optional = []

        for field in optional_fields:
            value = company_data.get(field)
            if value and value != "" and value != "null" and value is not None:
                present_optional.append(field)

        optional_completeness = len(present_optional) / len(optional_fields) if optional_fields else 0.0

        # Overall score (weighted: 80% required, 20% optional)
        overall_score = (required_completeness * 0.8) + (optional_completeness * 0.2)

        # Determine if meets threshold
        meets_threshold = required_completeness >= config.min_data_completeness
        auto_publish = overall_score >= config.auto_publish_threshold

        validation_result = {
            "overall_score": overall_score,
            "required_completeness": required_completeness,
            "optional_completeness": optional_completeness,
            "meets_threshold": meets_threshold,
            "auto_publish_ready": auto_publish,
            "missing_required_fields": missing_required,
            "present_required_fields": present_required,
            "present_optional_fields": present_optional,
            "total_fields_present": len(present_required) + len(present_optional)
        }

        activity.logger.info(f"✅ Validation complete: {overall_score:.1%} complete, "
                           f"meets threshold: {meets_threshold}")

        return validation_result

    except Exception as e:
        activity.logger.error(f"❌ Validation failed: {e}")
        return {
            "overall_score": 0.0,
            "meets_threshold": False,
            "error": str(e)
        }


@activity.defn(name="format_company_profile")
async def format_company_profile(
    company_data: Dict[str, Any],
    company_type: str
) -> Dict[str, Any]:
    """
    Format company data into a structured profile document

    Args:
        company_data: Validated company data
        company_type: Type of company profile

    Returns:
        Formatted company profile with sections
    """
    from config.app_configs import get_company_config

    activity.logger.info("📝 Formatting company profile")

    try:
        config = get_company_config(company_type)

        # Generate profile sections using Gemini
        sections_prompt = f"""Create a professional company profile with these sections:

{chr(10).join([f'- {section}' for section in config.profile_sections])}

Company Data:
{json.dumps(company_data, indent=2)}

Tone: {config.tone}
Target Audience: {config.target_audience}

Return ONLY a JSON object with this structure:
{{
  "title": "Company Name - Brief Tagline",
  "sections": [
    {{
      "heading": "Section Name",
      "content": "Well-written section content..."
    }}
  ],
  "summary": "Brief 1-sentence company summary",
  "tags": ["tag1", "tag2", "tag3"]
}}

Guidelines:
- Write in {config.tone} tone
- Target {config.target_audience}
- Be factual and well-structured
- Each section should be 2-4 paragraphs
- Use professional formatting"""

        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(sections_prompt)
        content = response.text

        # Extract JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        profile_data = json.loads(content)

        # Combine with original company data
        formatted_profile = {
            **company_data,
            "profile_title": profile_data.get("title", ""),
            "profile_sections": profile_data.get("sections", []),
            "profile_summary": profile_data.get("summary", ""),
            "profile_tags": profile_data.get("tags", []),
            "company_type": company_type
        }

        activity.logger.info(f"✅ Formatted profile with {len(profile_data.get('sections', []))} sections")

        return formatted_profile

    except Exception as e:
        activity.logger.error(f"❌ Profile formatting failed: {e}")
        # Return basic formatted profile
        return {
            **company_data,
            "profile_title": company_data.get("company_name", "Unknown Company"),
            "profile_sections": [],
            "profile_summary": company_data.get("description", ""),
            "profile_tags": [],
            "error": str(e)
        }


@activity.defn(name="extract_company_logo")
async def extract_company_logo(company_url: str, company_name: str) -> Optional[str]:
    """
    Extract company logo URL from website

    Args:
        company_url: Company website URL
        company_name: Company name for searching

    Returns:
        Logo image URL or None
    """
    activity.logger.info(f"🎨 Extracting logo from: {company_url}")

    try:
        # Try multiple common logo locations
        logo_patterns = [
            r'<link[^>]+rel=["\'](?:icon|apple-touch-icon|shortcut icon)["\'][^>]+href=["\']([^"\']+)["\']',
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<img[^>]+(?:class|id)=["\'][^"\']*logo[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
            r'<img[^>]+src=["\']([^"\']*logo[^"\']+)["\']',
            r'<img[^>]+alt=["\'][^"\']*logo[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(company_url, follow_redirects=True)
            response.raise_for_status()
            html_content = response.text

            # Try each pattern
            for pattern in logo_patterns:
                matches = re.finditer(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    logo_url = match.group(1)

                    # Make URL absolute if relative
                    if not logo_url.startswith(('http://', 'https://')):
                        logo_url = urljoin(company_url, logo_url)

                    # Check if it's a valid image URL
                    if any(ext in logo_url.lower() for ext in ['.png', '.jpg', '.jpeg', '.svg', '.webp', '.ico']):
                        activity.logger.info(f"✅ Found logo: {logo_url}")
                        return logo_url

        activity.logger.warning(f"⚠️  No logo found for {company_name}")
        return None

    except Exception as e:
        activity.logger.error(f"❌ Logo extraction failed: {e}")
        return None


@activity.defn(name="process_company_logo")
async def process_company_logo(
    logo_url: Optional[str],
    company_name: str,
    company_id: str,
    company_type: str,
    stylize: bool = False
) -> Dict[str, Any]:
    """
    Process company logo: download, optionally stylize, and upload to Cloudinary

    Args:
        logo_url: URL of the company logo (or None)
        company_name: Company name
        company_id: Unique company identifier
        company_type: Type of company profile
        stylize: Whether to create a stylized version

    Returns:
        Dict with original_logo_url, stylized_logo_url, and fallback_image_url
    """
    from config.app_configs import get_company_config

    activity.logger.info(f"🎨 Processing logo for: {company_name}")

    result = {
        "original_logo_url": None,
        "stylized_logo_url": None,
        "fallback_image_url": None,
        "logo_source": None
    }

    try:
        config = get_company_config(company_type)

        # If we have a logo URL, download and upload to Cloudinary
        if logo_url:
            try:
                # Upload original logo to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    logo_url,
                    folder=f"companies/{company_type}",
                    public_id=f"{company_id}_logo",
                    overwrite=True,
                    resource_type="image"
                )

                result["original_logo_url"] = upload_result.get("secure_url")
                result["logo_source"] = "website"

                activity.logger.info(f"✅ Uploaded original logo to Cloudinary")

                # Optionally create stylized version (if enabled and configured)
                # Note: Actual stylization would require image generation API
                # For now, we'll just mark that stylization was requested
                if stylize and config.logo_style in ["stylized", "both"]:
                    result["stylized_logo_url"] = result["original_logo_url"]  # Placeholder
                    activity.logger.info(f"ℹ️  Stylization requested but not yet implemented")

            except Exception as e:
                activity.logger.error(f"❌ Failed to upload logo: {e}")

        # If no logo or upload failed, generate fallback image using Replicate
        if not result["original_logo_url"]:
            activity.logger.info(f"🎨 Generating fallback image for {company_name}")

            # Generate fallback using the company's fallback prompt
            fallback_prompt = config.fallback_image_prompt.format(
                company_name=company_name,
                industry=company_type.replace("_", " "),
                service_type=company_type.replace("_", " ")
            )

            # Use Replicate to generate fallback image
            replicate_api_token = os.getenv("REPLICATE_API_TOKEN")
            if replicate_api_token:
                try:
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = await client.post(
                            "https://api.replicate.com/v1/predictions",
                            headers={
                                "Authorization": f"Bearer {replicate_api_token}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "version": "black-forest-labs/flux-schnell",
                                "input": {
                                    "prompt": fallback_prompt,
                                    "aspect_ratio": "1:1",
                                    "output_format": "png"
                                }
                            }
                        )
                        response.raise_for_status()
                        prediction = response.json()

                        # Poll for completion
                        prediction_id = prediction["id"]
                        for _ in range(30):  # Max 30 attempts
                            await asyncio.sleep(2)

                            status_response = await client.get(
                                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                                headers={"Authorization": f"Bearer {replicate_api_token}"}
                            )
                            status_data = status_response.json()

                            if status_data["status"] == "succeeded":
                                generated_url = status_data["output"][0]

                                # Upload to Cloudinary
                                upload_result = cloudinary.uploader.upload(
                                    generated_url,
                                    folder=f"companies/{company_type}",
                                    public_id=f"{company_id}_fallback",
                                    overwrite=True
                                )

                                result["fallback_image_url"] = upload_result.get("secure_url")
                                result["logo_source"] = "generated"

                                activity.logger.info(f"✅ Generated and uploaded fallback image")
                                break
                            elif status_data["status"] == "failed":
                                activity.logger.error(f"❌ Image generation failed")
                                break

                except Exception as e:
                    activity.logger.error(f"❌ Fallback image generation failed: {e}")

        return result

    except Exception as e:
        activity.logger.error(f"❌ Logo processing failed: {e}")
        return {
            "original_logo_url": None,
            "stylized_logo_url": None,
            "fallback_image_url": None,
            "error": str(e)
        }
