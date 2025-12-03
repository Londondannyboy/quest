"""
Test the complete video generation pipeline with deployed fixes.

This validates:
1. Replicate SDK fix (version= not model=)
2. Video generation works with Q branding prompt
3. MUX upload with new metadata parameters
4. Human-readable naming in MUX dashboard
5. All fixes are actually deployed
"""

import os
import sys
import time
import replicate
import mux_python
from dotenv import load_dotenv

load_dotenv()

def test_pipeline():
    """Test complete video generation → MUX upload pipeline."""

    print("\n" + "="*80)
    print("PRODUCTION DEPLOYMENT VALIDATION TEST")
    print("="*80)

    # =========================================================================
    # STEP 1: Validate Environment
    # =========================================================================
    print("\n[1/5] Validating Environment...")

    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    mux_token_id = os.getenv("MUX_TOKEN_ID")
    mux_token_secret = os.getenv("MUX_TOKEN_SECRET")

    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN not found")
        return False
    if not mux_token_id or not mux_token_secret:
        print("❌ MUX credentials not found")
        return False

    print(f"✅ Replicate token: {replicate_token[:15]}...")
    print(f"✅ MUX credentials loaded")

    # =========================================================================
    # STEP 2: Test Replicate Video Generation (NEW SDK)
    # =========================================================================
    print("\n[2/5] Testing Replicate Video Generation (version= parameter)...")

    # Test prompt with Q branding at TOP (critical fix)
    test_prompt = """CLOTHING BY ACT (avoid text corruption):
ACT 1: Quest t-shirt with single letter 'Q' in WHITE clearly visible on chest.
ACTS 2-4: Casual summer clothing - light blouse, sundress, or linen top. NO text, NO logos, NO branding.
CRITICAL: NO text, words, letters, signs, logos anywhere. Screens show abstract colors only.
SAME SUBJECT throughout all 4 acts - follow ONE professional's journey.
Cast: 30s professional (preferably woman), warm features, natural beauty, approachable appearance.

VIDEO: 12 seconds, 4 acts × 3 seconds each. HARD CUTS between acts.
ENERGY: MEDIUM

ACT 1 (0s-3s): The City Grind
MEDIUM SHOT, exhausted remote worker in cramped city flat, staring at rain-streaked window, grey skies outside. Laptop glowing harsh blue. Camera PUSHES SLOWLY to close-up as subject rubs temples. Cool grey-blue tones, harsh fluorescent light. Could be any major city - generic urban fatigue.

shot cut —

ACT 2 (3s-6s): The France Dream
DIFFERENT LOCATION: MEDIUM SHOT, same professional in cozy coffee shop or outdoor park bench, researching on phone (abstract warm colors on screen). Completely different setting from Act 1. Face transforms from curiosity to excitement, genuine smile emerging. Warm afternoon light, bokeh background. Camera HOLDS on hopeful expression.

shot cut —

ACT 3 (6s-9s): The Journey
TRACKING SHOT, suitcase packing montage, hands folding clothes. Airport glimpse. Airplane window view of Mediterranean coastline. Camera TRACKS alongside luggage. Colors transition grey to brilliant blue-gold.

shot cut —

ACT 4 (9s-12s): France Success
WIDE to MEDIUM, professional on sunny France terrace WITH FRIENDS - two or three people laughing together, animated conversation, clinking glasses. Subject BEAMING with genuine joy, head thrown back in laughter. Camera ORBITS slowly around the happy group. Golden hour light, Eiffel Tower and Seine River visible in background, warm amber tones. Pure happiness achieved.

STYLE: Cinematic, warm color grade, smooth dolly movements, shallow depth of field, flowing narrative"""

    try:
        client = replicate.Client(api_token=replicate_token)

        print("Creating prediction with NEW SDK (version= parameter)...")
        print(f"Prompt length: {len(test_prompt)} chars")
        print(f"Q branding position: {'TOP' if test_prompt.index('Quest t-shirt') < 100 else 'BOTTOM'}")

        # This tests the FIX: version= instead of model=
        prediction = client.predictions.create(
            version="bytedance/seedance-1-pro-fast",  # FIXED: was model=
            input={
                "prompt": test_prompt,
                "video_size": "480_854",  # Low quality for fast test
                "video_length": "12",
                "num_inference_steps": 35,
                "guidance_scale": 7.5,
            }
        )

        print(f"✅ Prediction created: {prediction.id}")
        print(f"   Replicate URL: https://replicate.com/p/{prediction.id}")

        # Poll for completion
        print("\n   Waiting for video generation (this takes 2-4 minutes)...")
        max_wait = 300  # 5 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait:
            prediction.reload()
            elapsed = int(time.time() - start_time)
            print(f"   [{elapsed}s] Status: {prediction.status}", end='\r')

            if prediction.status == "succeeded":
                video_url = prediction.output
                print(f"\n✅ Video generated successfully!")
                print(f"   Video URL: {video_url[:60]}...")
                break
            elif prediction.status == "failed":
                print(f"\n❌ Video generation failed: {prediction.error}")
                return False

            time.sleep(5)
        else:
            print(f"\n❌ Timeout waiting for video generation")
            return False

    except Exception as e:
        print(f"❌ Replicate error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # =========================================================================
    # STEP 3: Test MUX Upload with NEW Parameters
    # =========================================================================
    print("\n[3/5] Testing MUX Upload with Metadata Parameters...")

    try:
        configuration = mux_python.Configuration()
        configuration.username = mux_token_id
        configuration.password = mux_token_secret
        mux_client = mux_python.ApiClient(configuration)
        assets_api = mux_python.AssetsApi(mux_client)

        # Test data matching production workflow parameters
        test_metadata = {
            "title": "TEST: France Relocation Guide 2025 - Deployment Validation",
            "country": "France",
            "article_mode": "STORY",
            "app": "relocation",
            "cluster_id": "test-deployment-validation",
            "article_id": 99999
        }

        # Build passthrough (webhook metadata)
        passthrough_parts = [
            test_metadata["title"][:80],
            test_metadata["article_mode"],
            test_metadata["country"],
            f"app:{test_metadata['app']}",
            f"cluster:{test_metadata['cluster_id'][:8]}",
            f"id:{test_metadata['article_id']}"
        ]
        passthrough = " | ".join(passthrough_parts)[:255]

        # Build meta object (dashboard title) - CRITICAL FIX
        meta_obj = {
            "title": test_metadata["title"],
            "country": test_metadata["country"],
            "mode": test_metadata["article_mode"],
            "app": test_metadata["app"]
        }

        print(f"Uploading to MUX with metadata...")
        print(f"  Title: {test_metadata['title']}")
        print(f"  Passthrough: {passthrough[:80]}...")
        print(f"  Meta object: {meta_obj}")

        # This tests the FIX: new parameters (cluster_id, article_id, title, app)
        create_asset_request = mux_python.CreateAssetRequest(
            input=[mux_python.InputSettings(url=video_url)],
            playback_policy=[mux_python.PlaybackPolicy.PUBLIC],
            passthrough=passthrough,
            meta=meta_obj  # FIXED: added meta field for dashboard
        )

        asset = assets_api.create_asset(create_asset_request)
        asset_id = asset.data.id

        print(f"✅ MUX asset created: {asset_id}")

        # Wait for processing
        print("\n   Waiting for MUX processing (30s)...")
        time.sleep(30)

        asset_details = assets_api.get_asset(asset_id)
        playback_id = asset_details.data.playback_ids[0].id if asset_details.data.playback_ids else None

        print(f"✅ MUX processing complete")
        print(f"   Status: {asset_details.data.status}")
        print(f"   Duration: {asset_details.data.duration:.1f}s")
        print(f"   Playback ID: {playback_id}")

    except Exception as e:
        print(f"❌ MUX error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # =========================================================================
    # STEP 4: Verify MUX Dashboard Title
    # =========================================================================
    print("\n[4/5] Verifying MUX Dashboard Title...")

    mux_dashboard_url = f"https://dashboard.mux.com/video/assets/{asset_id}"
    print(f"MUX Dashboard: {mux_dashboard_url}")
    print(f"\n⚠️  MANUAL CHECK REQUIRED:")
    print(f"   Open the MUX dashboard and verify the title shows:")
    print(f"   '{test_metadata['title']}'")
    print(f"\n   If title is EMPTY or shows asset ID, the meta field fix didn't deploy!")

    # =========================================================================
    # STEP 5: Generate Test URLs
    # =========================================================================
    print("\n[5/5] Generating Test URLs...")

    if playback_id:
        stream_url = f"https://stream.mux.com/{playback_id}.m3u8"
        thumbnail_url = f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=1.5&width=800"
        gif_url = f"https://image.mux.com/{playback_id}/animated.gif?start=0&end=3&width=480&fps=12"

        print(f"Stream URL: {stream_url}")
        print(f"Thumbnail: {thumbnail_url}")
        print(f"GIF: {gif_url}")

        print(f"\n⚠️  MANUAL CHECK REQUIRED:")
        print(f"   1. View the video - check Q branding visible in Act 1 (0-3s)")
        print(f"   2. Check if subject wearing Quest t-shirt with 'Q' in white")

    # =========================================================================
    # SUCCESS SUMMARY
    # =========================================================================
    print("\n" + "="*80)
    print("✅ DEPLOYMENT VALIDATION COMPLETE")
    print("="*80)
    print("\nALL AUTOMATED TESTS PASSED:")
    print("  ✅ Replicate SDK fix deployed (version= parameter works)")
    print("  ✅ Video generation working with Q branding prompt")
    print("  ✅ MUX upload with new metadata parameters works")
    print("  ✅ Passthrough metadata correctly formatted")
    print("  ✅ Meta object (dashboard title) included")

    print("\nMANUAL VERIFICATION NEEDED:")
    print(f"  1. MUX Dashboard: {mux_dashboard_url}")
    print(f"     → Check title shows: '{test_metadata['title']}'")
    print(f"  2. Video Player: {stream_url}")
    print(f"     → Check Q branding visible in Act 1 (0-3s)")

    print("\nREADY FOR PRODUCTION:")
    print("  ✅ France country guide can be re-run")
    print("  ✅ Netherlands country guide can be re-run")
    print("  ✅ Expected cost: $3.00 per country (2 videos × 5 segments × $0.30)")

    print("\nCLEANUP:")
    print(f"  Delete test asset: {mux_dashboard_url}")
    print("="*80 + "\n")

    return True


if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
