#!/usr/bin/env python3
"""
Full pipeline test: Curation (Gemini Pro) → Article (Sonnet) → Video → Images
Run on Replit or locally to test all stages.

Usage:
    python test_full_pipeline.py              # Full pipeline
    python test_full_pipeline.py curation     # Just curation
    python test_full_pipeline.py article      # Curation + article
    python test_full_pipeline.py video        # Just video with test prompt
    python test_full_pipeline.py images       # Just images with test prompt
"""

import asyncio
import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Test topic
TEST_TOPIC = "Cyprus Digital Nomad Visa 2025"
TEST_APP = "relocation"

# Mock research data for quick testing (skip actual crawling)
MOCK_RESEARCH = {
    "crawled_pages": [
        {
            "url": "https://www.visitcyprus.com/digital-nomad-visa",
            "title": "Cyprus Digital Nomad Visa - Official Guide",
            "content": """Cyprus Digital Nomad Visa allows remote workers to live and work in Cyprus for up to 1 year, renewable for 2 more years.

Requirements:
- Monthly income of at least €3,500 (or €4,200 for families)
- Valid employment contract or proof of freelance work
- Health insurance valid in Cyprus
- Clean criminal record
- Valid passport with 6+ months validity

Application fee: €70
Processing time: Approximately 4-8 weeks

Benefits:
- Access to EU country
- Low cost of living compared to Western Europe
- 300+ days of sunshine
- English widely spoken
- Growing digital nomad community in Limassol and Paphos

Tax: Digital nomads are NOT tax residents if staying less than 183 days. Those staying longer may benefit from Cyprus's 12.5% corporate tax rate."""
        },
        {
            "url": "https://nomadlist.com/cyprus",
            "title": "Cyprus for Digital Nomads - NomadList",
            "content": """Cyprus ranks highly for digital nomads. Limassol is the main hub with fast internet (average 100Mbps), coworking spaces, and a vibrant expat community.

Cost of living: €1,500-2,500/month
- Rent: €600-1,200 for 1BR apartment
- Food: €300-500/month
- Coworking: €150-250/month

Pros: Great weather, beach lifestyle, EU access, English spoken, low taxes
Cons: Hot summers, limited nightlife, car needed outside cities

Popular areas: Limassol (business hub), Paphos (quieter, cheaper), Larnaca (near airport)"""
        }
    ],
    "news_articles": [
        {
            "url": "https://cyprus-mail.com/2025/01/digital-nomad-visa-applications-surge",
            "title": "Cyprus sees 300% increase in digital nomad visa applications",
            "snippet": "Applications for Cyprus's digital nomad visa have surged 300% in 2024, with most applicants coming from the UK, US, and Russia."
        }
    ],
    "exa_results": [
        {
            "url": "https://expatfocus.com/cyprus-digital-nomad-guide",
            "title": "Complete Guide to Cyprus Digital Nomad Visa 2025",
            "content": "The Cyprus digital nomad visa has become one of Europe's most popular options. Key changes in 2025 include faster processing and a new online application portal."
        }
    ]
}


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n📌 {title}")
    print("-" * 60)


