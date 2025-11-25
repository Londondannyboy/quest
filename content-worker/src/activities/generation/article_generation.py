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


def extract_image_prompts(content: str) -> tuple:
    """
    Extract image prompts from article content.

    Looks for ---IMAGE PROMPTS--- section and extracts:
    - FEATURED: prompt
    - SECTION N: prompt

    Returns:
        Tuple of (cleaned_content, featured_prompt, section_prompts)
    """
    featured_prompt = ""
    section_prompts = []

    # Find image prompts section
    match = re.search(r'---\s*IMAGE PROMPTS\s*---\s*(.+)', content, re.DOTALL | re.IGNORECASE)

    if match:
        prompts_section = match.group(1)

        # Extract FEATURED: line
        featured_match = re.search(r'FEATURED:\s*([^\n]+)', prompts_section)
        if featured_match:
            featured_prompt = featured_match.group(1).strip().strip('[]')

        # Extract SECTION N: lines
        section_matches = re.findall(r'SECTION\s*\d+:\s*([^\n]+)', prompts_section)
        section_prompts = [p.strip().strip('[]') for p in section_matches]

        # Remove prompts section from article content
        content = re.sub(r'---\s*IMAGE PROMPTS\s*---\s*.+', '', content, flags=re.DOTALL | re.IGNORECASE).strip()

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

Start with the title on the first line (plain text, no HTML):
Leonard Green Takes Control of Topgolf in $1.1bn Carve-Out

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

1. **Professional Journalism Tone**
   - Write with authority and expertise on the topic
   - Authoritative but accessible to readers
   - Match the tone to the story context

2. **Rich Source Attribution (CRITICAL - MANY LINKS)**
   - Link to EVERY source mentioned in the research
   - Use inline links: <a href="URL" class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener">Source Name</a>
   - Cite specific numbers, dates, and facts from sources
   - Include at least 15-20 source links throughout the article
   - Link to official sources, government sites, and authoritative references
   - MORE LINKS IS BETTER - aim for 2-3 links per paragraph
   - Each paragraph should have 100-150 words of substantive analysis

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

4. **Image Prompts (REQUIRED - 4 prompts minimum)**
   After the article content, add image generation prompts:

   ---IMAGE PROMPTS---
   FEATURED: [Vivid cinematic description for hero image - must include specific story elements like golf course, boardroom, etc]
   SECTION 1: [First content image - opening scene establishing context]
   SECTION 2: [Second content image - development/action scene]
   SECTION 3: [Third content image - different angle/moment]
   SECTION 4: [Fourth content image - resolution/implications scene]

   Rules for image prompts:
   - MUST include 4+ prompts (FEATURED + 3-4 SECTION prompts)
   - Match tone to article sentiment (somber for layoffs, celebratory for deals)
   - MEDIA STYLE FOR THIS APP: {media_style}
   - DETAILED STYLE GUIDE: {media_style_details}
   - Include SPECIFIC visual elements from the story (Mediterranean coastline for Cyprus visa, laptop at beach cafe for digital nomad, etc)
   - Each image should show DIFFERENT scene/angle - visual progression telling the story
   - Be vivid and specific - describe scenes, emotions, lighting, atmosphere in detail

   CRITICAL - AVOID CONTENT FILTER:
   - NEVER ask to show logos, brand marks, or trademarked visual elements
   - WRONG: "Callaway logo", "Nike swoosh", "show the Apple logo"
   - Company names for CONTEXT are OK: "executives from the golf company celebrating"
   - But NOT for visual replication: "logo on the wall", "branded equipment"
   - Focus on scenes, people, emotions, locations - NOT brand identity or logos
   - For people: describe the SCENE and EMOTION, not specific individuals

   DO NOT include any {{IMAGE_N}} placeholders in the article content. Images will be inserted automatically.

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

