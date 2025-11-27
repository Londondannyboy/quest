"""
Article Content Generation - Gemini 3 Pro (primary) / Anthropic SDK (fallback)

4-ACT STRUCTURE:
- Article written FIRST with 4 H2 sections aligned to video acts
- Each section has: title, factoid, four_act_visual_hint (for video generation)
- Additional components: callouts, FAQ, comparison, timeline, stat_highlight
- Video prompt generated FROM article sections (article-first approach)

Uses Gemini 3 Pro Preview by default for cost efficiency (~30% cheaper than Sonnet).
Falls back to Anthropic Claude if Gemini unavailable.
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
from slugify import slugify
import re
import json

# AI SDKs - Gemini primary, Anthropic fallback
import google.generativeai as genai
import anthropic

# Pydantic for validation
from pydantic import BaseModel, Field, field_validator

from src.utils.config import config
from src.config.app_config import get_app_config, APP_CONFIGS, CharacterStyle, CHARACTER_STYLE_PROMPTS


# ===== PYDANTIC MODELS FOR 4-ACT VALIDATION =====

class FourActSection(BaseModel):
    """One act/section with all required fields."""
    act: int = Field(..., ge=1, le=4, description="Act number 1-4")
    title: str = Field(..., min_length=10, description="Section H2 title")
    factoid: str = Field(..., min_length=10, description="Stat or fact for thumbnail overlay")
    video_title: str = Field(..., min_length=2, max_length=30, description="Short 2-4 word title like 'The Grind'")
    four_act_visual_hint: str = Field(..., min_length=100, max_length=400, description="45-55 word cinematic scene description")

    @field_validator('four_act_visual_hint')
    @classmethod
    def validate_visual_hint(cls, v):
        word_count = len(v.split())
        if word_count < 30:
            raise ValueError(f"four_act_visual_hint must be 45-55 words, got {word_count}")
        return v


class FourActContent(BaseModel):
    """Validated 4-act content structure. MUST have exactly 4 sections."""
    sections: List[FourActSection] = Field(..., min_length=4, max_length=4)

    @field_validator('sections')
    @classmethod
    def validate_four_sections(cls, v):
        if len(v) != 4:
            raise ValueError(f"Must have exactly 4 sections, got {len(v)}")
        # Verify acts are 1, 2, 3, 4
        acts = sorted([s.act for s in v])
        if acts != [1, 2, 3, 4]:
            raise ValueError(f"Must have acts 1, 2, 3, 4 - got {acts}")
        return v


def extract_media_prompts(content: str) -> tuple:
    """
    Extract media prompts from article content.

    Looks for ---MEDIA PROMPTS--- section (or legacy ---IMAGE PROMPTS---) and extracts:
    - FEATURED: prompt (for hero video/image)
    - SECTION N: prompt (for content videos/images)

    Returns:
        Tuple of (cleaned_content, featured_prompt, section_prompts)
    """
    featured_prompt = ""
    section_prompts = []

    # Find media prompts section (support both new MEDIA and legacy IMAGE)
    match = re.search(r'---\s*(MEDIA|IMAGE)\s*PROMPTS\s*---\s*(.+)', content, re.DOTALL | re.IGNORECASE)

    if match:
        prompts_section = match.group(2)

        # Extract FEATURED: line (can be multi-line prompt up to next SECTION or end)
        featured_match = re.search(r'FEATURED:\s*(.+?)(?=SECTION\s*\d+:|$)', prompts_section, re.DOTALL)
        if featured_match:
            featured_prompt = featured_match.group(1).strip().strip('[]').replace('\n', ' ')

        # Extract SECTION N: lines (can be multi-line prompts)
        section_matches = re.findall(r'SECTION\s*\d+:\s*(.+?)(?=SECTION\s*\d+:|$)', prompts_section, re.DOTALL)
        section_prompts = [p.strip().strip('[]').replace('\n', ' ') for p in section_matches]

        # Remove prompts section from article content
        content = re.sub(r'---\s*(MEDIA|IMAGE)\s*PROMPTS\s*---\s*.+', '', content, flags=re.DOTALL | re.IGNORECASE).strip()

    return content, featured_prompt, section_prompts


def extract_structured_data(response_text: str) -> Dict[str, Any]:
    """
    Extract structured JSON data from article response.

    Looks for ---STRUCTURED DATA--- section with 4-act sections, callouts, FAQ, etc.

    Returns:
        Dict with sections, callouts, faq, comparison, timeline, stat_highlight, guide_mode
    """
    structured_data = {
        "sections": [],
        "callouts": [],
        "faq": [],
        "comparison": None,
        "timeline": [],
        "stat_highlight": None,
        "sources": [],
        # Guide mode data (for frontend toggle view)
        "guide_mode": {
            "summary": "",
            "checklist": [],
            "requirements": [],
            "key_facts": [],
            "cost_breakdown": None
        },
        # YOLO mode data (for action-oriented toggle view)
        "yolo_mode": {
            "headline": "",
            "motivation": "",
            "primary_action": None,
            "secondary_actions": [],
            "extracted_entities": {
                "locations": [],
                "companies": [],
                "job_titles": [],
                "salary_range": None,
                "deadline": None
            }
        }
    }

    # Find structured data section
    # First try: with ```json code fence
    match = re.search(r'---\s*STRUCTURED\s*DATA\s*---\s*```json\s*(.+?)\s*```', response_text, re.DOTALL | re.IGNORECASE)

    if not match:
        # Second try: find the JSON by locating opening brace and finding balanced closing brace
        header_match = re.search(r'---\s*STRUCTURED\s*DATA\s*---\s*', response_text, re.IGNORECASE)
        if header_match:
            start_pos = header_match.end()
            # Find the first { after the header
            brace_pos = response_text.find('{', start_pos)
            if brace_pos != -1:
                # Find balanced closing brace
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
                    match = type('Match', (), {'group': lambda self, n: json_str})()  # Fake match object

    if match:
        json_str = match.group(1).strip()
        try:
            data = json.loads(json_str)
            structured_data.update(data)
            print(f"✅ STRUCTURED DATA extracted: {len(data.get('sections', []))} sections")
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error (attempting fix): {str(e)[:100]}")
            # Try to fix common JSON issues
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # Remove trailing commas
            try:
                data = json.loads(json_str)
                structured_data.update(data)
                print(f"✅ STRUCTURED DATA extracted after fix: {len(data.get('sections', []))} sections")
            except json.JSONDecodeError as e2:
                print(f"❌ STRUCTURED DATA JSON PARSE FAILED: {str(e2)[:200]}")
                print(f"❌ JSON string (first 500 chars): {json_str[:500]}")
    else:
        print(f"❌ NO STRUCTURED DATA SECTION FOUND in response")
        # Log what we're looking for to help debug
        if '---' in response_text and 'STRUCTURED' in response_text.upper():
            print(f"⚠️ Found partial match - header may be malformed")

    return structured_data


def generate_video_narrative_from_sections(sections: List[Dict], playback_id: str = None) -> Dict[str, Any]:
    """
    Generate video_narrative JSON from article sections.

    Maps 4 sections to 4 video acts with thumbnail timestamps.

    Args:
        sections: List of 4 section dicts with title, factoid, four_act_visual_hint
        playback_id: Mux playback ID for thumbnail URLs

    Returns:
        video_narrative dict for database storage
    """
    if not playback_id:
        return {}

    # Map sections to video acts (4 acts × 3 seconds = 12 seconds)
    act_timestamps = [1.5, 4.5, 7.5, 10.5]  # Mid-point of each act

    section_thumbnails = []
    for i, section in enumerate(sections[:4]):
        timestamp = act_timestamps[i] if i < len(act_timestamps) else 1.5
        section_thumbnails.append({
            "time": timestamp,
            "title": section.get("title", f"Section {i+1}"),
            "factoid": section.get("factoid", ""),
            "four_act_visual_hint": section.get("four_act_visual_hint", ""),
            "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time={timestamp}&width=800"
        })

    return {
        "playback_id": playback_id,
        "duration": 12,
        "acts": 4,
        "thumbnails": {
            "hero": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.5&width=1200",
            "sections": section_thumbnails,
            "faq": [
                {"time": 1.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=1.0&width=400"},
                {"time": 4.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=4.0&width=400"},
                {"time": 7.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=7.0&width=400"},
                {"time": 10.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.0&width=400"}
            ],
            "backgrounds": [
                {"time": 10.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.0&width=1920"},
                {"time": 5.0, "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=5.0&width=1920"}
            ]
        }
    }


@activity.defn
async def generate_four_act_article(
    topic: str,
    article_type: str,
    app: str,
    research_context: Dict[str, Any],
    target_word_count: int = 1500,
    custom_slug: str = None,
    target_keyword: str = None,
    secondary_keywords: List[str] = None
) -> Dict[str, Any]:
    """Generate article content using Anthropic SDK directly.

    Args:
        topic: The article topic
        article_type: Type of article (news, guide, etc.)
        app: App name (relocation, placement, etc.)
        research_context: Research data for the article
        target_word_count: Target word count
        custom_slug: Optional custom URL slug
        target_keyword: Optional SEO target keyword (from DataForSEO research)
        secondary_keywords: Optional list of secondary SEO keywords
    """
    activity.logger.info(f"Generating {article_type} article: {topic}")
    if custom_slug:
        activity.logger.info(f"Using custom slug: {custom_slug}")

    try:
        # Build prompt with research context
        prompt = build_prompt(topic, research_context)

        # Use Gemini 3 Pro by default (30% cheaper than Sonnet)
        # Fallback to Anthropic if GOOGLE_API_KEY not available
        use_gemini = bool(config.GOOGLE_API_KEY)

        if use_gemini:
            activity.logger.info("Using AI: google:gemini-3-pro-preview")
            genai.configure(api_key=config.GOOGLE_API_KEY)
        else:
            activity.logger.info("Using AI: anthropic:claude-sonnet-4 (Gemini unavailable)")
            anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        # Get app config for rich context
        app_config = APP_CONFIGS.get(app)

        # Create display-friendly app name for editorial attribution
        app_display_names = {
            "relocation": "Relocation",
            "placement": "Placement",
            "chief-of-staff": "Chief of Staff",
            "gtm": "GTM",
            "newsroom": "Newsroom"
        }
        app_name = app_display_names.get(app, app.title())

        if app_config:
            app_desc = app_config.description
            target_audience = app_config.target_audience
            content_tone = app_config.content_tone
            interests = ", ".join(app_config.interests[:5])
            media_style = app_config.media_style
            media_style_details = app_config.media_style_details

            # Get 4-act video template from app config (multi-template format)
            video_prompt_template = app_config.article_theme.video_prompt_template
            # Get the default template (or first available)
            default_template = video_prompt_template.get_template()
            if default_template:
                act_1_role = default_template.act_1_role
                act_1_mood = default_template.act_1_mood
                act_1_example = default_template.act_1_example
                act_2_role = default_template.act_2_role
                act_2_mood = default_template.act_2_mood
                act_2_example = default_template.act_2_example
                act_3_role = default_template.act_3_role
                act_3_mood = default_template.act_3_mood
                act_3_example = default_template.act_3_example
                act_4_role = default_template.act_4_role
                act_4_mood = default_template.act_4_mood
                act_4_example = default_template.act_4_example
            else:
                # Fallback if no templates defined
                act_1_role = "THE SETUP - Problem/current situation/challenge"
                act_1_mood = "Tension, stakes, context"
                act_1_example = ""
                act_2_role = "THE OPPORTUNITY - Discovery/solution/possibility"
                act_2_mood = "Hope, revelation, turning point"
                act_2_example = ""
                act_3_role = "THE JOURNEY - Action/process/transition"
                act_3_mood = "Movement, progress, momentum"
                act_3_example = ""
                act_4_role = "THE PAYOFF - Success/resolution/new reality"
                act_4_mood = "Achievement, satisfaction, forward-looking"
                act_4_example = ""
            no_text_rule = video_prompt_template.no_text_rule
            technical_notes = video_prompt_template.technical_notes

            # Get YOLO config for app-specific personality
            yolo_config = app_config.article_theme.yolo_config
            if yolo_config:
                yolo_personality = yolo_config.personality
                yolo_tagline = yolo_config.tagline
                yolo_voice = yolo_config.voice
                yolo_target_audience = yolo_config.target_audience
                yolo_motivational_kicks = yolo_config.motivational_kicks[:3]
                yolo_action_types = yolo_config.action_types
            else:
                yolo_personality = "motivational_chaos"
                yolo_tagline = "Stop reading. Start doing."
                yolo_voice = "Direct, irreverent, motivational"
                yolo_target_audience = "Career changers, dreamers"
                yolo_motivational_kicks = ["Fortune favors the bold."]
                yolo_action_types = ["flight", "job", "apply"]
        else:
            app_desc = f"a professional content platform called {app}"
            target_audience = "professionals interested in this topic"
            content_tone = "Professional, informative, authoritative"
            interests = "industry news, trends, analysis"
            media_style = "Cinematic, professional, high production value"
            media_style_details = "High quality, visually compelling imagery that matches the content tone."

            # Default 4-act template
            act_1_role = "THE SETUP - Problem/current situation/challenge"
            act_1_mood = "Tension, stakes, context"
            act_1_example = "Professional setting, serious tone, challenge visible"
            act_2_role = "THE OPPORTUNITY - Discovery/solution/possibility"
            act_2_mood = "Hope, revelation, turning point"
            act_2_example = "Expression change, new perspective emerging"
            act_3_role = "THE JOURNEY - Action/process/transition"
            act_3_mood = "Movement, progress, momentum"
            act_3_example = "Activity montage, steps being taken"
            act_4_role = "THE PAYOFF - Success/resolution/new reality"
            act_4_mood = "Achievement, satisfaction, forward-looking"
            act_4_example = "Positive outcome, celebration, new state"
            no_text_rule = "CRITICAL: NO text, words, letters, numbers, signs, logos anywhere."
            technical_notes = "Cinematic quality, smooth transitions, natural motion."

            # Default YOLO config
            yolo_personality = "motivational_chaos"
            yolo_tagline = "Stop reading. Start doing."
            yolo_voice = "Direct, irreverent, motivational"
            yolo_target_audience = "Career changers, dreamers"
            yolo_motivational_kicks = ["Fortune favors the bold."]
            yolo_action_types = ["flight", "job", "apply"]

        # Build SEO keyword guidance (optional - graceful if no keywords)
        if target_keyword:
            secondary_kw_list = ", ".join(secondary_keywords[:5]) if secondary_keywords else ""
            seo_keyword_guidance = f"""===== SEO KEYWORD TARGETING =====
