"""
Sequential Image Generation Activity

Orchestrates narrative-driven image generation for articles using Flux Kontext.

Process:
1. Analyze article sections (H2 headings, sentiment)
2. Select 3-5 sections for image generation
3. Generate featured and hero images first
4. Generate content images sequentially, each using previous as context
5. Generate SEO metadata (alt text, descriptions)
6. Return all image URLs and metadata for database storage

This implements the "context chaining" approach where each image uses
the previous one as a visual reference to maintain consistent style,
characters, and aesthetic throughout the narrative.
"""

from typing import Dict, Any, List, Optional
from temporalio import activity

from src.activities.articles.analyze_sections import analyze_article_sections
from src.activities.media.flux_api_client import generate_flux_image


def build_sequential_prompt(
    section: Dict[str, Any],
    app: str,
    is_first: bool = False,
    previous_description: Optional[str] = None
) -> str:
    """
    Build Flux Kontext prompt for sequential storytelling.

    Follows the prompting guide's three-part structure:
    1. Establish reference (from previous image or first image context)
    2. Specify transformation (new scene/section)
    3. Preserve identity (maintain style, aesthetic, characters)

    CRITICAL: Matches tone to business context (no smiling execs for layoffs!)

    Args:
        section: Section dict with title, visual_moment, sentiment, visual_tone, business_context
        app: Application context (placement, relocation, etc.)
        is_first: If True, no context reference needed
        previous_description: Visual description from previous image

    Returns:
        Optimized Kontext prompt with appropriate tone
    """
    # App-specific style guidance
    style_guides = {
        "placement": "Bloomberg editorial style, corporate photography, professional finance aesthetic, "
                     "modern clean design, subtle blues and grays, business imagery",
        "relocation": "National Geographic travel photography, lifestyle imagery, aspirational scenes, "
                      "golden hour lighting, authentic cultural moments, welcoming atmosphere",
        "chief-of-staff": "Fortune 500 executive photography, leadership imagery, premium corporate aesthetic, "
                          "authoritative professional scenes, polished business environment",
        "consultancy": "McKinsey-style advisory imagery, strategic business photography, analytical aesthetic, "
                       "clean modern professional design"
    }

    base_style = style_guides.get(app, style_guides["placement"])

    # Extract section details with context awareness
    title = section.get("title", "")
    visual_moment = section.get("visual_moment", "")
    sentiment = section.get("sentiment", "neutral")
    visual_tone = section.get("visual_tone", "professional")
    business_context = section.get("business_context", "general")

    # Build tone-appropriate description
    tone_guidance = {
        "somber-serious": "serious expressions, no smiling, subdued professional atmosphere",
        "professional-optimistic": "confident but measured, professional handshakes, positive energy",
        "tense-uncertain": "concerned expressions, uncertain atmosphere, problem-solving mode",
        "celebratory": "professional celebration, achievement moment, positive but tasteful",
        "analytical-neutral": "focused analytical work, neutral professional demeanor"
    }

    tone_desc = tone_guidance.get(visual_tone, "professional demeanor")

    if is_first:
        # First image: Set the visual foundation with appropriate tone
        prompt = (
            f"{visual_moment}. {base_style}. "
            f"Tone: {tone_desc}. "
            f"Context: {business_context}. "
            f"Professional, high-quality, editorial photography. "
            f"Mood matches the reality: {sentiment}."
        )
    else:
        # Subsequent images: Preserve previous context, add new scene, MAINTAIN TONE
        # This is the KEY to Kontext's sequential power
        prompt = (
            f"Using the same visual style, characters, and aesthetic as the previous image, "
            f"now show: {visual_moment}. "
            f"Keep the same artistic approach, color palette, and professional quality. "
            f"Change the scene to represent: {title}. "
            f"Tone: {tone_desc}. "
            f"Context: {business_context}. "
            f"Maintain consistency while depicting this new moment. "
            f"Mood: {sentiment}. {base_style}."
        )

    # Keep under 512 token limit (roughly 400-450 words)
    if len(prompt) > 2000:  # Rough character limit
        # Simplify if too long
        if is_first:
            prompt = f"{visual_moment}. {base_style}. Mood: {sentiment}."
        else:
            prompt = (
                f"Using the same style as the previous image, show: {visual_moment}. "
                f"Maintain consistency. {base_style}."
            )

    return prompt


