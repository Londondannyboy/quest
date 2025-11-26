#!/usr/bin/env python3
"""
4-Act Temporal Activity Test

Calls actual Temporal activities (via local worker or Temporal Cloud)
to test the video generation pipeline WITHOUT article AI generation.

Usage:
  python3 test_4act_temporal.py              # Full test (prompt → video → mux)
  python3 test_4act_temporal.py --prompt     # Just test prompt generation
  python3 test_4act_temporal.py --existing   # Use existing video, just show thumbnails
"""

import asyncio
import os
import sys
from datetime import timedelta
from dotenv import load_dotenv

from temporalio.client import Client

load_dotenv()

# Config
TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
TEMPORAL_API_KEY = os.environ.get("TEMPORAL_API_KEY")
TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "company-profiling-queue")

# Mock article with 4 sections (simulates what article_generation.py produces)
MOCK_ARTICLE = {
    "title": "Cyprus Digital Nomad Visa 2025: Your Complete Escape Plan",
    "slug": "cyprus-digital-nomad-visa-2025-test",
    "excerpt": "Test article for 4-act video pipeline",
    "content": "<p>Test content</p>",
    "word_count": 100,
    "section_count": 4,
    "structured_sections": [
        {
            "title": "The London Grind: Why Remote Workers Are Burning Out",
            "visual_hint": "Dark grey London office interior, rain streaming down floor-to-ceiling windows. A woman in her 30s sits at a desk, blue monitor glow on her tired face, grey suit, slouched posture. Dreary cityscape visible through rain-streaked glass. Muted colors, cold fluorescent lighting. Camera slowly pulls back."
        },
        {
            "title": "The Cyprus Opportunity: Tax Benefits That Make Sense",
            "visual_hint": "Same woman now at home, warm evening golden hour light streaming through window. She's looking at her laptop with hope and discovery. Screen shows Mediterranean coastline imagery. Warm color palette, soft shadows. Camera gently pushes in on her hopeful expression."
        },
        {
            "title": "Making the Move: From Application to Arrival",
            "visual_hint": "Travel montage: hands packing a suitcase with summer clothes, a passport being placed in a bag, airplane window showing clouds then transitioning to aerial view of Cyprus coastline, golden Mediterranean waters below. Warm sunlight, sense of anticipation. Smooth cinematic transitions."
        },
        {
            "title": "Life After the Move: Six Months in Cyprus",
            "visual_hint": "Golden sunset terrace overlooking the Mediterranean Sea. The woman now in a flowing linen dress, holding a wine glass, genuine smile on her face. Friends laughing at an outdoor table nearby. Warm golden light, vibrant colors, palm trees swaying. Camera slowly orbits around her, pure contentment."
        }
    ]
}


async def get_temporal_client():
    """Connect to Temporal (Cloud or local)"""
    print(f"\n  Connecting to Temporal...")
    print(f"    Address: {TEMPORAL_ADDRESS}")
    print(f"    Namespace: {TEMPORAL_NAMESPACE}")
    print(f"    Task Queue: {TASK_QUEUE}")

    if TEMPORAL_API_KEY:
        # Temporal Cloud
        client = await Client.connect(
            TEMPORAL_ADDRESS,
            namespace=TEMPORAL_NAMESPACE,
            api_key=TEMPORAL_API_KEY,
            tls=True,
        )
        print(f"    Connected to Temporal Cloud ✅")
    else:
        # Local Temporal
        client = await Client.connect(
            TEMPORAL_ADDRESS,
            namespace=TEMPORAL_NAMESPACE,
        )
        print(f"    Connected to Local Temporal ✅")

    return client


