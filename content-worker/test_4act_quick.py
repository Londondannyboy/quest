#!/usr/bin/env python3
"""
Quick 4-Act Video Test
Tests ONLY the video generation pipeline (skips article research)
"""

import asyncio
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Simulated article with 4 sections (like what article_generation.py produces)
MOCK_ARTICLE = {
    "title": "Cyprus Digital Nomad Visa 2025: Your Complete Escape Plan",
    "slug": "cyprus-digital-nomad-visa-2025",
    "structured_sections": [
        {
            "title": "The London Grind: Why Remote Workers Are Burning Out",
            "visual_hint": "Dark grey London office interior, rain streaming down floor-to-ceiling windows. A woman in her 30s sits at a desk, blue monitor glow on her tired face, grey suit, slouched posture. Dreary cityscape visible through rain-streaked glass. Muted colors, cold fluorescent lighting. Camera slowly pulls back revealing the isolating cubicle environment."
        },
        {
            "title": "The Cyprus Opportunity: Tax Benefits That Actually Make Sense",
            "visual_hint": "Same woman now at home, warm evening golden hour light streaming through window. She's looking at her laptop with an expression of hope and discovery. Screen shows Mediterranean coastline imagery (no text visible). Warm color palette, soft shadows, the beginning of transformation. Camera gently pushes in on her hopeful expression."
        },
        {
            "title": "Making the Move: From Application to Arrival",
            "visual_hint": "Travel montage: hands packing a suitcase with summer clothes, a passport being placed in a bag, airplane window showing clouds then transitioning to aerial view of Cyprus coastline, golden Mediterranean waters below. Warm sunlight, sense of movement and anticipation. Smooth cinematic transitions between each moment."
        },
        {
            "title": "Life After the Move: What Six Months in Cyprus Actually Looks Like",
            "visual_hint": "Golden sunset terrace overlooking the Mediterranean Sea. The woman now in a flowing linen dress, holding a wine glass, genuine smile on her face. Friends laughing at an outdoor table nearby. Warm golden light, vibrant colors, palm trees swaying gently. Camera slowly orbits around her as she takes in the view, pure contentment."
        }
    ]
}


def test_1_video_prompt_generation():
    """Test: Generate 4-act video prompt from article sections"""
    print("\n" + "=" * 70)
    print("  TEST 1: Generate 4-Act Video Prompt")
    print("=" * 70)

    sections = MOCK_ARTICLE["structured_sections"]

    # This is what generate_four_act_video_prompt does
    no_text_rule = "CRITICAL: NO text, words, letters, numbers anywhere. Purely visual."
    media_style = "Cinematic, warm Mediterranean tones, professional documentary style"

    act_prompts = []
    for i, section in enumerate(sections[:4]):
        act_num = i + 1
        visual_hint = section.get("visual_hint", "")
        title = section.get("title", f"Section {act_num}")

        start_time = (act_num - 1) * 3
        end_time = act_num * 3

        act_prompts.append(f"ACT {act_num} ({start_time}s-{end_time}s): {title}\n{visual_hint}")

    acts_text = "\n\n".join(act_prompts)

    prompt = f"""{no_text_rule}

STYLE: {media_style}

VIDEO STRUCTURE: 12 seconds, 4 acts of 3 seconds each.

{acts_text}

{no_text_rule}"""

    # Enforce 2000 char limit for Seedance
    if len(prompt) > 2000:
        print(f"  WARNING: Prompt {len(prompt)} chars exceeds 2000 limit - truncating")
        prompt = prompt[:2000]

    print(f"\n  Prompt length: {len(prompt)} chars (limit: 2000)")
    print(f"  Acts with visual_hints: {len([s for s in sections if s.get('visual_hint')])}/4")
    print("\n  --- PROMPT PREVIEW (first 500 chars) ---")
    print(f"  {prompt[:500]}...")

    return prompt


async def test_2_video_generation(prompt):
    """Test: Generate video with Seedance"""
    print("\n" + "=" * 70)
    print("  TEST 2: Generate Seedance Video (12s, 480p)")
    print("=" * 70)

    import replicate

    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("  ERROR: REPLICATE_API_TOKEN not set")
        return None

    print(f"\n  Model: bytedance/seedance-1-pro-fast")
    print(f"  Duration: 12s | Resolution: 480p | Aspect: 16:9")
    print(f"  Generating... (typically 50-70 seconds)")

    client = replicate.Client(api_token=replicate_token)

    start = time.time()
    output = client.run(
        "bytedance/seedance-1-pro-fast",
        input={
            "prompt": prompt,
            "duration": 12,
            "resolution": "480p",
            "aspect_ratio": "16:9",
        }
    )
    elapsed = time.time() - start

    video_url = str(output) if not hasattr(output, 'url') else output.url

    print(f"\n  ✅ Video generated in {elapsed:.1f}s")
    print(f"  URL: {video_url[:80]}...")
    print(f"  Cost: ~$0.18")

    return video_url