async def test_curation():
    """Test Gemini Pro curation."""
    from src.activities.generation.research_curation import curate_research_sources

    print_header("CURATION TEST (Gemini 2.5 Pro)")
    print(f"Topic: {TEST_TOPIC}")

    start = time.time()

    result = await curate_research_sources(
        topic=TEST_TOPIC,
        crawled_pages=MOCK_RESEARCH["crawled_pages"],
        news_articles=MOCK_RESEARCH["news_articles"],
        exa_results=MOCK_RESEARCH["exa_results"],
        max_sources=10
    )

    elapsed = time.time() - start

    print_section(f"Curation Complete ({elapsed:.1f}s)")
    print(f"Model: {result.get('model', 'unknown')}")
    print(f"Sources: {result.get('total_output', 0)} curated from {result.get('total_input', 0)}")

    # Show extracted data
    print_section("Key Facts Extracted")
    for fact in result.get("key_facts", [])[:10]:
        print(f"  • {fact[:100]}...")
    print(f"  ... ({len(result.get('key_facts', []))} total)")

    print_section("Opinions & Sentiment")
    for opinion in result.get("opinions_and_sentiment", [])[:5]:
        if isinstance(opinion, dict):
            print(f"  • [{opinion.get('sentiment')}] {opinion.get('opinion', '')[:80]}...")
        else:
            print(f"  • {str(opinion)[:80]}...")

    print_section("Unique Angles")
    for angle in result.get("unique_angles", [])[:5]:
        print(f"  • {angle[:80]}...")

    print_section("Article Outline")
    for section in result.get("article_outline", [])[:6]:
        if isinstance(section, dict):
            print(f"  {section.get('section', 'Section')}")
            for point in section.get("key_points", [])[:3]:
                print(f"    • {point}")

    print_section("Warnings & Gotchas")
    for warning in result.get("warnings_and_gotchas", [])[:5]:
        print(f"  ⚠️  {warning[:80]}...")

    return result


async def test_article_generation(curation_result: dict = None):
    """Test Sonnet article generation."""
    from src.activities.generation.article_generation import generate_article_content

    print_header("ARTICLE GENERATION TEST (Claude Sonnet)")

    # Use curation result or run curation first
    if not curation_result:
        print("Running curation first...")
        curation_result = await test_curation()

    print_section("Generating Article")
    start = time.time()

    result = await generate_article_content(
        topic=TEST_TOPIC,
        article_type="guide",
        app=TEST_APP,
        research_context=curation_result,
        target_word_count=2000
    )

    elapsed = time.time() - start

    print_section(f"Article Generated ({elapsed:.1f}s)")

    article = result.get("article", {})
    print(f"Title: {article.get('title')}")
    print(f"Words: {article.get('word_count')}")
    print(f"Sections: {article.get('section_count')}")
    print(f"Cost: ${result.get('cost', 0):.4f}")
    print(f"Model: {result.get('model_used')}")

    # Check for AI-isms
    content = article.get("content", "")
    ai_isms = ["dive into", "delve", "unleash", "transformative", "robust", "seamless", "—"]
    found_ai_isms = [word for word in ai_isms if word.lower() in content.lower()]

    print_section("AI-ism Check")
    if found_ai_isms:
        print(f"  ❌ Found AI-isms: {', '.join(found_ai_isms)}")
    else:
        print(f"  ✅ No obvious AI-isms detected!")

    # Show media prompts
    print_section("Media Prompts Extracted")
    featured = article.get("featured_image_prompt", "")
    if featured:
        print(f"  FEATURED: {featured[:150]}...")
    else:
        print(f"  ❌ No FEATURED prompt found!")

    section_prompts = article.get("section_image_prompts", [])
    for i, prompt in enumerate(section_prompts[:4]):
        print(f"  SECTION {i+1}: {prompt[:100]}...")

    # Show excerpt
    print_section("Article Excerpt")
    print(f"  {article.get('excerpt', '')[:300]}...")

    return result


async def test_video_generation(prompt: str = None):
    """Test video generation with Seedance."""
    from src.activities.media.video_generation import generate_article_video

    print_header("VIDEO GENERATION TEST")

    if not prompt:
        prompt = """Young professional in crisp linen shirt opens MacBook slowly at seaside cafe terrace,
takes a gentle sip of espresso, looks up and smiles warmly at the Mediterranean horizon.
Camera pushes in gradually from wide establishing shot to medium close-up.
Golden hour lighting, warm amber tones, cinematic travel documentary style."""

    print(f"Prompt: {prompt[:100]}...")

    start = time.time()

    result = await generate_article_video(
        title=TEST_TOPIC,
        content="<p>Test content</p>",
        app=TEST_APP,
        quality="low",  # Cheapest for testing
        duration=3,
        aspect_ratio="16:9",
        video_model="seedance",
        video_prompt=prompt
    )

    elapsed = time.time() - start

    print_section(f"Video Generated ({elapsed:.1f}s)")
    print(f"URL: {result.get('video_url', 'N/A')[:80]}...")
    print(f"Model: {result.get('model')}")
    print(f"Quality: {result.get('quality')}")
    print(f"Cost: ${result.get('cost', 0):.4f}")

    return result


