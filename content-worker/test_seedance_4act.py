#!/usr/bin/env python3
"""
Seedance 4-Act Narrative Test - Cyprus Digital Nomad Visa
12 seconds, 480p, 4 acts × 3 seconds each

Dramatic story with high contrast between acts:
- Act 1 (0-3s): The Grind - Rainy London office, woman stressed at desk
- Act 2 (3-6s): The Dream - Scrolling laptop, Mediterranean coast images, hope
- Act 3 (6-9s): The Journey - Packing, airport, plane window view of Cyprus coast
- Act 4 (9-12s): The Reality - Sunset terrace, wine with friends, laughter, freedom
"""

import asyncio
import os
import time
import json
import replicate
from dotenv import load_dotenv

load_dotenv()

# 4-Act timestamps for 12-second video
ACT_TIMESTAMPS = {
    "act_1": {"start": 0, "end": 3, "mid": 1.5, "title": "The Grind"},
    "act_2": {"start": 3, "end": 6, "mid": 4.5, "title": "The Dream"},
    "act_3": {"start": 6, "end": 9, "mid": 7.5, "title": "The Journey"},
    "act_4": {"start": 9, "end": 12, "mid": 10.5, "title": "The Reality"},
}

# Dramatic 4-act prompt with high contrast scenes
# CRITICAL: Explicit no-text instructions at start AND end
CYPRUS_VISA_PROMPT = """
CRITICAL INSTRUCTION: This video must contain ABSOLUTELY NO TEXT, NO WORDS, NO LETTERS, NO NUMBERS, NO WRITING, NO SIGNS, NO LOGOS, NO CAPTIONS, NO SUBTITLES anywhere in any frame. All screens, monitors, and displays must show only abstract colors or imagery, never text.

Cinematic 4-act story of transformation, professional woman's journey from London to Cyprus.

ACT 1 (0-3 seconds): THE GRIND
Dark grey London office, rain pelting against floor-to-ceiling windows. Young professional woman in her 30s sits at a cluttered desk, shoulders hunched, blue light from monitor illuminating her tired face (monitor shows only abstract blue glow, no text). Grey suit, cold fluorescent lighting, the city skyline blurred by rain outside. Mood: Exhaustion, confinement.

ACT 2 (3-6 seconds): THE DREAM
Same woman now at home, evening. Warm lamplight. She's on her laptop (screen shows only colorful abstract imagery of coastline, no text or words). Her expression transforms from tired to hopeful, eyes widening. Camera slowly pushes in on her face as she smiles for the first time. Mood: Hope, possibility.

ACT 3 (6-9 seconds): THE JOURNEY
Quick montage: Suitcase being zipped, glimpse of Cyprus flag colors (orange and white) on travel items but NO TEXT, airplane window showing brilliant blue Mediterranean below, rocky Cyprus coastline coming into view. Sunlight floods the frame. Colors shift from grey to golden. No airport signs, no text, no country names written anywhere. Mood: Anticipation, adventure.

ACT 4 (9-12 seconds): THE REALITY
Golden hour, sunset terrace overlooking Cyprus coast. Same woman now in flowy linen dress, glass of local wine in hand, surrounded by laughing friends at outdoor table. Mediterranean breeze in her hair, genuine smile on her face, laptop closed on table beside her. She raises her glass. No text on any objects. Mood: Freedom, joy, belonging.

Technical: Smooth transitions between acts. High contrast between London grey and Cyprus golden light. Cinematic color grading. Natural motion, no jarring cuts.

REMINDER: ZERO TEXT IN ANY FRAME. No words, letters, numbers, signs, logos, or writing of any kind.
"""

