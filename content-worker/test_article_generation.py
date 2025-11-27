"""
TEST ARTICLE GENERATION WITH GEMINI
Tests the `message` variable fix in generate_four_act_article
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from src.activities.generation.article_generation import generate_four_act_article

# Minimal research data to generate a short article
FAKE_RESEARCH = {
    "topic": "Digital Nomad Visa Portugal 2025",
    "curated_sources": [
        {
            "title": "Portugal D7 Visa Guide",
            "url": "https://example.com/portugal-d7",
            "full_content": "Portugal offers the D7 visa for passive income earners and remote workers. Requirements include proof of €760/month income, health insurance, and clean criminal record. Processing takes 2-3 months.",
            "relevance_score": 9
        },
        {
            "title": "Living Costs in Lisbon",
            "url": "https://example.com/lisbon-costs",
            "full_content": "Lisbon average rent is €1,200/month. Coworking spaces cost €150-300/month. Total monthly budget for nomads: €2,000-2,500.",
            "relevance_score": 8
        }
    ],
    "key_facts": [
        {"fact": "Portugal D7 visa requires €760/month minimum income"},
        {"fact": "Processing time is 2-3 months"},
        {"fact": "Visa valid for 2 years, renewable"}
    ]
}


async def test_article_generation():
    """
    Test article generation using Gemini.
    This tests the `message` variable fix.
    """
    print("\n" + "="*70)
    print("TEST: ARTICLE GENERATION WITH GEMINI")
    print("="*70)
    print(f"Topic: {FAKE_RESEARCH['topic']}")
    print(f"Sources: {len(FAKE_RESEARCH['curated_sources'])}")
    print("\n⏳ Generating article (30-60 seconds)...")

    try:
        result = await generate_four_act_article(
            topic=FAKE_RESEARCH["topic"],
            article_type="guide",
            app="relocation",
            research_context=FAKE_RESEARCH,  # Pass full research context
            target_word_count=800,  # Short for testing
            custom_slug=None,
            target_keyword="portugal d7 visa",
            secondary_keywords=["portugal digital nomad", "lisbon remote work"]
        )

        print("\n" + "-"*50)
        print("RESULT")
        print("-"*50)
        print(f"Success: {result.get('success')}")
        print(f"Model: {result.get('model_used')}")
        print(f"Cost: ${result.get('cost', 0):.4f}")

        if result.get("success"):
            article = result.get("article", {})
            print(f"\n📄 ARTICLE:")
            print(f"   Title: {article.get('title')}")
            print(f"   Slug: {article.get('slug')}")
            print(f"   Word count: {article.get('word_count')}")
            print(f"   Sections: {article.get('section_count')}")

            # Check four_act_content
            four_act = article.get("four_act_content", [])
            if four_act:
                print(f"\n🎬 FOUR ACT CONTENT ({len(four_act)} sections):")
                for i, section in enumerate(four_act[:4]):
                    title = section.get("title", section.get("video_title", f"Act {i+1}"))
                    hint = section.get("four_act_visual_hint", "")[:60]
                    print(f"   Act {i+1}: {title}")
                    if hint:
                        print(f"          Hint: {hint}...")
            else:
                print(f"\n⚠️ No four_act_content in article")

            # Show excerpt
            print(f"\n📝 Excerpt: {article.get('excerpt', '')[:150]}...")

        else:
            print(f"\n❌ Error: {result.get('error')}")

        return result

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    print("\n" + "#"*70)
    print("# ARTICLE GENERATION TEST")
    print("# Tests: Gemini API, message variable fix, four_act_content output")
    print("#"*70)

    result = await test_article_generation()

    print("\n" + "#"*70)
    if result and result.get("success"):
        print("# ✅ TEST PASSED")
    else:
        print("# ❌ TEST FAILED")
    print("#"*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
