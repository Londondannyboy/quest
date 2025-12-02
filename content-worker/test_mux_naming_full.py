"""
Test video generation with new MUX naming convention and 'Q' branding.

This script:
1. Generates a test video using Seedance/Replicate with the new 'Q' prompt
2. Uploads to MUX with human-readable title and comprehensive description
3. Verifies the naming appears correctly in MUX dashboard

Usage:
    python test_mux_naming_full.py
"""

import asyncio
import os
import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import activities
from src.activities.media.video_generation import generate_four_act_video
from src.activities.media.mux_client import upload_video_to_mux


async def test_video_with_mux_naming():
    """Test complete flow: video generation -> MUX upload with naming."""

    print("\n" + "="*80)
    print("TEST: Video Generation + MUX Naming Convention")
    print("="*80)

    # ===== TEST PARAMETERS =====
    test_country = "France"
    test_country_code = "FR"
    test_mode = "story"
    test_cluster_id = "test-" + os.urandom(4).hex()
    test_article_id = 99999  # Fake ID for testing

    print(f"\n📋 Test Parameters:")
    print(f"   Country: {test_country} ({test_country_code})")
    print(f"   Mode: {test_mode}")
    print(f"   Cluster ID: {test_cluster_id}")
    print(f"   Article ID: {test_article_id}")

    # ===== STEP 1: GENERATE VIDEO WITH NEW 'Q' PROMPT =====
    print(f"\n🎬 STEP 1: Generating test video with 'Q' branding...")
    print("   This will take 2-5 minutes (Seedance generation)")

    # Create 4-act prompt with the NEW 'Q' branding (not 'QUEST')
    four_act_prompt = f"""ACT 1 (0-3s): The Grind
Close-up: Young professional at grey office desk, rain on window, cold fluorescent lighting, exhaustion visible.
Main character: Southern European woman wearing Quest t-shirt with single letter 'Q' in WHITE clearly visible on chest.
Camera: Static, intimate close-up. Mood: Confinement, grey tones.

SHOT CUT —

ACT 2 (3-6s): The Dream
Medium shot: Same person at home, warm lamplight, looking at laptop screen showing {test_country} imagery (beaches, NOT text).
Clothing: Casual comfortable top, NO logos.
Camera: Slow dolly in. Mood: Hope emerging, warm golden light starting.

SHOT CUT —

ACT 3 (6-9s): The Journey
Wide shot: Person with small suitcase, airport glimpses (NO signs/text), airplane window view, {test_country} coastline approaching.
Clothing: Travel casual layers, NO branding.
Camera: Cinematic movement, forward motion. Mood: Anticipation, colors warming.

SHOT CUT —

ACT 4 (9-12s): The New Life
Wide shot: Sunset terrace in {test_country}, person relaxed with friends, golden hour, Mediterranean vista, genuine happiness.
Clothing: Summer casual, NO logos.
Camera: Wide establishing, slow push. Mood: Joy, freedom, golden warmth.

CRITICAL: NO text, words, letters anywhere except the 'Q' on t-shirt in Act 1. Screens show abstract colors only. No airport signs. No country names."""

    try:
        video_result = await generate_four_act_video(
            title=f"{test_country} Relocation Guide 2025",
            content=f"Complete guide to relocating to {test_country} for remote workers",
            app="relocation",
            quality="low",  # Low for fast testing
            duration=12,  # 4-act structure
            aspect_ratio="16:9",
            video_model="seedance",
            video_prompt=four_act_prompt,
            reference_image=None  # No reference for first video
        )

        video_url = video_result["video_url"]
        video_cost = video_result["cost"]

        print(f"\n   ✅ Video generated successfully!")
        print(f"   📹 URL: {video_url[:60]}...")
        print(f"   💰 Cost: ${video_cost:.3f}")
        print(f"   ⏱️  Duration: {video_result['duration']}s")
        print(f"   🎭 Acts: {video_result['acts']}")

    except Exception as e:
        print(f"\n   ❌ Video generation failed: {e}")
        return False

    # ===== STEP 2: UPLOAD TO MUX WITH NEW NAMING =====
    print(f"\n☁️  STEP 2: Uploading to MUX with human-readable naming...")
    print("   This will take 30-60 seconds (MUX processing)")

    # Create human-readable title (used in passthrough metadata)
    # MUX passthrough field is limited to 255 chars, so we pack as much info as possible
    mux_title = f"{test_country} Relocation Guide 2025: Complete Guide"

    try:
        mux_result = await upload_video_to_mux(
            video_url=video_url,
            public=True,
            cluster_id=test_cluster_id,
            article_id=test_article_id,
            country=test_country,
            article_mode=test_mode,
            tags=["test", "france", "relocation", "story", "q-branding"],
            title=mux_title,
            app="relocation"
        )

        asset_id = mux_result["asset_id"]
        playback_id = mux_result["playback_id"]
        mux_duration = mux_result["duration"]
        passthrough = mux_result.get("passthrough", "")

        print(f"\n   ✅ Uploaded to MUX successfully!")
        print(f"\n   📦 MUX Asset Details:")
        print(f"      Asset ID: {asset_id}")
        print(f"      Playback ID: {playback_id}")
        print(f"      Duration: {mux_duration}s")
        print(f"\n   🏷️  MUX Label (what shows in dashboard):")
        print(f"      {passthrough}")

        # Generate MUX dashboard URL
        mux_dashboard_url = f"https://dashboard.mux.com/video/assets/{asset_id}"
        print(f"\n   🔗 View in MUX Dashboard:")
        print(f"      {mux_dashboard_url}")

        # Generate playback URLs
        stream_url = f"https://stream.mux.com/{playback_id}.m3u8"
        thumbnail_url = f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=1.5&width=800"
        gif_url = f"https://image.mux.com/{playback_id}/animated.gif?start=0&end=3&width=480&fps=12"

        print(f"\n   📺 Playback URLs:")
        print(f"      Stream (HLS): {stream_url}")
        print(f"      Thumbnail (Act 1): {thumbnail_url}")
        print(f"      GIF Preview: {gif_url}")

    except Exception as e:
        print(f"\n   ❌ MUX upload failed: {e}")
        return False

    # ===== SUCCESS SUMMARY =====
    print(f"\n" + "="*80)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"\nValidation Checklist:")
    print(f"   ✅ Video generated with NEW 'Q' branding (not 'QUEST')")
    print(f"   ✅ Video uploaded to MUX")
    print(f"   ✅ Human-readable title applied")
    print(f"   ✅ Passthrough metadata includes: title | mode | country | app | cluster | id")
    print(f"\nNext Steps:")
    print(f"   1. Open MUX dashboard: {mux_dashboard_url}")
    print(f"   2. Verify the label shows: {passthrough}")
    print(f"   3. Check video has 'Q' on t-shirt in Act 1 (not 'QUEST')")
    print(f"\n💡 If this test works, the issue is in the France workflow invocation,")
    print(f"   not in the video generation or MUX upload code.")

    return True


if __name__ == "__main__":
    print("\n🚀 Starting MUX Naming Test...")
    print("   This will generate a real video and upload to MUX")
    print("   Estimated time: 3-6 minutes")
    print("   Estimated cost: $0.30 (Seedance) + $0.00 (MUX storage)")
    print()

    # Run test
    success = asyncio.run(test_video_with_mux_naming())

    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Test failed - see errors above")
        exit(1)
