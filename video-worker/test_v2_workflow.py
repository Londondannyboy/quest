"""
Test VideoEnrichmentV2 - Simulate Temporal Execution

Runs the workflow steps locally without Temporal:
1. Fetch content
2. Generate prompt
3. Generate video (FRESH ACTIVITY - NO VALIDATION)
4. Upload to MUX
5. Update database

Run: python3 test_v2_workflow.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.activities.storage.neon_database import (
    get_article_by_slug,
    get_hub_by_slug,
    update_article_four_act_content,
    update_hub_video,
)
from src.activities.generation.article_generation import (
    generate_simple_video_prompt,
)
from src.activities.media.simple_video_generation import (
    generate_video_simple,
)
from src.activities.media.mux_client import (
    upload_video_to_mux,
)


async def test_v2_workflow():
    """Test VideoEnrichmentV2 workflow end-to-end"""

    print("=" * 70)
    print("🎬 VideoEnrichmentV2 Workflow Test (Simulating Temporal)")
    print("=" * 70)

    # Test configuration
    slug = "netherlands-relocation-move-uk-moved-relocate-guide"
    app = "relocation"

    # ===== STEP 1: Get Content =====
    print("\n" + "=" * 70)
    print("STEP 1/5: Fetching content from database")
    print("=" * 70)

    try:
        print(f"🔍 Looking for article: {slug}")
        article = await get_article_by_slug(slug)

        if not article:
            print(f"   Not found in articles, trying country_hubs...")
            article = await get_hub_by_slug(slug)

        if not article:
            print(f"❌ FAILED: Content not found: {slug}")
            return False

        article_id = article.get("id")
        title = article.get("title", "Untitled")
        is_hub = article.get("is_hub", False)

        print(f"✅ SUCCESS: Found {'hub' if is_hub else 'article'}")
        print(f"   ID: {article_id}")
        print(f"   Title: {title}")
        print(f"   Is Hub: {is_hub}")

        # Check existing video
        existing = article.get("video_playback_id")
        if existing:
            print(f"⚠️  Video already exists: {existing}")
            print(f"   (Continuing anyway for testing)")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ===== STEP 2: Generate Prompt =====
    print("\n" + "=" * 70)
    print("STEP 2/5: Generating simple video prompt")
    print("=" * 70)

    try:
        prompt_result = await generate_simple_video_prompt(
            article=article,
            app=app,
            video_model="seedance"
        )

        if not prompt_result.get("success"):
            print(f"❌ FAILED: Prompt generation failed")
            return False

        video_prompt = prompt_result.get("prompt", "")
        print(f"✅ SUCCESS: Generated prompt ({len(video_prompt)} chars)")
        print(f"\n📝 Prompt preview:")
        print("-" * 70)
        print(video_prompt[:400] + "..." if len(video_prompt) > 400 else video_prompt)
        print("-" * 70)

        # Validate acts (just for visibility)
        acts = ["ACT 1", "ACT 2", "ACT 3", "ACT 4"]
        found_acts = [act for act in acts if act in video_prompt]
        print(f"   Acts found: {', '.join(found_acts)}")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ===== STEP 3: Generate Video - FRESH ACTIVITY =====
    print("\n" + "=" * 70)
    print("STEP 3/5: Generating video with Seedance (FRESH ACTIVITY)")
    print("=" * 70)
    print("⚠️  This will take 1-3 minutes and cost $0.30...")
    print("   Using generate_video_simple (NO validation logic!)")

    try:
        video_result = await generate_video_simple(
            prompt=video_prompt,
            duration=12,
            resolution="720p",
            aspect_ratio="16:9",
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

    # ===== STEP 4: Upload to MUX =====
    print("\n" + "=" * 70)
    print("STEP 4/5: Uploading to MUX with descriptive name")
    print("=" * 70)
    print("⚠️  This will take 30-60 seconds...")

    try:
        mux_result = await upload_video_to_mux(
            video_url=video_url,
            article_id=article_id,
            title=title,  # This names the video in MUX!
            app=app,
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
        print(f"   MUX Name: {title}")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ===== STEP 5: Update Database =====
    print("\n" + "=" * 70)
    print("STEP 5/5: Updating database with playback_id")
    print("=" * 70)

    try:
        if is_hub:
            print(f"   Updating country_hubs (id={article_id})...")
            await update_hub_video(
                hub_id=article_id,
                video_playback_id=playback_id,
                four_act_content=[]  # Empty for hubs
            )
        else:
            print(f"   Updating articles (id={article_id})...")
            await update_article_four_act_content(
                article_id=article_id,
                four_act_content=[],  # Empty for hubs
                video_prompt=video_prompt
            )

        print(f"✅ SUCCESS: Database updated!")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ===== SUCCESS =====
    print("\n" + "=" * 70)
    print("✅ ALL STEPS PASSED - VideoEnrichmentV2 Complete!")
    print("=" * 70)

    print(f"\n📊 Results:")
    print(f"   Article ID: {article_id}")
    print(f"   Title: {title}")
    print(f"   Type: {'Hub' if is_hub else 'Article'}")
    print(f"   Playback ID: {playback_id}")
    print(f"   Asset ID: {asset_id}")

    print(f"\n📺 Watch your video:")
    print(f"   https://stream.mux.com/{playback_id}.m3u8")

    print(f"\n🖼️  Thumbnail:")
    print(f"   https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.5")

    print(f"\n🎞️  GIF:")
    print(f"   https://image.mux.com/{playback_id}/animated.gif?start=0&end=12&width=640&fps=12")

    return True


if __name__ == "__main__":
    print("\n🚀 Starting VideoEnrichmentV2 Workflow Test")
    print("   This simulates Temporal by calling activities directly")
    print("   Cost: ~$0.30 | Time: ~2-4 minutes\n")

    # Check environment variables
    required_vars = [
        "REPLICATE_API_TOKEN",
        "MUX_TOKEN_ID",
        "MUX_TOKEN_SECRET",
        "DATABASE_URL"
    ]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    try:
        result = asyncio.run(test_v2_workflow())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
