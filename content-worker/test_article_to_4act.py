#!/usr/bin/env python3
"""
Article → 4-Act Video Prompt Pipeline Test

Tests the full article generation → video prompt flow:
1. generate_article_content (Sonnet) → 4 sections with visual_hints
2. generate_four_act_video_prompt → combines hints into 4-act prompt

This is the expensive AI call (~$0.10-0.20) but skips video generation.

Usage:
  python3 test_article_to_4act.py              # Full test
  python3 test_article_to_4act.py --mock       # Use mock article (skip AI)
"""

import asyncio
import sys
import json
from dotenv import load_dotenv

load_dotenv()


async def test_article_generation():
    """Test: generate_article_content creates 4 sections with visual_hints"""
    print("\n" + "=" * 70)
    print("  TEST 1: generate_article_content (Sonnet)")
    print("  Expecting: 4 sections, each with visual_hint")
    print("=" * 70)

    from src.activities.generation.article_generation import generate_article_content

    # Test topic
    topic = "Cyprus Digital Nomad Visa 2025"
    app = "relocation"

    # Mock research context (minimal - just enough for article generation)
    research_context = {
        "sources": [
            {
                "url": "https://example.com/cyprus-visa",
                "title": "Cyprus Digital Nomad Visa Guide",
                "content": "Cyprus launched its Digital Nomad Visa in 2022. Requirements: €3,500/month income, valid passport, health insurance. Duration: 1 year renewable for 2 more. Tax benefits available. Cost of living 30-40% lower than London. 3,400 hours sunshine annually vs UK's 1,500 hours.",
                "relevance_score": 0.95
            },
            {
                "url": "https://example.com/cyprus-tax",
                "title": "Cyprus Tax Benefits for Remote Workers",
                "content": "Cyprus offers favorable tax treatment for digital nomads. Non-dom status available. Corporate tax 12.5%. No inheritance tax. Strategic location between Europe, Middle East and Africa.",
                "relevance_score": 0.90
            }
        ],
        "key_facts": [
            "Cyprus Digital Nomad Visa launched 2022",
            "Income requirement: €3,500/month",
            "Duration: 1 year + 2 renewals possible",
            "3,400 hours sunshine vs UK's 1,500",
            "Cost of living 30-40% lower than London",
            "Processing time: 4-6 weeks"
        ],
        "jurisdiction": "Cyprus"
    }

    print(f"\n  Topic: {topic}")
    print(f"  App: {app}")
    print(f"  Generating article... (takes 30-60 seconds)")

    result = await generate_article_content(
        topic=topic,
        article_type="guide",
        app=app,
        research_context=research_context,
        target_word_count=1500
    )

    print(f"\n  --- ARTICLE GENERATION RESULT ---")
    print(f"  Success: {'title' in result}")
    print(f"  Title: {result.get('title', 'N/A')}")
    print(f"  Word count: {result.get('word_count', 0)}")
    print(f"  Section count: {result.get('section_count', 0)}")
    print(f"  Cost: ${result.get('cost', 0):.4f}")

    # Check structured_sections
    structured_sections = result.get("structured_sections", [])
    print(f"\n  --- STRUCTURED SECTIONS ({len(structured_sections)}) ---")

    all_have_visual_hints = True
    for i, section in enumerate(structured_sections):
        title = section.get("title", "No title")
        visual_hint = section.get("visual_hint", "")
        has_hint = bool(visual_hint)

        if not has_hint:
            all_have_visual_hints = False

        print(f"\n  Section {i+1}: {title}")
        print(f"    Has visual_hint: {'✅' if has_hint else '❌'}")
        if has_hint:
            print(f"    Visual hint: {visual_hint[:100]}...")

    print(f"\n  --- VALIDATION ---")
    print(f"  Has 4 sections: {'✅' if len(structured_sections) == 4 else '❌'} ({len(structured_sections)})")
    print(f"  All have visual_hints: {'✅' if all_have_visual_hints else '❌'}")

    return result