async def generate_seedance_video():
    """Generate 12-second 480p video using Seedance 1 Pro Fast."""

    print("=" * 70)
    print("  SEEDANCE 4-ACT VIDEO GENERATION TEST")
    print("  Cyprus Digital Nomad Visa - Transformation Story")
    print("=" * 70)

    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("ERROR: REPLICATE_API_TOKEN not set")
        return None

    print("\n--- Parameters ---")
    print("Model: bytedance/seedance-1-pro-fast")
    print("Duration: 12 seconds")
    print("Resolution: 480p")
    print("Aspect Ratio: 16:9")
    print(f"Prompt length: {len(CYPRUS_VISA_PROMPT)} chars")

    print("\n--- 4-Act Structure ---")
    for act_id, act_data in ACT_TIMESTAMPS.items():
        print(f"  {act_id}: {act_data['title']} ({act_data['start']}-{act_data['end']}s)")

    print("\n--- Generating Video ---")
    print("(This may take 2-5 minutes with Seedance)")

    client = replicate.Client(api_token=replicate_token)

    try:
        start_time = time.time()

        # Create prediction using run() for official models
        # This handles the model lookup automatically
        output = client.run(
            "bytedance/seedance-1-pro-fast",
            input={
                "prompt": CYPRUS_VISA_PROMPT,
                "duration": 12,
                "resolution": "480p",
                "aspect_ratio": "16:9",
            }
        )

        generation_time = time.time() - start_time

        # Get video URL from output
        if hasattr(output, 'url'):
            video_url = output.url
        elif isinstance(output, str):
            video_url = output
        else:
            video_url = str(output)

        print(f"\n--- SUCCESS ---")
        print(f"Generation time: {generation_time:.1f}s")
        print(f"Video URL: {video_url}")

        # Calculate cost
        cost = 0.015 * 12  # $0.015/second at 480p
        print(f"Estimated cost: ${cost:.3f}")

        return {
            "video_url": video_url,
            "generation_time": generation_time,
            "cost": cost,
            "prediction_id": "run_method"
        }

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def generate_seedance_video_v2():
    """Alternative: Generate using predictions.create with version lookup."""

    print("=" * 70)
    print("  SEEDANCE 4-ACT VIDEO GENERATION TEST (v2)")
    print("=" * 70)

    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("ERROR: REPLICATE_API_TOKEN not set")
        return None

    print("\n--- Parameters ---")
    print("Model: bytedance/seedance-1-pro-fast")
    print("Duration: 12 seconds")
    print("Resolution: 480p")

    client = replicate.Client(api_token=replicate_token)

    try:
        start_time = time.time()

        # Get the latest version of the model
        model = client.models.get("bytedance/seedance-1-pro-fast")
        version = model.latest_version

        print(f"Using version: {version.id}")
        print("\n--- Generating Video ---")

        # Create prediction with version
        prediction = client.predictions.create(
            version=version.id,
            input={
                "prompt": CYPRUS_VISA_PROMPT,
                "duration": 12,
                "resolution": "480p",
                "aspect_ratio": "16:9",
            }
        )

        print(f"Prediction ID: {prediction.id}")

        # Poll for completion
        max_wait = 600  # 10 minutes max
        poll_interval = 10
        elapsed = 0

        while elapsed < max_wait:
            prediction.reload()
            status = prediction.status
            print(f"  Status: {status} ({elapsed}s elapsed)")

            if status == "succeeded":
                break
            elif status == "failed":
                print(f"ERROR: Generation failed: {prediction.error}")
                return None
            elif status == "canceled":
                print("ERROR: Generation was canceled")
                return None

            time.sleep(poll_interval)
            elapsed += poll_interval

        generation_time = time.time() - start_time

        if prediction.status != "succeeded":
            print(f"ERROR: Timed out after {max_wait}s")
            return None

        # Get video URL
        output = prediction.output
        if hasattr(output, 'url'):
            video_url = output.url
        elif isinstance(output, str):
            video_url = output
        else:
            video_url = str(output)

        print(f"\n--- SUCCESS ---")
        print(f"Generation time: {generation_time:.1f}s")
        print(f"Video URL: {video_url}")

        # Calculate cost
        cost = 0.015 * 12  # $0.015/second at 480p
        print(f"Estimated cost: ${cost:.3f}")

        return {
            "video_url": video_url,
            "generation_time": generation_time,
            "cost": cost,
            "prediction_id": prediction.id
        }

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def upload_to_mux(video_url: str):
    """Upload video to Mux and get playback details."""

    print("\n" + "=" * 70)
    print("  MUX UPLOAD")
    print("=" * 70)

    mux_token_id = os.environ.get("MUX_TOKEN_ID")
    mux_token_secret = os.environ.get("MUX_TOKEN_SECRET")

    if not mux_token_id or not mux_token_secret:
        print("WARNING: MUX credentials not set, skipping upload")
        return None

    try:
        import mux_python
        from mux_python.rest import ApiException

        config = mux_python.Configuration()
        config.username = mux_token_id
        config.password = mux_token_secret

        assets_api = mux_python.AssetsApi(mux_python.ApiClient(config))

        print(f"Uploading: {video_url[:60]}...")

        # Create asset (without auto-generated captions for now)
        create_asset_request = mux_python.CreateAssetRequest(
            input=[mux_python.InputSettings(url=video_url)],
            playback_policy=[mux_python.PlaybackPolicy.PUBLIC]
        )

        asset_response = assets_api.create_asset(create_asset_request)
        asset = asset_response.data

        print(f"Asset ID: {asset.id}")
        print("Waiting for asset to be ready...")

        # Wait for asset to be ready
        max_wait = 300
        poll_interval = 5
        elapsed = 0

        while elapsed < max_wait:
            asset_data = assets_api.get_asset(asset.id).data
            status = asset_data.status
            print(f"  Status: {status} ({elapsed}s)")

            if status == "ready":
                break
            elif status == "errored":
                print(f"ERROR: Asset errored")
                return None

            time.sleep(poll_interval)
            elapsed += poll_interval

        if asset_data.status != "ready":
            print("ERROR: Asset not ready after timeout")
            return None

        playback_id = asset_data.playback_ids[0].id if asset_data.playback_ids else None
        duration = asset_data.duration

        print(f"\n--- MUX SUCCESS ---")
        print(f"Playback ID: {playback_id}")
        print(f"Duration: {duration}s")
        print(f"Asset ID: {asset.id}")

        return {
            "playback_id": playback_id,
            "asset_id": asset.id,
            "duration": duration
        }

    except Exception as e:
        print(f"ERROR uploading to Mux: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_mux_urls(playback_id: str):
    """Generate all Mux URLs for 4-act structure."""

    base_image = f"https://image.mux.com/{playback_id}"
    base_stream = f"https://stream.mux.com/{playback_id}"

    urls = {
        "stream_url": f"{base_stream}.m3u8",
        "playback_id": playback_id,
        "acts": {}
    }

    for act_id, act_data in ACT_TIMESTAMPS.items():
        urls["acts"][act_id] = {
            "title": act_data["title"],
            "start": act_data["start"],
            "end": act_data["end"],
            "thumbnail": f"{base_image}/thumbnail.jpg?time={act_data['mid']}&width=800",
            "gif": f"{base_image}/animated.gif?start={act_data['start']}&end={act_data['end']}&width=480&fps=15",
        }

    # Additional in-between thumbnails for section images
    urls["section_thumbnails"] = [
        {"time": 1.5, "url": f"{base_image}/thumbnail.jpg?time=1.5&width=800"},
        {"time": 2.5, "url": f"{base_image}/thumbnail.jpg?time=2.5&width=800"},
        {"time": 4.5, "url": f"{base_image}/thumbnail.jpg?time=4.5&width=800"},
        {"time": 5.5, "url": f"{base_image}/thumbnail.jpg?time=5.5&width=800"},
        {"time": 7.5, "url": f"{base_image}/thumbnail.jpg?time=7.5&width=800"},
        {"time": 8.5, "url": f"{base_image}/thumbnail.jpg?time=8.5&width=800"},
        {"time": 10.5, "url": f"{base_image}/thumbnail.jpg?time=10.5&width=800"},
        {"time": 11.5, "url": f"{base_image}/thumbnail.jpg?time=11.5&width=800"},
    ]

    return urls


def generate_demo_html(mux_urls: dict, video_result: dict):
    """Generate HTML demo showcasing 4-act structure."""

    playback_id = mux_urls["playback_id"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Seedance 4-Act Test - Cyprus Visa</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <link rel="stylesheet" href="https://unpkg.com/@mux/mux-player/dist/mux-player.css">
    <script src="https://unpkg.com/@mux/mux-player"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen p-8">
    <div class="max-w-6xl mx-auto">
        <h1 class="text-4xl font-bold mb-2">Seedance 4-Act Narrative Test</h1>
        <p class="text-gray-400 mb-8">Cyprus Digital Nomad Visa - 12 seconds, 480p, $0.18</p>

        <!-- Video Stats -->
        <div class="bg-gray-800 rounded-lg p-4 mb-8">
            <h2 class="text-xl font-semibold mb-2">Generation Stats</h2>
            <div class="grid grid-cols-4 gap-4 text-sm">
                <div><span class="text-gray-400">Model:</span> Seedance 1 Pro Fast</div>
                <div><span class="text-gray-400">Duration:</span> 12 seconds</div>
                <div><span class="text-gray-400">Resolution:</span> 480p</div>
                <div><span class="text-gray-400">Cost:</span> ${video_result.get('cost', 0.18):.3f}</div>
            </div>
        </div>

        <!-- Main Video Player with Chapters -->
        <div class="mb-12">
            <h2 class="text-2xl font-semibold mb-4">Full Video with Chapters</h2>
            <mux-player
                playback-id="{playback_id}"
                accent-color="#f59e0b"
                autoplay="muted"
                loop
                default-show-captions
                class="w-full rounded-lg"
            ></mux-player>
            <script>
                document.querySelector('mux-player').addChapters([
                    {{ startTime: 0, endTime: 3, value: "Act 1: The Grind" }},
                    {{ startTime: 3, endTime: 6, value: "Act 2: The Dream" }},
                    {{ startTime: 6, endTime: 9, value: "Act 3: The Journey" }},
                    {{ startTime: 9, endTime: 12, value: "Act 4: The Reality" }}
                ]);
            </script>
        </div>

        <!-- 4 Act Thumbnails -->
        <h2 class="text-2xl font-semibold mb-4">4-Act Thumbnails (at midpoints)</h2>
        <div class="grid grid-cols-4 gap-4 mb-12">
"""

    for act_id, act_data in mux_urls["acts"].items():
        html += f"""
            <div class="bg-gray-800 rounded-lg overflow-hidden">
                <img src="{act_data['thumbnail']}" class="w-full aspect-video object-cover" />
                <div class="p-3">
                    <h3 class="font-semibold">{act_data['title']}</h3>
                    <p class="text-sm text-gray-400">{act_data['start']}-{act_data['end']}s (mid: {ACT_TIMESTAMPS[act_id]['mid']}s)</p>
                </div>
            </div>
"""

    html += """
        </div>

        <!-- Bounded Video Players per Act -->
        <h2 class="text-2xl font-semibold mb-4">Bounded Video per Act (Auto-play)</h2>
        <div class="grid grid-cols-2 gap-6 mb-12">
"""

    for act_id, act_data in mux_urls["acts"].items():
        html += f"""
            <div class="bg-gray-800 rounded-lg overflow-hidden">
                <div class="relative">
                    <video
                        id="video-{act_id}"
                        class="w-full aspect-video"
                        muted
                        playsinline
                    ></video>
                    <div class="absolute top-2 left-2 bg-black/70 px-2 py-1 rounded text-sm">
                        {act_data['title']}
                    </div>
                </div>
                <div class="p-3">
                    <p class="text-sm text-gray-400">Bounded: {act_data['start']}s - {act_data['end']}s</p>
                </div>
            </div>
            <script>
                (function() {{
                    const video = document.getElementById('video-{act_id}');
                    const hls = new Hls();
                    hls.loadSource('{mux_urls["stream_url"]}');
                    hls.attachMedia(video);
                    hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                        video.currentTime = {act_data['start']};
                        video.play();
                    }});
                    video.addEventListener('timeupdate', function() {{
                        if (video.currentTime >= {act_data['end']}) {{
                            video.currentTime = {act_data['start']};
                        }}
                    }});
                }})();
            </script>
