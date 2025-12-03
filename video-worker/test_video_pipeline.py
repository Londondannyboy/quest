"""
Test Video Pipeline - Replicate + Mux Integration

Tests the full video generation pipeline:
1. Simple prompt generation
2. Video generation with Replicate (Seedance)
3. MUX upload
4. Validation

Run: python3 test_video_pipeline.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.activities.generation.article_generation import generate_simple_video_prompt
from src.activities.media.video_generation import generate_four_act_video
from src.activities.media.mux_client import upload_video_to_mux


async def test_pipeline():
    """Test the full video pipeline"""

    print("=" * 70)
    print("🎬 VIDEO PIPELINE TEST")
    print("=" * 70)

    # Test article data (simulating a hub)
    test_article = {
        "id": 999,
        "title": "France Relocation Guide",
        "slug": "france-relocation-guide",
        "location_name": "France",
        "country": "France",
        "is_hub": True
    }

    # ===== STEP 1: Generate Simple Prompt =====
    print("\n" + "=" * 70)
    print("STEP 1: Generate Simple Video Prompt")
    print("=" * 70)

    try:
        prompt_result = await generate_simple_video_prompt(
            article=test_article,
            app="relocation",
            video_model="seedance"
        )

        if not prompt_result.get("success"):
            print("❌ FAILED: Prompt generation failed")
            return False

        prompt = prompt_result.get("prompt", "")
        print(f"✅ SUCCESS: Generated prompt ({len(prompt)} chars)")
        print(f"\nPrompt preview:")
        print("-" * 70)
        print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
        print("-" * 70)

        # Validate prompt structure
        required_acts = ["ACT 1", "ACT 2", "ACT 3", "ACT 4"]
        missing_acts = [act for act in required_acts if act not in prompt]

        if missing_acts:
            print(f"❌ FAILED: Missing acts in prompt: {missing_acts}")
            return False

        print(f"✅ Validation: All 4 acts present (ACT 1, ACT 2, ACT 3, ACT 4)")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ===== STEP 2: Generate Video with Replicate =====
    print("\n" + "=" * 70)
    print("STEP 2: Generate Video with Replicate (Seedance)")
    print("=" * 70)
    print("⚠️  This will take 1-3 minutes and cost $0.30...")

    try:
        video_result = await generate_four_act_video(
            title=test_article["title"],
            content="",  # Not needed when video_prompt is provided
            app="relocation",
            quality="low",
            duration=12,
            aspect_ratio="16:9",
            video_model="seedance",
            video_prompt=prompt,
            reference_image=None
        )

        if not video_result.get("video_url"):
            print(f"❌ FAILED: No video URL returned")
            print(f"Result: {video_result}")
            return False

        video_url = video_result.get("video_url")
        print(f"✅ SUCCESS: Video generated")
        print(f"   URL: {video_url}")
        print(f"   Model: {video_result.get('model')}")
        print(f"   Duration: {video_result.get('duration')}s")
        print(f"   Cost: ${video_result.get('cost', 0):.3f}")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ===== STEP 3: Upload to MUX =====
    print("\n" + "=" * 70)
    print("STEP 3: Upload Video to MUX")
    print("=" * 70)
    print("⚠️  This will take 30-60 seconds...")

    try:
        mux_result = await upload_video_to_mux(
            video_url=video_url,
            article_id=test_article["id"],
            title=test_article["title"],
            app="relocation",
        )

        if not mux_result.get("playback_id"):
            print(f"❌ FAILED: No playback_id returned")
            print(f"   Result: {mux_result}")
            return False

        playback_id = mux_result.get("playback_id")
        asset_id = mux_result.get("asset_id")

        print(f"✅ SUCCESS: Video uploaded to MUX")
        print(f"   Playback ID: {playback_id}")
        print(f"   Asset ID: {asset_id}")
        print(f"   Stream URL: https://stream.mux.com/{playback_id}.m3u8")
        print(f"   Thumbnail: https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.5")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ===== SUCCESS =====
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print(f"\n📺 Watch your video:")
    print(f"   https://stream.mux.com/{playback_id}.m3u8")
    print(f"\n🖼️  Thumbnail:")
    print(f"   https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.5")
    print(f"\n🎞️  GIF:")
    print(f"   https://image.mux.com/{playback_id}/animated.gif?start=0&end=12&width=640&fps=12")

    return True


if __name__ == "__main__":
    print("\n🎬 Starting Video Pipeline Test...")
    print("   This will test: Prompt → Replicate → MUX")
    print("   Cost: ~$0.30 | Time: ~2-4 minutes\n")

    # Check environment variables
    required_vars = ["REPLICATE_API_TOKEN", "MUX_TOKEN_ID", "MUX_TOKEN_SECRET"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    try:
        result = asyncio.run(test_pipeline())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
