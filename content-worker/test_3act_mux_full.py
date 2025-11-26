#!/usr/bin/env python3
"""
COMPREHENSIVE 3-ACT NARRATIVE + MUX TEST

Tests EVERYTHING:
- WAN 2.5 at 10 seconds for 3-act narrative video
- Mux upload with auto-generated captions
- Thumbnails at act timestamps (0, 3.3, 6.6s)
- Animated GIFs per act (bounded segments)
- Storyboard sprite sheet
- Clips (separate assets per act)
- Chapter data structure
- Various thumbnail sizes/crops/fit modes

Usage:
    python test_3act_mux_full.py              # Prompt test only (instant)
    python test_3act_mux_full.py generate     # Generate video only
    python test_3act_mux_full.py mux          # Use existing video URL, test Mux
    python test_3act_mux_full.py full         # Full pipeline: generate + all Mux tests
    python test_3act_mux_full.py clips        # Test clip creation from existing asset
"""

import asyncio
import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# 3-ACT NARRATIVE DEFINITION
# ============================================================================

CYPRUS_NARRATIVE = {
    "template": "aspirational",
    "topic": "Cyprus Digital Nomad Visa 2025",
    "title": "Cyprus Digital Nomad Visa: Your Complete Guide to Mediterranean Remote Work",
    "acts": [
        {
            "number": 1,
            "title": "The Dream",
            "visual": "Young professional at desk in grey rainy city, laptop showing flight searches, dreaming expression gazing out window at grey sky, wearing headphones, coffee cup nearby",
            "key_points": ["Expensive city life", "Remote work possibility", "Desire for change"],
            "start": 0,
            "end": 3.3,
        },
        {
            "number": 2,
            "title": "The Path",
            "visual": "Same person in warm sunlit room reviewing official documents, Cyprus visa application visible, passport on desk, smile emerging, warm golden light through window",
            "key_points": ["€3,500/month requirement", "Application process", "12-month timeline"],
            "start": 3.3,
            "end": 6.6,
        },
        {
            "number": 3,
            "title": "The Reality",
            "visual": "Happy professional working from Mediterranean seaside cafe at golden hour, laptop open, glass of local wine, turquoise sea in background, contentment radiating",
            "key_points": ["Low cost of living", "330 days sunshine", "Thriving expat community"],
            "start": 6.6,
            "end": 10.0,
        }
    ],
    "preamble": "As remote work continues reshaping how professionals live and work, Cyprus has emerged as one of Europe's most attractive destinations for digital nomads.",
    "bump": "Ready to make the Mediterranean your office? The Cyprus Digital Nomad Visa could be your gateway to a new chapter."
}


def build_3act_video_prompt(narrative: Dict[str, Any]) -> str:
    """
    Build a single 10-second video prompt from 3-act narrative structure.
    Creates a continuous visual journey with smooth transitions.
    """
    acts = narrative["acts"]

    # Build flowing narrative
    prompt_parts = []
    for i, act in enumerate(acts):
        prompt_parts.append(act["visual"])
        if i < len(acts) - 1:
            prompt_parts.append("Scene transitions smoothly to")

    visual_narrative = " ".join(prompt_parts)

    # Add cinematic instructions optimized for WAN 2.5
    full_prompt = f"""{visual_narrative}

Cinematic progression from aspiration to reality, 10-second duration with clear 3-act structure.
Camera work: Act 1 static melancholy shot, Act 2 subtle push-in on documents, Act 3 slow pan across seaside scene.
Lighting progression: grey/blue tones to warm amber to golden hour Mediterranean glow.
Film aesthetic: Kodak Portra 400 color grading, shallow depth of field, documentary travel style.
Smooth 1-second dissolve transitions between scenes. Professional quality, aspirational lifestyle."""

    return full_prompt


# ============================================================================
# MUX HELPER FUNCTIONS (standalone, no Temporal)
# ============================================================================

