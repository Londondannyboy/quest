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


def get_mode_specific_prompt(
    mode: str,
    country_name: str,
    voices: List[Dict[str, Any]]
) -> str:
    """
    Get mode-specific writing instructions for Story/Guide/YOLO modes.

    Args:
        mode: One of "story", "guide", "yolo"
        country_name: Country name for context
        voices: List of extracted voices from curation

    Returns:
        Mode-specific prompt additions
    """
    # Format voices for prompts
    voices_text = ""
    if voices:
        for v in voices[:10]:
            voice_type = v.get("type", "unknown")
            source = v.get("source", "Unknown")
            quote = v.get("quote", "")
            stance = v.get("stance", "neutral")
            insight = v.get("key_insight", "")
            voices_text += f"\n- [{voice_type.upper()}] {source} ({stance}): \"{quote[:200]}...\" - Insight: {insight}"

    if mode == "story":
        return f"""
===== STORY MODE: NARRATIVE WRITING STYLE =====

Write this guide as a NARRATIVE JOURNEY - like a documentary or travel memoir.
The reader is the protagonist considering a life change.

**NARRATIVE STRUCTURE:**
- Open with a scene: "The fluorescent lights flicker as another grey London morning bleeds into afternoon..."
- Use second-person ("you") to draw the reader in
- Build emotional arc: Frustration → Discovery → Possibility → Transformation
- Weave facts into story naturally ("You learn that the D7 visa costs just €90...")
- Use sensory details: sounds, smells, visuals of {country_name}
- End sections with forward momentum

**INCORPORATING VOICES:**
Weave these real voices into your narrative as blockquotes and personal anecdotes:
{voices_text if voices_text else "No voices available - create compelling narrative arc"}

Use blockquotes for impact:
<blockquote class="border-l-4 border-blue-500 pl-4 italic my-4">
  "Quote from expat or expert..."
  <cite class="block text-sm text-gray-500 mt-2">— Attribution</cite>
</blockquote>

**TONE:**
- Warm, empathetic, slightly wistful
- Literary but accessible (Malcolm Gladwell meets travel memoir)
- Build tension and release
- End with hope and possibility

**EXAMPLE OPENING:**
"It starts, as these things often do, with a grey morning. You're scrolling through your phone on the Northern Line,
faces illuminated by screen glow, rain streaking the windows above. €900 for a one-bedroom flat. 52% marginal tax.
And then you see it: a photo of golden beaches, white villages tumbling down hillsides, and a headline that reads
'{country_name}: The Digital Nomad's Mediterranean Secret.' Something shifts."
"""

    elif mode == "guide":
        return f"""
===== GUIDE MODE: PRACTICAL REFERENCE STYLE =====

Write this as a COMPREHENSIVE REFERENCE GUIDE - think government handbook meets expert consultation.
The reader wants facts, costs, timelines, and checklists.

**STRUCTURE:**
- Start with TL;DR summary box at the top of each section
- Use tables for comparisons (tax rates, visa costs, etc.)
- Numbered/bulleted lists for requirements and steps
- Clear headings and subheadings for scannability
- Cost breakdowns with exact figures

**INCORPORATING VOICES:**
Add "What Expats Say" testimonial boxes throughout:
{voices_text if voices_text else "No voices available - focus on factual content"}

Use testimonial cards:
<div class="bg-blue-50 border border-blue-200 rounded-lg p-4 my-4">
  <p class="text-blue-800">"Quote from expat..."</p>
  <p class="text-sm text-blue-600 mt-2">— Name, Background</p>
</div>

**FORMAT REQUIREMENTS:**
- Quick Summary boxes at section starts
- Comparison tables where applicable
- Step-by-step numbered lists
- Cost calculators/breakdowns
- Timeline estimates
- Checklist formats for requirements

**EXAMPLE OPENING:**
"## Quick Summary: {country_name} at a Glance

| Factor | Details |
|--------|---------|
| Digital Nomad Visa | €90 application, €760/month minimum income |
| Processing Time | 60-90 days |
| Tax Rate | 20% flat rate for NHR |
| Cost of Living | €1,500-2,500/month single |
| Healthcare | SNS public + private options |

**Bottom Line:** {country_name} offers one of Europe's most accessible relocation paths with favorable tax treatment and low cost of living."

**TONE:**
- Professional, authoritative, trustworthy
- Data-driven with specific numbers
- Balanced (pros AND cons)
- Practical and actionable
"""

    elif mode == "yolo":
        return f"""
===== YOLO MODE: PROVOCATIVE ACTION-ORIENTED STYLE =====

Write this as a MOTIVATIONAL KICK IN THE PANTS - direct, provocative, action-oriented.
The reader is overthinking. You're cutting through the BS.

**YOLO CHARACTERISTICS:**
- Big bold declarations
- Call out the absurdity of staying put
- Direct comparisons that sting ("Your Zone 2 flat vs Mediterranean villa")
- Action-oriented CTAs throughout
- Humor and irreverence
- Real talk about risks AND rewards

**INCORPORATING VOICES:**
Use voices as social proof and "real talk" bullets:
{voices_text if voices_text else "No voices available - be the provocative voice yourself"}

Format as reality checks:
<div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 my-4">
  <p class="font-bold text-yellow-800">🔥 REAL TALK</p>
  <p class="text-yellow-700">"Everyone who moved said the same thing: why didn't I do this sooner?"</p>
</div>

**FORMAT REQUIREMENTS:**
- Bold declarative headers ("Just Book the Flight")
- Comparison callouts (London vs {country_name})
- Action buttons/CTAs throughout
- "Stop overthinking" moments
- Fun disclaimer at the end
- Energy and momentum

**EXAMPLE OPENING:**
"# Stop Scrolling. Start Living.

Your flat costs £2,100/month. For that privilege, you get:
- 149 days of sunshine (yes, really)
- A Northern Line commute with someone's armpit in your face
- 52% tax on anything you earn over £125k

Meanwhile, in {country_name}:
- 300+ days of sunshine
- A 3-bedroom villa with a pool for €1,200/month
- 20% flat tax rate (NHR program)
- Beaches. Everywhere.

**The only thing stopping you is... you.**

Let's break down exactly how to make this happen. No fluff. Just action."

**TONE:**
- Provocative but not reckless
- Energetic and punchy
- Humor with substance
- Direct address ("you need to...")
- Permission-giving ("It's okay to want more")

**END WITH:**
A fun disclaimer: "YOLO Mode is for inspiration. Please do actual research before selling your flat and booking a one-way ticket. But also... life is short. 🌊"
"""

    else:
        # Default to story mode
        return get_mode_specific_prompt("story", country_name, voices)


