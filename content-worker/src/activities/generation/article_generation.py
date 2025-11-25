"""
Article Content Generation - Direct Anthropic SDK

Bypasses pydantic_ai structured output to avoid validation issues.
Just gets raw markdown text from Claude and parses it.
"""

from temporalio import activity
from typing import Dict, Any
from slugify import slugify
import anthropic
import re

from src.utils.config import config
from src.config.app_config import get_app_config, APP_CONFIGS


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


@activity.defn
async def generate_article_content(
    topic: str,
    article_type: str,
    app: str,
    research_context: Dict[str, Any],
    target_word_count: int = 1500,
    custom_slug: str = None
) -> Dict[str, Any]:
    """Generate article content using Anthropic SDK directly."""
    activity.logger.info(f"Generating {article_type} article: {topic}")
    if custom_slug:
        activity.logger.info(f"Using custom slug: {custom_slug}")

    try:
        # Get model config
        provider, model_name = config.get_ai_model()
        activity.logger.info(f"Using AI: {provider}:{model_name}")

        # Build prompt with research context
        prompt = build_prompt(topic, research_context)

        # Use Anthropic SDK directly - no pydantic_ai structured output
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

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
        else:
            app_desc = f"a professional content platform called {app}"
            target_audience = "professionals interested in this topic"
            content_tone = "Professional, informative, authoritative"
            interests = "industry news, trends, analysis"
            media_style = "Cinematic, professional, high production value"
            media_style_details = "High quality, visually compelling imagery that matches the content tone."

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

3. **CRITICAL: Minimum Word Count ({target_word_count}+ words, aim for 3000-4000)**
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

4. **Media Prompts (REQUIRED - 4 prompts minimum for video/image generation)**
   After the article content, add prompts for video and image generation:

   ---MEDIA PROMPTS---
   FEATURED: [Hero scene - the defining visual moment of this story]
   SECTION 1: [Opening - establishing context and setting]
   SECTION 2: [Development - action, progress, or key moment]
   SECTION 3: [Different angle - alternative perspective or detail]
   SECTION 4: [Resolution - implications, outcome, or emotional payoff]

   **OPTIMAL LENGTH: 80-120 words per prompt** (works best for both Seedance and WAN 2.5)

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

   ===== EXAMPLE PROMPT (80-120 words, follow this structure) =====
   "Young professional in crisp white linen shirt opens MacBook slowly at seaside cafe terrace, takes a gentle sip of espresso, looks up and smiles warmly at the Mediterranean horizon. Camera pushes in gradually from wide establishing shot to medium close-up. Golden hour lighting with warm amber tones, dappled light filtering through olive tree canopy, soft shadows on sun-weathered stone table. Foreground coffee cup in soft focus while subject sharp. Cinematic travel documentary style, shallow depth of field, teal-and-orange color grade, Kodak Portra warmth."

   ===== IMPORTANT GUIDELINES =====
   - Be SPECIFIC to THIS article's topic and location (Cyprus = Limassol marina, Portugal = Lisbon trams)
   - Always include MOTION - never describe static scenes
   - Use degree adverbs for intensity control (slowly, gently, dramatically)
   - Include characteristic details: "woman wearing oversized sunglasses", "weathered fisherman's hands"
   - Split motion deliberately: subject performs action WHILE camera moves separately
   - Focus on what you WANT to see (models work better with positive descriptions)
   - Lock the vibe: state a single dominant light source and clear atmosphere

   DO NOT include any {{IMAGE_N}} placeholders in the article content. Media will be inserted automatically.

5. **Structure**
   - Strong lead paragraph (who, what, when, where, why)
   - 4-6 sections with h2 headings
   - Use blockquotes for key quotes or statistics
   - Use lists for key points, deal terms, or comparisons
   - End with implications/what's next
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
1. Title on first line (specific to THIS topic, not an example)
2. Full HTML article content WITH INLINE SOURCE LINKS IN EVERY PARAGRAPH
3. Sources & References section with all URLs used
4. ---MEDIA PROMPTS--- section at the end (REQUIRED - do not skip!)
   - FEATURED: [80-120 word prompt for hero video]
   - SECTION 1-4: [prompts for content media]

The media prompts section is MANDATORY - without it, no video/images can be generated.
Source links are MANDATORY - articles without <a href> tags will be rejected."""

        # Haiku max is 8192, Sonnet/Opus can do more
        # Use 8192 for compatibility with all models
        message = client.messages.create(
            model=model_name,
            max_tokens=16384,  # Increased to ensure room for media prompts after long articles
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        article_text = message.content[0].text

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

        # Extract media prompts from content (FEATURED for hero, SECTION N for content)
        content, featured_prompt, section_prompts = extract_media_prompts(raw_content)

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
                "featured_asset_prompt": featured_prompt,
                "section_asset_prompts": section_prompts
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