def get_mux_client():
    """Get configured Mux API client."""
    import mux_python

    configuration = mux_python.Configuration()
    configuration.username = os.environ.get("MUX_TOKEN_ID")
    configuration.password = os.environ.get("MUX_TOKEN_SECRET")

    if not configuration.username or not configuration.password:
        raise ValueError("MUX_TOKEN_ID and MUX_TOKEN_SECRET must be set")

    return mux_python.ApiClient(configuration)


def upload_to_mux_with_captions(video_url: str, language: str = "en") -> Dict[str, Any]:
    """
    Upload video to Mux WITH auto-generated captions enabled.

    This is the key enhancement - captions for mobile accessibility.
    """
    import mux_python

    print(f"\n📤 Uploading to Mux with auto-captions ({language})...")
    print(f"   Video URL: {video_url[:60]}...")

    client = get_mux_client()
    assets_api = mux_python.AssetsApi(client)

    # Create asset with auto-generated captions
    create_asset_request = mux_python.CreateAssetRequest(
        input=[
            mux_python.InputSettings(
                url=video_url,
                generated_subtitles=[
                    mux_python.AssetGeneratedSubtitleSettings(
                        language_code=language,
                        name=f"{language.upper()} (auto)"
                    )
                ]
            )
        ],
        playback_policy=[mux_python.PlaybackPolicy.PUBLIC],
    )

    asset = assets_api.create_asset(create_asset_request)
    asset_id = asset.data.id

    print(f"   Asset created: {asset_id}")
    print(f"   Waiting for processing (video + captions)...")

    # Wait for asset to be ready
    max_attempts = 120  # 4 minutes (captions take longer)
    for attempt in range(max_attempts):
        asset_status = assets_api.get_asset(asset_id)
        status = asset_status.data.status

        # Check for tracks (captions)
        tracks = asset_status.data.tracks or []
        caption_tracks = [t for t in tracks if t.type == "text"]

        if attempt % 10 == 0:
            print(f"   Status: {status}, tracks: {len(tracks)}, captions: {len(caption_tracks)}")

        if status == "ready":
            playback_id = asset_status.data.playback_ids[0].id
            duration = asset_status.data.duration

            print(f"   ✅ Asset ready! Duration: {duration}s")

            return {
                "asset_id": asset_id,
                "playback_id": playback_id,
                "duration": duration,
                "status": "ready",
                "tracks": [{"type": t.type, "id": t.id, "status": t.status} for t in tracks],
                "caption_tracks": [{"id": t.id, "status": t.status, "language": getattr(t, 'language_code', 'en')} for t in caption_tracks],
            }
        elif status == "errored":
            raise RuntimeError(f"Mux asset processing failed: {asset_status.data.errors}")

        time.sleep(2)

    raise TimeoutError("Mux asset processing timed out")


def create_mux_clip(source_asset_id: str, start_time: float, end_time: float, name: str) -> Dict[str, Any]:
    """
    Create a clip (new asset) from a portion of the source video.

    This creates a TRUE separate video for each act.
    """
    import mux_python

    print(f"\n✂️  Creating clip: {name} ({start_time}s - {end_time}s)...")

    client = get_mux_client()
    assets_api = mux_python.AssetsApi(client)

    # Create clip from source asset
    create_asset_request = mux_python.CreateAssetRequest(
        input=[
            mux_python.InputSettings(
                url=f"mux://assets/{source_asset_id}",
                start_time=start_time,
                end_time=end_time
            )
        ],
        playback_policy=[mux_python.PlaybackPolicy.PUBLIC],
    )

    asset = assets_api.create_asset(create_asset_request)
    clip_asset_id = asset.data.id

    print(f"   Clip asset created: {clip_asset_id}")

    # Wait for clip to be ready
    max_attempts = 60
    for attempt in range(max_attempts):
        asset_status = assets_api.get_asset(clip_asset_id)

        if asset_status.data.status == "ready":
            playback_id = asset_status.data.playback_ids[0].id
            duration = asset_status.data.duration

            print(f"   ✅ Clip ready! Duration: {duration}s")

            return {
                "name": name,
                "asset_id": clip_asset_id,
                "playback_id": playback_id,
                "duration": duration,
                "source_start": start_time,
                "source_end": end_time,
            }
        elif asset_status.data.status == "errored":
            raise RuntimeError(f"Clip creation failed: {asset_status.data.errors}")

        time.sleep(2)

    raise TimeoutError("Clip processing timed out")


