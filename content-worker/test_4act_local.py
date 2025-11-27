"""
Local test for 4-act article + video flow.
Bypasses Temporal and research to test generation directly.
"""

import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

# Mock the activity module
import src.activities.generation.article_generation as article_gen
import src.activities.media.video_generation as video_gen

class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARN: {msg}")
    def error(self, msg, **kwargs): print(f"ERROR: {msg}")

class MockActivity:
    logger = MockLogger()

article_gen.activity = MockActivity()
video_gen.activity = MockActivity()

from src.activities.generation.article_generation import (
    generate_four_act_article,
    generate_four_act_video_prompt
)
from src.activities.media.video_generation import generate_four_act_video


async def test_full_flow(skip_video: bool = True):
    """
    Test the full 4-act flow:
    1. generate_four_act_article (with mock research)
    2. generate_four_act_video_prompt (assembles video prompt)
    3. generate_four_act_video (optional - costs money)
    """

    print("\n" + "="*70)
    print("LOCAL TEST: 4-Act Article → Video Prompt → Video")
    print("="*70 + "\n")

    # ========== STEP 1: Generate Article ==========
    print("STEP 1: Generating 4-act article...")

    # Minimal research context (skip the 10-minute crawl)
    research_context = {
        "curated_sources": [
            {
                "title": "Cyprus Digital Nomad Visa 2025 Guide",
                "url": "https://www.cyprusvisa.gov.cy/digital-nomad",
                "relevance_score": 9,
                "full_content": """
                Cyprus launched its Digital Nomad Visa in 2022, allowing remote workers
                to live and work from the Mediterranean island.

                Requirements:
                - Minimum monthly income: €3,500 from remote work
                - Health insurance with €30,000 coverage
                - Clean criminal record
                - Valid passport (6+ months)

                Costs:
                - Application fee: €70
                - Residence permit: €150
                - Total government fees: €220

                Timeline:
                - Processing time: 6-8 weeks
                - Valid for: 1 year
                - Renewable: Up to 3 years total

                Benefits:
                - 17-year non-dom tax status available
                - EU member state access
                - 340 days of sunshine per year
                - Cost of living 30-40% lower than London

                Popular locations: Limassol, Paphos, Nicosia, Larnaca
                """
            }
        ],
        "key_facts": [
            "Cyprus Digital Nomad Visa requires €3,500/month income",
            "Total cost: €220 (€70 application + €150 permit)",
            "Processing takes 6-8 weeks",
            "Valid for 1 year, renewable twice",
            "17-year non-dom tax status available"
        ],
        "all_source_urls": [
            {"url": "https://www.cyprusvisa.gov.cy", "title": "Official Cyprus Visa Portal", "authority": "government"}
        ]
    }

    article_result = await generate_four_act_article(
        topic="Cyprus Digital Nomad Visa 2025: Complete Guide",
        article_type="guide",
        app="relocation",
        research_context=research_context,
        target_word_count=1500,
        custom_slug=None
    )

    if not article_result.get("success"):
        print(f"❌ Article generation failed: {article_result.get('error')}")
        return

    article = article_result["article"]
    print(f"✅ Article generated: {article.get('title')}")
    print(f"   Words: {article.get('word_count')}")
    print(f"   Sections: {len(article.get('four_act_content', []))}")

    # Show guide_mode and yolo_mode
    guide_mode = article.get("guide_mode", {})
    yolo_mode = article.get("yolo_mode", {})

    print(f"\n   Guide Mode: {len(guide_mode.get('key_facts', []))} facts, {len(guide_mode.get('checklist', []))} checklist items")
    print(f"   YOLO Mode: '{yolo_mode.get('headline', 'N/A')[:50]}...'")

    # ========== STEP 2: Generate Video Prompt ==========
    print("\n" + "-"*70)
    print("STEP 2: Generating video prompt from 4-act content...")

    four_act_content = article.get("four_act_content", [])

    if not four_act_content:
        print("❌ No four_act_content in article!")
        return

    # Show the visual hints
    print(f"\n   4-Act Visual Hints:")
    for i, section in enumerate(four_act_content[:4]):
        hint = section.get("four_act_visual_hint", "No hint")
        print(f"   Act {i+1}: {hint[:80]}...")

    video_prompt_result = await generate_four_act_video_prompt(
        article=article,
        app="relocation",
        video_model="seedance"
    )

    if not video_prompt_result.get("success"):
        print(f"❌ Video prompt failed: {video_prompt_result.get('error')}")
        return

    video_prompt = video_prompt_result.get("prompt", "")
    print(f"\n✅ Video prompt generated ({len(video_prompt)} chars)")
    print(f"\n   PROMPT:\n   {video_prompt[:500]}...")

    # ========== STEP 3: Generate Video (Optional) ==========
    if skip_video:
        print("\n" + "-"*70)
        print("STEP 3: SKIPPED (set skip_video=False to generate actual video)")
        print("        This would cost ~$0.05-0.10 via Replicate")
    else:
        print("\n" + "-"*70)
        print("STEP 3: Generating 4-act video via Replicate...")

        video_result = await generate_four_act_video(
            title=article.get("title"),
            video_prompt=video_prompt,
            app="relocation",
            quality="medium",
            duration=12,
            aspect_ratio="16:9",
            model="seedance",
            featured_image_prompt=""  # Optional
        )

        if video_result.get("success"):
            print(f"✅ Video generated!")
            print(f"   Mux Playback ID: {video_result.get('mux_playback_id')}")
            print(f"   Duration: {video_result.get('duration')}s")
            print(f"   Thumbnails: {len(video_result.get('thumbnails', []))}")
        else:
            print(f"❌ Video generation failed: {video_result.get('error')}")

    # ========== Summary ==========
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Article: {article.get('title')}")
    print(f"Words: {article.get('word_count')}")
    print(f"4-Act Sections: {len(four_act_content)}")
    print(f"Video Prompt: {len(video_prompt)} chars")
    print(f"Guide Mode: ✅" if guide_mode.get("summary") else "Guide Mode: ❌")
    print(f"YOLO Mode: ✅" if yolo_mode.get("headline") else "YOLO Mode: ❌")
    print(f"Cost: ${article_result.get('cost', 0):.4f}")

    # Save full output for inspection
    with open("/Users/dankeegan/quest/content-worker/test_4act_output.json", "w") as f:
        json.dump({
            "article": article,
            "video_prompt": video_prompt,
            "guide_mode": guide_mode,
            "yolo_mode": yolo_mode
        }, f, indent=2)
    print(f"\n📄 Full output saved to: test_4act_output.json")


if __name__ == "__main__":
    # Set skip_video=False to actually generate video (costs money)
    asyncio.run(test_full_flow(skip_video=True))
