"""
Country Guide Content Generation

Generates comprehensive country relocation guides covering all 8 motivations:
- corporate, trust, wealth, retirement, digital-nomad, lifestyle, new-start, family

Outputs structured payload matching [country].astro frontend expectations.
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
from slugify import slugify
import re
import json

# AI SDKs - Gemini primary, Anthropic fallback
import google.generativeai as genai
import anthropic

from src.utils.config import config


# 8 motivations with display info
MOTIVATIONS = {
    "corporate": {
        "title": "Corporate Relocation",
        "description": "Company-sponsored relocation, business visas, corporate tax",
        "planning_types": ["visa", "tax", "business", "housing"],
        "icon": "briefcase"
    },
    "trust": {
        "title": "Trust & Asset Protection",
        "description": "Estate planning, trust structures, asset protection",
        "planning_types": ["tax", "banking", "legal"],
        "icon": "shield"
    },
    "wealth": {
        "title": "Wealth Management",
        "description": "Tax optimization, investment visas, golden visas, banking",
        "planning_types": ["tax", "visa", "banking", "business"],
        "icon": "trending-up"
    },
    "retirement": {
        "title": "Retirement",
        "description": "Pension transfers, retirement visas, healthcare, quality of life",
        "planning_types": ["visa", "healthcare", "housing", "tax"],
        "icon": "sun"
    },
    "digital-nomad": {
        "title": "Digital Nomad",
        "description": "Remote work visas, coworking, internet quality, nomad communities",
        "planning_types": ["visa", "tax", "housing"],
        "icon": "laptop"
    },
    "lifestyle": {
        "title": "Lifestyle Change",
        "description": "Quality of life, climate, culture, expat communities",
        "planning_types": ["housing", "healthcare", "visa"],
        "icon": "heart"
    },
    "new-start": {
        "title": "Fresh Start",
        "description": "New beginning, career change, adventure, lower cost of living",
        "planning_types": ["visa", "housing", "tax"],
        "icon": "rocket"
    },
    "family": {
        "title": "Family Relocation",
        "description": "Schools, family visas, healthcare, child-friendly areas",
        "planning_types": ["visa", "education", "healthcare", "housing"],
        "icon": "users"
    }
}


def extract_country_guide_data(response_text: str) -> Dict[str, Any]:
    """
    Extract structured JSON data from country guide response.

    Looks for ---COUNTRY GUIDE DATA--- section with motivations, facts, FAQ, etc.
    """
    guide_data = {
        "overview": {
            "headline": "",
            "intro": "",
            "quick_stats": []
        },
        "motivations": [],
        "faq": [],
        "sources": [],
        "facts": {},
        "four_act_content": []
    }

    # Find structured data section
    match = re.search(r'---\s*COUNTRY\s*GUIDE\s*DATA\s*---\s*```json\s*(.+?)\s*```', response_text, re.DOTALL | re.IGNORECASE)

    if not match:
        # Try without code fence
        header_match = re.search(r'---\s*COUNTRY\s*GUIDE\s*DATA\s*---\s*', response_text, re.IGNORECASE)
        if header_match:
            start_pos = header_match.end()
            brace_pos = response_text.find('{', start_pos)
            if brace_pos != -1:
                depth = 0
                end_pos = brace_pos
                for i, char in enumerate(response_text[brace_pos:], start=brace_pos):
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            end_pos = i + 1
                            break
                if depth == 0:
                    json_str = response_text[brace_pos:end_pos]
                    match = type('Match', (), {'group': lambda self, n: json_str})()

    if match:
        json_str = match.group(1).strip()
        try:
            data = json.loads(json_str)
            guide_data.update(data)
        except json.JSONDecodeError:
            # Try to fix common JSON issues
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            try:
                data = json.loads(json_str)
                guide_data.update(data)
            except:
                pass

    return guide_data


@activity.defn
async def generate_country_guide_content(
    country_name: str,
    country_code: str,
    research_context: Dict[str, Any],
    seo_keywords: Optional[Dict[str, Any]] = None,
    target_word_count: int = 4000
) -> Dict[str, Any]:
    """
    Generate comprehensive country guide content covering all 8 motivations.

    Args:
        country_name: Country name (e.g., "Cyprus")
        country_code: ISO 3166-1 alpha-2 code (e.g., "CY")
        research_context: Research data including visa info, tax rates, cost of living
        seo_keywords: Optional SEO research from DataForSEO
        target_word_count: Target word count for the guide

    Returns:
        Dict with title, slug, content, payload (matching [country].astro expectations)
    """
    activity.logger.info(f"Generating country guide for {country_name} ({country_code})")

    # Build SEO keyword guidance
    seo_guidance = ""
    if seo_keywords:
        primary = seo_keywords.get("primary_keywords", [])[:5]
        questions = seo_keywords.get("questions", [])[:10]
        if primary:
            keywords_list = ", ".join([k.get("keyword", "") for k in primary])
            seo_guidance = f"""