TARGET KEYWORD: "{target_keyword}"
{f'SECONDARY KEYWORDS: {secondary_kw_list}' if secondary_kw_list else ''}

SEO REQUIREMENTS (IMPORTANT):
- Include target keyword in the TITLE (naturally, not forced)
- Include target keyword in the META description
- Include target keyword in at least one H2 heading
- Use target keyword naturally in the first paragraph
- Sprinkle secondary keywords throughout where natural
- DO NOT sacrifice narrative quality for keyword stuffing
- If the keyword doesn't fit naturally, use a close variation
- Aim for ~1-2% keyword density (natural, not robotic)
"""
            activity.logger.info(f"SEO targeting: '{target_keyword}' + {len(secondary_keywords or [])} secondary")
        else:
            seo_keyword_guidance = ""  # No SEO targeting - proceed normally

        # Build comprehensive system prompt with app context
        system_prompt = f"""You are an expert journalist writing for {app} - {app_desc}.

TARGET AUDIENCE: {target_audience}
CONTENT TONE: {content_tone}
KEY INTERESTS: {interests}

Write a COMPREHENSIVE {target_word_count}+ word {article_type} article using HTML with Tailwind CSS classes.

CRITICAL: The article MUST be AT LEAST {target_word_count} words - aim for 3000-4000 words. This is a detailed, authoritative, well-researched piece - not a summary. You have extensive research material to work with. Expand on EVERY point with thorough analysis, historical context, practical implications, and expert insights. Your readers are professionals who want comprehensive depth, multiple perspectives, and actionable information - not surface-level coverage.

===== OUTPUT FORMAT =====

Start with this EXACT format for SEO metadata (3 lines):
TITLE: [Aim for ~60-70 chars, max 90. Snappy, compelling, front-load keywords]
META: [EXACTLY 150-160 characters, compelling summary with keywords]
SLUG: [lowercase-hyphens-3-6-words]

TITLE GUIDELINES:
- Aim for 60-70 characters (ideal for Google), but can extend to 90 if needed for readability
- Must be snappy and complete - never awkwardly truncated
- Front-load important keywords (topic first, hook second)
- Good examples: "Cyprus Digital Nomad Visa 2025: Your Complete Guide to Mediterranean Remote Work"
- Good examples: "Goldman Sachs Acquires AI Startup for $500M in Landmark Deal"
- Meta description: 150-160 characters exactly (deliberately written)
- Slug: clean, memorable, SEO-friendly (e.g., "cyprus-digital-nomad-visa-2025")

{seo_keyword_guidance}

Then the full article body in HTML with Tailwind CSS:

<p class="text-lg text-gray-700 leading-relaxed mb-6">
  Strong opening paragraph that hooks the reader...
</p>

<h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Section Heading</h2>

<p class="text-gray-700 leading-relaxed mb-4">
  Section content with <a href="https://source.com" class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener">inline source links</a>...
</p>

<blockquote class="border-l-4 border-blue-500 pl-4 my-6 italic text-gray-600">
  Important quote or key statistic...
</blockquote>

<ul class="list-disc list-inside space-y-2 mb-6 text-gray-700">
  <li>Key point one</li>
  <li>Key point two</li>
</ul>

===== CONTENT REQUIREMENTS =====