async def test_four_act_prompt(article):
    """Test: generate_four_act_video_prompt creates proper 4-act prompt"""
    print("\n" + "=" * 70)
    print("  TEST 2: generate_four_act_video_prompt")
    print("  Expecting: 4 acts from visual_hints, app config styling")
    print("=" * 70)

    from src.activities.generation.media_prompts import generate_four_act_video_prompt

    app = "relocation"

    print(f"\n  App: {app}")
    print(f"  Video model: seedance")
    print(f"  Generating prompt...")

    result = await generate_four_act_video_prompt(
        article=article,
        app=app,
        video_model="seedance"
    )

    print(f"\n  --- VIDEO PROMPT RESULT ---")
    print(f"  Success: {result.get('success')}")
    print(f"  Acts: {result.get('acts')}")
    print(f"  Prompt length: {len(result.get('prompt', ''))} chars")
    print(f"  Was truncated: {result.get('was_truncated')}")
    print(f"  Model: {result.get('model')}")

    prompt = result.get("prompt", "")

    # Check for 4-act structure
    print(f"\n  --- 4-ACT STRUCTURE CHECK ---")
    has_act_1 = "ACT 1" in prompt
    has_act_2 = "ACT 2" in prompt
    has_act_3 = "ACT 3" in prompt
    has_act_4 = "ACT 4" in prompt

    print(f"  ACT 1 present: {'✅' if has_act_1 else '❌'}")
    print(f"  ACT 2 present: {'✅' if has_act_2 else '❌'}")
    print(f"  ACT 3 present: {'✅' if has_act_3 else '❌'}")
    print(f"  ACT 4 present: {'✅' if has_act_4 else '❌'}")

    # Check for app config elements
    print(f"\n  --- APP CONFIG CHECK (relocation) ---")
    has_no_text_rule = "NO text" in prompt or "no text" in prompt.lower()
    has_style = "STYLE:" in prompt
    has_timing = "0s-3s" in prompt or "0-3" in prompt

    print(f"  No-text rule: {'✅' if has_no_text_rule else '❌'}")
    print(f"  Style directive: {'✅' if has_style else '❌'}")
    print(f"  Act timing: {'✅' if has_timing else '❌'}")

    print(f"\n  --- FULL PROMPT ---")
    print(f"  {prompt}")

    return result


def get_mock_article():
    """Return a mock article for testing without AI generation"""
    return {
        "title": "Cyprus Digital Nomad Visa 2025: Your Complete Escape Plan",
        "slug": "cyprus-digital-nomad-visa-2025",
        "content": "<p>Test content</p>",
        "word_count": 1500,
        "section_count": 4,
        "structured_sections": [
            {
                "title": "The London Grind: Why Remote Workers Are Burning Out",
                "content": "<p>Section 1 content</p>",
                "visual_hint": "Dark grey London office interior, rain streaming down floor-to-ceiling windows. A woman in her 30s sits at a desk, blue monitor glow on her tired face, grey suit, slouched posture. Dreary cityscape visible through rain-streaked glass. Muted colors, cold fluorescent lighting. Camera slowly pulls back."
            },
            {
                "title": "The Cyprus Opportunity: Tax Benefits That Make Sense",
                "content": "<p>Section 2 content</p>",
                "visual_hint": "Same woman now at home, warm evening golden hour light streaming through window. She's looking at her laptop with hope and discovery. Screen shows Mediterranean coastline imagery. Warm color palette, soft shadows. Camera gently pushes in on her hopeful expression."
            },
            {
                "title": "Making the Move: From Application to Arrival",
                "content": "<p>Section 3 content</p>",
                "visual_hint": "Travel montage: hands packing a suitcase with summer clothes, a passport being placed in a bag, airplane window showing clouds then transitioning to aerial view of Cyprus coastline, golden Mediterranean waters below. Warm sunlight, sense of anticipation. Smooth cinematic transitions."
            },
            {
                "title": "Life After the Move: Six Months in Cyprus",
                "content": "<p>Section 4 content</p>",
                "visual_hint": "Golden sunset terrace overlooking the Mediterranean Sea. The woman now in a flowing linen dress, holding a wine glass, genuine smile on her face. Friends laughing at an outdoor table nearby. Warm golden light, vibrant colors, palm trees swaying. Camera slowly orbits around her, pure contentment."
            }
        ],
        "cost": 0
    }


async def main():
    print("\n" + "=" * 70)
    print("  ARTICLE → 4-ACT VIDEO PROMPT PIPELINE TEST")
    print("=" * 70)

    use_mock = "--mock" in sys.argv

    if use_mock:
        print("\n  Using MOCK article (skipping AI generation)")
        article = get_mock_article()
    else:
        print("\n  Running FULL test (AI article generation)")
        print("  This will cost ~$0.10-0.20 for Claude Sonnet")

        # Test 1: Article generation
        article = await test_article_generation()

        if not article.get("structured_sections"):
            print("\n  ❌ FAILED: No structured_sections in article")
            return

    # Test 2: 4-act video prompt
    prompt_result = await test_four_act_prompt(article)

    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)

    sections = article.get("structured_sections", [])
    has_4_sections = len(sections) == 4
    all_have_hints = all(s.get("visual_hint") for s in sections)
    prompt_success = prompt_result.get("success", False)
    has_4_acts = prompt_result.get("acts", 0) == 4

    print(f"\n  Article has 4 sections: {'✅' if has_4_sections else '❌'}")
    print(f"  All sections have visual_hints: {'✅' if all_have_hints else '❌'}")
    print(f"  Video prompt generated: {'✅' if prompt_success else '❌'}")
    print(f"  Prompt has 4 acts: {'✅' if has_4_acts else '❌'}")

    if has_4_sections and all_have_hints and prompt_success and has_4_acts:
        print("\n  ✅ ALL TESTS PASSED - 4-Act Pipeline Working!")
    else:
        print("\n  ❌ SOME TESTS FAILED")


if __name__ == "__main__":
    asyncio.run(main())
