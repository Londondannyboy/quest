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
from src.utils.currency import get_currency_display_guidance, get_country_currency, get_currency_symbol


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


def detect_target_market(title: str, topic: str = "") -> str:
    """
    Detect target market from title/topic keywords for video prompt customization.

    Returns: 'indian', 'chinese', 'european', 'global'
    """
    text = f"{title} {topic}".lower()

    # Indian market indicators
    indian_keywords = ['indian', 'india', 'indians', 'delhi', 'mumbai', 'bangalore', 'indian expat', 'from india']
    if any(keyword in text for keyword in indian_keywords):
        return 'indian'

    # Chinese market indicators
    chinese_keywords = ['chinese', 'china', 'beijing', 'shanghai', 'chinese national', 'from china']
    if any(keyword in text for keyword in chinese_keywords):
        return 'chinese'

    # Default to European/global
    return 'european'


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
    voices: List[Dict[str, Any]],
    primary_slug: str = None,
    sibling_slugs: List[str] = None
) -> str:
    """
    Get mode-specific writing instructions for Story/Guide/YOLO modes.

    Args:
        mode: One of "story", "guide", "yolo"
        country_name: Country name for context
        voices: List of extracted voices from curation
        primary_slug: Primary cluster article slug for internal linking
        sibling_slugs: List of sibling article slugs for cross-linking

    Returns:
        Mode-specific prompt additions
    """
    # Build internal linking instructions (applies to ALL modes)
    internal_links_section = f"""

===== INTERNAL LINKS (Critical for SEO) =====

You MUST include 3-5 internal links naturally throughout the content:

**Required Links:**
- Link back to primary guide: /{primary_slug or country_name.lower() + '-relocation-guide'} (mention 1-2 times with descriptive anchor text)
"""

    if sibling_slugs:
        internal_links_section += f"""
**Cross-Link Opportunities (pick 2-3):**
{chr(10).join(f'- /{slug}' for slug in sibling_slugs[:5])}
"""

    internal_links_section += f"""
**Link Format:**
- SHORT anchor text (2-4 words): [practical guide](/slug) or [{country_name} visa guide](/slug)
- NOT long anchors like "our comprehensive guide to relocating to {country_name}"
- NOT generic: "click here" or "read more"
- Distribute naturally - don't cluster links together

**Example:** "For a detailed breakdown of visa costs, see our [complete {country_name} relocation guide](/{primary_slug or country_name.lower() + '-relocation-guide'})."
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
- Open with a scene: "The fluorescent lights flicker as another grey morning bleeds into afternoon..." (NO specific city - readers are global)
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
And then you see it: a photo of {country_name}'s iconic scenery - historic architecture, stunning landscapes, a life that feels different - and a headline that reads
'{country_name}: Europe's Best-Kept Secret.' Something shifts."
""" + internal_links_section

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
""" + internal_links_section

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
- Comparison callouts (vs major cities relevant to the destination region)
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
""" + internal_links_section

    elif mode == "voices":
        return f"""
===== VOICES MODE: TESTIMONIAL & COMMUNITY STYLE =====

**MANDATORY DISCLAIMER:** Start the article with this exact disclaimer block (copy verbatim):

<div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-8">
  <p class="text-sm text-gray-700">
    <strong>Note:</strong> The video above is AI-generated for visual storytelling.
    All experiences, quotes, and testimonials below are from real people who have
    relocated to {country_name} or are considering it. Sources include Reddit
    communities, expat forums, and verified media interviews.
  </p>
</div>

**PRIMARY FOCUS:** This is about REAL PEOPLE and their REAL EXPERIENCES. The expat voices ARE the content.

**STRUCTURE:**
1. Opening: Set the scene - why these voices matter
2. Each major section features 2-3 testimonials as the centerpiece
3. Your commentary connects and contextualizes the voices
4. Let the expats speak for themselves through extended quotes

**INCORPORATING VOICES - THESE ARE YOUR STARS:**
{voices_text if voices_text else "No voices available - create fictional but realistic testimonials"}

**FORMATTING VOICES:**
Use blockquote format for every testimonial:

> "Quote from expat goes here - make it substantial, 2-3 sentences minimum."
> — **Name**, relocated from [Country] in [Year]

**SECTION STRUCTURE:**
Each H2 section should:
1. Brief intro (1-2 sentences max)
2. 2-3 testimonial blockquotes
3. Brief synthesis (1-2 sentences connecting them)
4. Transition to next theme

**THEMES TO EXPLORE:**
- First impressions & arrival stories
- The bureaucracy battles (visas, paperwork)
- Finding community & making friends
- Cost of living reality checks
- Work & career adjustments
- Culture shock moments
- What they wish they knew before
- Would they do it again?

**CONTENT REQUIREMENTS:**
**INCLUDE:**
- Direct quotes from Reddit posts and expat forums (attribute as "Reddit user", "Expat forum member")
- Before/after transformation stories
- Specific challenges people faced and how they overcame them
- Cultural adjustment experiences
- Practical day-to-day life observations
- Honest pros and cons from real people

**EXCLUDE (These belong in Guide mode, NOT Voices):**
- Expert legal/tax advice
- Official government statements
- Dry factual information about visa requirements
- Statistical data without personal context
- Corporate immigration lawyer opinions
- Government policy explanations

**TONE:**
- Warm and personal
- Documentary authenticity
- Community-focused ("you're not alone")
- Encouraging but honest
- Let struggles be voiced alongside wins
- Authentic, empathetic, balanced (both positive and negative experiences)

**AVOID:**
- Generic advice without personal stories
- Your opinions overshadowing expat voices
- Sanitizing the difficult parts
- Making it feel corporate or promotional
- Expert opinions or professional advice
- Factual visa/tax information (save for Guide mode)
""" + internal_links_section

    else:
        # Default to story mode
        return get_mode_specific_prompt("story", country_name, voices, primary_slug, sibling_slugs)