1. **Professional Journalism Tone - Write Like a Human, Not an AI**
   - Write with authority and expertise on the topic
   - Authoritative but accessible to readers
   - Match the tone to the story context

   **CRITICAL: Avoid AI-Sounding Writing**

   BANNED WORDS (never use these):
   - dive/dive into, delve, unlock, unleash, harness, leverage
   - transformative, revolutionary, game-changing, cutting-edge
   - robust, scalable, seamless, streamlined
   - utilize (use "use"), opt (use "choose"), facilitate (use "help")
   - tapestry, realm, landscape, paradigm, synergy
   - meticulous, intricate, bustling, vibrant
   - embark, navigate, foster, empower

   BANNED PHRASES (never use these):
   - "In today's world" / "In this day and age"
   - "At the end of the day"
   - "It's important to note" / "It's worth noting"
   - "Let's dive in" / "Let's explore"
   - "Unleash your potential"
   - "Game-changing solution"
   - "Best practices"
   - "In order to" (just use "to")
   - "On the other hand" (overused)
   - "As previously mentioned"
   - "To put it simply"
   - "And honestly?" (AI giveaway)

   PUNCTUATION RULES:
   - NEVER use em dashes (—). Use commas, parentheses, or rewrite the sentence
   - Avoid excessive colons in headings
   - Don't overuse semicolons

   WRITING STYLE:
   - Use simple, direct language
   - Vary sentence length - mix short punchy sentences with longer flowing ones
   - Start some sentences with "And" or "But" (natural)
   - Use contractions (it's, don't, won't) - sounds more human
   - Be direct: "Here's how it works" not "Let's dive into how this works"
   - Avoid hype and marketing language
   - Reference real, specific details from research
   - Use active voice primarily

2. **Rich Source Attribution (CRITICAL - MANY LINKS)**
   - Link to EVERY source mentioned in the research
   - Use inline links: <a href="URL" class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener">Source Name</a>
   - Cite specific numbers, dates, and facts from sources
   - Include at least 15-20 source links throughout the article
   - MORE LINKS IS BETTER - aim for 2-3 links per paragraph
   - Each paragraph should have 100-150 words of substantive analysis

   **HIGH AUTHORITY LINKS FIRST (Critical for SEO/Lighthouse):**
   - Put highest authority sources in the FIRST 2-3 paragraphs (above the fold)
   - Priority order: Government sites (.gov), Wikipedia, BBC, Reuters, official sources
   - Example first paragraph: "According to the <a href="gov.uk">UK Government</a>, the visa requires..."
   - This signals credibility to Google immediately
   - Lower authority sources (blogs, smaller news) can appear later in the article

   **INTERNAL LINKS (Critical for SEO and Engagement):**
   - Link to related topics on our site using relative URLs: <a href="/portugal-d7-visa-guide">Portugal's D7 visa</a>
   - Include 3-5 internal links naturally within the content
   - Link text should be descriptive (not "click here") and relevant to the destination
   - Good: "Similar to <a href="/portugal-d7-visa-guide">Portugal's popular D7 visa program</a>, Cyprus offers..."
   - Use context like "For comparison, see our guide to [destination]" or "Related: [topic]"

3. **KEY TERM HIGHLIGHTING (Bold Important Information)**
   - Use <strong> tags to highlight key statistics, requirements, and critical information
   - Bold important numbers: <strong>€3,500 monthly income</strong>
   - Bold key requirements: <strong>valid for 3 years</strong>
   - Bold warnings/critical info: <strong>must apply before arrival</strong>
   - 3-5 bolded items per section for scannable content
   - Don't over-bold - only the most important facts

4. **PARAGRAPH FORMATTING (Critical for Readability)**
   - NEVER write more than 3 sentences in a single paragraph
   - Each paragraph should be 50-80 words maximum
   - Add a blank line between every paragraph (double line break)
   - Use short paragraphs for impact - break up dense information
   - Good: "The visa costs €500. Processing takes 6-8 weeks. Apply at least 3 months before your planned move."
   - Bad: Long paragraph with 5+ sentences cramming multiple topics

5. **CRITICAL: Minimum Word Count ({target_word_count}+ words, aim for 3000-4000)**
   - This article MUST be at least {target_word_count} words - aim for 3000-4000 words
   - You have EXTENSIVE research material - USE ALL OF IT
   - Do NOT write a summary - write a COMPREHENSIVE, AUTHORITATIVE article
   - Expand on ALL key points with thorough analysis and multiple angles
   - Include historical context, background, current state, and future implications
   - Explain the "why", "how", "who benefits", "what are the risks"
   - Use EVERY specific metric, date, requirement, quote, and fact from research
   - Add broader industry context and implications for different stakeholders
   - Include multiple perspectives, expert insights, and contrasting viewpoints
   - Cover edge cases, exceptions, requirements, and practical considerations
   - If the research provides information, USE ALL OF IT - integrate everything

6. **Media Prompts (REQUIRED - 4 prompts minimum for video/image generation)**
   After the article content, add prompts for video and image generation:

   ---MEDIA PROMPTS---
   FEATURED: [Hero scene - the defining visual moment of this story]
   SECTION 1: [Opening - establishing context and setting]
   SECTION 2: [Development - action, progress, or key moment]
   SECTION 3: [Different angle - alternative perspective or detail]
   SECTION 4: [Resolution - implications, outcome, or emotional payoff]

   **OPTIMAL LENGTH: 60-80 words per prompt** (works best for both Seedance and WAN 2.5)

   **UNIVERSAL PROMPT FORMULA (works for all video models):**
   [Subject + Description] + [Scene + Environment] + [Motion + Action] + [Camera Movement] + [Aesthetic/Style]

   ===== CAMERA LANGUAGE =====
   **Movement Types:**
   - Push/Dolly: "camera pushes in slowly", "dolly out to reveal", "camera moves closer gradually"
   - Pan/Tilt: "pan left across scene", "tilt up to sky", "pan right following subject"
   - Tracking: "camera follows closely", "tracks alongside subject", "smooth tracking shot"
   - Orbital: "orbits smoothly around subject", "orbital arc reveals setting"
   - Crane: "crane up dramatically", "crane down into scene"
   - Static: "fixed camera", "static wide shot", "locked off frame"

   **Shot Types:**
   - "wide establishing shot", "medium shot", "close-up", "extreme close-up"
   - "over-the-shoulder", "low angle looking up", "high angle looking down"
   - "bird's eye aerial view", "macro detail shot"

   ===== MOTION DESCRIPTORS =====
   **Speed Modifiers:**
   - "slowly", "quickly", "gradually", "suddenly", "gently"
   - "slow-motion", "time-lapse", "whip-pan", "rapid"

   **Intensity Adverbs (critical for AI video models):**
   - "violently", "softly", "dramatically", "subtly", "gracefully"
   - Examples: "waves crash violently", "leaves flutter gently", "camera pushes in slowly"

   **Sequential Actions (describe motion chronologically):**
   - Format: [Subject] + [Action 1] + [Action 2] + [Action 3]
   - GOOD: "Woman opens laptop slowly, takes a gentle sip of coffee, looks up and smiles warmly"
   - BAD: "Woman working at laptop" (static, no action sequence)

   **Depth & Parallax (WAN 2.5 excels at this):**
   - "Foreground grass sways while mountains remain still in background"
   - "Foreground elements blur past while subject stays sharp"

   ===== LIGHTING & ATMOSPHERE =====
   **Time of Day:**
   - "golden hour warm light", "soft early morning glow", "dramatic dusk"
   - "volumetric dusk lighting", "harsh noon sun", "neon rim light at night"

   **Light Quality:**
   - "dappled light through leaves", "god rays filtering through", "soft diffused lighting"
   - "high contrast shadows", "soft ambient glow", "dramatic side lighting"

   **Color Grading (film looks):**
   - "teal-and-orange color grade", "warm amber tones", "cool Mediterranean blues"
   - "Kodak Portra warmth", "bleach-bypass desaturated", "rich saturated colors"

   **Lens Styles:**
   - "anamorphic bokeh", "16mm film grain", "shallow depth of field"
   - "cinematic widescreen", "documentary handheld", "clean digital look"

   ===== APP STYLE GUIDE =====
   - TONE: {media_style}
   - DETAILS: {media_style_details}

   ===== EXAMPLE PROMPT STRUCTURE (60-80 words) =====
   "[Subject + appearance] [performs action slowly/gently] at [location specific to YOUR topic], [secondary action]. Camera [movement type] from [starting frame] to [ending frame]. [Time of day] lighting with [color tones], [environmental detail]. [Foreground element] in soft focus while subject sharp. [Cinematic style], shallow depth of field, [color grade]."

   ===== IMPORTANT GUIDELINES =====
   - Be SPECIFIC to YOUR article's topic - use locations, settings, and details from the actual content
   - Always include MOTION - never describe static scenes
   - Use degree adverbs for intensity control (slowly, gently, dramatically)
   - Include characteristic details: "woman wearing oversized sunglasses", "weathered fisherman's hands"
   - Split motion deliberately: subject performs action WHILE camera moves separately
   - Focus on what you WANT to see (models work better with positive descriptions)
   - Lock the vibe: state a single dominant light source and clear atmosphere

   DO NOT include any {{IMAGE_N}} placeholders in the article content. Media will be inserted automatically.

5. **Structure - 4-ACT ALIGNED SECTIONS**
   CRITICAL: The article must have EXACTLY 4 main sections (H2 headings) that align with a 4-act video structure:

   **ACT 1 (Section 1)**: The Setup - Problem/context/current situation
   - Hook the reader with a compelling observation or problem
   - Establish why this matters NOW
   - Example: "The London Grind: Why Remote Workers Are Burning Out"

   **ACT 2 (Section 2)**: The Opportunity - Solution/discovery/revelation
   - Present the main opportunity or solution
   - Key benefits and what makes it unique
   - Example: "The Cyprus Opportunity: Tax Benefits That Actually Make Sense"

   **ACT 3 (Section 3)**: The Journey - Process/how-to/requirements
   - Practical steps, requirements, timeline
   - The "how to actually do this" section
   - Example: "Making the Move: From Application to Arrival"

   **ACT 4 (Section 4)**: The Payoff - Results/outcomes/future
   - Real outcomes and what life looks like after
   - Future implications and next steps
   - Example: "Life After the Move: What Six Months Actually Looks Like"

   Additional structure elements:
   - Strong lead paragraph before Section 1 (who, what, when, where, why)
   - Use blockquotes for key quotes or statistics
   - Use lists for key points, deal terms, or comparisons
   - ALWAYS include a "Sources & References" section at the end with all URLs used:
     <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Sources & References</h2>
     <ul class="list-disc list-inside space-y-2 mb-6 text-gray-700">
       <li><a href="URL" class="text-blue-600 hover:text-blue-800 underline" target="_blank">Source Name</a> - Brief description</li>
     </ul>

   - ALWAYS end with an Editorial Footer (after Sources):
     <hr class="my-8 border-gray-200" />
     <div class="bg-gray-50 rounded-lg p-6 mt-8">
       <p class="text-sm text-gray-500 mb-3">
         <em>This article was written with AI assistance and curated by the Quest {app_name} editorial team.
         While we strive for accuracy, please verify important details independently before making decisions.</em>
       </p>
       <p class="text-sm font-medium text-gray-700">Quest {app_name} Editorial Team</p>
     </div>

6. **Tailwind Classes to Use**
   - Paragraphs: text-gray-700 leading-relaxed mb-4 (or mb-6 for spacing)
   - Headings: text-2xl font-bold text-gray-900 mt-8 mb-4
   - Links: text-blue-600 hover:text-blue-800 underline
   - Blockquotes: border-l-4 border-blue-500 pl-4 my-6 italic text-gray-600
   - Lists: list-disc list-inside space-y-2 mb-6 text-gray-700
   - Bold: font-semibold
   - Images: my-8

7. **Context Awareness**
   - Understand the story: Is this a deal? Layoffs? IPO? Crisis?
   - Match tone to context (don't be celebratory about job losses)
   - Include relevant industry context and implications

CRITICAL: SOURCE LINKS ARE MANDATORY
Every paragraph MUST contain at least one <a href="URL"> link to a source from the research.
- Use the URLs provided in the research context (look for "URL:" lines)
- Format: <a href="https://..." class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener">Source Name</a>
- Minimum 15 links throughout the article
- ALWAYS end with a "Sources & References" section listing all URLs used
- Articles without source links will be REJECTED

CRITICAL OUTPUT FORMAT:
1. TITLE: line (specific to THIS topic, not an example)
2. META: line (150-160 char description)
3. SLUG: line (lowercase-hyphens)
4. Full HTML article content WITH INLINE SOURCE LINKS IN EVERY PARAGRAPH
5. Sources & References section with all URLs used
6. Editorial Footer
7. ---STRUCTURED DATA--- section at the very end (REQUIRED - JSON for video generation)

===== STRUCTURED DATA FORMAT (REQUIRED) =====

After the Editorial Footer, include this JSON block for video thumbnail and component generation:

---STRUCTURED DATA---
```json
{{
  "sections": [
    {{
      "act": 1,
      "title": "Section 1 H2 title exactly as in article",
      "video_title": "STORY-SPECIFIC 2-4 word label (e.g., 'Rule 5.4 Falls', 'Arizona Opens Up', 'Visa Cap Doubles' - NOT generic like 'The Grind')",
      "factoid": "One compelling stat or fact for this section (shown on thumbnail overlay)",
      "four_act_visual_hint": "45-55 word cinematic scene. Example: 'Exhausted professional in cramped flat stares at rain-streaked window, laptop glowing harsh. Camera pushes slowly to close-up as subject rubs temples. Cool blue-grey tones, harsh fluorescent light. Documentary realism, shallow depth of field.'"
    }},
    {{
      "act": 2,
      "title": "Section 2 H2 title",
      "video_title": "STORY-SPECIFIC 2-4 word label for this section's key insight",
      "factoid": "Compelling stat for section 2",
      "four_act_visual_hint": "45-55 word cinematic scene for act 2 (opportunity/discovery)"
    }},
    {{
      "act": 3,
      "title": "Section 3 H2 title",
      "video_title": "STORY-SPECIFIC 2-4 word label for this section's key insight",
      "factoid": "Compelling stat for section 3",
      "four_act_visual_hint": "45-55 word cinematic scene for act 3 (journey/process)"
    }},
    {{
      "act": 4,
      "title": "Section 4 H2 title",
      "video_title": "STORY-SPECIFIC 2-4 words WITH '?' (e.g., 'PE-Backed Future?', 'Global Expansion?', 'Schengen Access?' - question mark acknowledges future uncertainty)",
      "factoid": "Compelling stat for section 4",
      "four_act_visual_hint": "45-55 word cinematic scene for act 4 (payoff/resolution)"
    }}
  ],
  "callouts": [
    {{
      "type": "pro_tip",
      "title": "Short callout title",
      "content": "Useful tip or insight (2-3 sentences)",
      "placement": "after_section_2"
    }},
    {{
      "type": "warning",
      "title": "Important warning",
      "content": "Critical warning or gotcha",
      "placement": "after_section_3"
    }}
  ],
  "faq": [
    {{"q": "Common question 1?", "a": "Concise answer..."}},
    {{"q": "Common question 2?", "a": "Concise answer..."}},
    {{"q": "Common question 3?", "a": "Concise answer..."}},
    {{"q": "Common question 4?", "a": "Concise answer..."}}
  ],
  "comparison": {{
    "title": "Comparison title (if applicable)",
    "items": [
      {{"name": "Option A", "col1": "value", "col2": "value"}},
      {{"name": "Option B", "col1": "value", "col2": "value"}}
    ]
  }},
  "timeline": [
    {{"date": "Month Year", "title": "Event title", "description": "What happened"}},
    {{"date": "Month Year", "title": "Event title", "description": "What happened"}}
  ],
  "stat_highlight": {{
    "headline": "Main takeaway in one sentence",
    "stats": [
      {{"value": "3,400", "label": "Hours sunshine/year"}},
      {{"value": "30-40%", "label": "Lower cost of living"}}
    ]
  }},
  "sources": [
    {{"name": "Source Name", "url": "https://...", "description": "Brief description"}}
  ],
  "guide_mode": {{
    "summary": "2-3 sentence factual summary of the key takeaway. No fluff, just facts.",
    "checklist": [
      {{"item": "Action item 1", "detail": "Brief explanation"}},
      {{"item": "Action item 2", "detail": "Brief explanation"}},
      {{"item": "Action item 3", "detail": "Brief explanation"}}
    ],
    "requirements": [
      {{"requirement": "Requirement 1", "detail": "What's needed"}},
      {{"requirement": "Requirement 2", "detail": "What's needed"}}
    ],
    "key_facts": [
      "Key fact 1 with specific number/date",
      "Key fact 2 with specific number/date",
      "Key fact 3 with specific number/date",
      "Key fact 4 with specific number/date",
      "Key fact 5 with specific number/date"
    ],
    "cost_breakdown": {{
      "total_estimate": "Total cost range",
      "items": [
        {{"item": "Cost item 1", "amount": "€X"}},
        {{"item": "Cost item 2", "amount": "€X"}}
      ],
      "notes": "Any important cost notes"
    }}
  }},
  "yolo_mode": {{
    "headline": "Bold, punchy 5-10 word action headline (e.g., 'Book the flight. Stop overthinking.')",
    "motivation": "One sentence kick-in-the-pants motivation specific to this article",
    "primary_action": {{
      "label": "Main CTA button text (e.g., 'Apply Now', 'Book Flight')",
      "description": "Why they should do this NOW (irreverent, direct)",
      "url_params": {{"destination": "extracted city/country", "company": "extracted company if any"}}
    }},
    "secondary_actions": [
      {{"type": "job|flight|guide|apply", "label": "Action label", "context": "Relevant extracted data"}}
    ],
    "extracted_entities": {{
      "locations": ["City/Country mentioned"],
      "companies": ["Company names mentioned"],
      "job_titles": ["Roles mentioned if any"],
      "salary_range": "If mentioned",
      "deadline": "If any urgency/deadline mentioned"
    }}
  }}
}}
```

===== GUIDE MODE DATA (REQUIRED for toggle view) =====

The guide_mode object provides data for the "fact sheet" view toggle on the frontend:

- **summary**: 2-3 sentences, pure facts, no narrative. Example: "The Cyprus Digital Nomad Visa costs €150 and requires proof of €3,500/month income. Processing takes 6-8 weeks. Valid for 1 year, renewable twice."

- **checklist**: 3-5 action items the reader needs to complete. Be specific and actionable.

- **requirements**: Key eligibility requirements. Include income thresholds, document needs, etc.

- **key_facts**: 5-8 bullet points with specific numbers, dates, costs. These are the "at a glance" facts.

- **cost_breakdown**: If costs are relevant (visa guides, moving guides), break down the total cost. Set to null for news/analysis articles where costs aren't relevant.

IMPORTANT: Always populate guide_mode even for news articles - users may want the fact sheet view.

===== YOLO MODE DATA (REQUIRED for action view) =====

YOLO Mode is the "just do it" action view for {yolo_target_audience}.

YOLO PERSONALITY: {yolo_personality}
YOLO TAGLINE: "{yolo_tagline}"
YOLO VOICE: {yolo_voice}
ACTION TYPES TO EXTRACT: {yolo_action_types}

EXAMPLE MOTIVATIONAL STYLE:
{yolo_motivational_kicks}

- **headline**: Bold, punchy, matches the "{yolo_personality}" voice. Example: "{yolo_tagline}"

- **motivation**: One sentence specific to THIS article in the {yolo_personality} voice. Reference the actual opportunity.

- **primary_action**: The ONE thing they should do right now. Extract destination/company/opportunity.

- **secondary_actions**: 2-3 supporting actions from these types: {yolo_action_types}

- **extracted_entities**: Pull out all actionable data - locations, companies, job titles, salaries, deadlines.

TONE: {yolo_voice}. No hedging. No "consider" or "you might want to". It's "Do it. Now."

===== 4-ACT VIDEO FRAMEWORK (CRITICAL) =====

Each section's four_act_visual_hint must follow this 4-act story structure for video generation:

ACT 1 (0-3s) - {act_1_role}
  Mood: {act_1_mood}
  Example style (DO NOT COPY - adapt to YOUR topic): {act_1_example}

ACT 2 (3-6s) - {act_2_role}
  Mood: {act_2_mood}
  Example style: {act_2_example}

ACT 3 (6-9s) - {act_3_role}
  Mood: {act_3_mood}
  Example style: {act_3_example}

ACT 4 (9-12s) - {act_4_role}
  Mood: {act_4_mood}
  Example style: {act_4_example}

{no_text_rule}
Technical: {technical_notes}

VISUAL_HINT REQUIREMENTS (CRITICAL FOR VIDEO - STRICT LENGTH):
- 45-55 words MAXIMUM (strict limit to fit 4 acts in 2000 chars)
- video_title must be 2-4 words, STORY-SPECIFIC (e.g., "Rule 5.4 Falls", "Visa Cap Doubles", "New Wealth" - NOT generic like "The Grind" or "Discovery")
- Act 4 video_title MUST end with "?" to acknowledge future uncertainty (e.g., "PE-Backed Future?", "Schengen Access?", "Global Expansion?")
- Must describe MOTION (action sequences, camera movement)
- Include: subject + action, environment, lighting, camera movement, color grade
- Formula: [Subject + Action] + [Environment] + [Camera] + [Color/Mood]
- Be specific to YOUR topic but CONCISE

CHARACTER DEMOGRAPHICS (infer from article context):
When describing people in visual hints, consider the geographic and business context:
- Geographic: Singapore deal = East/Southeast Asian professionals. UAE sovereign wealth fund = Middle Eastern/Arab. London PE firm = North European.
- Cross-border deals: Show BOTH parties appropriately (e.g., "Middle Eastern investor meets North European club executives")
- Industry context may influence gender mix, but default to mixed gender unless article specifically mentions otherwise.
- If article is abstract/market analysis with no specific parties, omit people entirely (cityscapes, abstract data visuals).

HOLISTIC VIDEO QUALITY (AI video models struggle with these - follow strictly):
- FACES: Keep at mid-distance or further. Close-ups distort. Prefer 3/4 angles, not direct frontal.
- SCREENS/DEVICES: Show ambient glow only, NEVER readable content. Keep screens distant or at edge-of-frame.
- CAMERA: Slow, deliberate motion using adverbs (slowly, gently, gradually). No fast cuts.
- CONTINUITY: Consistent lighting temperature and color palette across all 4 acts.
- NO TEXT anywhere - no signs, logos, words, letters. Screens show abstract colors only.

Source links are MANDATORY - articles without <a href> tags will be rejected.
The STRUCTURED DATA section is MANDATORY - without it, no video can be generated."""

        # Generate article using Gemini (primary) or Anthropic (fallback)
        if use_gemini:
            # Gemini 3 Pro Preview
            model = genai.GenerativeModel(
                model_name='gemini-3-pro-preview',
                system_instruction=system_prompt
            )
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=16384,
                    temperature=0.7
                )
            )
            article_text = response.text
            activity.logger.info(f"Gemini response received: {len(article_text)} chars")
        else:
            # Anthropic Claude fallback
            message = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16384,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            article_text = message.content[0].text
            activity.logger.info(f"Anthropic response received: {len(article_text)} chars")

        # Parse SEO metadata from structured output
        lines = article_text.strip().split('\n')

        # Extract TITLE:, META:, SLUG: from first lines
        title = topic  # fallback
        meta_description = None
        ai_suggested_slug = None
        content_start_idx = 0

        for idx, line in enumerate(lines[:10]):  # Check first 10 lines for metadata
            line_stripped = line.strip()
            if line_stripped.startswith('TITLE:'):
                title = line_stripped[6:].strip()
                # Soft limit 90 chars - only truncate if way over, and only at natural breaks
                if len(title) > 90:
                    activity.logger.warning(f"Title too long ({len(title)} chars), truncating to ~90")
                    # Try to truncate at colon (natural headline break)
                    colon_pos = title[:90].rfind(':')
                    if colon_pos > 40:
                        # Keep the part before colon + colon itself
                        title = title[:colon_pos + 1].strip()
                    else:
                        # No colon, try dash or em-dash
                        dash_pos = max(title[:90].rfind(' - '), title[:90].rfind(' – '))
                        if dash_pos > 40:
                            title = title[:dash_pos].strip()
                        else:
                            # Last resort: just keep under 90 at word boundary
                            truncated = title[:90]
                            last_space = truncated.rfind(' ')
                            if last_space > 60:
                                title = truncated[:last_space].rstrip(':,-–')
                content_start_idx = idx + 1
            elif line_stripped.startswith('META:'):
                meta_description = line_stripped[5:].strip()
                content_start_idx = idx + 1
            elif line_stripped.startswith('SLUG:'):
                ai_suggested_slug = line_stripped[5:].strip().lower().replace(' ', '-')
                content_start_idx = idx + 1
            elif line_stripped.startswith('<'):
                # HTML content started
                break

        # Fallback: if no structured metadata, use first line as title
        if title == topic and lines:
            title = lines[0].strip().lstrip('#').strip()
            content_start_idx = 1

        raw_content = '\n'.join(lines[content_start_idx:]).strip()

        # Log extracted metadata
        activity.logger.info(f"SEO Metadata - Title ({len(title)} chars): {title[:70]}")
        if meta_description:
            activity.logger.info(f"SEO Metadata - Meta ({len(meta_description)} chars): {meta_description[:160]}")
        if ai_suggested_slug:
            activity.logger.info(f"SEO Metadata - AI Slug: {ai_suggested_slug}")

        # Extract structured data (sections, callouts, FAQ, etc.) for 4-act video
        structured_data = extract_structured_data(raw_content)

        # Also extract legacy media prompts for backwards compatibility
        content, featured_prompt, section_prompts = extract_media_prompts(raw_content)

        # Remove structured data section from content (it's metadata, not display content)
        content = re.sub(r'---\s*STRUCTURED\s*DATA\s*---\s*```json\s*.+?\s*```', '', content, flags=re.DOTALL | re.IGNORECASE).strip()
        content = re.sub(r'---\s*STRUCTURED\s*DATA\s*---\s*\{.+?\}', '', content, flags=re.DOTALL | re.IGNORECASE).strip()

        # Log structured data extraction
        sections = structured_data.get("sections", [])
        if sections:
            activity.logger.info(f"✅ Extracted {len(sections)} structured sections for 4-act video")
            for i, sec in enumerate(sections[:4]):
                activity.logger.info(f"  Section {i+1}: {sec.get('title', 'Untitled')[:50]}...")
                if sec.get('four_act_visual_hint'):
                    activity.logger.info(f"    Visual hint: {sec['four_act_visual_hint'][:60]}...")
        else:
            activity.logger.warning(f"⚠️ No structured sections found - video generation may fail")

        # Log guide_mode extraction (for frontend toggle view)
        guide_mode = structured_data.get("guide_mode", {})
        if guide_mode.get("summary"):
            activity.logger.info(f"✅ Guide mode data extracted: {len(guide_mode.get('key_facts', []))} key facts, {len(guide_mode.get('checklist', []))} checklist items")
        else:
            activity.logger.warning(f"⚠️ No guide_mode summary found - fact sheet toggle may be empty")

        # Log yolo_mode extraction (for action-oriented toggle view)
        yolo_mode = structured_data.get("yolo_mode", {})
        if yolo_mode.get("headline"):
            entities = yolo_mode.get("extracted_entities", {})
            activity.logger.info(f"✅ YOLO mode data extracted: '{yolo_mode['headline'][:50]}...' | {len(entities.get('locations', []))} locations, {len(entities.get('companies', []))} companies")
        else:
            activity.logger.warning(f"⚠️ No yolo_mode headline found - action view may be empty")

        # Check for source links - warn if missing (critical for SEO)
        link_count = content.count('<a href')
        if link_count == 0:
            activity.logger.warning(f"⚠️ Article has NO source links! This is bad for SEO.")
        elif link_count < 10:
            activity.logger.warning(f"⚠️ Article has only {link_count} links (should have 15+)")
        else:
            activity.logger.info(f"✅ Article has {link_count} source links")

        # Check for Sources section
        has_sources_section = 'Sources' in content or 'References' in content
        if not has_sources_section:
            activity.logger.warning(f"⚠️ Article missing Sources & References section")

        # Determine slug: custom > AI-suggested > auto-generated from title
        if custom_slug:
            slug = custom_slug
        elif ai_suggested_slug:
            slug = slugify(ai_suggested_slug, max_length=60)
        else:
            slug = slugify(title, max_length=60)

        # Count words (strip HTML tags for accurate count)
        text_only = re.sub(r'<[^>]+>', '', content)
        word_count = len(text_only.split())

        # Use AI-generated meta_description if available, else extract from content
        if not meta_description:
            # Fallback: extract first paragraph
            first_p_match = re.search(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
            if first_p_match:
                excerpt_html = first_p_match.group(1)
                meta_description = re.sub(r'<[^>]+>', '', excerpt_html).strip()[:160]
            else:
                meta_description = f"Article about {topic}"

        excerpt = meta_description  # Use meta_description as excerpt

        activity.logger.info(f"Extracted media prompts: FEATURED={bool(featured_prompt)}, SECTIONS={len(section_prompts)}")
        if featured_prompt:
            activity.logger.info(f"FEATURED prompt: {featured_prompt[:100]}...")
        if section_prompts:
            for i, sp in enumerate(section_prompts[:4]):
                activity.logger.info(f"SECTION {i+1} prompt: {sp[:80]}...")

        activity.logger.info(f"Article generated: {word_count} words")

        # Calculate cost (rough estimate for Claude Sonnet)
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000

        return {
            "article": {
                "title": title,
                "slug": slug,
                "content": content,
                "excerpt": excerpt,
                "app": app,
                "article_type": article_type,
                "meta_description": meta_description,  # AI-generated 150-160 char description
                "tags": [],
                "word_count": word_count,
                "reading_time_minutes": max(1, word_count // 200),
                "section_count": content.count('<h2'),
                "featured_asset_url": None,
                "hero_asset_url": None,
                "image_count": 0,
                "author": "Quest Editorial Team",
                "status": "draft",
                "confidence_score": 1.0,
                # Legacy prompts for backwards compatibility
                "featured_asset_prompt": featured_prompt,
                "section_asset_prompts": section_prompts,
                # NEW: 4-act structured data for video generation
                "four_act_content": structured_data.get("sections", []),
                "callouts": structured_data.get("callouts", []),
                "faq": structured_data.get("faq", []),
                "comparison": structured_data.get("comparison"),
                "timeline": structured_data.get("timeline", []),
                "stat_highlight": structured_data.get("stat_highlight"),
                "structured_sources": structured_data.get("sources", []),
                # SEO keyword targeting (optional - from DataForSEO)
                "target_keyword": target_keyword,
                "secondary_keywords": secondary_keywords or [],
                # GUIDE MODE: Structured data for fact sheet toggle view
                "guide_mode": structured_data.get("guide_mode", {
                    "summary": "",
                    "checklist": [],
                    "requirements": [],
                    "key_facts": [],
                    "cost_breakdown": None
                }),
                # YOLO MODE: Structured data for action-oriented toggle view
                "yolo_mode": structured_data.get("yolo_mode", {
                    "headline": "",
                    "motivation": "",
                    "primary_action": None,
                    "secondary_actions": [],
                    "extracted_entities": {}
                })
            },
            "cost": cost,
            "model_used": f"{provider}:{model_name}",
            "success": True
        }

    except Exception as e:
        activity.logger.error(f"FAILED: {e}", exc_info=True)

        slug = slugify(topic, max_length=100)
        return {
            "article": {
                "title": topic,
                "slug": slug,
                "content": f"## {topic}\n\nArticle generation failed: {e}",
                "excerpt": f"Article about {topic}.",
                "app": app,
                "article_type": article_type,
                "meta_description": f"Article about {topic}.",
                "tags": [],
                "word_count": 10,
                "reading_time_minutes": 1,
                "section_count": 1,
                "featured_asset_url": None,
                "hero_asset_url": None,
                "image_count": 0,
                "author": "Quest Editorial Team",
                "status": "draft",
                "confidence_score": 0.0
            },
            "cost": 0.0,
            "model_used": "fallback",
            "success": False,
            "error": str(e)
        }


def build_prompt(topic: str, research_context: Dict[str, Any]) -> str:
    """Build prompt with rich curated research from Gemini Pro analysis."""
    parts = [f"Write an article about: {topic}\n"]

    # Check for curated sources (new two-stage approach with Gemini Pro)
    curated = research_context.get("curated_sources", [])
    key_facts = research_context.get("key_facts", [])

    if curated:
        # === ALL SOURCE URLs - USE THESE FOR CITATIONS ===
        all_urls = research_context.get("all_source_urls", [])
        if all_urls:
            parts.append("\n=== AVAILABLE SOURCE URLS FOR CITATIONS (USE THESE - copy URLs exactly) ===")
            parts.append("CRITICAL: Use these URLs in your <a href='...'> tags. High authority sources should appear in first paragraphs.")
            for source in all_urls[:50]:
                authority_tag = f"[{source.get('authority', 'standard').upper()}]" if source.get('authority') in ['official', 'high_authority'] else ""
                parts.append(f"• {authority_tag} {source.get('title', 'Source')[:60]}")
                parts.append(f"  URL: {source.get('url', '')}")

        # === KEY FACTS - the backbone of the article ===
        if key_facts:
            parts.append("\n=== KEY FACTS (USE ALL OF THESE - specific numbers, dates, costs, requirements) ===")
            for fact in key_facts[:100]:
                parts.append(f"• {fact}")

        # === OPINIONS & SENTIMENT - add depth and nuance ===
        opinions = research_context.get("opinions_and_sentiment", [])
        if opinions:
            parts.append("\n=== OPINIONS & SENTIMENT (weave these perspectives throughout) ===")
            for opinion in opinions[:20]:
                if isinstance(opinion, dict):
                    parts.append(f"• [{opinion.get('sentiment', 'neutral')}] {opinion.get('source', 'source')}: {opinion.get('opinion', '')}")
                else:
                    parts.append(f"• {opinion}")

        # === UNIQUE ANGLES - make the article stand out ===
        unique_angles = research_context.get("unique_angles", [])
        if unique_angles:
            parts.append("\n=== UNIQUE ANGLES (insights others miss - INCORPORATE THESE) ===")
            for angle in unique_angles[:15]:
                parts.append(f"• {angle}")

        # === DIRECT QUOTES - add credibility and voice ===
        direct_quotes = research_context.get("direct_quotes", [])
        if direct_quotes:
            parts.append("\n=== QUOTABLE QUOTES (use these for blockquotes) ===")
            for quote in direct_quotes[:15]:
                if isinstance(quote, dict):
                    parts.append(f"• \"{quote.get('quote', '')}\" — {quote.get('attribution', 'source')}")
                else:
                    parts.append(f"• {quote}")

        # === COMPARISONS - provide context ===
        comparisons = research_context.get("comparisons", [])
        if comparisons:
            parts.append("\n=== COMPARISONS (help readers understand relative value) ===")
            for comp in comparisons[:10]:
                parts.append(f"• {comp}")

        # === RECENT CHANGES - what's new ===
        recent_changes = research_context.get("recent_changes", [])
        if recent_changes:
            parts.append("\n=== RECENT CHANGES (2024-2025 updates to highlight) ===")
            for change in recent_changes[:15]:
                parts.append(f"• {change}")

        # === WARNINGS - important caveats ===
        warnings = research_context.get("warnings_and_gotchas", [])
        if warnings:
            parts.append("\n=== WARNINGS & GOTCHAS (important caveats to include) ===")
            for warning in warnings[:15]:
                parts.append(f"• {warning}")

        # === TIMELINE - chronological context ===
        timeline = research_context.get("timeline", [])
        if timeline:
            parts.append("\n=== TIMELINE (incorporate chronologically) ===")
            for event in timeline[:20]:
                parts.append(f"• {event}")

        # === ARTICLE OUTLINE - suggested structure ===
        outline = research_context.get("article_outline", [])
        if outline:
            parts.append("\n=== SUGGESTED ARTICLE STRUCTURE (follow this outline) ===")
            for i, section in enumerate(outline):
                if isinstance(section, dict):
                    parts.append(f"\n{i+1}. {section.get('section', 'Section')}")
                    for point in section.get('key_points', []):
                        parts.append(f"   • {point}")
                else:
                    parts.append(f"• {section}")

        # === HIGH AUTHORITY SOURCES - cite early ===
        high_auth = research_context.get("high_authority_sources", [])
        if high_auth:
            parts.append("\n=== HIGH AUTHORITY SOURCES (cite these in first 2-3 paragraphs for SEO) ===")
            for source in high_auth[:10]:
                if isinstance(source, dict):
                    parts.append(f"• {source.get('authority', 'official')}: {source.get('url', '')}")
                else:
                    parts.append(f"• {source}")

        # === ZEP KNOWLEDGE GRAPH CONTEXT ===
        # This contains facts/relationships from our knowledge graph about the topic
        zep_context = research_context.get("zep_context", {})
        if zep_context and zep_context.get("available"):
            parts.append("\n=== KNOWLEDGE GRAPH CONTEXT (from our database - use to add depth/context) ===")

            # Include edge facts (the valuable relationship data)
            # Facts now include temporal metadata: {fact, uuid, valid_at, invalid_at, name}
            zep_facts = zep_context.get("facts", [])
            if zep_facts:
                parts.append("\nKNOWN FACTS (from our knowledge graph):")
                for fact_obj in zep_facts[:20]:
                    # Handle both old format (string) and new format (dict with metadata)
                    if isinstance(fact_obj, dict):
                        fact_text = fact_obj.get("fact", "")
                        valid_at = fact_obj.get("valid_at")
                        # Include date if available so Claude knows how recent the fact is
                        if valid_at:
                            parts.append(f"• {fact_text} (as of {valid_at[:10]})")
                        else:
                            parts.append(f"• {fact_text}")
                    else:
                        parts.append(f"• {fact_obj}")

            # Include existing coverage info
            zep_articles = zep_context.get("articles", [])
            if zep_articles:
                parts.append(f"\nPREVIOUS COVERAGE: We have {len(zep_articles)} existing articles on this topic")
                for article in zep_articles[:5]:
                    parts.append(f"• {article.get('name', article.get('title', 'Article'))}")

            # Include known deals
            zep_deals = zep_context.get("deals", [])
            if zep_deals:
                parts.append("\nKNOWN DEALS/TRANSACTIONS:")
                for deal in zep_deals[:10]:
                    if isinstance(deal, dict):
                        parts.append(f"• {deal.get('name', 'Deal')}")
                    else:
                        parts.append(f"• {deal}")

            # Include known people
            zep_people = zep_context.get("people", [])
            if zep_people:
                parts.append("\nKNOWN KEY PEOPLE:")
                for person in zep_people[:10]:
                    if isinstance(person, dict):
                        parts.append(f"• {person.get('name', 'Person')} - {person.get('role', '')}")
                    else:
                        parts.append(f"• {person}")

            parts.append("")  # Empty line after Zep context

        # === CURATED SOURCES with full content ===
        parts.append("\n=== CURATED SOURCES (ranked by relevance - use for inline citations) ===")
        for source in curated[:30]:
            parts.append(f"\n--- Source (relevance: {source.get('relevance_score', '?')}/10) ---")
            parts.append(f"Title: {source.get('title', '')}")
            parts.append(f"URL: {source.get('url', '')}")
            if source.get('unique_value'):
                parts.append(f"Unique Value: {source['unique_value']}")
            if source.get('full_content') and source.get('relevance_score', 0) >= 5:
                parts.append(f"Full Content:\n{source['full_content'][:6000]}")

    else:
        # Fallback to old approach (uncurated sources)
        news = research_context.get("news_articles", [])
        if news:
            parts.append("\n=== NEWS ===")
            for a in news[:20]:
                parts.append(f"\n{a.get('title', '')}")
                parts.append(f"URL: {a.get('url', '')}")
                if a.get('snippet'):
                    parts.append(a['snippet'])

        crawled = research_context.get("crawled_pages", [])
        if crawled:
            parts.append("\n=== SOURCES ===")
            for p in crawled[:20]:
                parts.append(f"\n{p.get('title', '')}")
                content = p.get('content', '')[:6000]
                if content:
                    parts.append(content)

        exa = research_context.get("exa_results", [])
        if exa:
            parts.append("\n=== RESEARCH ===")
            for r in exa[:10]:
                parts.append(f"\n{r.get('title', '')}")
                content = r.get('content', '') or r.get('text', '')
                if content:
                    parts.append(content[:6000])

    return '\n'.join(parts)


# ============================================================================
# 3-ACT NARRATIVE ARTICLE GENERATION
# ============================================================================

@activity.defn
async def generate_narrative_article(
    narrative: Dict[str, Any],
    research_context: Dict[str, Any],
    app: str,
    mux_urls: Dict[str, Any] = None,
    target_word_count: int = 2000
) -> Dict[str, Any]:
    """
    Generate article content driven by a 3-act narrative structure.

    The narrative defines:
    - 3 acts with titles, key_points, and timestamps
    - Preamble context for authority
    - Tone guidance

    The article structure:
    - Preamble (authority/context from Zep or market context)
    - Act 1 Section (expanding act 1 key_points)
    - Act 2 Section (expanding act 2 key_points)
    - Act 3 Section (expanding act 3 key_points)
    - Bump (summary/CTA)

    Args:
        narrative: 3-act narrative from build_3_act_narrative
        research_context: Curated research for content
        app: Application name
        mux_urls: Optional Mux URLs for embedding video/thumbnails
        target_word_count: Target length (default 2000)

    Returns:
        Article dict with content, title, slug, etc.
    """
    activity.logger.info(f"Generating narrative article: {narrative.get('title', 'Untitled')}")

    acts = narrative.get("acts", [])
    if len(acts) != 3:
        activity.logger.error(f"Narrative must have exactly 3 acts, got {len(acts)}")
        return {"success": False, "error": "Invalid narrative structure"}

    # Get app config
    app_config = APP_CONFIGS.get(app)
    if app_config:
        target_audience = app_config.target_audience
        content_tone = app_config.content_tone
    else:
        target_audience = "professionals interested in this topic"
        content_tone = "Professional, informative"

    # Build the acts structure for the prompt
    acts_structure = ""
    for act in acts:
        acts_structure += f"""
ACT {act['number']}: {act['title']} ({act['start']}s - {act['end']}s)
Key Points to Cover:
{chr(10).join(f"- {kp}" for kp in act.get('key_points', []))}
Section Hook: {act.get('section_hook', '')}
"""

    # Build Mux media embedding instructions
    media_instructions = ""
    if mux_urls:
        playback_id = mux_urls.get("playback_id", "")
        media_instructions = f"""
MEDIA EMBEDDING (use these exact URLs):

For each act section, embed the bounded video player and thumbnail:

ACT 1 MEDIA:
- Thumbnail: <img src="https://image.mux.com/{playback_id}/thumbnail.jpg?time=1.5&width=1200" class="w-full rounded-lg mb-4" alt="Act 1">
- Video (optional, for hero): Use bounded player from 0s-3.3s

ACT 2 MEDIA:
- Thumbnail: <img src="https://image.mux.com/{playback_id}/thumbnail.jpg?time=5&width=1200" class="w-full rounded-lg mb-4" alt="Act 2">

ACT 3 MEDIA:
- Thumbnail: <img src="https://image.mux.com/{playback_id}/thumbnail.jpg?time=8&width=1200" class="w-full rounded-lg mb-4" alt="Act 3">

Place the thumbnail image at the START of each act section, before the section heading.
"""

    system_prompt = f"""You are writing an article driven by a 3-ACT NARRATIVE structure.

The video and article tell ONE UNIFIED STORY. The article expands on each act.

NARRATIVE TEMPLATE: {narrative.get('template', 'Unknown')}
TONE: {narrative.get('tone', content_tone)}
TARGET AUDIENCE: {target_audience}

===== 3-ACT STRUCTURE =====
{acts_structure}

PREAMBLE CONTEXT: {narrative.get('preamble_context', '')}

===== ARTICLE STRUCTURE =====

1. **PREAMBLE** (100-150 words)
   - Establish authority: "As we've been tracking..." or market context
   - Set up the stakes: Why does this matter?
   - Hook: "It's no surprise that..."

2. **ACT 1 SECTION: {acts[0]['title']}** (400-600 words)
   - Expand on Act 1 key points with research
   - Set the scene, establish the problem/dream/event
   - Use specific facts and sources

3. **ACT 2 SECTION: {acts[1]['title']}** (400-600 words)
   - Expand on Act 2 key points
   - The journey, process, or impact
   - Include practical details, requirements, analysis

4. **ACT 3 SECTION: {acts[2]['title']}** (400-600 words)
   - Expand on Act 3 key points
   - The outcome, winners/losers, resolution
   - Future implications

5. **BUMP** (100-150 words)
   - Summary of key takeaways
   - Call to action or forward look
{media_instructions}

===== OUTPUT FORMAT =====

TITLE: {narrative.get('title', '')}
META: [150-160 char compelling description]
SLUG: [suggested-slug-here]

[Full HTML article with Tailwind CSS classes]
[DO NOT include ---MEDIA PROMPTS--- section - video is already generated]

===== WRITING RULES =====
- Use inline source links: <a href="URL" class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener">
- Minimum 10-15 source links throughout
- NO AI words: dive, delve, unlock, unleash, harness, leverage, robust, seamless
- Use contractions, vary sentence length
- Be specific with facts from research
- Each section should match its act's key_points exactly"""

    # Build research prompt
    research_prompt = build_prompt(narrative.get("topic", ""), research_context)

    user_prompt = f"""Write the 3-act narrative article.

TITLE TO USE: {narrative.get('title', '')}
TOPIC: {narrative.get('topic', '')}

{research_prompt}

Remember:
- Preamble establishes authority
- Each act section expands on its key_points
- Use sources throughout
- Bump summarizes and closes

Write the article now:"""

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        provider, model_name = config.get_ai_model()

        message = client.messages.create(
            model=model_name,
            max_tokens=12000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        article_text = message.content[0].text

        # Parse metadata
        lines = article_text.strip().split('\n')
        title = narrative.get("title", "")
        meta_description = ""
        slug = ""

        for idx, line in enumerate(lines[:10]):
            line_stripped = line.strip()
            if line_stripped.startswith('TITLE:'):
                title = line_stripped[6:].strip()
            elif line_stripped.startswith('META:'):
                meta_description = line_stripped[5:].strip()
            elif line_stripped.startswith('SLUG:'):
                slug = line_stripped[5:].strip()

        # Find content start
        content_start = 0
        for idx, line in enumerate(lines):
            if line.strip().startswith('<'):
                content_start = idx
                break

        content = '\n'.join(lines[content_start:])

        # Generate slug if not provided
        if not slug:
            slug = slugify(title)[:60]

        # Calculate word count
        text_only = re.sub(r'<[^>]+>', '', content)
        word_count = len(text_only.split())

        # Calculate cost
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000

        activity.logger.info(f"Narrative article generated: {word_count} words")

        return {
            "success": True,
            "article": {
                "title": title,
                "slug": slug,
                "meta_description": meta_description,
                "content": content,
                "word_count": word_count,
                "section_count": 5,  # Preamble + 3 acts + bump
                "narrative_template": narrative.get("template", ""),
            },
            "cost": cost
        }

    except Exception as e:
        activity.logger.error(f"Narrative article generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "article": None,
            "cost": 0
        }


@activity.defn
async def refine_broken_links(
    article_content: str,
    broken_urls: List[Dict[str, Any]],
    topic: str
) -> Dict[str, Any]:
    """
    Refine article content to fix or remove broken links.

    Uses Haiku (fast & cheap) to:
    - Find alternative sources for broken links
    - Reword sentences if no alternative available
    - Gracefully remove references to unavailable content

    Args:
        article_content: The HTML article content
        broken_urls: List of {url, score, status, reason} for broken links
        topic: Article topic for context

    Returns:
        Dict with refined_content, changes_made, cost
    """
    activity.logger.info(f"Refining {len(broken_urls)} broken links in article")

    if not broken_urls:
        return {
            "success": True,
            "refined_content": article_content,
            "changes_made": [],
            "cost": 0
        }

    try:
        # Extract paragraphs containing broken URLs for context
        broken_contexts = []
        for item in broken_urls:
            url = item.get("url", "")
            reason = item.get("reason", "unknown")
            status = item.get("status", "broken")

            # Find the paragraph containing this URL
            pattern = rf'<p[^>]*>(?:(?!</p>).)*{re.escape(url)}(?:(?!</p>).)*</p>'
            match = re.search(pattern, article_content, re.DOTALL | re.IGNORECASE)

            if match:
                broken_contexts.append({
                    "url": url,
                    "reason": reason,
                    "status": status,
                    "paragraph": match.group(0)
                })
            else:
                # Try finding in any tag
                simple_pattern = rf'<a[^>]*href="{re.escape(url)}"[^>]*>([^<]+)</a>'
                simple_match = re.search(simple_pattern, article_content)
                if simple_match:
                    broken_contexts.append({
                        "url": url,
                        "reason": reason,
                        "status": status,
                        "link_text": simple_match.group(1),
                        "full_match": simple_match.group(0)
                    })

        if not broken_contexts:
            activity.logger.warning("Could not find broken URLs in content")
            return {
                "success": True,
                "refined_content": article_content,
                "changes_made": [],
                "cost": 0
            }

        # Build prompt for Haiku
        broken_list = "\n".join([
            f"- URL: {ctx['url']}\n  Status: {ctx['status']} ({ctx['reason']})\n  Context: {ctx.get('paragraph', ctx.get('link_text', 'N/A'))[:300]}"
            for ctx in broken_contexts
        ])

        prompt = f"""You are editing an article about "{topic}". Some links in the article are broken or inaccessible.

For each broken link below, provide a fix. Return ONLY a JSON array with your fixes.

BROKEN LINKS:
{broken_list}

For each broken link, decide:
1. If the link is to a general concept/fact that doesn't need a source, remove the link but keep the text
2. If the link is critical for credibility, suggest removing the entire claim or rewording without the link
3. If you know a working alternative source for the same information, suggest it (only if you're confident it exists)

Return a JSON array like:
```json
[
  {{
    "url": "the broken url",
    "action": "remove_link" | "reword" | "replace",
    "original_html": "<a href=...>text</a>",
    "fixed_html": "text without link OR reworded sentence OR <a href='new_url'>text</a>"
  }}
]
```

IMPORTANT:
- Be conservative - when in doubt, just remove the link wrapper and keep the text
- Don't invent sources - only suggest replacements if you're certain they exist
- Keep fixes minimal - don't rewrite entire paragraphs"""

        # Use Gemini 3 Pro for better quality link fixing
        genai.configure(api_key=config.GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-3-pro-preview')

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=2000,
                temperature=0.3
            )
        )

        response_text = response.text
        # Estimate cost: Gemini 3 Pro is $2/1M input, $12/1M output
        # Rough estimate based on prompt size
        cost = 0.002  # ~$0.002 per link fix call

        # Parse JSON response
        json_match = re.search(r'```json\s*(\[.+?\])\s*```', response_text, re.DOTALL)
        if not json_match:
            json_match = re.search(r'(\[.+?\])', response_text, re.DOTALL)

        if not json_match:
            activity.logger.warning("Could not parse Gemini response, falling back to link removal")
            # Fallback: just remove links
            refined_content = article_content
            for ctx in broken_contexts:
                url = ctx["url"]
                pattern = rf'<a[^>]*href="{re.escape(url)}"[^>]*>([^<]+)</a>'
                refined_content = re.sub(pattern, r'\1', refined_content)
            return {
                "success": True,
                "refined_content": refined_content,
                "changes_made": [{"url": ctx["url"], "action": "remove_link_fallback"} for ctx in broken_contexts],
                "cost": cost
            }

        fixes = json.loads(json_match.group(1))
        changes_made = []
        refined_content = article_content

        for fix in fixes:
            url = fix.get("url", "")
            action = fix.get("action", "remove_link")
            original = fix.get("original_html", "")
            fixed = fix.get("fixed_html", "")

            if original and fixed and original in refined_content:
                refined_content = refined_content.replace(original, fixed)
                changes_made.append({"url": url, "action": action})
            elif url:
                # Fallback: remove link wrapper
                pattern = rf'<a[^>]*href="{re.escape(url)}"[^>]*>([^<]+)</a>'
                refined_content = re.sub(pattern, r'\1', refined_content)
                changes_made.append({"url": url, "action": "remove_link_fallback"})

        activity.logger.info(f"Refined {len(changes_made)} broken links (cost: ${cost:.4f})")

        return {
            "success": True,
            "refined_content": refined_content,
            "changes_made": changes_made,
            "cost": cost
        }

    except Exception as e:
        activity.logger.error(f"Link refinement failed: {e}")
        # Fallback: just remove all broken links
        refined_content = article_content
        for item in broken_urls:
            url = item.get("url", "")
            pattern = rf'<a[^>]*href="{re.escape(url)}"[^>]*>([^<]+)</a>'
            refined_content = re.sub(pattern, r'\1', refined_content)

        return {
            "success": False,
            "error": str(e),
            "refined_content": refined_content,
            "changes_made": [{"url": item["url"], "action": "remove_link_error"} for item in broken_urls],
            "cost": 0
        }


# ============================================================================
# 4-ACT VIDEO PROMPT ASSEMBLY
# ============================================================================

# Model-specific limits for video prompt optimization
VIDEO_MODEL_LIMITS = {
    "seedance": {"char_limit": 2000, "words_per_act": "45-55"},
    "wan-2.5": {"char_limit": 2500, "words_per_act": "80-120"},
}


@activity.defn
async def generate_four_act_video_prompt(
    article: Dict[str, Any],
    app: str,
    video_model: str = "seedance",
    character_style: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a 4-act video prompt - HYBRID approach:

    1. FIRST: Try to assemble from article's four_act_content (if AI generated it)
    2. FALLBACK: Use Gemini 2.0 Flash to generate from scratch

    Args:
        article: Article dict with title, content, excerpt, four_act_content (optional)
        app: Application (relocation, placement, pe_news)
        video_model: Target model (seedance or wan-2.5)
        character_style: Override character style

    Returns:
        {"prompt": str, "model": str, "acts": int, "success": bool, "cost": float, "source": "assembled"|"ai_generated"}
    """
    activity.logger.info(f"🎬 Generating 4-act video prompt: {article.get('title', 'Untitled')[:50]}...")

    # Get app config for no-text rule, holistic guidelines, and character style
    app_config = APP_CONFIGS.get(app)
    if app_config:
        no_text_rule = app_config.article_theme.video_prompt_template.no_text_rule
        holistic = getattr(app_config.article_theme.video_prompt_template, 'holistic_guidelines', '')
        effective_style = CharacterStyle(character_style) if character_style else app_config.character_style
    else:
        no_text_rule = "CRITICAL: NO text, words, letters, numbers anywhere. Purely visual."
        holistic = ""
        effective_style = CharacterStyle(character_style) if character_style else CharacterStyle.DIVERSE

    character_prompt = CHARACTER_STYLE_PROMPTS.get(effective_style, "")
    activity.logger.info(f"Character style: {effective_style.value}")

    # Get model character limit
    model_info = VIDEO_MODEL_LIMITS.get(video_model, VIDEO_MODEL_LIMITS["seedance"])
    char_limit = model_info.get("char_limit", 2000)

    # ===== STEP 1: TRY TO ASSEMBLE FROM ARTICLE'S four_act_content =====
    sections = article.get("four_act_content", [])

    if sections and len(sections) >= 4:
        # Check if sections have four_act_visual_hint
        hints_count = sum(1 for s in sections[:4] if s.get("four_act_visual_hint"))

        if hints_count >= 4:
            activity.logger.info(f"✅ ASSEMBLING from article's four_act_content ({hints_count}/4 hints found)")

            # Build the 4-act prompt from visual hints
            act_prompts = []
            for i, section in enumerate(sections[:4]):
                act_num = i + 1
                hint = section.get("four_act_visual_hint", "")
                video_title = section.get("video_title") or section.get("title", f"Act {act_num}")
                start_time = (act_num - 1) * 3
                end_time = act_num * 3
                act_prompts.append(f"ACT {act_num} ({start_time}s-{end_time}s): {video_title}\n{hint}")

            acts_text = "\n\n".join(act_prompts)
            holistic_block = f"\n{holistic}" if holistic else ""
            character_block = f"\n{character_prompt}" if character_prompt else ""

            assembled_prompt = f"""{no_text_rule}{character_block}{holistic_block}

VIDEO: 12 seconds, 4 acts × 3 seconds each.

{acts_text}"""

            # Enforce character limit
            was_truncated = len(assembled_prompt) > char_limit
            if was_truncated:
                assembled_prompt = assembled_prompt[:char_limit]

            activity.logger.info(f"✅ Assembled 4-act prompt: {len(assembled_prompt)} chars (source: article four_act_content)")

            return {
                "prompt": assembled_prompt,
                "model": video_model,
                "acts": 4,
                "success": True,
                "was_truncated": was_truncated,
                "source": "assembled",
                "cost": 0  # No AI call
            }
        else:
            activity.logger.warning(f"⚠️ Article has {len(sections)} sections but only {hints_count}/4 have four_act_visual_hint")
    else:
        activity.logger.warning(f"⚠️ Article missing four_act_content (sections: {len(sections) if sections else 0})")

    # ===== STEP 2: GENERATE WITH AI + PYDANTIC VALIDATION =====
    activity.logger.info("📝 Generating 4-act content via AI (Pydantic validated)...")

    # Extract article info for AI
    title = article.get("title", "")
    excerpt = article.get("excerpt", "")
    content = article.get("content", "")[:4000]  # First 4000 chars

    # Build AI prompt - request JSON for Pydantic validation
    ai_prompt = f"""Generate 4-act video content for this article. Return ONLY valid JSON.

ARTICLE TITLE: {title}
ARTICLE EXCERPT: {excerpt}
ARTICLE CONTENT:
{content}

===== REQUIRED JSON FORMAT =====
{{
  "sections": [
    {{
      "act": 1,
      "title": "Section title from article",
      "factoid": "Key stat or fact (10+ chars)",
      "video_title": "2-4 word label like 'The Grind'",
      "four_act_visual_hint": "45-55 word cinematic scene. Include: setting, lighting (warm golden/cool blue), camera movement (push in/track/orbit), subject emotion. Documentary style. NO text/words/signs."
    }},
    {{"act": 2, "title": "...", "factoid": "...", "video_title": "...", "four_act_visual_hint": "45-55 words for discovery moment"}},
    {{"act": 3, "title": "...", "factoid": "...", "video_title": "...", "four_act_visual_hint": "45-55 words for journey/process"}},
    {{"act": 4, "title": "...", "factoid": "...", "video_title": "Short label with ?", "four_act_visual_hint": "45-55 words for resolution"}}
  ]
}}

===== RULES =====
1. MUST have EXACTLY 4 sections with acts 1, 2, 3, 4
2. Each four_act_visual_hint MUST be 45-55 words with camera/lighting details
3. {no_text_rule}
4. {character_prompt if character_prompt else "Use diverse professional subjects."}
5. Return ONLY JSON, no other text

Return ONLY the 4-act prompt, nothing else."""

    max_retries = 2
    last_error = None

    for attempt in range(max_retries):
        try:
            activity.logger.info(f"Attempt {attempt + 1}/{max_retries} to generate 4-act content")

            # Use Gemini 2.0 Flash
            genai.configure(api_key=config.GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-2.0-flash')

            response = model.generate_content(
                ai_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.5
                )
            )

            response_text = response.text.strip()
            activity.logger.info(f"AI response: {len(response_text)} chars")

            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            # Find JSON object
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                raise ValueError("No JSON object found in AI response")

            json_str = json_match.group()
            data = json.loads(json_str)

            # ===== PYDANTIC VALIDATION - MUST HAVE 4 VALID ACTS =====
            validated = FourActContent(sections=[
                FourActSection(**s) for s in data.get("sections", [])
            ])

            activity.logger.info(f"✅ Pydantic validation passed: 4 acts with valid visual hints")

            # Assemble into video prompt format
            act_prompts = []
            for section in validated.sections:
                act_num = section.act
                start_time = (act_num - 1) * 3
                end_time = act_num * 3
                act_prompts.append(f"ACT {act_num} ({start_time}s-{end_time}s): {section.video_title}\n{section.four_act_visual_hint}")

            acts_text = "\n\n".join(act_prompts)
            holistic_block = f"\n{holistic}" if holistic else ""
            character_block = f"\n{character_prompt}" if character_prompt else ""

            final_prompt = f"""{no_text_rule}{character_block}{holistic_block}

VIDEO: 12 seconds, 4 acts × 3 seconds each.

{acts_text}"""

            # Enforce character limit
            was_truncated = len(final_prompt) > char_limit
            if was_truncated:
                final_prompt = final_prompt[:char_limit]

            activity.logger.info(f"✅ 4-act video prompt generated: {len(final_prompt)} chars (Pydantic validated)")

            return {
                "prompt": final_prompt,
                "model": video_model,
                "acts": 4,
                "success": True,
                "was_truncated": was_truncated,
                "source": "ai_generated_validated",
                "four_act_content": [s.model_dump() for s in validated.sections],  # Return for database storage
                "cost": 0.001
            }

        except Exception as e:
            last_error = str(e)
            activity.logger.warning(f"Attempt {attempt + 1} failed: {last_error}")

    # All retries failed - RAISE to fail the workflow
    error_msg = f"❌ FAILED to generate valid 4-act video prompt after {max_retries} attempts. Last error: {last_error}"
    activity.logger.error(error_msg)
    raise ValueError(error_msg)



# NOTE: generate_four_act_content has been merged into generate_four_act_video_prompt
# which now handles both structured content generation AND video prompt assembly
# with Pydantic validation. Use generate_four_act_video_prompt instead.