"""

    html += """
        </div>

        <!-- Section Image Examples with Overlay -->
        <h2 class="text-2xl font-semibold mb-4">Section Images with Title Overlay (Astro/CSS Demo)</h2>
        <div class="grid grid-cols-4 gap-4 mb-12">
"""

    section_titles = [
        "The European Titans",
        "Rising Stars",
        "Application Masterclass",
        "Tax Labyrinth",
        "Hidden Costs",
        "Future Trends",
        "Making It Reality",
        "Sources"
    ]

    for i, thumb in enumerate(mux_urls["section_thumbnails"]):
        title = section_titles[i] if i < len(section_titles) else f"Section {i+1}"
        html += f"""
            <div class="relative overflow-hidden rounded-lg">
                <img src="{thumb['url']}" class="w-full aspect-video object-cover" />
                <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent"></div>
                <div class="absolute bottom-2 left-2 right-2">
                    <p class="text-white font-semibold text-sm drop-shadow-lg">{title}</p>
                    <p class="text-gray-300 text-xs">@{thumb['time']}s</p>
                </div>
            </div>
"""

    html += f"""
        </div>

        <!-- GIFs per Act -->
        <h2 class="text-2xl font-semibold mb-4">Animated GIFs per Act</h2>
        <div class="grid grid-cols-4 gap-4 mb-12">