@activity.defn
async def generate_sequential_article_images(
    article_id: str,
    title: str,
    content: str,
    app: str = "placement",
    model: str = "kontext-pro",  # Articles always use Pro
    generate_featured: bool = True,
    generate_hero: bool = True,
    min_content_images: int = 3,
    max_content_images: int = 5
) -> Dict[str, Any]:
    """
    Generate complete image suite for article with contextual consistency.

    This activity:
    1. Analyzes article structure and sentiment (with business context awareness)
    2. Generates featured image (social sharing, 1200x630)
    3. Generates hero image (article header, 16:9) using featured as context
    4. Generates 3-5 content images sequentially, each using previous as context
    5. Ensures tone matches content (no smiling execs for layoffs!)
    6. Returns all URLs and metadata for database storage

    CRITICAL: Always uses Kontext Pro for articles (not Max)

    Args:
        article_id: Article database ID
        title: Article title
        content: Full article markdown content
        app: Application (placement, relocation, etc.)
        model: Flux model (default "kontext-pro" - articles don't use Max)
        generate_featured: Generate featured image
        generate_hero: Generate hero image
        min_content_images: Minimum content images (3)
        max_content_images: Maximum content images (5)

    Returns:
        Dict with all image URLs and metadata:
        {
            "featured_image_url": str,
            "hero_image_url": str,
            "content_image1_url": str,
            ...
            "sections": [...],  # Section analysis with business context
            "total_cost": float,
            "images_generated": int
        }
    """
    activity.logger.info(
        f"Generating sequential images for article {article_id}: {title}"
    )

    result = {
        "featured_image_url": None,
        "featured_image_alt": None,
        "featured_image_description": None,
        "featured_image_title": None,
        "hero_image_url": None,
        "hero_image_alt": None,
        "hero_image_description": None,
        "hero_image_title": None,
        "total_cost": 0.0,
        "images_generated": 0,
        "success": True,
        "errors": []
    }

    try:
        # Step 1: Analyze article sections
        activity.logger.info("Analyzing article sections...")

        analysis = await analyze_article_sections(
            content=content,
            title=title,
            app=app
        )

        sections = analysis["sections"]
        recommended_count = analysis["recommended_image_count"]

        # Ensure count is within min/max bounds
        content_image_count = max(min_content_images, min(recommended_count, max_content_images))

        activity.logger.info(
            f"Analyzed {len(sections)} sections, "
            f"generating {content_image_count} content images"
        )

        result["sections"] = sections
        result["recommended_image_count"] = content_image_count

        # Get sections marked for images
        image_sections = [s for s in sections if s.get("should_generate_image", False)]

        # If AI didn't mark enough sections, select evenly distributed ones
        if len(image_sections) < content_image_count:
            activity.logger.info(
                f"Only {len(image_sections)} sections marked, "
                f"selecting {content_image_count} evenly distributed"
            )

            # Select evenly across article
            step = len(sections) / content_image_count
            image_sections = [
                sections[int(i * step)]
                for i in range(content_image_count)
            ]

        # Limit to max_content_images
        image_sections = image_sections[:max_content_images]

        # Step 2: Generate featured image (if enabled)
        previous_image_url = None

        if generate_featured:
            activity.logger.info("Generating featured image...")

            # Use first section or article summary for featured
            first_section = sections[0] if sections else {
                "title": title,
                "visual_moment": f"Professional illustration representing {title}",
                "sentiment": "professional"
            }

            featured_prompt = build_sequential_prompt(
                section=first_section,
                app=app,
                is_first=True
            )

            featured_result = await generate_flux_image(
                prompt=featured_prompt,
                context_image_url=None,  # No context for first image
                aspect_ratio="1200:630",  # Social sharing dimensions
                model=model,
                cloudinary_folder=f"quest-articles/{article_id}",
                cloudinary_public_id=f"{article_id}-featured"
            )

            if featured_result.get("success"):
                result["featured_image_url"] = featured_result["cloudinary_url"]
                result["featured_image_alt"] = f"{title} - Featured image"
                result["featured_image_description"] = first_section.get("visual_moment", title)
                result["featured_image_title"] = title
                result["total_cost"] += featured_result.get("cost", 0)
                result["images_generated"] += 1

                # Use this as context for hero image
                previous_image_url = featured_result["cloudinary_url"]

                activity.logger.info("Featured image generated successfully")
            else:
                result["errors"].append(f"Featured image failed: {featured_result.get('error')}")

        # Step 3: Generate hero image (if enabled)
        if generate_hero:
            activity.logger.info("Generating hero image...")

            # Use second section or similar to featured
            hero_section = sections[1] if len(sections) > 1 else sections[0]

            hero_prompt = build_sequential_prompt(
                section=hero_section,
                app=app,
                is_first=(previous_image_url is None),
                previous_description=result.get("featured_image_description")
            )

            hero_result = await generate_flux_image(
                prompt=hero_prompt,
                context_image_url=previous_image_url,  # Use featured as context
                aspect_ratio="16:9",  # Hero banner
                model=model,
                cloudinary_folder=f"quest-articles/{article_id}",
                cloudinary_public_id=f"{article_id}-hero"
            )

            if hero_result.get("success"):
                result["hero_image_url"] = hero_result["cloudinary_url"]
                result["hero_image_alt"] = f"{title} - Hero image"
                result["hero_image_description"] = hero_section.get("visual_moment", title)
                result["hero_image_title"] = title
                result["total_cost"] += hero_result.get("cost", 0)
                result["images_generated"] += 1

                # Use this as context for content images
                previous_image_url = hero_result["cloudinary_url"]

                activity.logger.info("Hero image generated successfully")
            else:
                result["errors"].append(f"Hero image failed: {hero_result.get('error')}")

        # Step 4: Generate content images sequentially (THE KEY FEATURE!)
        for i, section in enumerate(image_sections, start=1):
            if i > max_content_images:
                break

            activity.logger.info(f"Generating content image {i}/{len(image_sections)}...")

            content_prompt = build_sequential_prompt(
                section=section,
                app=app,
                is_first=(previous_image_url is None),
                previous_description=section.get("visual_moment")
            )

            content_result = await generate_flux_image(
                prompt=content_prompt,
                context_image_url=previous_image_url,  # CONTEXT CHAINING!
                aspect_ratio="4:3",  # In-content image
                model=model,
                cloudinary_folder=f"quest-articles/{article_id}",
                cloudinary_public_id=f"{article_id}-content-{i}"
            )

            if content_result.get("success"):
                # Store in result dict
                result[f"content_image{i}_url"] = content_result["cloudinary_url"]
                result[f"content_image{i}_alt"] = f"{section.get('title', title)} - {section.get('sentiment')}"
                result[f"content_image{i}_description"] = section.get("visual_moment", "")
                result[f"content_image{i}_title"] = section.get("title", f"Section {i}")
                result["total_cost"] += content_result.get("cost", 0)
                result["images_generated"] += 1

                # Update context for next image
                previous_image_url = content_result["cloudinary_url"]

                activity.logger.info(f"Content image {i} generated successfully")
            else:
                result["errors"].append(
                    f"Content image {i} failed: {content_result.get('error')}"
                )

        # Final summary
        activity.logger.info(
            f"Image generation complete: {result['images_generated']} images, "
            f"${result['total_cost']:.4f} total cost"
        )

        if result["errors"]:
            activity.logger.warning(f"Errors encountered: {result['errors']}")
            result["success"] = False

        return result

    except Exception as e:
        activity.logger.error(f"Sequential image generation failed: {e}")
        result["success"] = False
        result["errors"].append(str(e))
        return result