async def test_generate_four_act_video_prompt(client):
    """Test: Call generate_four_act_video_prompt activity"""
    print("\n" + "=" * 70)
    print("  TEST 1: generate_four_act_video_prompt (Temporal Activity)")
    print("=" * 70)

    # Execute activity via a simple workflow
    # We use execute_activity directly since we're testing the activity
    from temporalio import workflow
    from temporalio.worker import Worker

    # Import the actual activity
    from src.activities.generation.media_prompts import generate_four_act_video_prompt

    # Create a temporary worker just to execute this activity
    async with Worker(
        client,
        task_queue=TASK_QUEUE + "-test",
        activities=[generate_four_act_video_prompt],
    ):
        # Execute the activity
        result = await client.execute_workflow(
            "test-4act-prompt",
            id=f"test-4act-prompt-{int(asyncio.get_event_loop().time())}",
            task_queue=TASK_QUEUE + "-test",
            run_timeout=timedelta(minutes=2),
        )

    return result


async def test_via_activity_directly():
    """Test activities by importing and calling directly (simpler)"""
    print("\n" + "=" * 70)
    print("  TEST: Direct Activity Calls (no workflow needed)")
    print("=" * 70)

    # Import activities
    from src.activities.generation.media_prompts import generate_four_act_video_prompt
    from src.activities.media.video_generation import generate_article_video
    from src.activities.media.mux_client import upload_video_to_mux

    # Test 1: Generate 4-act video prompt
    print("\n  1. Generating 4-act video prompt...")
    prompt_result = await generate_four_act_video_prompt(
        article=MOCK_ARTICLE,
        app="relocation",
        video_model="seedance"
    )

    print(f"    Success: {prompt_result.get('success')}")
    print(f"    Acts: {prompt_result.get('acts')}")
    print(f"    Prompt length: {len(prompt_result.get('prompt', ''))} chars")
    print(f"    Was truncated: {prompt_result.get('was_truncated')}")

    if not prompt_result.get('success'):
        print(f"    ERROR: {prompt_result.get('error')}")
        return None

    prompt = prompt_result['prompt']
    print(f"\n    --- PROMPT PREVIEW ---")
    print(f"    {prompt[:400]}...")

    return prompt_result


async def test_video_generation(prompt):
    """Test video generation activity"""
    print("\n" + "=" * 70)
    print("  TEST 2: generate_article_video (Seedance 12s)")
    print("=" * 70)

    from src.activities.media.video_generation import generate_article_video

    print(f"\n  Generating video... (takes ~60 seconds)")

    result = await generate_article_video(
        article_slug=MOCK_ARTICLE["slug"],
        article_title=MOCK_ARTICLE["title"],
        article_content=MOCK_ARTICLE["content"],
        app="relocation",
        video_prompt=prompt,
        quality="medium",
        duration=12,
        aspect_ratio="16:9"
    )

    print(f"\n  Success: {result.get('success')}")
    if result.get('success'):
        print(f"  Video URL: {result.get('video_url', '')[:60]}...")
        print(f"  Cost: ${result.get('cost', 0):.2f}")
    else:
        print(f"  ERROR: {result.get('error')}")

    return result


async def test_mux_upload(video_url):
    """Test Mux upload activity"""
    print("\n" + "=" * 70)
    print("  TEST 3: upload_video_to_mux")
    print("=" * 70)

    from src.activities.media.mux_client import upload_video_to_mux

    print(f"\n  Uploading to Mux...")

    result = await upload_video_to_mux(
        video_url=video_url,
        generate_gif=True
    )

    print(f"\n  Success: {result.get('success')}")
    if result.get('success'):
        print(f"  Playback ID: {result.get('playback_id')}")
        print(f"  Asset ID: {result.get('asset_id')}")
        print(f"  Stream URL: {result.get('stream_url')}")
    else:
        print(f"  ERROR: {result.get('error')}")

    return result