Output ONLY the title on line 1, then the HTML content. No other text or explanation."""

        # Haiku max is 8192, Sonnet/Opus can do more
        # Use 8192 for compatibility with all models
        message = client.messages.create(
            model=model_name,
            max_tokens=8192,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        article_text = message.content[0].text

        # Parse title from first line
        lines = article_text.strip().split('\n')
        title = lines[0].strip().lstrip('#').strip() if lines else topic
        raw_content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else article_text

        # Extract image prompts from content
        content, featured_prompt, section_prompts = extract_image_prompts(raw_content)

        # Generate metadata - use custom slug if provided
        slug = custom_slug if custom_slug else slugify(title, max_length=100)

        # Count words (strip HTML tags for accurate count)
        text_only = re.sub(r'<[^>]+>', '', content)
        word_count = len(text_only.split())

        # Extract first paragraph as excerpt (strip HTML)
        # Find first <p> tag content
        first_p_match = re.search(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
        if first_p_match:
            excerpt_html = first_p_match.group(1)
            excerpt = re.sub(r'<[^>]+>', '', excerpt_html).strip()[:200]
        else:
            excerpt = f"Article about {topic}"

        activity.logger.info(f"Extracted {len(section_prompts)} section image prompts")

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
                "meta_description": excerpt[:160],
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
                "featured_image_prompt": featured_prompt,
                "section_image_prompts": section_prompts
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
    """Build prompt with research - uses curated sources if available."""
    parts = [f"Write an article about: {topic}\n"]

    # Check for curated sources (new two-stage approach)
    curated = research_context.get("curated_sources", [])
    key_facts = research_context.get("key_facts", [])
    perspectives = research_context.get("perspectives", [])

    if curated:
        # Use curated sources (filtered, deduped, summarized)
        parts.append("\n=== KEY FACTS (verified from multiple sources - USE ALL OF THESE) ===")
        for fact in key_facts[:100]:  # Up to 100 facts for comprehensive articles
            parts.append(f"• {fact}")

        if perspectives:
            parts.append("\n=== DIFFERENT PERSPECTIVES (include all viewpoints) ===")
            for perspective in perspectives[:15]:  # More perspectives
                parts.append(f"• {perspective}")

        # Include timeline if available
        timeline = research_context.get("timeline", [])
        if timeline:
            parts.append("\n=== TIMELINE (incorporate chronologically) ===")
            for event in timeline[:20]:
                parts.append(f"• {event}")

        parts.append("\n=== CURATED SOURCES (ranked by relevance) ===")
        for source in curated[:30]:  # Use up to 30 curated sources for comprehensive articles
            parts.append(f"\n--- Source (relevance: {source.get('relevance_score', '?')}/10) ---")
            parts.append(f"Title: {source.get('title', '')}")
            parts.append(f"URL: {source.get('url', '')}")
            if source.get('summary'):
                parts.append(f"Summary: {source['summary']}")
            if source.get('key_quote'):
                parts.append(f"Key Quote: \"{source['key_quote']}\"")
            # Include full content for sources with relevance 5+ (lowered from 7)
            if source.get('full_content') and source.get('relevance_score', 0) >= 5:
                parts.append(f"Full Content:\n{source['full_content'][:6000]}")  # 6k chars per source

    else:
        # Fallback to old approach (uncurated sources) - increased limits
        news = research_context.get("news_articles", [])
        if news:
            parts.append("\n=== NEWS ===")
            for a in news[:20]:  # Increased from 10 to 20
                parts.append(f"\n{a.get('title', '')}")
                parts.append(f"URL: {a.get('url', '')}")
                if a.get('snippet'):
                    parts.append(a['snippet'])

        crawled = research_context.get("crawled_pages", [])
        if crawled:
            parts.append("\n=== SOURCES ===")
            for p in crawled[:20]:  # Increased from 10 to 20
                parts.append(f"\n{p.get('title', '')}")
                content = p.get('content', '')[:6000]  # Increased from 3000 to 6000
                if content:
                    parts.append(content)

        exa = research_context.get("exa_results", [])
        if exa:
            parts.append("\n=== RESEARCH ===")
            for r in exa[:10]:  # Increased from 5 to 10
                parts.append(f"\n{r.get('title', '')}")
                content = r.get('content', '') or r.get('text', '')
                if content:
                    parts.append(content[:6000])  # Increased from 3000 to 6000

    return '\n'.join(parts)