async def test_3_mux_upload(video_url):
    """Test: Upload to Mux and get playback_id"""
    print("\n" + "=" * 70)
    print("  TEST 3: Upload to Mux")
    print("=" * 70)

    mux_token_id = os.environ.get("MUX_TOKEN_ID")
    mux_token_secret = os.environ.get("MUX_TOKEN_SECRET")

    if not mux_token_id or not mux_token_secret:
        print("  ERROR: MUX credentials not set")
        return None

    import mux_python

    config = mux_python.Configuration()
    config.username = mux_token_id
    config.password = mux_token_secret

    assets_api = mux_python.AssetsApi(mux_python.ApiClient(config))

    print(f"\n  Creating Mux asset from: {video_url[:50]}...")

    create_request = mux_python.CreateAssetRequest(
        input=[mux_python.InputSettings(url=video_url)],
        playback_policy=[mux_python.PlaybackPolicy.PUBLIC]
    )

    asset = assets_api.create_asset(create_request).data
    print(f"  Asset ID: {asset.id}")

    # Wait for ready
    elapsed = 0
    while elapsed < 120:
        asset_data = assets_api.get_asset(asset.id).data
        print(f"    Status: {asset_data.status} ({elapsed}s)")
        if asset_data.status == "ready":
            break
        await asyncio.sleep(5)
        elapsed += 5

    if asset_data.status != "ready":
        print("  ERROR: Asset not ready after 120s")
        return None

    playback_id = asset_data.playback_ids[0].id

    print(f"\n  ✅ Mux upload complete!")
    print(f"  Playback ID: {playback_id}")

    return playback_id


def test_4_thumbnail_urls(playback_id):
    """Test: Generate Mux thumbnail URLs"""
    print("\n" + "=" * 70)
    print("  TEST 4: Generate Mux Thumbnail URLs")
    print("=" * 70)

    base = f"https://image.mux.com/{playback_id}"

    thumbnails = {
        "Act 1 (1.5s)": f"{base}/thumbnail.jpg?time=1.5&width=800",
        "Act 2 (4.5s)": f"{base}/thumbnail.jpg?time=4.5&width=800",
        "Act 3 (7.0s)": f"{base}/thumbnail.jpg?time=7.0&width=800",
        "Act 4 (10.5s)": f"{base}/thumbnail.jpg?time=10.5&width=800",
        "Hero (10.5s)": f"{base}/thumbnail.jpg?time=10.5&width=1200&height=630&fit_mode=smartcrop",
    }

    print(f"\n  Thumbnail URLs:")
    for name, url in thumbnails.items():
        print(f"    {name}: {url}")

    # Video stream URL
    stream_url = f"https://stream.mux.com/{playback_id}.m3u8"
    print(f"\n  Stream URL: {stream_url}")

    return thumbnails


def generate_test_html(playback_id, thumbnails):
    """Generate test HTML to view the results"""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>4-Act Video Test</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/@mux/mux-player"></script>
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold mb-8">4-Act Video Test Results</h1>

        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4">Full Video (12 seconds, 4 acts)</h2>
            <mux-player
                playback-id="{playback_id}"
                accent-color="#f59e0b"
                class="w-full aspect-video rounded-lg"
            ></mux-player>
        </div>

        <div class="bg-white rounded-lg shadow-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Act Thumbnails (from Mux API)</h2>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <p class="text-sm text-gray-500 mb-2">Act 1 (0-3s) - London Grind</p>
                    <img src="{thumbnails['Act 1 (1.5s)']}" class="w-full rounded-lg" />
                </div>
                <div>
                    <p class="text-sm text-gray-500 mb-2">Act 2 (3-6s) - Opportunity</p>
                    <img src="{thumbnails['Act 2 (4.5s)']}" class="w-full rounded-lg" />
                </div>
                <div>
                    <p class="text-sm text-gray-500 mb-2">Act 3 (6-9s) - Travel</p>
                    <img src="{thumbnails['Act 3 (7.0s)']}" class="w-full rounded-lg" />
                </div>
                <div>
                    <p class="text-sm text-gray-500 mb-2">Act 4 (9-12s) - Cyprus Life</p>
                    <img src="{thumbnails['Act 4 (10.5s)']}" class="w-full rounded-lg" />
                </div>
            </div>
        </div>

        <div class="mt-8 text-sm text-gray-500">
            <p>Playback ID: {playback_id}</p>
        </div>
    </div>
</body>
</html>"""

    output_path = "/Users/dankeegan/quest/content-worker/test_4act_result.html"
    with open(output_path, "w") as f:
        f.write(html)

    print(f"\n  ✅ Test HTML saved: {output_path}")
    print(f"  Open: file://{output_path}")

    return output_path


async def main():
    import sys

    print("\n" + "=" * 70)
    print("  QUICK 4-ACT VIDEO PIPELINE TEST")
    print("=" * 70)

    # Check for --skip-video flag to use existing playback_id
    if "--existing" in sys.argv:
        # Use an existing playback_id for quick thumbnail testing
        playback_id = "a2WovgYswGqojcLdc6Mv8YabXbHsU02MTPHoDbcE700Yc"  # From earlier test
        print(f"\n  Using existing playback_id: {playback_id}")
        thumbnails = test_4_thumbnail_urls(playback_id)
        generate_test_html(playback_id, thumbnails)
        return

    # Test 1: Video prompt generation
    prompt = test_1_video_prompt_generation()

    if "--prompt-only" in sys.argv:
        print("\n  --prompt-only flag: Stopping after prompt generation")
        return

    # Test 2: Video generation (this takes ~60 seconds)
    video_url = await test_2_video_generation(prompt)
    if not video_url:
        return

    # Test 3: Mux upload
    playback_id = await test_3_mux_upload(video_url)
    if not playback_id:
        return

    # Test 4: Thumbnail URLs
    thumbnails = test_4_thumbnail_urls(playback_id)

    # Generate test HTML
    generate_test_html(playback_id, thumbnails)

    print("\n" + "=" * 70)
    print("  ALL TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
