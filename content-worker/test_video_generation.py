#!/usr/bin/env python3
"""
Direct video generation testing script - bypasses Temporal for faster testing.
Tests video generation and Mux upload without workflow overhead.

Usage:
    python test_video_generation.py

Or in Replit with this content.
"""

import asyncio
import os
import json
import time
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the activities directly
from src.activities.media.video_generation import generate_article_video
from src.activities.media.mux_client import upload_video_to_mux


# Test data - matches what the dashboard sends
TEST_CASES = {
    "real_madrid": {
        "title": "Real Madrid Considers Opening 5% Stake to External Investors",
        "content": """<p class="text-lg text-gray-700 leading-relaxed mb-6">
  <a href="https://www.reuters.com/sports/soccer/real-madrid-members-meet-ownership-change-considered-2025-11-23/"
     class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener">Real Madrid</a>,
  one of the world's most prestigious football clubs, is exploring a groundbreaking strategy to attract external investment
  by potentially selling a 5% stake in a newly created subsidiary, signaling a significant shift in the club's
  traditionally member-owned structure.
</p>

<h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Ownership Evolution Strategy</h2>

<p class="text-gray-700 leading-relaxed mb-4">
  Club President <a href="https://sports.yahoo.com/article/real-madrid-president-wants-investors-201027254.html"
     class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener">Florentino Pérez</a>
  announced the potential transformation during the club's annual general assembly, emphasizing that the move would
  maintain the club's core membership model while strategically opening a limited avenue for external investment.
</p>

<blockquote class="border-l-4 border-blue-500 pl-4 my-6 italic text-gray-600">
  "We will continue to be a members' club, but we must create a subsidiary in which the 100,000 members of Real Madrid
  will always retain absolute control," Pérez stated.
</blockquote>

<h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Investment Parameters</h2>

<ul class="list-disc list-inside space-y-2 mb-6 text-gray-700">
  <li>Potential stake: 5-10% in a new subsidiary</li>
  <li>Members will retain "absolute control"</li>
  <li>Investors must commit to long-term engagement</li>
  <li>Club reserves right to buy back assets</li>
</ul>""",
        "app": "placement",
        "quality": "low",
        "duration": 3,
        "aspect_ratio": "16:9",
        "video_model": "seedance",
        "video_prompt": "A private equity guy kicking a football with the word Quest printed on it through the office of a glass skyscraper in Madrid and then celebrating"
    },
    "startup_funding": {
        "title": "AI Startup Raises $50M Series B for Legal Tech Platform",
        "content": "<p>An AI startup focused on legal technology solutions has raised $50M in Series B funding...</p>",
        "app": "placement",
        "quality": "medium",
        "duration": 3,
        "aspect_ratio": "16:9",
        "video_model": "seedance",
        "video_prompt": None  # Will auto-generate based on title/content/app
    },
    # NEW: Test relocation app with proper Sonnet-style media prompt
    "cyprus_relocation": {
        "title": "Cyprus Digital Nomad Visa 2025: Complete Guide to Living and Working",
        "content": "<p>Cyprus has emerged as a top destination for digital nomads...</p>",
        "app": "relocation",
        "quality": "medium",
        "duration": 3,
        "aspect_ratio": "16:9",
        "video_model": "seedance",
        # Sonnet-style prompt with full formula: Subject + Action + Scene + Camera + Style
        "video_prompt": """Young professional couple walks slowly along Limassol marina at golden hour,
pausing to admire luxury yachts gently bobbing in the harbor, then turning to smile warmly at each other.
Camera pushes in gradually from wide establishing shot to medium close-up.
Warm Mediterranean sunset light, soft amber tones, crystal blue water reflections.
Cinematic travel documentary style, shallow depth of field, aspirational lifestyle aesthetic,
Conde Nast Traveller quality."""
    },
    # Test prompt transformation only (no API call)
    "prompt_test": {
        "title": "Test Prompt Transformation",
        "content": "<p>Test content</p>",
        "app": "relocation",
        "quality": "low",
        "duration": 3,
        "aspect_ratio": "16:9",
        "video_model": "seedance",
        "video_prompt": """Digital nomad opens laptop slowly at seaside cafe, takes a gentle sip of espresso,
looks up and smiles at the Mediterranean view. Camera tracks alongside smoothly.
Golden hour lighting, warm tones, travel magazine aesthetic."""
    }
}


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n📌 {title}")
    print("-" * 80)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


