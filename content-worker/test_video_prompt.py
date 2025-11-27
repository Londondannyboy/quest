"""
Quick test script for video prompt workflow phases.
Skips research/crawling - uses fake article content to test:
1. generate_four_act_video_prompt_brief (Phase 8a)
2. generate_four_act_video_prompt (Phase 8b)
"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

# Import the activities we want to test
from src.activities.generation.article_generation import (
    generate_four_act_video_prompt,
    generate_four_act_video_prompt_brief,
)

# Fake article with 4 sections (simulates what comes from generate_four_act_article)
FAKE_ARTICLE = {
    "id": 999,
    "title": "Digital Nomad Visa Cyprus 2025",
    "slug": "digital-nomad-visa-cyprus-2025",
    "app": "relocation",
    "article_type": "guide",
    "content": "<h2>Section 1</h2><p>Content about Cyprus visa requirements...</p>",
    "four_act_content": [
        {
            "title": "The Dream Begins",
            "content": "Many professionals dream of working from Cyprus...",
            "four_act_visual_hint": "",  # Empty - needs brief generation
            "video_title": "THE SPARK"
        },
        {
            "title": "The Challenge",
            "content": "The application process can be complex...",
            "four_act_visual_hint": "",
            "video_title": "THE GRIND"
        },
        {
            "title": "The Solution",
            "content": "Cyprus offers a straightforward digital nomad visa...",
            "four_act_visual_hint": "",
            "video_title": "THE BREAKTHROUGH"
        },
        {
            "title": "The New Life",
            "content": "Living and working in Cyprus opens new opportunities...",
            "four_act_visual_hint": "",
            "video_title": "THE HORIZON"
        }
    ]
}

# Article WITH briefs already filled (for testing assembly only)
FAKE_ARTICLE_WITH_BRIEFS = {
    "id": 999,
    "title": "Digital Nomad Visa Cyprus 2025",
    "slug": "digital-nomad-visa-cyprus-2025",
    "app": "relocation",
    "article_type": "guide",
    "four_act_content": [
        {
            "title": "The Dream Begins",
            "four_act_visual_hint": "Wide establishing shot of Limassol marina at golden hour, boats bobbing gently, Mediterranean sea sparkling",
            "video_title": "THE SPARK"
        },
        {
            "title": "The Challenge",
            "four_act_visual_hint": "Close-up of hands typing on laptop in busy cafe, documents scattered, stressed expression",
            "video_title": "THE GRIND"
        },
        {
            "title": "The Solution",
            "four_act_visual_hint": "Person receiving approval letter, smile spreading across face, relief and joy",
            "video_title": "THE BREAKTHROUGH"
        },
        {
            "title": "The New Life",
            "four_act_visual_hint": "Aerial drone shot pulling back from person working on rooftop terrace overlooking Cyprus hills",
            "video_title": "THE HORIZON"
        }
    ]
}


async def test_brief_generation():
    """Test Phase 8a: Generate briefs from article sections"""
    print("\n" + "="*60)
    print("TEST 1: generate_four_act_video_prompt_brief (Phase 8a)")
    print("="*60)

    try:
        result = await generate_four_act_video_prompt_brief(
            article=FAKE_ARTICLE,
            app="relocation",
            character_style=None
        )

        print(f"\nSuccess: {result.get('success')}")
        print(f"Template used: {result.get('template_used')}")
        print(f"Cost: ${result.get('cost', 0):.4f}")

        if result.get("success"):
            four_act = result.get("four_act_content", [])
            print(f"\nGenerated {len(four_act)} sections:")
            for i, section in enumerate(four_act[:4]):
                hint = section.get("four_act_visual_hint", "")[:80]
                print(f"  Act {i+1}: {hint}...")
        else:
            print(f"\nError: {result.get('error')}")

        return result

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_prompt_assembly():
    """Test Phase 8b: Assemble video prompt from briefs"""
    print("\n" + "="*60)
    print("TEST 2: generate_four_act_video_prompt (Phase 8b)")
    print("="*60)

    try:
        result = await generate_four_act_video_prompt(
            article=FAKE_ARTICLE_WITH_BRIEFS,
            app="relocation",
            video_model="seedance",
            character_style=None
        )

        print(f"\nSuccess: {result.get('success')}")
        print(f"Model: {result.get('model')}")
        print(f"Acts: {result.get('acts')}")
        print(f"Cost: ${result.get('cost', 0):.4f}")

        if result.get("success"):
            prompt = result.get("prompt", "")
            print(f"\n--- ASSEMBLED PROMPT ({len(prompt)} chars) ---")
            print(prompt[:1000])
            if len(prompt) > 1000:
                print(f"... (truncated, {len(prompt)} total chars)")
        else:
            print(f"\nError: {result.get('error')}")

        return result

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_assembly_without_briefs():
    """Test Phase 8b with missing briefs - should fail cleanly"""
    print("\n" + "="*60)
    print("TEST 3: Assembly WITHOUT briefs (should fail cleanly)")
    print("="*60)

    try:
        result = await generate_four_act_video_prompt(
            article=FAKE_ARTICLE,  # Has empty four_act_visual_hint
            app="relocation",
            video_model="seedance",
            character_style=None
        )

        print(f"\nSuccess: {result.get('success')}")
        if not result.get("success"):
            print(f"Expected failure: {result.get('error')}")
        else:
            print("WARNING: Should have failed but didn't!")

        return result

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    print("\n" + "#"*60)
    print("# VIDEO PROMPT WORKFLOW TEST")
    print("# Testing fixes for Phase 8a/8b")
    print("#"*60)

    # Test 1: Brief generation (uses AI - costs ~$0.01)
    await test_brief_generation()

    # Test 2: Prompt assembly (no AI - free)
    await test_prompt_assembly()

    # Test 3: Assembly without briefs (should fail cleanly)
    await test_assembly_without_briefs()

    print("\n" + "#"*60)
    print("# TESTS COMPLETE")
    print("#"*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