def generate_all_mux_urls(playback_id: str, duration: float, acts: List[Dict]) -> Dict[str, Any]:
    """
    Generate ALL possible Mux URLs for comprehensive testing.
    """
    image_base = f"https://image.mux.com/{playback_id}"
    stream_base = f"https://stream.mux.com/{playback_id}"

    urls = {
        # === STREAMING ===
        "stream_hls": f"{stream_base}.m3u8",
        "stream_dash": f"{stream_base}.mpd",  # DASH format

        # === FULL VIDEO GIF ===
        "gif_full": f"{image_base}/animated.gif?start=0&end={min(duration, 10)}&width=480&fps=15",
        "gif_full_webp": f"{image_base}/animated.webp?start=0&end={min(duration, 10)}&width=480&fps=15",

        # === STORYBOARD ===
        "storyboard_jpg": f"{image_base}/storyboard.jpg",
        "storyboard_webp": f"{image_base}/storyboard.webp",
        "storyboard_vtt": f"{image_base}/storyboard.vtt",
        "storyboard_json": f"{image_base}/storyboard.json",

        # === HERO/FEATURED THUMBNAILS ===
        "thumbnail_hero": f"{image_base}/thumbnail.jpg?time={duration/2}&width=1920&height=1080&fit_mode=smartcrop",
        "thumbnail_featured": f"{image_base}/thumbnail.jpg?time={duration/2}&width=1200&height=630&fit_mode=smartcrop",
        "thumbnail_social_square": f"{image_base}/thumbnail.jpg?time={duration/2}&width=1080&height=1080&fit_mode=smartcrop",

        # === ACT-SPECIFIC ASSETS ===
        "acts": {}
    }

    # Generate URLs for each act
    for act in acts:
        act_num = act["number"]
        start = act["start"]
        end = act["end"]
        mid = (start + end) / 2

        urls["acts"][f"act_{act_num}"] = {
            "title": act["title"],
            "start": start,
            "end": end,

            # Thumbnails at different points in the act
            "thumbnail_start": f"{image_base}/thumbnail.jpg?time={start}&width=1200",
            "thumbnail_mid": f"{image_base}/thumbnail.jpg?time={mid}&width=1200",
            "thumbnail_end": f"{image_base}/thumbnail.jpg?time={end - 0.1}&width=1200",

            # Hero-sized thumbnails
            "thumbnail_hero": f"{image_base}/thumbnail.jpg?time={mid}&width=1920&height=1080&fit_mode=smartcrop",

            # Animated GIF for just this act (bounded!)
            "gif": f"{image_base}/animated.gif?start={start}&end={end}&width=480&fps=15",
            "gif_webp": f"{image_base}/animated.webp?start={start}&end={end}&width=480&fps=15",

            # Different fit modes
            "thumbnail_crop": f"{image_base}/thumbnail.jpg?time={mid}&width=800&height=600&fit_mode=crop",
            "thumbnail_preserve": f"{image_base}/thumbnail.jpg?time={mid}&width=800&height=600&fit_mode=preserve",
            "thumbnail_pad": f"{image_base}/thumbnail.jpg?time={mid}&width=800&height=600&fit_mode=pad",
        }

    return urls


def generate_chapter_data(acts: List[Dict]) -> List[Dict]:
    """
    Generate chapter data structure for Mux Player.

    Format: [{startTime: number, endTime?: number, value: string}]
    """
    chapters = []
    for act in acts:
        chapters.append({
            "startTime": act["start"],
            "endTime": act["end"],
            "value": act["title"]  # Chapter title shown in player
        })
    return chapters