@activity.defn
async def generate_country_guide_content(
    country_name: str,
    country_code: str,
    research_context: Dict[str, Any],
    seo_keywords: Optional[Dict[str, Any]] = None,
    target_word_count: int = 4000,
    mode: str = "story",
    voices: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive country guide content covering all 8 motivations.

    Args:
        country_name: Country name (e.g., "Cyprus")
        country_code: ISO 3166-1 alpha-2 code (e.g., "CY")
        research_context: Research data including visa info, tax rates, cost of living
        seo_keywords: Optional SEO research from DataForSEO
        target_word_count: Target word count for the guide
        mode: Content mode - "story" (narrative), "guide" (practical), "yolo" (punchy)
        voices: Optional list of extracted voices from curation for enrichment

    Returns:
        Dict with title, slug, content, payload (matching [country].astro expectations)
    """
    activity.logger.info(f"Generating country guide for {country_name} ({country_code}) - MODE: {mode.upper()}")

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

    # Build guidance from DISCOVERED keywords and audiences
    # This is the key insight from DataForSEO Labs - what people ACTUALLY search for
    discovered_guidance = ""
    discovered_keywords = research_context.get("discovered_keywords", [])
    unique_audiences = research_context.get("unique_audiences", [])
    content_themes = research_context.get("content_themes", {})

    if discovered_keywords or unique_audiences:
        discovered_guidance = f"""
===== DISCOVERED SEARCH INTENT (CRITICAL) =====
These are ACTUAL search queries people use - your content MUST address these:

**TOP SEARCHED KEYWORDS:**
{chr(10).join(['- ' + kw for kw in discovered_keywords[:15]]) if discovered_keywords else '- No keywords discovered'}

**UNIQUE AUDIENCES TO ADDRESS:**
{chr(10).join(['- ' + (a.get("keyword", "") if isinstance(a, dict) else str(a)) + f' (volume: {a.get("volume", "?")})' for a in unique_audiences[:10]]) if unique_audiences else '- Standard UK/US expat audience'}

These audiences reveal GLOBAL interest - not just UK/US expats!
For example, if "portugal visa for indians" appears, include a dedicated section or FAQ for Indian nationals.
Address visa requirements, tax treaties, and practical considerations for EACH unique audience discovered.

**CONTENT THEMES BY SEARCH VOLUME:**
"""
        for theme, keywords in content_themes.items():
            if keywords:
                top_kws = [k.get("keyword", "") if isinstance(k, dict) else str(k) for k in keywords[:3]]
                discovered_guidance += f"- {theme.upper()}: {', '.join(top_kws)}\n"

        discovered_guidance += """
Structure your content to address these ACTUAL search intents, not assumed topics.
"""

    # Build PAA guidance - Google's "People Also Ask" questions
    paa_guidance = ""
    paa_questions = research_context.get("paa_questions", [])
    if paa_questions:
        paa_guidance = f"""
===== PEOPLE ALSO ASK (from Google SERP) =====
These are ACTUAL questions Google shows for {country_name} relocation searches.
Your FAQ section MUST answer these:

{chr(10).join(['- ' + q for q in paa_questions[:15]])}

These questions reveal what people REALLY want to know. Prioritize answering these in your FAQ section.
"""

    # Build AI Overview guidance - this is CRITICAL
    # Google's AI Overview contains structured info like "Family Reunification D6", "Healthcare SNS"
    ai_guidance = ""
    ai_sources = research_context.get("ai_overview_sources", [])
    if ai_sources:
        # Extract AI Overview text content
        ai_text_content = []
        ai_references = []

        for source in ai_sources:
            source_type = source.get("type", "")
            if source_type in ["ai_overview_content", "ai_overview_section"]:
                text = source.get("text", "")
                if text:
                    ai_text_content.append(text)
            elif source_type == "reference" and source.get("title"):
                ai_references.append(source.get("title", ""))

        if ai_text_content:
            ai_guidance = f"""
===== GOOGLE AI OVERVIEW (CRITICAL - USE THIS!) =====
This is what Google's AI says about {country_name} relocation.
It often contains VITAL topics we might miss (e.g., "Family Reunification D6 Visa", "Healthcare SNS system").

INCLUDE THESE TOPICS IN YOUR GUIDE:

{chr(10).join([text[:800] for text in ai_text_content[:5]])}

**AI Overview References:**
{chr(10).join(['- ' + ref for ref in ai_references[:8]])}

Ensure your guide covers ALL visa types mentioned (D7, D8, D6 Family Reunification, Golden Visa, Work Visas).
Ensure you cover Healthcare (SNS public system + private options).
"""
        elif ai_references:
            ai_guidance = f"""
===== AI OVERVIEW REFERENCES =====
Google's AI cites these sources - reference them:

{chr(10).join(['- ' + ref for ref in ai_references[:8]])}
"""

    # Build system prompt for country guide
    system_prompt = f"""You are an expert relocation consultant writing a comprehensive guide for {country_name}.

===== GLOBAL AUDIENCE (NOT JUST UK/US) =====
This guide serves a GLOBAL English-speaking audience:
- **UK citizens** - Address UK-specific concerns (NHS vs private healthcare, UK tax treaties, pension transfers)
- **US citizens** - Address US-specific concerns (FATCA, US tax obligations abroad, social security totalization)
- **Indian nationals** - If discovered in search data, address Indian visa requirements, tax treaties with India
- **Other nationalities** - Australians, Canadians, Irish, South Africans, Singaporeans, etc.

The world is moving around - not just British and Americans!
If keyword research reveals interest from specific nationalities (e.g., "portugal visa for indians"),
dedicate FAQ sections or subsections to those audiences.

{discovered_guidance}

{paa_guidance}

{ai_guidance}

===== CROSS-PLATFORM FOCUS =====
This guide serves multiple platforms:
- **relocation.quest** - Primary focus: comprehensive relocation guidance
- **placement.quest** - Job opportunities, career considerations, work permits
- **Rainmaker** - Finance, wealth management, investment opportunities

Balance the content to be holistic while keeping relocation as the core focus.

===== FINANCE & WEALTH FOCUS =====
This guide is ALSO used for financial planning. Include comprehensive coverage of:
- Banking options for non-residents and new residents
- Investment opportunities and restrictions
- Property purchase rules for foreigners
- Tax optimization strategies (legal)
- Wealth protection and trust structures
- Currency considerations and money transfer
- Mortgage and credit options for foreigners

===== PRACTICAL SETTLING-IN TOPICS (CRITICAL!) =====
These are topics competitors rank well for - MUST include:
- **Where to Live** - Compare top cities/regions for expats (NOT just the capital!):
  - Capital city pros/cons
  - Alternative cities (e.g., Chiang Mai not just Bangkok, Porto not just Lisbon, Barcelona not just Madrid)
  - Coastal vs inland, urban vs rural
  - Best areas for families, digital nomads, retirees
  - Cost of living comparison between cities
- **Pet Relocation** - How to bring pets (EU Pet Passport, microchipping, vaccinations, quarantine)
- **Driving License** - Converting foreign license, car purchase, insurance requirements
- **School Search** - International schools, public vs private, enrollment process, fees
- **Utilities Setup** - Electricity, water, gas, internet, mobile providers
- **Administrative Setup** - NIF (tax number), NISS (social security), healthcare registration
- **Professional Qualifications** - Recognition of foreign degrees and certifications
- **Insurance** - Health insurance options, home insurance, car insurance
- **Emergencies** - Local emergency numbers, embassy contacts, healthcare access
- **Returning to Home Country** - What to consider if plans change

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

{get_mode_specific_prompt(mode, country_name, voices or [])}

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
        activity.logger.info("Using AI: google:gemini-3-pro-preview")
        genai.configure(api_key=config.GOOGLE_API_KEY)

        model = genai.GenerativeModel(
            model_name='gemini-3-pro-preview',
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
        "content_mode": mode,  # story/guide/yolo
        # Country guide specific payload
        "overview": guide_data.get("overview", {}),
        "motivations": guide_data.get("motivations", []),
        "faq": guide_data.get("faq", []),
        "sources": guide_data.get("sources", []),
        "four_act_content": guide_data.get("four_act_content", []),
        # Facts for countries.facts JSONB
        "extracted_facts": guide_data.get("facts", {})
    }

    activity.logger.info(f"✅ Generated {country_name} guide [{mode.upper()} mode]: {word_count} words, {len(guide_data.get('motivations', []))} motivations")

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


# Segment video templates for multi-video country guides
# DETAILED PROMPTS - Cyprus style (50-60 words per act with camera, lighting, emotion)
SEGMENT_VIDEO_TEMPLATES = {
    "hero": {
        "title": "Your Journey to {country}",
        "style": "Cinematic, warm color grade, smooth camera movements, shallow depth of field",
        "preamble": "CRITICAL: NO clearly readable text, words, letters, signs, logos anywhere. Screens show abstract colors only. SAME SUBJECT throughout all 4 acts - follow ONE professional's journey. Cast: 30s professional, Mediterranean features, dark hair, casual smart clothing.",
        "acts": [
            {
                "title": "The London Grind",
                "hint": "Exhausted remote worker in cramped city flat stares at rain-streaked window, laptop glowing harsh blue. Camera pushes slowly to close-up as subject rubs temples, sighs deeply. Cool grey-blue tones, harsh fluorescent light. Documentary realism, shallow depth of field."
            },
            {
                "title": "The {country} Dream",
                "hint": "Same professional at home office bathed in warm lamplight, researching {country} on laptop screen showing abstract warm colors. Face transforms from fatigue to hope, gentle smile emerging. Golden hour light through window, colors shifting warm. Camera holds on emotional shift."
            },
            {
                "title": "The Journey",
                "hint": "Suitcase packing montage, hands folding summer clothes gently. Airport departure lounge glimpse, airplane window view of Mediterranean coastline approaching. Camera tracks alongside luggage, colors transitioning from grey urban to brilliant blue-gold Mediterranean light."
            },
            {
                "title": "{country} Success",
                "hint": "Professional works confidently on sunny {country} terrace overlooking scenic vista, laptop closed beside fresh coffee. Camera orbits slowly around subject enjoying genuine moment of satisfaction. Golden hour Mediterranean light, warm amber tones, local trees swaying gently."
            }
        ]
    },
    "family": {
        "title": "Family Life in {country}",
        "style": "Warm, personal, intimate lighting, handheld feel but stable, documentary authenticity",
        "preamble": "CRITICAL: NO clearly readable text, words, letters, signs, logos anywhere. SAME FAMILY throughout all 4 acts - follow ONE family's journey. Cast: parents (30s-40s), two children (ages 8 and 11), golden retriever. Mediterranean features, casual summer clothing.",
        "acts": [
            {
                "title": "School Morning",
                "hint": "Parent and child walking hand-in-hand toward modern international school gates in {country}. Other families visible in soft focus. Child looks up excitedly at new surroundings. Camera tracks alongside at child height. Warm golden morning light, green grounds, hopeful energy building."
            },
            {
                "title": "Weekend Adventures",
                "hint": "Golden retriever bounds across {country} beach, children chasing behind laughing. Parents watch contentedly from blanket. Camera follows dog in tracking shot, then pulls back to reveal whole family scene. Bright afternoon Mediterranean light, joyful energy, vibrant saturated colors."
            },
            {
                "title": "Healthcare Confidence",
                "hint": "Modern {country} clinic interior, parent sits calmly with child in clean waiting area. Friendly nurse approaches with warm smile, child relaxes visibly. Camera holds steady, capturing reassurance on faces. Soft clinical lighting with warm undertones, professional yet welcoming atmosphere."
            },
            {
                "title": "Family Table",
                "hint": "Outdoor terrace dinner scene as sun sets over {country} landscape. Family gathered around table laden with local dishes, grandmother passing plates. Laughter and animated conversation. Camera orbits slowly around table. Golden sunset light, warm amber tones, deep sense of belonging achieved."
            }
        ]
    },
    "finance": {
        "title": "Finance & Admin in {country}",
        "style": "Professional, clean, modern lighting, confident and capable, premium feel",
        "preamble": "CRITICAL: NO clearly readable text, words, letters, signs, logos anywhere. Documents show abstract patterns only. SAME SUBJECT throughout all 4 acts - follow ONE professional's admin journey. Cast: 40s professional, sharp business casual, confident posture, wedding ring visible.",
        "acts": [
            {
                "title": "Property Discovery",
                "hint": "Sunlight streams through floor-to-ceiling windows of modern {country} apartment. Professional explores space, hand trailing along marble countertop, gazing at scenic view. Real estate agent gestures expansively. Camera follows subject's eyeline to vista. Natural light flooding in, aspirational atmosphere, possibility palpable."
            },
            {
                "title": "Banking Partnership",
                "hint": "Clean modern {country} bank office, professional seated across from friendly banker. Documents with abstract patterns on polished desk. Banker explains enthusiastically, client nods with growing confidence. Handshake moment, genuine smiles. Camera holds on connection. Professional lighting, trust established."
            },
            {
                "title": "The Signature",
                "hint": "Close-up of confident hand signing important document with quality pen. Camera pulls back slowly to reveal bright {country} legal office, advisor nodding approvingly. Coffee cups, morning light through windows. Serious but positive expressions, milestone moment captured. Warm professional tones."
            },
            {
                "title": "Keys to New Life",
                "hint": "Person stands outside beautiful {country} property as agent hands over keys. Close-up of keys dropping into palm, then wide shot as new owner opens door. Light floods into frame revealing stunning interior. Camera pushes forward through doorway. Pure accomplishment, new chapter beginning."
            }
        ]
    },
    "daily": {
        "title": "Daily Life in {country}",
        "style": "Relaxed, documentary, natural light, slice-of-life authenticity, European cinema feel",
        "preamble": "CRITICAL: NO clearly readable text, words, letters, signs, logos anywhere. SAME SUBJECT throughout all 4 acts - follow ONE person's daily routine. Cast: 30s creative professional, relaxed linen clothing, content expression, comfortable in new environment.",
        "acts": [
            {
                "title": "Coastal Drive",
                "hint": "Dashboard POV driving along stunning {country} coastal road, turquoise sea glimpsed through window. Driver's hand relaxed on wheel, window down, warm breeze implied. Camera captures scenery passing, then subject's contented profile. Golden hour light, freedom feeling, colors shifting from road grey to ocean blue-gold."
            },
            {
                "title": "Making Home",
                "hint": "Bright {country} apartment being transformed into home. Hands carefully unpack books onto shelf, hang artwork on white wall, arrange plants on sunny windowsill. Camera follows hands intimately, then pulls back to reveal cozy space taking shape. Soft afternoon light, nesting energy, personal touches appearing."
            },
            {
                "title": "Market Rhythm",
                "hint": "Bustling {country} farmers market, subject selecting fresh produce, exchanging smile with vendor. Vibrant colors of fruits and vegetables fill frame. Camera moves through crowd at shoulder height, stopping as subject finds perfect tomatoes. Authentic atmosphere, belonging starting, Saturday morning ritual established."
            },
            {
                "title": "Neighborhood Regular",
                "hint": "Subject sits at favorite neighborhood cafe, laptop open, coffee arriving without ordering. Barista nods knowingly, subject waves to passing neighbor. Camera orbits slowly as local life flows around comfortable scene. Warm afternoon light, dappled shade, contentment achieved, new community embraced."
            }
        ]
    },
    "yolo": {
        "title": "YOLO Mode: Just Do It",
        "style": "FAST CUTS (0.5-1s per shot), energetic, shaky/tracking camera, high contrast, punchy colors",
        "preamble": "CRITICAL: NO text anywhere. SAME SUBJECT throughout all 4 acts - follow ONE person's spontaneous leap. Cast: late 20s, athletic build, determined expression, dressed for action. FAST PACED throughout Acts 1-3, then ONE slow-mo moment at the dive in Act 4.",
        "acts": [
            {
                "title": "Breaking Point",
                "hint": "Grey office cubicle, rain hammering window, subject slumps with head in hands. Harsh fluorescent flicker. SMASH CUT to hand slamming laptop shut. Eyes snap up with sudden determination. Camera shakes with energy burst. Cool grey tones exploding to warm flash. Transformation igniting. FAST: 0.5s cuts."
            },
            {
                "title": "The Sprint",
                "hint": "RAPID CUTS: Running through airport terminal, tracking shot. Hand grabs passport. Feet pound escalator. Bag hurled onto conveyor. Security sprint. Gate closing, just making it. Plane window, takeoff thrust. Clouds below. Each shot 0.75s. Urgent handheld camera. High contrast. No looking back. Momentum building."
            },
            {
                "title": "Arrival Montage",
                "hint": "RAPID CUTS: Wheels touchdown. {country} sun blasting through airplane window. Taxi weaving through new streets. Keys slapped into palm. Apartment door bursting open. Boxes being dragged in. Fridge stocked. Balcony discovered. View revealed. Each shot 0.75s. Pure momentum. Colors saturated. Energy peaking."
            },
            {
                "title": "The Leap",
                "hint": "Wide shot: subject sprints across empty {country} beach toward sea, arms pumping. Camera tracks alongside. Building speed. Then: SLOW MOTION as subject launches into Mediterranean dive, body suspended mid-air against blue sky. Underwater shot looking up through crystal water at sun. Pure bliss achieved. Serene resolution."
            }
        ]
    }
}


@activity.defn
async def generate_segment_video_prompt(
    country_name: str,
    segment: str,
    four_act_content: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate video prompt for a specific segment of the country guide.

    Uses detailed Cyprus-style prompts with:
    - 50-60 words per act
    - Specific camera movements, lighting, emotional beats
    - Preamble with critical NO TEXT instruction and cast guidance

    Args:
        country_name: Country name for context
        segment: One of "hero", "family", "finance", "daily", "yolo"
        four_act_content: Optional four_act_content from article (used for hero video)

    Returns:
        Dict with segment info and video_prompt
    """
    activity.logger.info(f"Generating {segment.upper()} video prompt for {country_name}")

    # Get template for this segment
    template = SEGMENT_VIDEO_TEMPLATES.get(segment)
    if not template:
        activity.logger.warning(f"Unknown segment '{segment}', falling back to hero")
        template = SEGMENT_VIDEO_TEMPLATES["hero"]

    # Get preamble and style
    preamble = template.get("preamble", "CRITICAL: NO clearly readable text, words, letters, signs, logos anywhere.")
    style = template["style"]
    title = template["title"].format(country=country_name)

    # Build act prompts
    prompts = []
    for i, act_template in enumerate(template["acts"]):
        act_num = i + 1
        start_time = i * 3
        end_time = (i + 1) * 3

        # Format title and hint with country name
        act_title = act_template["title"].format(country=country_name)
        hint = act_template["hint"].format(country=country_name)

        prompts.append(f"""ACT {act_num} ({start_time}s-{end_time}s): {act_title}
{hint}""")

    # Build full video prompt with preamble
    video_prompt = f"""{preamble}

VIDEO: 12 seconds, 4 acts × 3 seconds each.

{chr(10).join(prompts)}

STYLE: {style}"""

    activity.logger.info(f"Generated {segment} video prompt: {len(video_prompt)} chars")
    activity.logger.info(f"Prompt preview: {video_prompt[:200]}...")

    return {
        "segment": segment,
        "title": title,
        "video_prompt": video_prompt,
        "style": style,
        "cluster": "yolo" if segment == "yolo" else "story"
    }
