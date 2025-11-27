"""
FULL END-TO-END VIDEO PIPELINE TEST
Uses real article from Neon → Assembles prompt → Triggers Replicate
"""

import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

from src.activities.generation.article_generation import generate_four_act_video_prompt
from src.activities.media.video_generation import generate_four_act_video

# Real article from Neon (Cyprus Digital Nomad Visa)
REAL_ARTICLE = {
    "id": 81,
    "slug": "cyprus-digital-nomad-visa-2025-guide",
    "title": "Cyprus Digital Nomad Visa 2025: Your Complete Guide to Mediterranean Remote Work",
    "app": "relocation",  # Changed to relocation for proper config
    "article_type": "guide",
    "four_act_content": [
        {
            "act": 1,
            "title": "The Grind: Why Remote Workers Are Burning Out in Expensive Cities",
            "factoid": "£2,500+ monthly for London one-bedroom flats",
            "video_title": "Urban Burnout",
            "four_act_visual_hint": "Exhausted professional in cramped London flat stares at rain-streaked window, laptop glowing harsh. Camera pushes slowly to close-up as subject rubs temples. Cool blue-grey tones, harsh fluorescent light. Documentary realism, shallow depth of field."
        },
        {
            "act": 2,
            "title": "The Cyprus Opportunity: Tax Benefits That Actually Make Sense",
            "factoid": "Up to 17 years of tax exemptions available",
            "video_title": "Mediterranean Dream",
            "four_act_visual_hint": "Same person at home, warm lamplight on face reading Cyprus visa information on laptop screen. Expression shifts from tired to hopeful, soft smile emerging. Golden hour glow through window, warm amber tones, intimate close-up."
        },
        {
            "act": 3,
            "title": "Making the Move: From Application to Arrival",
            "factoid": "6-8 weeks processing time from application",
            "video_title": "The Journey",
            "four_act_visual_hint": "Airport departure lounge, person with laptop bag walks toward gate, airplane window view of Mediterranean coastline approaching. Camera follows movement, reveals Cyprus hills and beaches. Bright natural lighting, travel documentary style."
        },
        {
            "act": 4,
            "title": "Life After the Move: What Six Months Actually Looks Like",
            "factoid": "Average €1,800-2,400 monthly savings vs London",
            "video_title": "Cyprus Living?",
            "four_act_visual_hint": "Mediterranean terrace café, person working on laptop with sea view, closes computer and joins friends for sunset drinks. Camera orbits slowly around table, golden hour light, genuine laughter, lifestyle contentment."
        }
    ]
}


async def test_full_pipeline(trigger_replicate: bool = False):
    """
    Full pipeline test:
    1. Assemble video prompt from real article
    2. Optionally trigger Replicate (costs ~$0.10)
    """

    print("\n" + "="*70)
    print("FULL VIDEO PIPELINE TEST - REAL DATA")
    print("="*70)
    print(f"Article: {REAL_ARTICLE['title'][:50]}...")
    print(f"App: {REAL_ARTICLE['app']}")
    print(f"Has four_act_content: {len(REAL_ARTICLE['four_act_content'])} sections")

    # ===== PHASE 8b: ASSEMBLE VIDEO PROMPT =====
    print("\n" + "-"*50)
    print("PHASE 8b: Assembling video prompt...")
    print("-"*50)

    prompt_result = await generate_four_act_video_prompt(
        article=REAL_ARTICLE,
        app=REAL_ARTICLE["app"],
        video_model="seedance",
        character_style=None
    )

    if not prompt_result.get("success"):
        print(f"❌ FAILED: {prompt_result.get('error')}")
        return

    video_prompt = prompt_result.get("prompt", "")
    print(f"✅ SUCCESS: Generated {len(video_prompt)} char prompt")
    print(f"Model: {prompt_result.get('model')}")
    print(f"Acts: {prompt_result.get('acts')}")
    print(f"Cost: ${prompt_result.get('cost', 0):.4f}")

    print("\n--- FULL VIDEO PROMPT ---")
    print(video_prompt)
    print("--- END PROMPT ---\n")

    if not trigger_replicate:
        print("\n⏸️  Replicate trigger SKIPPED (set trigger_replicate=True to generate)")
        print("   This would cost ~$0.10 and take 2-5 minutes")
        return prompt_result

    # ===== PHASE 9: TRIGGER REPLICATE =====
    print("\n" + "-"*50)
    print("PHASE 9: Triggering Replicate (Seedance)...")
    print("-"*50)
    print("⏳ This takes 2-5 minutes...")

    import replicate
    import os

    # Direct Replicate call (simpler than activity wrapper for testing)
    try:
        output = replicate.run(
            "bytedance/seedance-1-pro-fast",
            input={
                "prompt": video_prompt,
                "duration": 12,
                "resolution": "480p",
                "aspect_ratio": "16:9",
                "camera_fixed": False,
                "fps": 24
            }
        )

        # Output is the video URL
        video_url = str(output)
        print(f"✅ VIDEO GENERATED!")
        print(f"   URL: {video_url}")
        print(f"   Duration: 12s")
        print(f"   Cost: ~$0.18")

        video_result = {"success": True, "video_url": video_url}

    except Exception as e:
        print(f"❌ Video generation failed: {e}")
        video_result = {"success": False, "error": str(e)}

    return video_result


async def main():
    import sys

    # Check if user wants to trigger Replicate
    trigger = "--trigger" in sys.argv or "-t" in sys.argv

    if trigger:
        print("\n🚀 FULL TEST MODE: Will trigger Replicate (~$0.10)")
    else:
        print("\n🔍 DRY RUN MODE: Prompt assembly only (free)")
        print("   Add --trigger or -t to actually generate video")

    await test_full_pipeline(trigger_replicate=trigger)

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