def show_thumbnails(playback_id):
    """Show Mux thumbnail URLs"""
    print("\n" + "=" * 70)
    print("  THUMBNAILS (Mux API)")
    print("=" * 70)

    base = f"https://image.mux.com/{playback_id}"

    thumbnails = {
        "Act 1 (1.5s)": f"{base}/thumbnail.jpg?time=1.5&width=800",
        "Act 2 (4.5s)": f"{base}/thumbnail.jpg?time=4.5&width=800",
        "Act 3 (7.0s)": f"{base}/thumbnail.jpg?time=7.0&width=800",
        "Act 4 (10.5s)": f"{base}/thumbnail.jpg?time=10.5&width=800",
        "Hero": f"{base}/thumbnail.jpg?time=10.5&width=1200&height=630&fit_mode=smartcrop",
    }

    for name, url in thumbnails.items():
        print(f"\n  {name}:")
        print(f"    {url}")

    # Generate test HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>4-Act Test Result</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/@mux/mux-player"></script>
</head>
<body class="bg-gray-900 text-white p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold mb-2">4-Act Video Test</h1>
        <p class="text-gray-400 mb-8">Playback ID: {playback_id}</p>

        <div class="bg-gray-800 rounded-xl p-6 mb-8">
            <h2 class="text-xl mb-4">Full Video (12 seconds)</h2>
            <mux-player playback-id="{playback_id}" accent-color="#f59e0b" class="w-full aspect-video rounded-lg"></mux-player>
        </div>

        <div class="bg-gray-800 rounded-xl p-6">
            <h2 class="text-xl mb-4">Act Thumbnails</h2>
            <div class="grid grid-cols-2 gap-4">
                <div><p class="text-sm text-gray-400 mb-2">Act 1 (0-3s)</p><img src="{thumbnails['Act 1 (1.5s)']}" class="rounded-lg" /></div>
                <div><p class="text-sm text-gray-400 mb-2">Act 2 (3-6s)</p><img src="{thumbnails['Act 2 (4.5s)']}" class="rounded-lg" /></div>
                <div><p class="text-sm text-gray-400 mb-2">Act 3 (6-9s)</p><img src="{thumbnails['Act 3 (7.0s)']}" class="rounded-lg" /></div>
                <div><p class="text-sm text-gray-400 mb-2">Act 4 (9-12s)</p><img src="{thumbnails['Act 4 (10.5s)']}" class="rounded-lg" /></div>
            </div>
        </div>
    </div>
</body>
</html>"""

    output_path = "/Users/dankeegan/quest/content-worker/test_4act_result.html"
    with open(output_path, "w") as f:
        f.write(html)

    print(f"\n  Test HTML: file://{output_path}")

    return thumbnails


async def main():
    print("\n" + "=" * 70)
    print("  4-ACT TEMPORAL ACTIVITY TEST")
    print("  (Calls actual activities, skips article AI generation)")
    print("=" * 70)

    # Handle flags
    if "--existing" in sys.argv:
        playback_id = "a2WovgYswGqojcLdc6Mv8YabXbHsU02MTPHoDbcE700Yc"
        print(f"\n  Using existing playback_id: {playback_id}")
        show_thumbnails(playback_id)
        return

    # Test 1: Generate 4-act video prompt
    prompt_result = await test_via_activity_directly()

    if "--prompt" in sys.argv:
        print("\n  --prompt flag: Stopping after prompt generation")
        return

    if not prompt_result or not prompt_result.get('success'):
        print("\n  FAILED: Prompt generation failed")
        return

    # Test 2: Generate video (takes ~60 seconds)
    video_result = await test_video_generation(prompt_result['prompt'])

    if not video_result or not video_result.get('success'):
        print("\n  FAILED: Video generation failed")
        return

    # Test 3: Upload to Mux
    mux_result = await test_mux_upload(video_result['video_url'])

    if not mux_result or not mux_result.get('success'):
        print("\n  FAILED: Mux upload failed")
        return

    # Show thumbnails
    show_thumbnails(mux_result['playback_id'])

    print("\n" + "=" * 70)
    print("  ALL TESTS PASSED! ✅")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