"""

    for act_id, act_data in mux_urls["acts"].items():
        html += f"""
            <div class="bg-gray-800 rounded-lg overflow-hidden">
                <img src="{act_data['gif']}" class="w-full aspect-video object-cover" />
                <div class="p-2 text-center">
                    <p class="text-sm font-semibold">{act_data['title']}</p>
                </div>
            </div>
"""

    html += f"""
        </div>

        <!-- JSON Data -->
        <h2 class="text-2xl font-semibold mb-4">video_narrative JSON (for database)</h2>
        <pre class="bg-gray-800 rounded-lg p-4 overflow-x-auto text-sm mb-8">
{json.dumps(mux_urls, indent=2)}
        </pre>

        <div class="text-center text-gray-500 text-sm mt-12">
            <p>Generated with Seedance 1 Pro Fast | 12s 480p | ~$0.18</p>
            <p>Playback ID: {playback_id}</p>
        </div>
    </div>
</body>
</html>
"""

    return html


async def main():
    """Run the full 4-act Seedance test."""

    print("\n" + "=" * 70)
    print("  SEEDANCE 4-ACT NARRATIVE TEST")
    print("  Cyprus Digital Nomad Visa Story")
    print("=" * 70)

    # Step 1: Generate video
    video_result = await generate_seedance_video()

    if not video_result:
        print("\n!!! Video generation failed, stopping test")
        return

    # Step 2: Upload to Mux
    mux_result = await upload_to_mux(video_result["video_url"])

    if not mux_result:
        print("\n!!! Mux upload failed or skipped")
        print(f"Video URL (manual test): {video_result['video_url']}")
        return

    # Step 3: Generate URLs
    print("\n" + "=" * 70)
    print("  GENERATING MUX URLS")
    print("=" * 70)

    mux_urls = generate_mux_urls(mux_result["playback_id"])

    print("\n4-Act Thumbnail URLs:")
    for act_id, act_data in mux_urls["acts"].items():
        print(f"  {act_id} ({act_data['title']}): {act_data['thumbnail']}")

    # Step 4: Generate demo HTML
    print("\n" + "=" * 70)
    print("  GENERATING DEMO HTML")
    print("=" * 70)

    html = generate_demo_html(mux_urls, video_result)

    demo_path = "/Users/dankeegan/quest/content-worker/test_seedance_4act_demo.html"
    with open(demo_path, "w") as f:
        f.write(html)

    print(f"Demo saved to: {demo_path}")
    print(f"\nOpen in browser: file://{demo_path}")

    print("\n" + "=" * 70)
    print("  TEST COMPLETE!")
    print("=" * 70)
    print(f"\nPlayback ID: {mux_result['playback_id']}")
    print(f"Cost: ${video_result['cost']:.3f}")
    print(f"Generation time: {video_result['generation_time']:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