@activity.defn
async def generate_country_guide_content(
    country_name: str,
    country_code: str,
    research_context: Dict[str, Any],
    seo_keywords: Optional[Dict[str, Any]] = None,
    target_word_count: int = 4000,
    mode: str = "story",
    voices: Optional[List[Dict[str, Any]]] = None,
    primary_slug: Optional[str] = None,
    sibling_slugs: Optional[List[str]] = None
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
{chr(10).join(['- ' + (a.get("keyword", "") if isinstance(a, dict) else str(a)) + f' (volume: {a.get("volume", "?")})' for a in unique_audiences[:10]]) if unique_audiences else '- Global expat audience (US, UK, EU, India, SE Asia, Commonwealth)'}

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

===== GLOBAL AUDIENCE - INTERNATIONAL POSITIONING (CRITICAL!) =====
This guide serves a GLOBAL English-speaking audience. DO NOT write from a UK-centric perspective!

**MANDATORY: Include dedicated sections for EACH major source region:**

🇺🇸 **US CITIZENS SECTION** (largest English-speaking expat source)
- FATCA compliance and US tax obligations abroad (you're taxed on worldwide income!)
- Social Security Totalization Agreements - which countries have them
- Medicare doesn't cover you abroad - insurance options
- 401k/IRA considerations when moving abroad
- State tax obligations (some states tax you even after leaving)
- Renouncing citizenship tax implications (exit tax)

🇬🇧 **UK/IRISH CITIZENS SECTION**
- NHS entitlements abroad (S1 form, GHIC card for EU)
- UK State Pension abroad - where it's frozen vs indexed
- UK tax treaties with destination country
- ISA and pension transfer options
- Post-Brexit rights in EU countries

🇪🇺 **EU/EEA CITIZENS SECTION** (they have FREE MOVEMENT rights within EU!)
- Freedom of movement within EU - registration not visa required
- Posted Workers rules for employment
- EU healthcare card (EHIC/GHIC) coverage
- Pension coordination between EU states
- Schengen vs non-Schengen considerations

🇮🇳 **SOUTH ASIAN CITIZENS SECTION** (India, Pakistan, Bangladesh, Sri Lanka, Nepal)
- Visa requirements specific to Indian passport holders (often more restrictive)
- OCI card holders - special considerations
- Tax treaty between India and destination country
- NRI status and FEMA compliance
- Popular expat hubs for South Asians in that country
- Community networks and cultural considerations

🇵🇭 **SOUTHEAST ASIAN CITIZENS SECTION** (Philippines, Vietnam, Indonesia, Malaysia, Thailand)
- Visa requirements for SE Asian passport holders
- OFW (Overseas Filipino Worker) specific guidance where relevant
- Remittance and money transfer options
- Embassy and consulate locations
- Existing SE Asian communities in destination

🇦🇺 **COMMONWEALTH CITIZENS SECTION** (Australia, New Zealand, Canada, South Africa)
- Working Holiday Visas where applicable
- Commonwealth pension arrangements
- Healthcare reciprocal agreements
- Easier pathways (some countries favor Commonwealth citizens)

🌍 **MIDDLE EAST EXPATS** (UAE, Saudi, Qatar residents looking to relocate)
- Tax-free savings considerations
- End of service gratuity planning
- Property investment from GCC countries
- Popular destinations for Gulf expats

**IMPORTANT:** Every major section (Visa, Tax, Healthcare, etc.) should include
nationality-specific callout boxes or subsections. Example format:
"📍 **For US Citizens:** Note that FATCA requires..."
"📍 **For Indian Nationals:** The visa process requires..."
"📍 **For EU Citizens:** You have automatic right to..."

The world is relocating - Americans to Portugal, Indians to UAE to Europe,
Filipinos everywhere, Brits post-Brexit exploring options, EU citizens using
their freedom of movement. Serve ALL of them!

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

{get_currency_display_guidance(country_name)}

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

===== CONTENT REQUIREMENTS (CRITICAL - READ CAREFULLY) =====

**ABSOLUTE MINIMUM: {target_word_count} WORDS TOTAL**
This is NON-NEGOTIABLE. Content under this threshold is UNUSABLE.

**SECTION DEPTH REQUIREMENTS:**
1. **8 MOTIVATION SECTIONS** - Each motivation gets its own <section id="motivation-id">
   - **EACH motivation section MUST be 400-600 words minimum**
   - This means 8 sections × 500 avg = 4000+ words just for motivations
   - Thin sections are REJECTED - write comprehensively!

2. **PLANNING SUBSECTIONS** - Each motivation section MUST have detailed H3 subsections:
   - Visa options (requirements, costs, processing time) - 100+ words
   - Tax implications (rates, deductions, treaties) - 100+ words
   - Cost of living (housing, healthcare, daily expenses) - 100+ words
   - Practical considerations (banking, healthcare access, language) - 100+ words

3. **DEPTH OVER BREADTH** - Better to write MORE about each topic than to skim surfaces
   - Include real examples, case studies, specific scenarios
   - Compare with UK/US baselines for context
   - Address common questions within each section
   - Include practical tips and insider knowledge

4. **RICH SOURCE LINKS** - EVERY fact, statistic, or claim needs a source citation
   - Minimum 20-30 external links throughout the article
   - Every paragraph with factual content MUST have at least 1-2 source links
5. **SPECIFIC DATA** - Real numbers: tax rates, visa costs, income requirements, processing times
6. **AVOID AI PHRASES** - No "dive into", "leverage", "unlock", etc.

**QUALITY CHECK:** Before finishing, mentally verify each motivation section has substantial content.
If any section feels thin (under 300 words), EXPAND IT with more detail, examples, and data.

===== WRITING STYLE & FORMATTING =====
- Professional but accessible
- Use contractions (it's, don't, won't)
- **CRITICAL: Short paragraphs (2-3 sentences max)**
- **LINE BREAKS: Add `<br>` or new `<p>` after every 2 sentences** - especially in first 2 paragraphs
- Bold key statistics: <strong>12.5% corporate tax</strong>
- Use blockquotes for key quotes or warnings
- Lists for requirements and steps
- **Visual components**: Use callout boxes, stat highlights, comparison tables frequently

===== EXTERNAL LINKS (CRITICAL - Back Up Every Claim) =====

**Every factual claim MUST have a source link.** When you state a tax rate, visa requirement, cost, or statistic, link to the source.

**Link Format:**
- Use SHORT anchor text (2-4 words max): [19% tax rate](url) NOT [Slovakia has a corporate tax rate of 19%](url)
- Link the specific fact, not generic text: [€5,500 minimum](url) NOT [click here](url)
- Inline links, naturally placed where the fact appears

**Required Sources Per Section:**
- Tax rates → Link to tax authority or reputable tax site
- Visa requirements → Link to government immigration site
- Cost of living → Link to Numbeo, Expatistan, or official stats
- Healthcare → Link to official health ministry or WHO
- Statistics → Link to source (Eurostat, World Bank, etc.)

**Examples:**
✅ "Slovakia offers a [19% flat tax](https://taxfoundation.org/slovakia-tax) for individuals."
✅ "The minimum bank balance is [€5,500](https://mzv.sk/business-visa)."
❌ "Slovakia has low taxes." (no source)
❌ "[Click here for more information about tax rates](url)" (bad anchor text)

**Minimum: 20-30 external source links throughout the article.** More is better - link every fact!

{get_mode_specific_prompt(mode, country_name, voices or [], primary_slug, sibling_slugs)}

===== REQUIRED SECTIONS =====
After the 8 motivation sections, include:

<h2>Frequently Asked Questions</h2>
Answer 10-15 common questions about relocating to {country_name}.

<h2>Sources & References</h2>
List ALL sources cited in the article. Format:
- [Source Name](URL) - Brief description of what this source covers
Include at least 8-12 authoritative sources (government sites, official statistics, reputable publications).

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
      "four_act_visual_hint": "45-55 word cinematic scene showing AUTHENTIC {country_name} landscape (see geography notes below)"
    }},
    {{
      "act": 2,
      "title": "The Opportunity: What {country_name} Offers",
      "factoid": "Key benefit statistic",
      "four_act_visual_hint": "45-55 word scene showing opportunity in AUTHENTIC {country_name} setting"
    }},
    {{
      "act": 3,
      "title": "Making the Move: The Journey",
      "factoid": "Practical statistic (visa processing, etc.)",
      "four_act_visual_hint": "45-55 word scene showing transition/action in recognizable {country_name} location"
    }},
    {{
      "act": 4,
      "title": "Life in {country_name}: The Payoff",
      "factoid": "Quality of life statistic",
      "four_act_visual_hint": "45-55 word scene showing successful new life in AUTHENTIC {country_name} environment"
    }}
  ]

  **CRITICAL: GEOGRAPHIC ACCURACY FOR VISUAL HINTS**
  Visual hints MUST reflect {country_name}'s ACTUAL geography and landmarks:

  - **Landlocked countries** (Slovakia, Austria, Switzerland, Czech Republic, Hungary): NO beaches, oceans, or coastal scenes!
    Use: mountains, castles, historic old towns, alpine meadows, rivers, vineyards, forests
  - **Coastal countries** (Portugal, Spain, Croatia, Greece): Can use beaches AND historic towns, coastal cliffs
  - **Nordic countries** (Norway, Sweden, Finland): Fjords, northern lights, forests, modern cities
  - **Tropical destinations** (Thailand, Bali, Mexico): Beaches appropriate, but include temples, rice terraces, markets

  For {country_name}, think about its ICONIC features:
  - Capital city landmarks, historic architecture
  - Natural landscapes unique to this country
  - Seasonal characteristics (Mediterranean sun, alpine snow, etc.)
  - Cultural settings (cafes, markets, festivals)

  NEVER use generic "beach/ocean" scenes unless {country_name} actually has significant coastline!
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

    # Validate we got real content - require substantial depth
    word_count = len(content.split()) if content else 0
    if word_count < 2500:
        activity.logger.error(f"CONTENT GENERATION FAILED: Only {word_count} words generated (minimum 2500 required)")
        activity.logger.error(f"Full response for debugging: {response_text[:2000]}...")
        raise ValueError(
            f"Country guide generation failed - only {word_count} words. "
            f"Expected 4000+, minimum 2500 for usable content. "
            f"Retry will generate more comprehensive content."
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

ACT 4 (9-12s) THE NEW LIFE: Happy expat enjoying life in authentic {country_name} setting - use iconic local scenery (mountain vista, historic town square, vineyard terrace, or coastline only if coastal country). Pull back to wide shot, golden hour, lens flare, satisfying conclusion.

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


# ============================================================================
# COUNTRY LANDMARKS DATABASE
# ============================================================================
# Iconic landmarks for video prompts - ensures geographically accurate visuals

COUNTRY_LANDMARKS = {
    # Central Europe
    'slovakia': {
        'landmarks': ['Bratislava Castle on the Danube', 'High Tatras mountains', 'Spiš Castle ruins', 'Devín Castle'],
        'scenery': 'Carpathian mountain peaks, medieval castle ruins, Danube riverside',
        'is_landlocked': True,
    },
    'slovenia': {
        'landmarks': ['Lake Bled with island church', 'Ljubljana castle', 'Triglav mountain', 'Postojna Cave'],
        'scenery': 'Alpine lakes, Julian Alps, emerald rivers, coastal Piran',
        'is_landlocked': False,
    },
    'czech republic': {
        'landmarks': ['Prague Castle and Charles Bridge', 'Old Town Square astronomical clock', 'Český Krumlov'],
        'scenery': 'Gothic spires, red rooftops, Vltava River, Bohemian countryside',
        'is_landlocked': True,
    },
    'czechia': {  # Alias
        'landmarks': ['Prague Castle and Charles Bridge', 'Old Town Square astronomical clock', 'Český Krumlov'],
        'scenery': 'Gothic spires, red rooftops, Vltava River, Bohemian countryside',
        'is_landlocked': True,
    },
    'austria': {
        'landmarks': ['Vienna Schönbrunn Palace', 'Salzburg fortress', 'Hallstatt village', 'Austrian Alps'],
        'scenery': 'Alpine peaks, baroque palaces, crystal lakes, Sound of Music hills',
        'is_landlocked': True,
    },
    'switzerland': {
        'landmarks': ['Matterhorn peak', 'Lake Geneva', 'Zurich old town', 'Lucerne Chapel Bridge'],
        'scenery': 'Snow-capped Alps, pristine lakes, chocolate-box villages, mountain railways',
        'is_landlocked': True,
    },
    'hungary': {
        'landmarks': ['Budapest Parliament on Danube', 'Buda Castle', 'Fisherman\'s Bastion', 'Chain Bridge'],
        'scenery': 'Danube river views, thermal baths, Hungarian plains, baroque architecture',
        'is_landlocked': True,
    },
    'poland': {
        'landmarks': ['Kraków Wawel Castle', 'Warsaw Old Town', 'Gdańsk waterfront', 'Tatra Mountains'],
        'scenery': 'Medieval squares, Gothic churches, Baltic coast, mountain resorts',
        'is_landlocked': False,
    },
    'germany': {
        'landmarks': ['Brandenburg Gate Berlin', 'Neuschwanstein Castle', 'Munich Marienplatz', 'Cologne Cathedral'],
        'scenery': 'Historic city squares, fairy-tale castles, Rhine Valley, Bavarian Alps',
        'is_landlocked': False,
    },

    # Western Europe
    'france': {
        'landmarks': ['Eiffel Tower Paris', 'Arc de Triomphe', 'Mont Saint-Michel', 'French Riviera'],
        'scenery': 'Parisian boulevards, lavender fields Provence, Mediterranean coast, Loire châteaux',
        'is_landlocked': False,
    },
    'uk': {
        'landmarks': ['Big Ben and Houses of Parliament', 'Tower Bridge London', 'Edinburgh Castle', 'Stonehenge'],
        'scenery': 'London skyline, rolling green hills, historic castles, coastal cliffs',
        'is_landlocked': False,
    },
    'united kingdom': {
        'landmarks': ['Big Ben and Houses of Parliament', 'Tower Bridge London', 'Edinburgh Castle', 'Stonehenge'],
        'scenery': 'London skyline, rolling green hills, historic castles, coastal cliffs',
        'is_landlocked': False,
    },
    'ireland': {
        'landmarks': ['Cliffs of Moher', 'Dublin Temple Bar', 'Ring of Kerry', 'Giant\'s Causeway'],
        'scenery': 'Emerald green hills, dramatic Atlantic cliffs, cozy pubs, ancient ruins',
        'is_landlocked': False,
    },
    'netherlands': {
        'landmarks': ['Amsterdam canals and bridges', 'Windmills at Kinderdijk', 'Rijksmuseum', 'tulip fields'],
        'scenery': 'Canal houses, cycling paths, tulip fields, flat polders with windmills',
        'is_landlocked': False,
    },
    'belgium': {
        'landmarks': ['Brussels Grand Place', 'Bruges medieval center', 'Ghent canals', 'Atomium'],
        'scenery': 'Cobblestone squares, Gothic belfries, chocolate shops, medieval architecture',
        'is_landlocked': False,
    },

    # Southern Europe
    'spain': {
        'landmarks': ['Sagrada Familia Barcelona', 'Alhambra Granada', 'Plaza Mayor Madrid', 'Park Güell'],
        'scenery': 'Mediterranean beaches, Moorish palaces, vibrant plazas, Andalusian white villages',
        'is_landlocked': False,
    },
    'portugal': {
        'landmarks': ['Belém Tower Lisbon', 'Sintra palaces', 'Porto Ribeira', 'Algarve cliffs'],
        'scenery': 'Atlantic coastline, tiled façades, hilltop castles, golden beaches',
        'is_landlocked': False,
    },
    'italy': {
        'landmarks': ['Colosseum Rome', 'Venice canals', 'Florence Duomo', 'Amalfi Coast'],
        'scenery': 'Renaissance piazzas, Mediterranean coast, Tuscan hills, ancient ruins',
        'is_landlocked': False,
    },
    'greece': {
        'landmarks': ['Acropolis Athens', 'Santorini white domes', 'Mykonos windmills', 'Meteora monasteries'],
        'scenery': 'Aegean blue waters, whitewashed villages, ancient temples, island sunsets',
        'is_landlocked': False,
    },
    'cyprus': {
        'landmarks': ['Paphos archaeological park', 'Kyrenia harbor', 'Troodos mountains', 'Aphrodite\'s Rock'],
        'scenery': 'Mediterranean beaches, mountain villages, ancient ruins, citrus groves',
        'is_landlocked': False,
    },
    'malta': {
        'landmarks': ['Valletta harbor', 'Mdina silent city', 'Blue Lagoon Comino', 'St John\'s Co-Cathedral'],
        'scenery': 'Honey-colored limestone, azure Mediterranean, fortified harbors, baroque churches',
        'is_landlocked': False,
    },
    'croatia': {
        'landmarks': ['Dubrovnik Old Town walls', 'Plitvice Lakes', 'Split Diocletian\'s Palace', 'Hvar harbor'],
        'scenery': 'Adriatic coastline, medieval walled cities, cascading waterfalls, island hopping',
        'is_landlocked': False,
    },

    # Nordic
    'sweden': {
        'landmarks': ['Stockholm Gamla Stan', 'Icehotel Jukkasjärvi', 'Gothenburg archipelago', 'Northern Lights Lapland'],
        'scenery': 'Archipelago islands, midnight sun, snowy forests, minimalist design',
        'is_landlocked': False,
    },
    'norway': {
        'landmarks': ['Bergen Bryggen wharf', 'Geirangerfjord', 'Oslo Opera House', 'Lofoten Islands'],
        'scenery': 'Dramatic fjords, Northern Lights, fishing villages, midnight sun',
        'is_landlocked': False,
    },
    'denmark': {
        'landmarks': ['Copenhagen Nyhavn', 'Tivoli Gardens', 'Little Mermaid statue', 'Kronborg Castle'],
        'scenery': 'Colorful harbors, hygge culture, cycling city, coastal dunes',
        'is_landlocked': False,
    },
    'finland': {
        'landmarks': ['Helsinki Cathedral', 'Santa Claus Village Rovaniemi', 'Suomenlinna fortress', 'Finnish Lakeland'],
        'scenery': 'Thousand lakes, Northern Lights, saunas, snowy forests',
        'is_landlocked': False,
    },
    'iceland': {
        'landmarks': ['Blue Lagoon', 'Hallgrímskirkja Reykjavik', 'Gullfoss waterfall', 'Northern Lights'],
        'scenery': 'Volcanic landscapes, geysers, glaciers, dramatic waterfalls',
        'is_landlocked': False,
    },

    # Eastern Europe
    'romania': {
        'landmarks': ['Bran Castle (Dracula\'s Castle)', 'Bucharest Palace of Parliament', 'Peleș Castle', 'Transylvania villages'],
        'scenery': 'Carpathian mountains, painted monasteries, medieval fortresses, Danube Delta',
        'is_landlocked': False,
    },
    'bulgaria': {
        'landmarks': ['Rila Monastery', 'Sofia Alexander Nevsky Cathedral', 'Plovdiv Old Town', 'Black Sea coast'],
        'scenery': 'Mountain monasteries, Black Sea beaches, rose valleys, Thracian tombs',
        'is_landlocked': False,
    },

    # Baltic
    'estonia': {
        'landmarks': ['Tallinn Old Town', 'Kadriorg Palace', 'Lahemaa National Park', 'Saaremaa island'],
        'scenery': 'Medieval spires, digital society, Baltic coast, forest trails',
        'is_landlocked': False,
    },
    'latvia': {
        'landmarks': ['Riga Art Nouveau district', 'Jurmala beach', 'Rundāle Palace', 'Gauja National Park'],
        'scenery': 'Art Nouveau architecture, Baltic beaches, pine forests, castles',
        'is_landlocked': False,
    },
    'lithuania': {
        'landmarks': ['Vilnius Old Town', 'Trakai Island Castle', 'Hill of Crosses', 'Curonian Spit dunes'],
        'scenery': 'Baroque churches, lake castles, sand dunes, amber coast',
        'is_landlocked': False,
    },

    # Americas
    'usa': {
        'landmarks': ['New York Statue of Liberty', 'San Francisco Golden Gate Bridge', 'Grand Canyon', 'Miami Beach'],
        'scenery': 'Diverse landscapes from skyscrapers to national parks, coastal cities',
        'is_landlocked': False,
    },
    'canada': {
        'landmarks': ['Toronto CN Tower', 'Niagara Falls', 'Banff National Park', 'Vancouver harbor'],
        'scenery': 'Rocky Mountains, autumn forests, urban skylines, vast wilderness',
        'is_landlocked': False,
    },
    'mexico': {
        'landmarks': ['Chichen Itza pyramid', 'Mexico City Zócalo', 'Cancun beaches', 'Guanajuato colorful streets'],
        'scenery': 'Ancient ruins, colonial cities, Caribbean coast, desert landscapes',
        'is_landlocked': False,
    },

    # Asia-Pacific
    'japan': {
        'landmarks': ['Mount Fuji', 'Tokyo Tower', 'Kyoto temples', 'Osaka Castle'],
        'scenery': 'Cherry blossoms, ancient temples, neon cities, mountain landscapes',
        'is_landlocked': False,
    },
    'thailand': {
        'landmarks': ['Bangkok Grand Palace', 'Phi Phi Islands', 'Chiang Mai temples', 'Ayutthaya ruins'],
        'scenery': 'Golden temples, tropical beaches, floating markets, jungle landscapes',
        'is_landlocked': False,
    },
    'vietnam': {
        'landmarks': ['Ha Long Bay', 'Hanoi Old Quarter', 'Hoi An lanterns', 'Mekong Delta'],
        'scenery': 'Limestone karsts, rice terraces, colonial architecture, river life',
        'is_landlocked': False,
    },
    'australia': {
        'landmarks': ['Sydney Opera House', 'Great Barrier Reef', 'Uluru', 'Melbourne laneways'],
        'scenery': 'Iconic harbors, coral reefs, red outback, coastal beaches',
        'is_landlocked': False,
    },
    'new zealand': {
        'landmarks': ['Milford Sound', 'Auckland Sky Tower', 'Hobbiton', 'Queenstown mountains'],
        'scenery': 'Dramatic fjords, rolling green hills, volcanic landscapes, adventure sports',
        'is_landlocked': False,
    },

    # Middle East
    'uae': {
        'landmarks': ['Burj Khalifa Dubai', 'Sheikh Zayed Mosque Abu Dhabi', 'Palm Jumeirah', 'Dubai Marina'],
        'scenery': 'Futuristic skyline, desert dunes, luxury resorts, traditional souks',
        'is_landlocked': False,
    },
    'dubai': {  # Common search term
        'landmarks': ['Burj Khalifa', 'Palm Jumeirah', 'Dubai Marina', 'Burj Al Arab'],
        'scenery': 'Futuristic skyline, desert dunes, luxury beaches, gold souks',
        'is_landlocked': False,
    },
}


def get_country_landmarks(country_name: str) -> dict:
    """
    Get iconic landmarks and scenery for a country.

    Args:
        country_name: Country name to look up

    Returns:
        Dict with landmarks, scenery, and is_landlocked flag
        Falls back to generic if country not found
    """
    country_key = country_name.lower().strip()

    if country_key in COUNTRY_LANDMARKS:
        return COUNTRY_LANDMARKS[country_key]

    # Fallback for unknown countries
    return {
        'landmarks': [f'iconic {country_name} landmark', f'{country_name} historic center', f'{country_name} natural scenery'],
        'scenery': f'authentic {country_name} landscapes and architecture',
        'is_landlocked': False,  # Assume coastal by default (safer for video)
    }


# ============================================================================
# DYNAMIC COMPARISON CITIES BY REGION
# ============================================================================
# Returns relevant comparison cities based on destination country's region
# Ensures global representation without being UK-centric

REGION_COMPARISON_CITIES = {
    'europe': {
        'primary': ['New York', 'London', 'Sydney', 'Toronto'],
        'regional': ['Berlin', 'Amsterdam', 'Paris', 'Barcelona'],
        'global_south': ['Mumbai', 'Singapore', 'Dubai', 'São Paulo'],
    },
    'asia': {
        'primary': ['Singapore', 'Hong Kong', 'Tokyo', 'Sydney'],
        'regional': ['Mumbai', 'Bangkok', 'Kuala Lumpur', 'Shanghai'],
        'global_north': ['New York', 'London', 'San Francisco', 'Toronto'],
    },
    'middle_east': {
        'primary': ['Dubai', 'London', 'Singapore', 'New York'],
        'regional': ['Abu Dhabi', 'Doha', 'Riyadh', 'Mumbai'],
        'global': ['Hong Kong', 'Sydney', 'San Francisco', 'Toronto'],
    },
    'americas': {
        'primary': ['New York', 'Miami', 'Los Angeles', 'Toronto'],
        'regional': ['Mexico City', 'São Paulo', 'Buenos Aires', 'Santiago'],
        'global': ['London', 'Sydney', 'Singapore', 'Dubai'],
    },
    'oceania': {
        'primary': ['Sydney', 'Melbourne', 'Auckland', 'Singapore'],
        'regional': ['Brisbane', 'Perth', 'Wellington', 'Fiji'],
        'global': ['London', 'New York', 'Hong Kong', 'Los Angeles'],
    },
    'africa': {
        'primary': ['Cape Town', 'Johannesburg', 'Dubai', 'London'],
        'regional': ['Nairobi', 'Lagos', 'Cairo', 'Casablanca'],
        'global': ['New York', 'Mumbai', 'Singapore', 'Sydney'],
    },
}

COUNTRY_REGIONS = {
    # Europe
    'portugal': 'europe', 'spain': 'europe', 'france': 'europe', 'germany': 'europe',
    'italy': 'europe', 'greece': 'europe', 'croatia': 'europe', 'malta': 'europe',
    'cyprus': 'europe', 'netherlands': 'europe', 'belgium': 'europe', 'uk': 'europe',
    'united kingdom': 'europe', 'ireland': 'europe', 'poland': 'europe', 'czechia': 'europe',
    'austria': 'europe', 'switzerland': 'europe', 'hungary': 'europe', 'romania': 'europe',
    'bulgaria': 'europe', 'slovakia': 'europe', 'slovenia': 'europe', 'estonia': 'europe',
    'latvia': 'europe', 'lithuania': 'europe', 'finland': 'europe', 'sweden': 'europe',
    'norway': 'europe', 'denmark': 'europe', 'iceland': 'europe', 'montenegro': 'europe',
    # Asia
    'thailand': 'asia', 'vietnam': 'asia', 'indonesia': 'asia', 'bali': 'asia',
    'malaysia': 'asia', 'singapore': 'asia', 'philippines': 'asia', 'japan': 'asia',
    'south korea': 'asia', 'taiwan': 'asia', 'hong kong': 'asia', 'india': 'asia',
    'sri lanka': 'asia', 'nepal': 'asia', 'cambodia': 'asia', 'laos': 'asia',
    # Middle East
    'uae': 'middle_east', 'dubai': 'middle_east', 'qatar': 'middle_east',
    'saudi arabia': 'middle_east', 'bahrain': 'middle_east', 'oman': 'middle_east',
    'turkey': 'middle_east', 'israel': 'middle_east', 'jordan': 'middle_east',
    # Americas
    'usa': 'americas', 'canada': 'americas', 'mexico': 'americas', 'brazil': 'americas',
    'argentina': 'americas', 'colombia': 'americas', 'costa rica': 'americas',
    'panama': 'americas', 'ecuador': 'americas', 'chile': 'americas', 'peru': 'americas',
    # Oceania
    'australia': 'oceania', 'new zealand': 'oceania', 'fiji': 'oceania',
    # Africa
    'south africa': 'africa', 'mauritius': 'africa', 'morocco': 'africa',
    'kenya': 'africa', 'egypt': 'africa', 'nigeria': 'africa', 'ghana': 'africa',
}


def get_comparison_cities(country_name: str, exclude_self: bool = True) -> str:
    """
    Get dynamic comparison cities based on destination country's region.

    Returns a varied list of comparison cities that's globally representative
    and contextually relevant to the destination.

    Args:
        country_name: Destination country name
        exclude_self: Whether to exclude the destination from comparisons

    Returns:
        String of comparison cities for use in prompts
    """
    country_key = country_name.lower().strip()
    region = COUNTRY_REGIONS.get(country_key, 'europe')  # Default to europe
    cities_config = REGION_COMPARISON_CITIES.get(region, REGION_COMPARISON_CITIES['europe'])

    # Build varied comparison list
    comparison_cities = []

    # Add primary comparisons (always include major global hubs)
    comparison_cities.extend(cities_config['primary'][:2])

    # Add regional comparisons relevant to destination
    if 'regional' in cities_config:
        comparison_cities.extend(cities_config['regional'][:2])

    # Add global south/north for balance
    global_key = 'global_south' if region in ['europe', 'americas'] else 'global_north'
    if global_key not in cities_config:
        global_key = 'global'
    if global_key in cities_config:
        comparison_cities.extend(cities_config[global_key][:2])

    # Remove destination country's capital if present
    if exclude_self:
        # Filter out the destination country's likely capital
        comparison_cities = [c for c in comparison_cities if country_key not in c.lower()]

    # Return unique cities, max 5
    unique_cities = list(dict.fromkeys(comparison_cities))[:5]
    return ', '.join(unique_cities)


# ============================================================================
# CLIMATE-AWARE CLOTHING BRANDING
# ============================================================================
# Cold countries get Quest jacket/sweatshirt, warm countries get Quest t-shirt
# YOLO mode always gets the YOLO t-shirt (yellow letters) regardless of climate

COLD_COUNTRIES = [
    'russia', 'canada', 'norway', 'sweden', 'finland', 'iceland', 'denmark',
    'uk', 'united kingdom', 'ireland', 'germany', 'poland', 'netherlands',
    'belgium', 'austria', 'switzerland', 'czech republic', 'czechia', 'slovakia'
]


def get_clothing_prompt(country: str, mode: str) -> str:
    """
    Get climate-aware clothing instruction for video prompts.

    CRITICAL: Quest/YOLO branding ONLY in ACT 1 to avoid text corruption in later acts.
    Acts 2-4 use appropriate casual clothing without branding.

    Args:
        country: Country name
        mode: Content mode (story, guide, yolo, voices, nomad)

    Returns:
        Clothing instruction string for video prompt
    """
    is_cold = country.lower() in COLD_COUNTRIES

    if mode == "yolo":
        return """CLOTHING BY ACT (avoid text corruption):
ACT 1: Bright YOLO t-shirt with YELLOW letters clearly visible on chest.
ACTS 2-4: Athletic/adventure wear - running jacket, sports top, or casual tee. NO text, NO logos."""

    if mode == "nomad":
        # Digital nomad - younger, tech-casual, modern aesthetic
        return """CLOTHING BY ACT (avoid text corruption):
ACT 1: Quest t-shirt with 'QUEST' in WHITE letters, wireless earbuds visible.
ACTS 2-4: Tech-casual style - fitted hoodie, clean minimalist tee, smart-casual layers. NO text, NO logos. Modern digital nomad aesthetic."""

    if is_cold:
        return """CLOTHING BY ACT (avoid text corruption):
ACT 1: Quest jacket or sweatshirt with 'QUEST' in WHITE letters clearly visible.
ACTS 2-4: Stylish casual layers - sweater, cardigan, or blouse. NO text, NO logos, NO branding."""
    else:
        return """CLOTHING BY ACT (avoid text corruption):
ACT 1: Quest t-shirt with 'QUEST' in WHITE letters clearly visible on chest.
ACTS 2-4: Casual summer clothing - light blouse, sundress, or linen top. NO text, NO logos, NO branding."""


# ============================================================================
# VARIED OPENING SCENARIOS
# ============================================================================
# Not always "rain on window" - vary the city fatigue scene for diversity
import random

OPENING_SCENARIOS = [
    "staring at rain-streaked window, grey skies outside",
    "watching city traffic through foggy glass, endless headlights",
    "looking at crowded metro through apartment window, rush hour chaos",
    "gazing at grey office buildings from cramped desk, sterile environment",
    "watching sunset through smoggy city skyline, another day ending",
    "staring at snow flurries outside, winter blues setting in",
    "observing busy street below through dusty blinds, urban noise",
]


def get_varied_opening_scenario() -> str:
    """Get a varied opening scenario for video Act 1 (city grind scene)."""
    return random.choice(OPENING_SCENARIOS)


# ============================================================================
# SEGMENT VIDEO TEMPLATES - Mode-Specific Styles
# ============================================================================
# Each mode has distinct energy, pacing, camera style:
#
# | Mode   | Energy | Pacing     | Camera Style     | Clothing                    |
# |--------|--------|------------|------------------|-----------------------------|
# | Story  | Medium | Flowing    | Cinematic dolly  | Quest t-shirt/jacket        |
# | Guide  | Calm   | Methodical | Static/slow push | Quest t-shirt/jacket        |
# | YOLO   | High   | Quick cuts | Handheld/dynamic | YOLO t-shirt (yellow)       |
# | Voices | Warm   | Intimate   | Close-ups        | Casual (no branding)        |
#
# HARD SCENE CUTS: Use "shot cut —" between acts to prevent AI drift
#
# NOTE: Female subjects preferred - better AI generation results for relocation content

SEGMENT_VIDEO_TEMPLATES = {
    # ========================================================================
    # STORY MODE (Hero) - Cinematic, emotional journey
    # ========================================================================
    "hero": {
        "title": "Your Journey to {country}",
        "mode": "story",
        "style": "Cinematic, warm color grade, smooth dolly movements, shallow depth of field, flowing narrative",
        "energy": "medium",
        "preamble": """CRITICAL: NO text, words, letters, signs, logos anywhere. Screens show abstract colors only.
SAME SUBJECT throughout all 4 acts - follow ONE professional's journey.
Cast: 30s professional (preferably woman), warm features, natural beauty, approachable appearance.
{clothing}""",
        "acts": [
            {
                "title": "The City Grind",
                "hint": "MEDIUM SHOT, exhausted remote worker in cramped city flat, {opening_scenario}. Laptop glowing harsh blue. Camera PUSHES SLOWLY to close-up as subject rubs temples. Cool grey-blue tones, harsh fluorescent light. Could be any major city - generic urban fatigue."
            },
            {
                "title": "The {country} Dream",
                "hint": "DIFFERENT LOCATION: MEDIUM SHOT, same professional in cozy coffee shop or outdoor park bench, researching on phone (abstract warm colors on screen). Completely different setting from Act 1. Face transforms from curiosity to excitement, genuine smile emerging. Warm afternoon light, bokeh background. Camera HOLDS on hopeful expression."
            },
            {
                "title": "The Journey",
                "hint": "TRACKING SHOT, suitcase packing montage, hands folding clothes. Airport glimpse. Airplane window view of {travel_scenery}. Camera TRACKS alongside luggage. Colors transition grey to brilliant blue-gold."
            },
            {
                "title": "{country} Success",
                "hint": "WIDE to MEDIUM, professional on sunny {country} terrace WITH FRIENDS - two or three people laughing together, animated conversation, clinking glasses. Subject BEAMING with genuine joy, head thrown back in laughter. Camera ORBITS slowly around the happy group. Golden hour light, {scenery} and {landmark} visible in background, warm amber tones. Pure happiness achieved."
            }
        ]
    },

    # ========================================================================
    # GUIDE MODE - Methodical, instructional, calm
    # ========================================================================
    "guide": {
        "title": "Practical Guide to {country}",
        "mode": "guide",
        "style": "Clean, professional, static shots with slow pushes, methodical pacing, instructional feel",
        "energy": "calm",
        "preamble": """CRITICAL: NO text, words, letters, signs, logos anywhere. Documents show abstract patterns only.
SAME SUBJECT throughout all 4 acts - follow ONE professional completing admin tasks.
Cast: 35s professional (preferably woman), composed demeanor, confident, business casual attire.
{clothing}""",
        "acts": [
            {
                "title": "Research Phase",
                "hint": "STATIC WIDE SHOT, professional at clean desk with laptop, taking methodical notes. Organized workspace. Camera SLOWLY PUSHES IN over 3 seconds. Soft natural window light, calm atmosphere, focused energy."
            },
            {
                "title": "Documentation",
                "hint": "CLOSE-UP hands organizing documents (abstract patterns), then MEDIUM SHOT of professional reviewing papers calmly. Neat stacks, quality pen. Camera HOLDS STEADY. Professional lighting, organized efficiency."
            },
            {
                "title": "Official Process",
                "hint": "MEDIUM SHOT, professional in modern {country} government office, seated across from helpful official. Calm exchange, nodding understanding. Camera STATIC with subtle push. Clean institutional lighting, reassuring atmosphere."
            },
            {
                "title": "Task Complete",
                "hint": "WIDE SHOT, professional exits building into {country} sunshine, documents in hand, satisfied expression. Camera HOLDS as subject walks toward camera. Natural daylight, sense of accomplishment, methodical success."
            }
        ]
    },

    # ========================================================================
    # YOLO MODE - High energy, fast cuts, spontaneous
    # ========================================================================
    "yolo": {
        "title": "YOLO Mode: Just Do It",
        "mode": "yolo",
        "style": "FAST CUTS (0.5-1s per shot), energetic handheld, high contrast, punchy saturated colors",
        "energy": "high",
        "preamble": """CRITICAL: NO text anywhere except the YOLO shirt.
SAME SUBJECT throughout all 4 acts - follow ONE person's spontaneous leap.
Cast: late 20s (preferably woman), athletic build, determined expression, adventurous spirit.
{clothing}
PACING: FAST throughout Acts 1-3, then ONE slow-mo moment at the dive in Act 4.""",
        "acts": [
            {
                "title": "Breaking Point",
                "hint": "RAPID CUTS: Grey office cubicle, rain on window. Subject slumps, head in hands. SMASH CUT hand slams laptop. Eyes snap up with determination. Camera SHAKES. Cool grey EXPLODING to warm flash. 0.5s cuts."
            },
            {
                "title": "The Sprint",
                "hint": "RAPID CUTS 0.75s each: TRACKING through airport terminal. Hand grabs passport. Feet pound escalator. Bag on conveyor. Gate closing, just making it. Plane window, takeoff. Urgent HANDHELD. High contrast. Momentum building."
            },
            {
                "title": "Arrival Montage",
                "hint": "RAPID CUTS 0.75s each: Wheels touchdown. {country} sun blasting through window. Taxi weaving streets. Keys slapped into palm. Door bursting open. Boxes dragged in. Balcony discovered. SATURATED colors. Energy peaking."
            },
            {
                "title": "The Leap",
                "hint": "WIDE TRACKING: subject sprints through {scenery}. Building speed. Then SLOW MOTION as subject leaps joyfully near {landmark}, body suspended mid-air. Sun flare, pure freedom moment."
            }
        ]
    },

    # ========================================================================
    # VOICES MODE - Intimate, warm, testimonial feel
    # ========================================================================
    "voices": {
        "title": "Expat Voices from {country}",
        "mode": "voices",
        "style": "Intimate close-ups, warm natural lighting, documentary authenticity, personal connection",
        "energy": "warm",
        "preamble": """CRITICAL: NO text, words, letters, signs, logos anywhere.
MULTIPLE SUBJECTS - show different expats sharing their experiences.
Cast: Diverse group of 30s-50s expats, casual comfortable clothing, genuine expressions.
NO branded clothing - this is about authentic personal stories.""",
        "acts": [
            {
                "title": "Morning Rituals",
                "hint": "CLOSE-UP, expat's hands preparing local coffee in sunny {country} kitchen. Camera PULLS BACK to reveal warm smile, content expression. Morning light streaming in. Intimate documentary feel, slice of life."
            },
            {
                "title": "Community Connection",
                "hint": "MEDIUM SHOT, different expat chatting with local neighbor over garden fence, genuine laughter. Camera HOLDS on authentic interaction. Soft afternoon light, warm tones, real connection visible."
            },
            {
                "title": "Reflection Moment",
                "hint": "CLOSE-UP profile, third expat gazing at sunset over {landmark} from balcony, peaceful expression. Camera SLOWLY ORBITS to reveal contemplative face. {scenery} in golden hour light, warm amber tones, contentment evident."
            },
            {
                "title": "New Home",
                "hint": "WIDE to CLOSE, expat family gathered on {country} terrace, sharing meal, animated conversation. Camera PUSHES IN slowly on happy faces. Warm evening light, sense of belonging achieved, authentic joy."
            }
        ]
    },

    # ========================================================================
    # FAMILY MODE - Warm, personal, family journey
    # ========================================================================
    "family": {
        "title": "Family Life in {country}",
        "mode": "story",
        "style": "Warm, personal, intimate lighting, stable handheld, documentary authenticity",
        "energy": "medium",
        "preamble": """CRITICAL: NO text, words, letters, signs, logos anywhere.
SAME FAMILY throughout all 4 acts - follow ONE family's journey.
Cast: mother (30s-40s, warm and capable), father, two children (ages 8 and 11), golden retriever.
{clothing}""",
        "acts": [
            {
                "title": "School Morning",
                "hint": "TRACKING LOW ANGLE at child height, parent and child walking hand-in-hand toward modern school gates. Child looks up excitedly. Warm golden morning light, green grounds, hopeful energy."
            },
            {
                "title": "Weekend Adventures",
                "hint": "TRACKING SHOT, golden retriever bounds through {scenery}, children chasing. Camera follows dog, then PULLS BACK to reveal whole family with {landmark} in distance. Bright afternoon light, joyful energy."
            },
            {
                "title": "Healthcare Confidence",
                "hint": "MEDIUM SHOT, bright modern pediatric waiting room (NOT hospital), cheerful decor, toys visible. Parent and child sitting relaxed together, child playing happily. Friendly receptionist waves, routine check-up energy. Camera HOLDS STEADY. Natural daylight through large windows, positive atmosphere, zero medical emergency vibes."
            },
            {
                "title": "Family Table",
                "hint": "ORBITING SHOT, outdoor terrace dinner as sun sets over {country}. Family gathered around table, grandmother passing plates. Laughter. Golden sunset light, warm amber tones, belonging achieved."
            }
        ]
    },

    # ========================================================================
    # FINANCE MODE - Professional, confident
    # ========================================================================
    "finance": {
        "title": "Finance & Admin in {country}",
        "mode": "guide",
        "style": "Professional, clean, modern lighting, confident and capable, premium feel",
        "energy": "calm",
        "preamble": """CRITICAL: NO text, words, letters, signs, logos anywhere. Documents show abstract patterns only.
SAME SUBJECT throughout all 4 acts - follow ONE professional's admin journey.
Cast: 40s professional (preferably woman), sharp business casual, confident posture, accomplished demeanor.
{clothing}""",
        "acts": [
            {
                "title": "Property Discovery",
                "hint": "TRACKING SHOT, sunlight streams through modern {country} apartment windows. Professional explores, hand trails marble countertop, gazes at view. Camera FOLLOWS eyeline. Natural light flooding in, aspirational."
            },
            {
                "title": "Banking Partnership",
                "hint": "MEDIUM SHOT, clean modern bank office, professional across from friendly banker. Documents with abstract patterns. Handshake moment, genuine smiles. Camera HOLDS on connection. Professional lighting."
            },
            {
                "title": "The Signature",
                "hint": "CLOSE-UP, confident hand signs document with quality pen. Camera PULLS BACK to reveal bright {country} office, advisor nodding. Morning light through windows. Milestone moment, warm professional tones."
            },
            {
                "title": "Keys to New Life",
                "hint": "MEDIUM to WIDE, agent hands keys outside beautiful {country} property with {landmark} visible in background. Close-up keys dropping into palm. New owner opens door, light floods in. Camera PUSHES THROUGH doorway. Accomplishment achieved."
            }
        ]
    },

    # ========================================================================
    # DAILY MODE - Slice of life, relaxed
    # ========================================================================
    "daily": {
        "title": "Daily Life in {country}",
        "mode": "story",
        "style": "Relaxed, documentary, natural light, slice-of-life authenticity, European cinema feel",
        "energy": "medium",
        "preamble": """CRITICAL: NO text, words, letters, signs, logos anywhere.
SAME SUBJECT throughout all 4 acts - follow ONE person's daily routine.
Cast: 30s creative professional (preferably woman), relaxed linen clothing, content expression, natural beauty.
{clothing}""",
        "acts": [
            {
                "title": "Scenic Drive",
                "hint": "POV through windshield, driving scenic {country} road through {scenery}. Driver's hand relaxed on wheel, window down. Camera captures {landmark} in distance, then subject's contented profile. Golden hour, freedom."
            },
            {
                "title": "Making Home",
                "hint": "CLOSE-UP hands unpacking books, hanging artwork, arranging plants on windowsill. Camera FOLLOWS intimately, then PULLS BACK to reveal cozy space. Soft afternoon light, personal touches appearing."
            },
            {
                "title": "Market Rhythm",
                "hint": "TRACKING SHOT shoulder height through bustling {country} market. Subject selects produce, exchanges smile with vendor. Vibrant colors fill frame. Authentic atmosphere, belonging starting."
            },
            {
                "title": "Neighborhood Regular",
                "hint": "ORBITING SHOT, subject at favorite cafe, coffee arriving without ordering. Barista nods knowingly, subject waves to neighbor. Warm afternoon light, dappled shade, community embraced."
            }
        ]
    },

    # ========================================================================
    # NOMAD MODE - Digital nomad lifestyle, young tech professional
    # ========================================================================
    "nomad": {
        "title": "Digital Nomad Life in {country}",
        "mode": "nomad",
        "style": "Contemporary, tech-forward, lifestyle vlog aesthetic, natural handheld, Instagram-ready",
        "energy": "upbeat",
        "preamble": """CRITICAL: NO text, words, letters, signs, logos anywhere. Laptop screens show abstract colors only.
SAME SUBJECT throughout all 4 acts - follow ONE digital nomad's day.
Cast: Late 20s creative (preferably woman), casual smart style, modern haircut, always has laptop or phone.
{clothing}""",
        "acts": [
            {
                "title": "Morning Workflow",
                "hint": "TRACKING SHOT following subject through stylish {country} coworking space. Finds perfect spot by window with {landmark} view. Opens laptop (abstract colors on screen), puts on wireless earbuds. Modern industrial decor, great wifi vibes. Natural morning light, productive energy."
            },
            {
                "title": "Cafe Office",
                "hint": "DIFFERENT LOCATION: MEDIUM SHOT, subject settled in hip {country} cafe, laptop open, artisan coffee beside. Typing focused, then looks up with satisfied smile at surroundings. Exposed brick, plants, other remote workers in background. Afternoon light, community of nomads."
            },
            {
                "title": "Golden Hour Break",
                "hint": "TRACKING SHOT, subject walks through scenic {country} streets with phone, taking photos of {scenery}. Stops at viewpoint overlooking {landmark}. Posts something (abstract screen), gets instant reactions. Sunset colors, content creation vibes."
            },
            {
                "title": "Sunset Social",
                "hint": "WIDE to MEDIUM, rooftop bar or terrace WITH OTHER YOUNG NOMADS, laptops closed, drinks clinking. Subject LAUGHING with new friends, animated conversation. {landmark} glowing in background sunset. Genuine connections, living the dream, community found."
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

    Uses detailed prompts with:
    - 50-60 words per act
    - Specific camera movements, lighting, emotional beats
    - Hard scene cuts ("shot cut —") between acts to prevent AI drift
    - Climate-aware Quest/YOLO branding
    - Mode-specific energy and pacing

    Args:
        country_name: Country name for context
        segment: One of "hero", "guide", "yolo", "voices", "family", "finance", "daily"
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

    # Get mode for clothing selection
    mode = template.get("mode", "story")

    # Get climate-aware clothing prompt
    clothing_prompt = get_clothing_prompt(country_name, mode)

    # Get country-specific landmarks for geographically accurate videos
    landmarks_info = get_country_landmarks(country_name)
    primary_landmark = landmarks_info['landmarks'][0] if landmarks_info['landmarks'] else f"{country_name} landmark"
    scenery = landmarks_info['scenery']
    is_landlocked = landmarks_info.get('is_landlocked', False)

    # For landlocked countries, use mountains/nature instead of coast
    travel_scenery = "mountain peaks and alpine meadows" if is_landlocked else "Mediterranean coastline"

    activity.logger.info(f"Country landmarks: {primary_landmark}, scenery: {scenery[:50]}..., landlocked: {is_landlocked}")

    # Get preamble and format with clothing
    preamble_template = template.get("preamble", "CRITICAL: NO text, words, letters, signs, logos anywhere.")
    preamble = preamble_template.format(clothing=clothing_prompt)

    style = template["style"]
    energy = template.get("energy", "medium")
    title = template["title"].format(country=country_name)

    # Build act prompts with HARD SCENE CUTS between acts
    prompts = []
    for i, act_template in enumerate(template["acts"]):
        act_num = i + 1
        start_time = i * 3
        end_time = (i + 1) * 3

        # Format title and hint with country name AND landmark info
        act_title = act_template["title"].format(country=country_name)

        # Get varied opening scenario for Act 1 (city grind scene)
        opening_scenario = get_varied_opening_scenario()

        hint = act_template["hint"].format(
            country=country_name,
            landmark=primary_landmark,
            scenery=scenery,
            travel_scenery=travel_scenery,
            opening_scenario=opening_scenario
        )

        # Add hard scene cut marker before acts 2, 3, 4
        if i > 0:
            prompts.append("shot cut —")

        prompts.append(f"""ACT {act_num} ({start_time}s-{end_time}s): {act_title}
{hint}""")

    # Build full video prompt with preamble
    video_prompt = f"""{preamble}

VIDEO: 12 seconds, 4 acts × 3 seconds each. HARD CUTS between acts.
ENERGY: {energy.upper()}

{chr(10).join(prompts)}

STYLE: {style}"""

    activity.logger.info(f"Generated {segment} video prompt: {len(video_prompt)} chars")
    activity.logger.info(f"Prompt preview: {video_prompt[:200]}...")
    activity.logger.info(f"Mode: {mode}, Energy: {energy}, Clothing: {clothing_prompt[:50]}...")

    return {
        "segment": segment,
        "title": title,
        "video_prompt": video_prompt,
        "style": style,
        "mode": mode,
        "energy": energy,
        "cluster": "yolo" if segment == "yolo" else "story"
    }


# ============================================================================
# TOPIC CLUSTER CONTENT GENERATION
# ============================================================================
# Generate SEO-targeted content for specific keywords like "slovakia cost of living"

@activity.defn
async def generate_topic_cluster_content(
    country_name: str,
    country_code: str,
    target_keyword: str,
    keyword_volume: int,
    planning_type: str,
    research_context: Dict[str, Any],
    parent_slug: str
) -> Dict[str, Any]:
    """
    Generate SEO-targeted content for a specific keyword topic.

    Unlike general country guides, this focuses DEEPLY on one topic
    to capture search traffic for that specific keyword.

    Args:
        country_name: Country name (e.g., "Slovakia")
        country_code: ISO code (e.g., "SK")
        target_keyword: Exact keyword to target (e.g., "slovakia cost of living")
        keyword_volume: Monthly search volume
        planning_type: Category (housing, visa, tax, retirement, etc.)
        research_context: Shared research data from parent guide
        parent_slug: Slug of parent guide for internal linking

    Returns:
        Dict with content, excerpt, meta_description, faq, word_count
    """
    activity.logger.info(
        f"Generating topic cluster content: '{target_keyword}' for {country_name} "
        f"(vol={keyword_volume}, type={planning_type})"
    )

    # Build topic-specific system prompt
    system_prompt = f"""You are an SEO expert and relocation specialist writing a definitive guide
targeting the EXACT keyword: "{target_keyword}"

===== PRIMARY SEO TARGET =====
TARGET KEYWORD: {target_keyword}
SEARCH VOLUME: {keyword_volume}/month
PLANNING TYPE: {planning_type}

YOUR MISSION: Create THE definitive resource for "{target_keyword}" that will DOMINATE
search results. This article should be THE answer Google wants to show.

===== KEYWORD DENSITY REQUIREMENTS =====
- Use "{target_keyword}" EXACTLY as written in:
  - H1 title
  - First paragraph (first 100 words)
  - At least 2 H2 headings
  - Meta description
  - Naturally throughout (8-12 times total for 2000 words)
- Use VARIATIONS naturally:
  - "{country_name} cost of living" / "cost of living in {country_name}"
  - "{country_name} living costs" / "how much does it cost to live in {country_name}"

===== CONTENT STRUCTURE =====
1. **Hook paragraph** - Address search intent immediately. What does someone searching "{target_keyword}" want to know?
2. **Key data summary** - Table or bullet list with the MOST searched-for facts
3. **Deep sections** - 3-5 H2 sections covering all aspects of this topic
4. **Comparison data** - vs relevant global cities (use region-appropriate comparisons)
5. **NATIONALITY-SPECIFIC CALLOUTS** - Include callout boxes for different nationalities:
   - 📍 **For US Citizens:** (FATCA, tax obligations, SS totalization)
   - 📍 **For UK Citizens:** (NHS, Brexit implications, pension)
   - 📍 **For EU Citizens:** (freedom of movement rights)
   - 📍 **For Indian Nationals:** (specific visa requirements, tax treaties)
   - 📍 **For SE Asian Citizens:** (visa requirements, communities)
6. **FAQ section** - Answer "People Also Ask" questions for this keyword
7. **Internal links (3-5 total):**
   - Link to parent guide: /{parent_slug} (2 mentions with descriptive anchor text)
   - Cross-link to 1-2 related topic pages if contextually relevant
   - Use natural anchor text: "our [comprehensive {country_name} guide](/{parent_slug})" NOT "click here"

===== GLOBAL AUDIENCE (CRITICAL!) =====
This content serves a GLOBAL English-speaking audience - NOT UK-centric!
- **US Citizens** - Largest English-speaking expat population, address their specific concerns
- **Indian Nationals** - Growing expat population, often face stricter visa requirements
- **EU Citizens** - Have different rights (freedom of movement within EU)
- **UK Citizens** - Post-Brexit considerations
- **SE Asian Citizens** - Philippines, Vietnam, etc. - growing mobile workforce
- **Commonwealth** - Australia, Canada, South Africa, New Zealand

Every major section should consider: "How does this apply to someone from the US? From India? From the EU?"

===== WRITING STYLE =====
- INLINE CSS ONLY (no Tailwind classes)
- Data-driven: specific numbers, dates, costs
- Practical: actionable advice
- Authority: cite sources, be definitive
- GLOBAL perspective: address ALL major nationalities, not just UK/US

===== OUTPUT FORMAT =====
Start with metadata lines:
TITLE: [SEO-optimized title containing "{target_keyword}"]
META: [160-char meta description containing "{target_keyword}"]
EXCERPT: [2-sentence excerpt containing "{target_keyword}"]

Then write HTML content with INLINE STYLES:

<p style="font-size: 1.125rem; line-height: 1.75; color: #374151; margin-bottom: 1.5rem;">
Opening paragraph with {target_keyword}...
</p>

<h2 style="font-size: 1.5rem; font-weight: 700; color: #111827; margin-top: 2rem; margin-bottom: 1rem;">
Section Heading
</h2>

<table style="width: 100%; border-collapse: collapse; margin: 1.5rem 0;">
<tr style="background: #f9fafb;">
<th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid #e5e7eb;">Item</th>
<th style="padding: 0.75rem; text-align: right; border-bottom: 2px solid #e5e7eb;">Cost</th>
</tr>
...
</table>

End with JSON FAQ block:
---FAQ DATA---
```json
[
  {{"q": "How much does it cost to live in {country_name}?", "a": "..."}},
  ...
]
```
"""

    # Build research prompt with relevant context
    # Filter research_context to just the relevant planning_type data
    # Handle None values for planning_type and target_keyword
    planning_type_safe = planning_type or ""
    target_keyword_safe = target_keyword or ""

    relevant_context = {
        "country": country_name,
        "target_keyword": target_keyword,
        "planning_type": planning_type,
        "summaries": research_context.get("summaries", [])[:10],
        "crawled_sources": [
            s for s in research_context.get("crawled_sources", [])[:15]
            if planning_type_safe.lower() in str(s).lower() or target_keyword_safe.lower() in str(s).lower()
        ],
        "paa_questions": [
            q for q in research_context.get("paa_questions", [])[:20]
            if any(term in q.lower() for term in target_keyword_safe.lower().split()) if target_keyword_safe
        ],
        "seo_keywords": research_context.get("seo_keywords", [])[:10],
    }

    research_prompt = f"""Write a comprehensive, SEO-optimized article targeting: "{target_keyword}"

RESEARCH DATA (filtered for {planning_type}):
{json.dumps(relevant_context, indent=2, default=str)[:30000]}

REQUIREMENTS:
- MINIMUM 1500 words
- Mention "{target_keyword}" 8-12 times naturally
- Include comparison table vs relevant global cities for the destination region
- Include 5-8 FAQ questions
- Include 3-5 internal links total:
  - Link to /{parent_slug} at least 2 times with descriptive anchor text
  - Cross-link to related topics if relevant
- Use INLINE CSS only (no Tailwind classes)

Write with authority. This should be THE definitive resource for "{target_keyword}"."""

    # Generate with Gemini
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
                max_output_tokens=8000,
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
            max_tokens=8000,
            system=system_prompt,
            messages=[{"role": "user", "content": research_prompt}]
        )

        response_text = response.content[0].text

    activity.logger.info(f"Response received: {len(response_text)} chars")

    # Parse response
    lines = response_text.strip().split('\n')
    title = ""
    meta = ""
    excerpt = ""

    for line in lines[:15]:
        line_stripped = line.strip()
        if line_stripped.startswith("TITLE:"):
            title = line_stripped.replace("TITLE:", "").strip()
        elif line_stripped.startswith("META:"):
            meta = line_stripped.replace("META:", "").strip()
        elif line_stripped.startswith("EXCERPT:"):
            excerpt = line_stripped.replace("EXCERPT:", "").strip()

    # Extract content
    content = ""
    content_match = re.search(r'EXCERPT:.*?\n(.+?)---FAQ DATA---', response_text, re.DOTALL)
    if content_match:
        content = content_match.group(1).strip()
    else:
        # Fallback: everything after EXCERPT
        excerpt_match = re.search(r'EXCERPT:.*?\n', response_text)
        if excerpt_match:
            after_excerpt = response_text[excerpt_match.end():]
            faq_marker = after_excerpt.find('---FAQ DATA---')
            if faq_marker > 0:
                content = after_excerpt[:faq_marker].strip()
            else:
                content = after_excerpt.strip()

    # Extract FAQ
    faq = []
    faq_match = re.search(r'---FAQ DATA---\s*```json\s*(.+?)\s*```', response_text, re.DOTALL)
    if faq_match:
        try:
            faq = json.loads(faq_match.group(1))
        except json.JSONDecodeError:
            activity.logger.warning("Failed to parse FAQ JSON")

    word_count = len(content.split()) if content else 0

    activity.logger.info(
        f"Generated topic cluster content: {word_count} words, {len(faq)} FAQs "
        f"for '{target_keyword}'"
    )

    return {
        "content": content,
        "title": title or f"{target_keyword.title()} - Complete Guide 2025",
        "excerpt": excerpt or f"Everything you need to know about {target_keyword}.",
        "meta_description": (meta or f"Complete guide to {target_keyword}")[:160],
        "faq": faq,
        "word_count": word_count,
        "target_keyword": target_keyword,
        "keyword_volume": keyword_volume,
        "planning_type": planning_type,
    }