===== SEO KEYWORD TARGETING =====
PRIMARY KEYWORDS: {keywords_list}
QUESTIONS TO ANSWER: {[q.get("keyword", "") for q in questions]}

Include these keywords naturally in headings and content.
"""

    # Build system prompt for country guide
    system_prompt = f"""You are an expert relocation consultant writing a comprehensive guide for {country_name}.

===== INTERNATIONAL PERSPECTIVE =====
This guide serves an INTERNATIONAL English-speaking audience, primarily:
- **UK citizens** - Address UK-specific concerns (NHS vs private healthcare, UK tax treaties, pension transfers from UK)
- **US citizens** - Address US-specific concerns (FATCA, US tax obligations abroad, social security totalization)
- **Other English-speaking expats** - Include relevant info for Australians, Canadians, Irish, etc.

When discussing tax, visas, or financial matters:
- Mention differences between UK and US citizens where relevant
- Note any bilateral tax treaties with UK and USA
- Include examples of real expats from different countries
- Consider both "leaving the UK" and "leaving the US" perspectives

===== FINANCE & WEALTH FOCUS =====
This guide is ALSO used for financial planning. Include comprehensive coverage of:
- Banking options for non-residents and new residents
- Investment opportunities and restrictions
- Property purchase rules for foreigners
- Tax optimization strategies (legal)
- Wealth protection and trust structures
- Currency considerations and money transfer

===== 8 RELOCATION MOTIVATIONS =====
Cover ALL 8 motivations with equal depth and authority:
1. CORPORATE - Company-sponsored moves, business visas, corporate tax
2. TRUST - Asset protection, estate planning, trust structures
3. WEALTH - Tax optimization, golden visas, investment options, banking
4. RETIREMENT - Retirement visas, pension transfers, healthcare, quality of life
5. DIGITAL-NOMAD - Remote work visas, coworking spaces, nomad communities, internet
6. LIFESTYLE - Quality of life, climate, culture, expat communities
7. NEW-START - Fresh beginning, career change, adventure, cost savings
8. FAMILY - Schools, family visas, healthcare for kids, child-friendly areas

Write with authority. Be specific. Use real data. Cite sources.

===== OUTPUT FORMAT =====

Start with:
TITLE: {country_name} Relocation Guide 2025: Complete Guide for Every Situation
META: Comprehensive {country_name} relocation guide covering visas, tax, cost of living, healthcare, and more for corporate transfers, digital nomads, retirees, and families.
SLUG: {country_name.lower().replace(' ', '-')}-relocation-guide

Then write COMPREHENSIVE HTML content with Tailwind CSS:

<p class="text-lg text-gray-700 leading-relaxed mb-6">
  Strong intro paragraph about {country_name} as a relocation destination...
</p>

For EACH of the 8 motivations, write a detailed section:

<section id="corporate" class="mb-12">
  <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Corporate Relocation to {country_name}</h2>
  <p class="text-gray-700 leading-relaxed mb-4">Detailed content...</p>

  <h3 class="text-xl font-semibold text-gray-800 mt-6 mb-3">Visa Options for Corporate Transfers</h3>
  <p class="text-gray-700 leading-relaxed mb-4">Content with <a href="URL" class="text-blue-600 hover:text-blue-800 underline" target="_blank">source links</a>...</p>

  <h3 class="text-xl font-semibold text-gray-800 mt-6 mb-3">Corporate Tax Structure</h3>
  ...
</section>

{seo_guidance}

===== CONTENT REQUIREMENTS =====

1. **MINIMUM {target_word_count} WORDS** - This must be comprehensive
2. **8 MOTIVATION SECTIONS** - Each motivation gets its own <section id="motivation-id">
3. **PLANNING SUBSECTIONS** - Each motivation section has H3 subsections for:
   - Visa options (requirements, costs, processing time)
   - Tax implications (rates, deductions, treaties)
   - Cost of living (housing, healthcare, daily expenses)
   - Practical considerations (banking, healthcare access, language)
4. **RICH SOURCE LINKS** - Every paragraph needs source citations
5. **SPECIFIC DATA** - Real numbers: tax rates, visa costs, income requirements, processing times
6. **AVOID AI PHRASES** - No "dive into", "leverage", "unlock", etc.

