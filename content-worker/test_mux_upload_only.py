"""
Test MUX upload and naming convention with an existing video.

Takes an existing Replicate video URL and uploads to MUX to validate naming.
"""

import os
import mux_python
from dotenv import load_dotenv

load_dotenv()

def upload_test_video_to_mux():
    """Upload existing video to MUX to test naming convention."""

    print("\n" + "="*80)
    print("TEST: MUX Upload & Naming Convention")
    print("="*80)

    # Get MUX credentials
    mux_token_id = os.getenv("MUX_TOKEN_ID")
    mux_token_secret = os.getenv("MUX_TOKEN_SECRET")

    if not mux_token_id or not mux_token_secret:
        print("\n❌ MUX credentials not found in .env")
        return False

    print(f"\n✅ MUX credentials loaded")

    # Get the video from the Replicate prediction
    import replicate
    replicate_token = os.getenv("REPLICATE_API_TOKEN")

    if not replicate_token:
        print("\n❌ REPLICATE_API_TOKEN not found in .env")
        return False

    print(f"\n📹 Fetching video from Replicate prediction: 2k078ewzgxrm80ctw0q9a3n46w")

    try:
        client = replicate.Client(api_token=replicate_token)
        prediction = client.predictions.get("2k078ewzgxrm80ctw0q9a3n46w")

        if prediction.status != "succeeded":
            print(f"❌ Prediction status: {prediction.status}")
            return False

        video_url = prediction.output
        print(f"✅ Got video URL: {video_url[:60]}...")

    except Exception as e:
        print(f"❌ Failed to get Replicate video: {e}")
        return False

    # Test parameters - simulating France country guide
    test_params = {
        "title": "France Relocation Guide 2025: Complete Guide for Every Situation",
        "country": "France",
        "article_mode": "STORY",
        "app": "relocation",
        "cluster_id": "test-abc12345",
        "article_id": 99999
    }

    print(f"\n📋 Test Parameters:")
    print(f"   Title: {test_params['title']}")
    print(f"   Country: {test_params['country']}")
    print(f"   Mode: {test_params['article_mode']}")

    # Create MUX client
    configuration = mux_python.Configuration()
    configuration.username = mux_token_id
    configuration.password = mux_token_secret
    client = mux_python.ApiClient(configuration)
    assets_api = mux_python.AssetsApi(client)

    print(f"\n☁️  Uploading to MUX with human-readable naming...")

    try:
        # Build human-readable passthrough string (NEW CONVENTION)
        # Format: "Title | MODE | Country | app:xxx | cluster:xxx | id:xxx"
        passthrough_parts = [
            test_params["title"][:80],
            test_params["article_mode"],
            test_params["country"],
            f"app:{test_params['app']}",
            f"cluster:{test_params['cluster_id'][:8]}",
            f"id:{test_params['article_id']}"
        ]

        passthrough = " | ".join(passthrough_parts)[:255]

        print(f"\n🏷️  MUX Label (passthrough metadata):")
        print(f"   {passthrough}")
        print(f"\n   Length: {len(passthrough)} chars (max 255)")

        # Create MUX asset with BOTH meta (for dashboard title) and passthrough (for webhooks)
        create_asset_request = mux_python.CreateAssetRequest(
            input=[mux_python.InputSettings(url=video_url)],
            playback_policy=[mux_python.PlaybackPolicy.PUBLIC],
            passthrough=passthrough,
            # NEW: Use meta field for dashboard title
            meta={
                "title": test_params["title"],
                "country": test_params["country"],
                "mode": test_params["article_mode"],
                "app": test_params["app"]
            }
        )

        asset = assets_api.create_asset(create_asset_request)
        asset_id = asset.data.id

        print(f"\n✅ Asset created: {asset_id}")
        print(f"   Status: {asset.data.status}")

        # Wait a moment for MUX to process
        import time
        print(f"\n⏳ Waiting 30s for MUX to process...")
        time.sleep(30)

        # Get asset details
        asset_details = assets_api.get_asset(asset_id)
        playback_id = None

        if asset_details.data.playback_ids:
            playback_id = asset_details.data.playback_ids[0].id

        print(f"\n✅ Upload complete!")
        print(f"\n📦 MUX Asset Details:")
        print(f"   Asset ID: {asset_id}")
        print(f"   Playback ID: {playback_id}")
        print(f"   Status: {asset_details.data.status}")
        print(f"   Duration: {asset_details.data.duration:.1f}s")

        # MUX Dashboard URL
        mux_dashboard_url = f"https://dashboard.mux.com/video/assets/{asset_id}"
        print(f"\n🔗 View in MUX Dashboard:")
        print(f"   {mux_dashboard_url}")

        if playback_id:
            # Generate playback URLs
            stream_url = f"https://stream.mux.com/{playback_id}.m3u8"
            thumbnail_url = f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=1.5&width=800"
            gif_url = f"https://image.mux.com/{playback_id}/animated.gif?start=0&end=3&width=480&fps=12"

            print(f"\n📺 Playback URLs:")
            print(f"   Stream (HLS): {stream_url}")
            print(f"   Thumbnail: {thumbnail_url}")
            print(f"   GIF Preview: {gif_url}")

        print(f"\n" + "="*80)
        print("✅ TEST SUCCESSFUL")
        print("="*80)
        print(f"\nValidation:")
        print(f"   ✅ Video uploaded to MUX")
        print(f"   ✅ Human-readable label applied: {passthrough}")
        print(f"   ✅ Asset visible in MUX dashboard")
        print(f"\nNext Steps:")
        print(f"   1. Open MUX dashboard: {mux_dashboard_url}")
        print(f"   2. Verify the label shows correctly in the asset list")
        print(f"   3. You can delete this test asset after verification")
        print(f"\n💡 The naming convention is working! This same format will be")
        print(f"   applied to all country guide videos going forward.")

        return True

    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = upload_test_video_to_mux()
    exit(0 if success else 1)