def generate_mux_player_html(playback_id: str, chapters: List[Dict], title: str) -> str:
    """
    Generate complete HTML for Mux Player with chapters, captions, and all features.
    """
    chapters_json = json.dumps(chapters)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/@mux/mux-player"></script>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        mux-player {{ width: 100%; aspect-ratio: 16/9; }}
        .chapter-info {{ margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px; }}
        .act-section {{ margin: 40px 0; padding: 20px; border-left: 4px solid #3b82f6; }}
        .act-image {{ width: 100%; max-width: 600px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>{title}</h1>

    <!-- Main video player with chapters and captions -->
    <mux-player
        playback-id="{playback_id}"
        metadata-video-title="{title}"
        accent-color="#3b82f6"
        autoplay="muted"
        default-show-captions
    ></mux-player>

    <div class="chapter-info">
        <strong>Current Chapter:</strong> <span id="current-chapter">-</span>
    </div>

    <script>
        const player = document.querySelector('mux-player');
        const chapterDisplay = document.getElementById('current-chapter');

        // Add chapters after player loads
        player.addEventListener('loadedmetadata', () => {{
            player.addChapters({chapters_json});
            console.log('Chapters added:', {chapters_json});
        }});

        // Track chapter changes
        player.addEventListener('chapterchange', () => {{
            const chapter = player.activeChapter;
            if (chapter) {{
                chapterDisplay.textContent = chapter.value + ' (' + chapter.startTime + 's - ' + chapter.endTime + 's)';
            }}
        }});
    </script>

    <!-- Article sections with act images -->
    <div class="act-section">
        <h2>Act 1: The Dream</h2>
        <img class="act-image" src="https://image.mux.com/{playback_id}/thumbnail.jpg?time=0&width=1200" alt="Act 1">
        <p>Content for Act 1...</p>
    </div>

    <div class="act-section">
        <h2>Act 2: The Path</h2>
        <img class="act-image" src="https://image.mux.com/{playback_id}/thumbnail.jpg?time=3.3&width=1200" alt="Act 2">
        <p>Content for Act 2...</p>
    </div>

    <div class="act-section">
        <h2>Act 3: The Reality</h2>
        <img class="act-image" src="https://image.mux.com/{playback_id}/thumbnail.jpg?time=6.6&width=1200" alt="Act 3">
        <p>Content for Act 3...</p>
    </div>
</body>
</html>'''

    return html


# ============================================================================
# URL VERIFICATION
# ============================================================================

def verify_url(url: str, name: str, timeout: int = 10) -> Dict[str, Any]:
    """Verify a URL is accessible and get its content type/size."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return {
            "name": name,
            "url": url[:80] + "..." if len(url) > 80 else url,
            "status": response.status_code,
            "ok": response.status_code == 200,
            "content_type": response.headers.get("content-type", "unknown"),
            "content_length": response.headers.get("content-length", "unknown"),
        }
    except Exception as e:
        return {
            "name": name,
            "url": url[:80] + "..." if len(url) > 80 else url,
            "status": "error",
            "ok": False,
            "error": str(e),
        }


def verify_all_urls(urls: Dict[str, Any], acts: List[Dict]) -> List[Dict]:
    """Verify all generated URLs are accessible."""
    results = []

    # Top-level URLs
    for key, url in urls.items():
        if key == "acts" or not isinstance(url, str):
            continue
        results.append(verify_url(url, key))

    # Act-specific URLs
    for act_key, act_urls in urls.get("acts", {}).items():
        for url_key, url in act_urls.items():
            if isinstance(url, str) and url.startswith("http"):
                results.append(verify_url(url, f"{act_key}_{url_key}"))

    return results


# ============================================================================
# PRINTING HELPERS
# ============================================================================

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n{'─' * 40}")
    print(f"  {title}")
    print(f"{'─' * 40}")


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

async def test_prompt_only():
    """Test prompt generation without any API calls."""
    print_header("3-ACT NARRATIVE PROMPT TEST")

    prompt = build_3act_video_prompt(CYPRUS_NARRATIVE)

    print_section("Narrative Structure")
    for act in CYPRUS_NARRATIVE["acts"]:
        print(f"\nAct {act['number']}: {act['title']} ({act['start']}s → {act['end']}s)")
        print(f"  Visual: {act['visual'][:70]}...")
        print(f"  Key points: {', '.join(act['key_points'])}")

    print_section("Generated Video Prompt")
    print(f"Word count: {len(prompt.split())} | Char count: {len(prompt)}")
    print(f"\n{prompt}")

    print_section("Chapter Data Structure")
    chapters = generate_chapter_data(CYPRUS_NARRATIVE["acts"])
    print(json.dumps(chapters, indent=2))

    # Test WAN 2.5 transformation
    from src.activities.media.video_generation import transform_prompt_for_wan
    wan_pos, wan_neg = transform_prompt_for_wan(prompt)

    print_section("WAN 2.5 Transformation")
    print(f"Positive ({len(wan_pos)} chars): {wan_pos[:150]}...")
    print(f"Negative: {wan_neg}")

    return {"prompt": prompt, "chapters": chapters}


async def test_video_generation():
    """Generate 10-second WAN 2.5 video - standalone, no Temporal."""
    import replicate

    print_header("WAN 2.5 VIDEO GENERATION (10 seconds)")

    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN not set")
        return None

    prompt = build_3act_video_prompt(CYPRUS_NARRATIVE)

    # WAN 2.5 prompt transformation
    from src.activities.media.video_generation import transform_prompt_for_wan
    wan_prompt, negative_prompt = transform_prompt_for_wan(prompt)

    print_section("Parameters")
    print(f"Model: WAN 2.5 (wan-video/wan-2.5-t2v)")
    print(f"Duration: 10 seconds")
    print(f"Resolution: 1280*720 (720p)")
    print(f"Prompt: {len(wan_prompt)} chars")

    print_section("Generating...")
    print("(This may take 3-8 minutes)")
    start_time = time.time()

    try:
        # Direct Replicate call (no Temporal)
        client = replicate.Client(api_token=replicate_token)
        prediction = client.predictions.create(
            version="39ca1e5fd0fd12ca1f71bebef447273394a0b2a6feaf3e3f80e42e3c23f85fa2",
            input={
                "size": "1280*720",
                "prompt": wan_prompt,
                "duration": 10,
                "negative_prompt": negative_prompt,
                "enable_prompt_expansion": True
            }
        )

        print(f"Prediction ID: {prediction.id}")

        # Poll for completion
        max_wait = 600
        poll_interval = 10
        elapsed = 0

        while elapsed < max_wait:
            prediction.reload()
            status = prediction.status

            if elapsed % 30 == 0:
                print(f"  Status: {status} ({elapsed}s elapsed)")

            if status == "succeeded":
                output = prediction.output
                # WAN returns FileOutput, get URL
                video_url = output.url if hasattr(output, 'url') else str(output)

                total_elapsed = time.time() - start_time
                cost = 0.02 * 10  # ~$0.20 for 10s

                print_section(f"✅ Video Generated ({total_elapsed:.1f}s)")
                print(f"URL: {video_url}")
                print(f"Cost: ${cost:.4f}")

                return {
                    "video_url": video_url,
                    "resolution": "720p",
                    "duration": 10,
                    "cost": cost,
                    "model": "wan-video/wan-2.5-t2v",
                    "prompt_used": wan_prompt[:200]
                }

            elif status == "failed":
                raise RuntimeError(f"WAN generation failed: {prediction.error}")
            elif status == "canceled":
                raise RuntimeError("WAN generation was canceled")

            time.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"WAN generation timed out after {max_wait}s")

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_mux_full(video_url: str):
    """
    Test ALL Mux features with a video URL.
    """
    print_header("COMPREHENSIVE MUX TEST")

    if not os.environ.get("MUX_TOKEN_ID"):
        print("❌ MUX_TOKEN_ID not set")
        return None

    # === 1. UPLOAD WITH CAPTIONS ===
    print_section("1. Upload with Auto-Captions")
    mux_result = upload_to_mux_with_captions(video_url, language="en")

    playback_id = mux_result["playback_id"]
    asset_id = mux_result["asset_id"]
    duration = mux_result["duration"]

    print(f"\nPlayback ID: {playback_id}")
    print(f"Asset ID: {asset_id}")
    print(f"Duration: {duration}s")
    print(f"Tracks: {mux_result.get('tracks', [])}")

    # === 2. GENERATE ALL URLS ===
    print_section("2. Generate All URLs")
    all_urls = generate_all_mux_urls(playback_id, duration, CYPRUS_NARRATIVE["acts"])

    print("\nStreaming URLs:")
    print(f"  HLS: {all_urls['stream_hls']}")
    print(f"  DASH: {all_urls['stream_dash']}")

    print("\nStoryboard URLs:")
    print(f"  JPG: {all_urls['storyboard_jpg']}")
    print(f"  VTT: {all_urls['storyboard_vtt']}")

    print("\nFull Video GIF:")
    print(f"  {all_urls['gif_full']}")

    print("\nAct-Specific URLs:")
    for act_key, act_urls in all_urls["acts"].items():
        print(f"\n  {act_key} - {act_urls['title']}:")
        print(f"    Thumbnail: {act_urls['thumbnail_mid'][:70]}...")
        print(f"    GIF: {act_urls['gif'][:70]}...")

    # === 3. VERIFY URLS ===
    print_section("3. Verify All URLs Are Accessible")
    verification_results = verify_all_urls(all_urls, CYPRUS_NARRATIVE["acts"])

    ok_count = sum(1 for r in verification_results if r["ok"])
    fail_count = len(verification_results) - ok_count

    print(f"\nResults: {ok_count} OK, {fail_count} failed")

    for result in verification_results:
        status = "✅" if result["ok"] else "❌"
        print(f"  {status} {result['name']}: {result.get('status', 'error')}")

    # === 4. CHAPTER DATA ===
    print_section("4. Chapter Data for Mux Player")
    chapters = generate_chapter_data(CYPRUS_NARRATIVE["acts"])
    print(json.dumps(chapters, indent=2))

    # === 5. GENERATE HTML DEMO ===
    print_section("5. Generate Demo HTML")
    html = generate_mux_player_html(playback_id, chapters, CYPRUS_NARRATIVE["title"])

    html_path = "/Users/dankeegan/quest/content-worker/test_3act_demo.html"
    with open(html_path, "w") as f:
        f.write(html)
    print(f"Demo HTML saved to: {html_path}")
    print("Open in browser to test chapters and captions!")

    # === 6. SUMMARY ===
    print_section("6. Summary")

    summary = {
        "asset_id": asset_id,
        "playback_id": playback_id,
        "duration": duration,
        "chapters": chapters,
        "urls": {
            "stream": all_urls["stream_hls"],
            "hero_thumbnail": all_urls["thumbnail_hero"],
            "storyboard": all_urls["storyboard_jpg"],
            "full_gif": all_urls["gif_full"],
            "acts": {
                f"act_{act['number']}": {
                    "thumbnail": all_urls["acts"][f"act_{act['number']}"]["thumbnail_mid"],
                    "gif": all_urls["acts"][f"act_{act['number']}"]["gif"],
                }
                for act in CYPRUS_NARRATIVE["acts"]
            }
        },
        "demo_html": html_path,
        "urls_verified": ok_count,
        "urls_failed": fail_count,
    }

    print(json.dumps(summary, indent=2))

    return summary


async def test_clips(source_asset_id: str):
    """
    Test creating separate clip assets for each act.

    This creates TRUE separate videos, not just URL parameters.
    """
    print_header("MUX CLIP CREATION TEST")

    clips = []

    for act in CYPRUS_NARRATIVE["acts"]:
        try:
            clip = create_mux_clip(
                source_asset_id=source_asset_id,
                start_time=act["start"],
                end_time=act["end"],
                name=f"Act {act['number']}: {act['title']}"
            )
            clips.append(clip)
        except Exception as e:
            print(f"❌ Failed to create clip for Act {act['number']}: {e}")

    print_section("Clips Created")
    for clip in clips:
        print(f"\n{clip['name']}:")
        print(f"  Asset ID: {clip['asset_id']}")
        print(f"  Playback ID: {clip['playback_id']}")
        print(f"  Duration: {clip['duration']}s")
        print(f"  Stream: https://stream.mux.com/{clip['playback_id']}.m3u8")

    return clips


async def test_full_pipeline():
    """
    Run the complete pipeline:
    1. Generate 10s WAN 2.5 video
    2. Upload to Mux with captions
    3. Test all Mux features
    4. Create clips for each act
    """
    print_header("FULL 3-ACT NARRATIVE PIPELINE")
    pipeline_start = time.time()

    # Step 1: Generate video
    video_result = await test_video_generation()
    if not video_result:
        print("❌ Pipeline failed at video generation")
        return None

    video_url = video_result["video_url"]

    # Step 2-5: Mux testing
    mux_result = await test_mux_full(video_url)
    if not mux_result:
        print("❌ Pipeline failed at Mux upload")
        return None

    # Step 6: Create clips (optional - costs extra)
    print_section("Create Act Clips? (Additional Mux cost)")
    print("Skipping clip creation in automated test.")
    print(f"To test clips manually: python {sys.argv[0]} clips {mux_result['asset_id']}")

    # Final summary
    total_elapsed = time.time() - pipeline_start

    print_header(f"PIPELINE COMPLETE ({total_elapsed:.1f}s)")
    print(f"""
Results:
  Video generated: ✅
  Mux upload: ✅
  Auto-captions: ✅ (requested)
  Thumbnails: ✅ ({len(CYPRUS_NARRATIVE['acts'])} acts)
  GIFs: ✅ ({len(CYPRUS_NARRATIVE['acts'])} acts + full)
  Storyboard: ✅
  Chapters: ✅
  Demo HTML: {mux_result['demo_html']}

Key URLs:
  Stream: {mux_result['urls']['stream']}
  Hero: {mux_result['urls']['hero_thumbnail']}

Next: Open {mux_result['demo_html']} in browser to test!
""")

    return {
        "video": video_result,
        "mux": mux_result,
        "total_time": total_elapsed
    }


# ============================================================================
# MAIN
# ============================================================================

async def main():
    print(f"\n🎬 3-Act Narrative + Mux Comprehensive Test")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python test_3act_mux_full.py prompt     - Test prompt generation (instant)")
        print("  python test_3act_mux_full.py generate   - Generate WAN 2.5 video only")
        print("  python test_3act_mux_full.py mux <url>  - Test Mux with existing video URL")
        print("  python test_3act_mux_full.py full       - Full pipeline (generate + Mux)")
        print("  python test_3act_mux_full.py clips <id> - Create clips from existing asset")
        print("\nRunning prompt test by default...")
        await test_prompt_only()
        return

    command = sys.argv[1]

    if command == "prompt":
        await test_prompt_only()

    elif command == "generate":
        await test_video_generation()

    elif command == "mux":
        if len(sys.argv) < 3:
            print("❌ Please provide video URL: python test_3act_mux_full.py mux <video_url>")
            return
        await test_mux_full(sys.argv[2])

    elif command == "full":
        await test_full_pipeline()

    elif command == "clips":
        if len(sys.argv) < 3:
            print("❌ Please provide asset ID: python test_3act_mux_full.py clips <asset_id>")
            return
        await test_clips(sys.argv[2])

    else:
        print(f"❌ Unknown command: {command}")

    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