async def test_video_generation(test_case_name: str = "real_madrid", quality: str = None):
    """
    Test video generation activity directly.

    Args:
        test_case_name: Which test case to run (real_madrid, startup_funding)
        quality: Override quality (None=use test case default)
    """

    if test_case_name not in TEST_CASES:
        print(f"❌ Unknown test case: {test_case_name}")
        print(f"   Available: {', '.join(TEST_CASES.keys())}")
        return

    test_data = TEST_CASES[test_case_name].copy()

    # Override quality if specified
    if quality:
        test_data["quality"] = quality

    print_header("VIDEO GENERATION TEST")

    print_section("Input Parameters")
    print(f"Title:       {test_data['title']}")
    print(f"App:         {test_data['app']}")
    print(f"Quality:     {test_data['quality']}")
    print(f"Duration:    {test_data['duration']}s")
    print(f"Model:       {test_data['video_model']}")
    print(f"Prompt:      {test_data['video_prompt'][:80] if test_data['video_prompt'] else '(auto-generated)'}")
    print(f"Content len: {len(test_data['content'])} chars")

    print_section("Starting Video Generation Activity")
    print(f"⏱️  Start time: {datetime.now().strftime('%H:%M:%S')}")
    start_time = time.time()

    try:
        # Call the video generation activity directly
        result = await generate_article_video(
            title=test_data["title"],
            content=test_data["content"],
            app=test_data["app"],
            quality=test_data["quality"],
            duration=test_data["duration"],
            aspect_ratio=test_data["aspect_ratio"],
            video_model=test_data["video_model"],
            video_prompt=test_data["video_prompt"]
        )

        elapsed = time.time() - start_time

        print_section("Video Generation Result ✅")
        print(f"⏱️  Duration:    {format_duration(elapsed)}")
        print(f"Video URL:     {result['video_url'][:80]}...")
        print(f"Quality:       {result['quality']}")
        print(f"Resolution:    {result['resolution']}")
        print(f"Model:         {result['model']}")
        print(f"Cost:          ${result['cost']:.4f}")
        print(f"Prompt used:   {result['prompt_used'][:100]}...")

        return result

    except Exception as e:
        elapsed = time.time() - start_time
        print_section(f"Video Generation Failed ❌ (after {format_duration(elapsed)})")
        print(f"Error type:    {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return None


async def test_mux_upload(video_url: str):
    """
    Test uploading video to Mux.

    Args:
        video_url: URL of generated video to upload
    """

    print_section("Starting Mux Upload")
    print(f"Video URL: {video_url[:80]}...")
    print(f"⏱️  Start time: {datetime.now().strftime('%H:%M:%S')}")
    start_time = time.time()

    try:
        # Call the Mux upload activity
        result = await upload_video_to_mux(video_url, public=True)

        elapsed = time.time() - start_time

        print_section("Mux Upload Result ✅")
        print(f"⏱️  Duration:        {format_duration(elapsed)}")
        print(f"Asset ID:           {result.get('asset_id', 'N/A')}")
        print(f"Playback ID:        {result.get('playback_id', 'N/A')}")
        print(f"Stream URL:         {result.get('stream_url', 'N/A')[:80]}...")
        print(f"Status:             {result.get('status', 'N/A')}")

        if 'thumbnail_featured' in result:
            print(f"\nThumbnails Generated:")
            print(f"  Featured (1200x630): {result['thumbnail_featured'][:80]}...")
            print(f"  Hero (1920x1080):    {result['thumbnail_hero'][:80]}...")
            print(f"  GIF:                 {result.get('gif_url', 'N/A')[:80]}...")

        return result

    except Exception as e:
        elapsed = time.time() - start_time
        print_section(f"Mux Upload Failed ❌ (after {format_duration(elapsed)})")
        print(f"Error type:    {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return None


async def test_full_pipeline(test_case_name: str = "real_madrid"):
    """
    Test the complete pipeline: video generation → Mux upload.

    Args:
        test_case_name: Which test case to run
    """

    print_header("FULL VIDEO PIPELINE TEST")
    pipeline_start = time.time()

    # Step 1: Generate video
    video_result = await test_video_generation(test_case_name, quality="low")

    if not video_result:
        print_section("Pipeline Failed ❌")
        return

    # Step 2: Upload to Mux
    mux_result = await test_mux_upload(video_result["video_url"])

    if not mux_result:
        print_section("Pipeline Failed ❌")
        return

    # Summary
    total_elapsed = time.time() - pipeline_start
    print_section("Pipeline Complete ✅")
    print(f"Total time:       {format_duration(total_elapsed)}")
    print(f"\n🎬 Video successfully created and uploaded to Mux!")
    print(f"   Asset ID:      {mux_result.get('asset_id')}")
    print(f"   Playback URL:  https://image.mux.com/{mux_result.get('playback_id')}/thumbnail.jpg")
    print(f"   Stream URL:    {mux_result.get('stream_url')}")

    return {
        "video": video_result,
        "mux": mux_result,
        "total_duration": total_elapsed
    }


async def test_cost_estimates():
    """Test cost estimation for different quality tiers."""
    from src.activities.media.video_generation import get_video_cost_estimate

    print_header("VIDEO COST ESTIMATES")

    qualities = ["low", "medium", "high"]
    durations = [3, 5, 10]

    print_section("Cost Summary")
    print(f"{'Quality':<12} {'Duration':<12} {'Cost':<10} {'Model':<40}")
    print("-" * 74)

    for quality in qualities:
        for duration in durations:
            try:
                estimate = await get_video_cost_estimate(quality=quality, duration=duration)
                cost = estimate["cost"]
                model = estimate["model"]
                print(f"{quality:<12} {duration}s{'':<9} ${cost:.4f}    {model:<40}")
            except Exception as e:
                print(f"{quality:<12} {duration}s{'':<9} ERROR: {str(e)[:40]}")


async def verify_env_vars():
    """Verify required environment variables are set."""

    print_header("ENVIRONMENT VERIFICATION")

    required_vars = {
        "REPLICATE_API_TOKEN": "Replicate API token for video generation",
        "MUX_TOKEN_ID": "Mux API token ID",
        "MUX_TOKEN_SECRET": "Mux API token secret",
    }

    missing = []
    set_vars = []

    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # Show masked value
            if len(value) > 20:
                masked = value[:10] + "..." + value[-5:]
            else:
                masked = "*" * len(value)
            print(f"✅ {var:<25} {masked:<20} {description}")
            set_vars.append(var)
        else:
            print(f"❌ {var:<25} NOT SET  {description}")
            missing.append(var)

    print()

    if missing:
        print(f"⚠️  Missing {len(missing)} required variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nSet them in .env file:")
        for var in missing:
            print(f"   {var}=your_value_here")
        return False
    else:
        print("✅ All required environment variables are set!")
        return True


async def test_prompt_transformation():
    """Test prompt transformation without API calls - instant!"""
    from src.activities.media.video_generation import (
        transform_prompt_for_seedance,
        transform_prompt_for_wan
    )

    print_header("PROMPT TRANSFORMATION TEST (No API calls)")

    for name, test_data in TEST_CASES.items():
        if not test_data.get("video_prompt"):
            continue

        print_section(f"Test Case: {name}")
        original = test_data["video_prompt"]
        print(f"Original ({len(original)} chars):")
        print(f"  {original[:150]}...")

        # Seedance transformation
        seedance = transform_prompt_for_seedance(original)
        print(f"\nSeedance ({len(seedance)} chars):")
        print(f"  {seedance[:150]}...")

        # WAN 2.5 transformation
        wan_pos, wan_neg = transform_prompt_for_wan(original)
        print(f"\nWAN 2.5 Positive ({len(wan_pos)} chars):")
        print(f"  {wan_pos[:150]}...")
        print(f"\nWAN 2.5 Negative:")
        print(f"  {wan_neg}")


async def main():
    """Main test runner."""

    import sys

    print(f"\n🎬 Video Generation Test Suite")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Verify environment
    env_ok = await verify_env_vars()

    print("\n📋 Available Tests:")
    print("   prompt  - Test prompt transformation (instant, no API)")
    print("   quick   - Cost Estimates")
    print("   generate - Single Video Generation")
    print("   cyprus  - Cyprus relocation video (Sonnet-style prompt)")
    print("   full    - Full Pipeline (generate + upload to Mux)")

    # For automated testing, run full pipeline
    if len(sys.argv) > 1:
        test = sys.argv[1]
        if test == "prompt":
            await test_prompt_transformation()
        elif test == "quick":
            await test_cost_estimates()
        elif test == "generate":
            if not env_ok:
                print("\n❌ Cannot proceed without required environment variables")
                sys.exit(1)
            await test_video_generation("real_madrid", quality="low")
        elif test == "cyprus":
            if not env_ok:
                print("\n❌ Cannot proceed without required environment variables")
                sys.exit(1)
            await test_video_generation("cyprus_relocation", quality="medium")
        elif test == "full":
            if not env_ok:
                print("\n❌ Cannot proceed without required environment variables")
                sys.exit(1)
            await test_full_pipeline("real_madrid")
        else:
            print(f"Unknown test: {test}")
            print("Available: prompt, quick, generate, cyprus, full")
    else:
        # Default: test prompt transformation (instant, no API)
        print("\n→ Running prompt transformation test (instant, no API)...")
        await test_prompt_transformation()

    print("\n" + "=" * 80)
    print("✅ Test suite complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