@activity.defn
async def generate_company_contextual_images(
    company_id: str,
    company_name: str,
    logo_url: Optional[str],
    description: str,
    country: str,
    app: str = "placement",
    use_max_for_featured: bool = True  # Companies use Max for featured/hero only
) -> Dict[str, Any]:
    """
    Generate contextual brand images for company profile.

    Uses logo as context to create consistent variations:
    - Featured image (social sharing with logo) - Uses Kontext MAX
    - Hero image (company header with brand aesthetic) - Uses Kontext MAX
    - Content images (if needed in future) - Uses Kontext Pro

    CRITICAL: Companies use Kontext Max ONLY for featured/hero (it's about the company)
              All other images use Kontext Pro

    Args:
        company_id: Company database ID
        company_name: Company name
        logo_url: Company logo URL (used as context)
        description: Company description
        country: Company country
        app: Application context
        use_max_for_featured: Use Kontext Max for featured/hero (default True)

    Returns:
        Dict with all image URLs and metadata
    """
    activity.logger.info(f"Generating contextual images for company: {company_name}")

    result = {
        "featured_image_url": None,
        "hero_image_url": None,
        "total_cost": 0.0,
        "images_generated": 0,
        "success": True
    }

    # Base prompt for company imagery
    base_context = f"Professional imagery for {company_name}, {description[:100]}, {country}"

    # Determine model for company images
    # Featured/Hero use Max (it's about the company itself)
    # Any future content images use Pro
    featured_model = "kontext-max" if use_max_for_featured else "kontext-pro"

    try:
        # Featured image with logo context - USE KONTEXT MAX
        activity.logger.info(f"Generating company featured image with {featured_model}")

        featured_prompt = (
            f"Professional business card design for {company_name}. "
            f"Clean modern corporate aesthetic. Premium brand imagery. "
            f"1200x630 aspect. {country} market. Sophisticated professional style. "
            f"High-end branding, company identity focus."
        )

        featured_result = await generate_flux_image(
            prompt=featured_prompt,
            context_image_url=logo_url,  # Use logo as brand context
            aspect_ratio="1200:630",
            model=featured_model,  # KONTEXT MAX for companies
            cloudinary_folder=f"companies/{company_id}",
            cloudinary_public_id=f"{company_id}-featured"
        )

        if featured_result.get("success"):
            result["featured_image_url"] = featured_result["cloudinary_url"]
            result["total_cost"] += featured_result.get("cost", 0)
            result["images_generated"] += 1

        # Hero image using featured as context - ALSO USE KONTEXT MAX
        activity.logger.info(f"Generating company hero image with {featured_model}")

        hero_prompt = (
            f"Using the same brand aesthetic, corporate office environment for {company_name}. "
            f"Modern professional workspace. Maintain brand consistency. "
            f"Premium business photography. 16:9 aspect. "
            f"Company identity and culture focus."
        )

        hero_result = await generate_flux_image(
            prompt=hero_prompt,
            context_image_url=result["featured_image_url"],
            aspect_ratio="16:9",
            model=featured_model,  # KONTEXT MAX for companies
            cloudinary_folder=f"companies/{company_id}",
            cloudinary_public_id=f"{company_id}-hero"
        )

        if hero_result.get("success"):
            result["hero_image_url"] = hero_result["cloudinary_url"]
            result["total_cost"] += hero_result.get("cost", 0)
            result["images_generated"] += 1

        activity.logger.info(
            f"Company images complete: {result['images_generated']} generated, "
            f"${result['total_cost']:.4f}"
        )

        return result

    except Exception as e:
        activity.logger.error(f"Company image generation failed: {e}")
        result["success"] = False
        return result