async def test_image_generation(prompts: list = None):
    """Test sequential image generation."""
    from src.activities.media.sequential_images import generate_sequential_images

    print_header("IMAGE GENERATION TEST")

    if not prompts:
        prompts = [
            "Digital nomad working at beachside cafe in Limassol Cyprus, laptop open, Mediterranean sea view",
            "Aerial view of Paphos harbor with colorful fishing boats, golden hour light",
            "Modern coworking space in Cyprus with young professionals, plants, natural light"
        ]

    print(f"Generating {len(prompts)} images...")

    sections = [{"title": f"Section {i+1}", "content": p} for i, p in enumerate(prompts)]

    start = time.time()

    result = await generate_sequential_images(
        article_title=TEST_TOPIC,
        sections=sections,
        app=TEST_APP,
        custom_prompts=prompts
    )

    elapsed = time.time() - start

    print_section(f"Images Generated ({elapsed:.1f}s)")

    images = result.get("images", [])
    for i, img in enumerate(images):
        print(f"  Image {i+1}: {img.get('url', 'N/A')[:60]}...")

    print(f"Total cost: ${result.get('total_cost', 0):.4f}")

    return result


async def test_full_pipeline():
    """Run the complete pipeline."""
    print_header("FULL PIPELINE TEST")
    print(f"Topic: {TEST_TOPIC}")
    print(f"App: {TEST_APP}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")

    total_start = time.time()

    # 1. Curation
    curation = await test_curation()

    # 2. Article generation
    article_result = await test_article_generation(curation)
    article = article_result.get("article", {})

    # 3. Video generation (using FEATURED prompt)
    featured_prompt = article.get("featured_image_prompt")
    if featured_prompt:
        video_result = await test_video_generation(featured_prompt)
    else:
        print("\n⚠️  Skipping video - no FEATURED prompt")
        video_result = None

    # 4. Image generation (using section prompts)
    section_prompts = article.get("section_image_prompts", [])
    if section_prompts:
        image_result = await test_image_generation(section_prompts[:3])
    else:
        print("\n⚠️  Skipping images - no section prompts")
        image_result = None

    # Summary
    total_elapsed = time.time() - total_start

    print_header(f"PIPELINE COMPLETE ({total_elapsed:.1f}s)")
    print(f"\n📝 Article: {article.get('title')}")
    print(f"   Words: {article.get('word_count')}")

    if video_result:
        print(f"\n🎬 Video: {video_result.get('video_url', 'N/A')[:60]}...")

    if image_result:
        print(f"\n🖼️  Images: {len(image_result.get('images', []))} generated")

    # Total cost
    total_cost = (
        article_result.get("cost", 0) +
        (video_result.get("cost", 0) if video_result else 0) +
        (image_result.get("total_cost", 0) if image_result else 0)
    )
    print(f"\n💰 Total cost: ${total_cost:.4f}")


async def main():
    """Main entry point."""

    if len(sys.argv) > 1:
        test = sys.argv[1].lower()

        if test == "curation":
            await test_curation()
        elif test == "article":
            await test_article_generation()
        elif test == "video":
            await test_video_generation()
        elif test == "images":
            await test_image_generation()
        else:
            print(f"Unknown test: {test}")
            print("Options: curation, article, video, images")
            sys.exit(1)
    else:
        await test_full_pipeline()

    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