===== WRITING STYLE =====
- Professional but accessible
- Use contractions (it's, don't, won't)
- Short paragraphs (2-3 sentences max)
- Bold key statistics: <strong>12.5% corporate tax</strong>
- Use blockquotes for key quotes or warnings
- Lists for requirements and steps

===== REQUIRED SECTIONS =====
After the 8 motivation sections, include:

<h2>Frequently Asked Questions</h2>
Answer 10-15 common questions about relocating to {country_name}.

<h2>Sources & References</h2>
List all sources used with URLs.

===== STRUCTURED DATA (REQUIRED) =====

After all content, include this JSON block:

---COUNTRY GUIDE DATA---
```json
{{
  "overview": {{
    "headline": "{country_name}: [Compelling tagline]",
    "intro": "2-3 sentence summary of {country_name} as a relocation destination",
    "quick_stats": ["Key stat 1", "Key stat 2", "Key stat 3", "Key stat 4"]
  }},
  "motivations": [
    {{
      "id": "corporate",
      "title": "Corporate Relocation",
      "relevance_score": 85,
      "summary": "One paragraph summary of corporate relocation to {country_name}",
      "planning_sections": {{
        "visa": {{
          "title": "Corporate Visa Options",
          "content": "Summary of visa options for corporate transfers",
          "key_facts": ["Fact 1", "Fact 2", "Fact 3"]
        }},
        "tax": {{
          "title": "Corporate Tax Structure",
          "content": "Summary of corporate tax benefits",
          "key_facts": ["12.5% corporate tax", "Fact 2"]
        }}
      }}
    }},
    // ... repeat for all 8 motivations
  ],
  "facts": {{
    "income_tax_rate": "Actual rate or range",
    "corporate_tax_rate": "Actual rate",
    "dn_visa_duration": "Duration if applicable",
    "dn_visa_cost": "Cost if applicable",
    "dn_visa_income_requirement": "Requirement if applicable",
    "cost_of_living_single": "Monthly range",
    "cost_of_living_family": "Monthly range for family",
    "healthcare_quality": "Brief assessment",
    "english_proficiency": "Level",
    "climate": "Brief description",
    "golden_visa_investment": "Minimum if applicable",
    "retirement_visa_income": "Requirement if applicable",
    "property_purchase_foreigners": "Rules",
    "timezone": "UTC offset",
    "internet_speed": "Average Mbps"
  }},
  "faq": [
    {{"q": "Question about {country_name}?", "a": "Detailed answer..."}},
    // ... 10-15 FAQs
  ],
  "sources": [
    {{"name": "Source Name", "url": "https://...", "description": "Brief description"}},
    // ... all sources used
  ],
  "four_act_content": [
    {{
      "act": 1,
      "title": "Why {country_name}? The Appeal",
      "factoid": "Key statistic about {country_name}",
      "four_act_visual_hint": "45-55 word cinematic scene: [Beautiful establishing shot of {country_name}, camera movement, lighting, atmosphere]"
    }},
    {{
      "act": 2,
      "title": "The Opportunity: What {country_name} Offers",
      "factoid": "Key benefit statistic",
      "four_act_visual_hint": "45-55 word scene showing opportunity/possibility"
    }},
    {{
      "act": 3,
      "title": "Making the Move: The Journey",
      "factoid": "Practical statistic (visa processing, etc.)",
      "four_act_visual_hint": "45-55 word scene showing transition/action"
    }},
    {{
      "act": 4,
      "title": "Life in {country_name}: The Payoff",
      "factoid": "Quality of life statistic",
      "four_act_visual_hint": "45-55 word scene showing successful new life"
    }}
  ]
}}
```
"""

    # Build research prompt
    research_prompt = f"""Write a comprehensive relocation guide for {country_name}.

RESEARCH DATA:
{json.dumps(research_context, indent=2, default=str)[:50000]}

Use ALL of this research. Be specific. Include real numbers, dates, and requirements.
Every claim needs a source link. This guide should be the definitive resource for anyone considering {country_name}."""

    # Generate with Gemini (primary) or Claude (fallback)
    # Prefer Gemini for cost efficiency and consistency with article generation
    use_gemini = bool(config.GOOGLE_API_KEY)

    if use_gemini:
        activity.logger.info("Using AI: google:gemini-2.5-pro-preview")
        genai.configure(api_key=config.GOOGLE_API_KEY)

        model = genai.GenerativeModel(
            model_name='gemini-2.5-pro-preview-06-05',
            system_instruction=system_prompt
        )

        response = model.generate_content(
            research_prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=16000,
                temperature=0.7
            )
        )

        response_text = response.text
    else:
        # Fallback to Claude
        activity.logger.info("Using AI: anthropic:claude-sonnet-4 (fallback)")
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            system=system_prompt,
            messages=[{"role": "user", "content": research_prompt}]
        )

        response_text = response.content[0].text

    # Log response length for debugging
    ai_provider = "Gemini" if use_gemini else "Claude"
    activity.logger.info(f"{ai_provider} response received: {len(response_text)} chars")
    activity.logger.info(f"First 500 chars: {response_text[:500]}")

    # Parse response - look for TITLE: anywhere in first 20 lines
    lines = response_text.strip().split('\n')
    title = ""
    meta = ""
    slug = ""

    for line in lines[:20]:
        line_stripped = line.strip()
        if line_stripped.startswith("TITLE:"):
            title = line_stripped.replace("TITLE:", "").strip()
        elif line_stripped.startswith("META:"):
            meta = line_stripped.replace("META:", "").strip()
        elif line_stripped.startswith("SLUG:"):
            slug = line_stripped.replace("SLUG:", "").strip()

    activity.logger.info(f"Parsed metadata - Title: '{title[:50]}...', Slug: '{slug}'")

    # Extract HTML content - try multiple patterns
    content = ""

    # Pattern 1: Between SLUG: and ---COUNTRY GUIDE DATA---
    content_match = re.search(r'SLUG:.*?\n(.+?)---COUNTRY GUIDE DATA---', response_text, re.DOTALL)
    if content_match:
        content = content_match.group(1).strip()
        activity.logger.info(f"Pattern 1 matched: {len(content)} chars")

    # Pattern 2: Between SLUG: and ```json (if no marker)
    if not content:
        content_match = re.search(r'SLUG:.*?\n(.+?)```json', response_text, re.DOTALL)
        if content_match:
            content = content_match.group(1).strip()
            activity.logger.info(f"Pattern 2 matched: {len(content)} chars")

    # Pattern 3: Everything after SLUG: line until we hit JSON-like content
    if not content:
        slug_match = re.search(r'SLUG:.*?\n', response_text)
        if slug_match:
            after_slug = response_text[slug_match.end():]
            # Find where JSON starts
            json_start = after_slug.find('{"')
            if json_start == -1:
                json_start = after_slug.find('---')
            if json_start > 100:  # At least some content
                content = after_slug[:json_start].strip()
                activity.logger.info(f"Pattern 3 matched: {len(content)} chars")

    # Pattern 4: Look for first <section or <p tag and extract from there
    if not content:
        html_match = re.search(r'(<(?:section|p|div)[^>]*>.*)', response_text, re.DOTALL)
        if html_match:
            html_content = html_match.group(1)
            # Cut at JSON data marker
            json_marker = html_content.find('---COUNTRY GUIDE DATA---')
            if json_marker > 0:
                content = html_content[:json_marker].strip()
            else:
                json_marker = html_content.find('```json')
                if json_marker > 0:
                    content = html_content[:json_marker].strip()
                else:
                    content = html_content.strip()
            activity.logger.info(f"Pattern 4 (HTML tags) matched: {len(content)} chars")

    # Fallback: Use full response minus metadata
    if not content:
        activity.logger.warning("No content pattern matched - using full response as fallback")
        # Remove the first few metadata lines
        content_lines = []
        found_content = False
        for line in lines:
            if found_content:
                content_lines.append(line)
            elif line.strip().startswith('<') or (not any(line.startswith(p) for p in ['TITLE:', 'META:', 'SLUG:', '---'])):
                found_content = True
                content_lines.append(line)
        content = '\n'.join(content_lines)
        # Cut at JSON data marker
        json_marker = content.find('---COUNTRY GUIDE DATA---')
        if json_marker > 0:
            content = content[:json_marker].strip()

    # Extract structured data
    guide_data = extract_country_guide_data(response_text)
    activity.logger.info(f"Extracted guide data: {len(guide_data.get('motivations', []))} motivations, {len(guide_data.get('faq', []))} FAQs")

    # Validate we got real content
    word_count = len(content.split()) if content else 0
    if word_count < 500:
        activity.logger.error(f"CONTENT GENERATION FAILED: Only {word_count} words generated (minimum 500)")
        activity.logger.error(f"Full response for debugging: {response_text[:2000]}...")
        raise ValueError(
            f"Country guide generation failed - only {word_count} words. "
            f"Expected 4000+. Claude may not have followed the format. "
            f"Check logs for full response."
        )

    # Generate title if not parsed
    if not title:
        title = f"{country_name} Relocation Guide 2025: Complete Guide for Every Situation"
        activity.logger.warning(f"Title not parsed, using default: {title}")

    # Build payload matching [country].astro expectations
    payload = {
        "title": title,
        "slug": slug or slugify(f"{country_name}-relocation-guide"),
        "content": content,
        "excerpt": meta or f"Comprehensive guide to relocating to {country_name}.",
        "meta_description": (meta or f"Complete {country_name} relocation guide")[:160],
        "article_type": "country_guide",
        "country_code": country_code,
        "guide_type": "country_comprehensive",
        "word_count": word_count,
        # Country guide specific payload
        "overview": guide_data.get("overview", {}),
        "motivations": guide_data.get("motivations", []),
        "faq": guide_data.get("faq", []),
        "sources": guide_data.get("sources", []),
        "four_act_content": guide_data.get("four_act_content", []),
        # Facts for countries.facts JSONB
        "extracted_facts": guide_data.get("facts", {})
    }

    activity.logger.info(f"✅ Generated {country_name} guide: {word_count} words, {len(guide_data.get('motivations', []))} motivations")

    return payload


@activity.defn
async def extract_country_facts(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract facts from country guide payload for countries.facts JSONB.

    Args:
        payload: Country guide payload with extracted_facts

    Returns:
        Dict of facts ready for countries.facts update
    """
    activity.logger.info("Extracting country facts from guide payload")

    # Get extracted facts from generation
    facts = payload.get("extracted_facts", {})

    # Also extract from motivations for backup
    motivations = payload.get("motivations", [])
    for mot in motivations:
        if mot.get("id") == "digital-nomad":
            planning = mot.get("planning_sections", {})
            visa = planning.get("visa", {})
            if visa.get("key_facts"):
                for fact in visa["key_facts"]:
                    if "€" in fact or "$" in fact:
                        if "cost" in fact.lower():
                            facts.setdefault("dn_visa_cost", fact)
                        elif "income" in fact.lower() or "requirement" in fact.lower():
                            facts.setdefault("dn_visa_income_requirement", fact)
                    if "year" in fact.lower() or "month" in fact.lower():
                        facts.setdefault("dn_visa_duration", fact)

    # Ensure we have the basics
    required_keys = [
        "income_tax_rate", "corporate_tax_rate", "cost_of_living_single",
        "healthcare_quality", "english_proficiency", "climate"
    ]

    for key in required_keys:
        if key not in facts:
            facts[key] = "N/A"

    activity.logger.info(f"Extracted {len(facts)} facts")
    return facts


@activity.defn
async def generate_country_video_prompt(
    country_name: str,
    four_act_content: List[Dict[str, Any]]
) -> str:
    """
    Generate 4-act video prompt from country guide content.

    Args:
        country_name: Country name for context
        four_act_content: List of 4 act dicts with four_act_visual_hint

    Returns:
        Combined video prompt string
    """
    activity.logger.info(f"Generating video prompt for {country_name}")

    if not four_act_content or len(four_act_content) < 4:
        activity.logger.warning("Insufficient four_act_content, using fallback")
        return f"""4-ACT COUNTRY SHOWCASE VIDEO FOR {country_name.upper()}:

ACT 1 (0-3s) THE DRAW: Sweeping aerial of {country_name}'s most iconic landscape, golden hour light, camera slowly pushing forward. Warm Mediterranean tones, cinematic lens flare.

ACT 2 (3-6s) THE OPPORTUNITY: Modern professional working at laptop in beautiful {country_name} cafe or coworking space, soft natural light streaming in, camera orbits slowly. Teal and warm tones.

ACT 3 (6-9s) THE JOURNEY: Montage feel - person walking through charming streets, exploring markets, settling into new apartment. Tracking shot, vibrant colors, documentary style.

ACT 4 (9-12s) THE NEW LIFE: Happy expat enjoying life - beach sunset, rooftop dinner, or community gathering. Pull back to wide shot, golden hour, lens flare, satisfying conclusion.

STYLE: Cinematic, warm color grade, smooth camera movements, shallow depth of field.
NO TEXT/LOGOS."""

    # Build from four_act_content
    prompts = []
    for i, act in enumerate(four_act_content[:4]):
        act_num = i + 1
        start_time = i * 3
        end_time = (i + 1) * 3
        hint = act.get("four_act_visual_hint", "")
        title = act.get("title", f"Act {act_num}")

        prompts.append(f"""ACT {act_num} ({start_time}-{end_time}s) {title.upper()}:
{hint}""")

    video_prompt = f"""4-ACT COUNTRY SHOWCASE VIDEO FOR {country_name.upper()}:

{chr(10).join(prompts)}

STYLE: Cinematic, warm color grade, smooth camera movements, shallow depth of field.
CRITICAL: NO text, words, letters, numbers, signs, or logos anywhere in the video."""

    activity.logger.info(f"Generated video prompt: {len(video_prompt)} chars")
    return video_prompt
