#!/usr/bin/env python3
"""
Quick test script for generate_article_video activity
Tests if custom video_prompt is being used
"""

import asyncio
import sys
import os
from pathlib import Path

# Add content-worker to path
sys.path.insert(0, str(Path(__file__).parent / "content-worker"))

# Load env vars
from dotenv import load_dotenv
load_dotenv("content-worker/.env")

from src.activities.media.video_generation import generate_article_video


async def test_with_custom_prompt():
    """Test video generation with custom prompt"""
    print("=" * 70)
    print("TEST 1: With Custom Prompt")
    print("=" * 70)

    try:
        result = await generate_article_video(
            title="Real Madrid Investment Deal",
            content="<p>Real Madrid is considering a 5% stake to external investors...</p>",
            app="placement",
            quality="low",
            duration=3,
            aspect_ratio="16:9",
            video_model="seedance",
            video_prompt="Investor in a boardroom shaking hands with executives"
        )

        print(f"\n✅ SUCCESS")
        print(f"Video URL: {result.get('video_url', 'N/A')[:80]}...")
        print(f"Prompt Used: {result.get('prompt_used', 'N/A')[:100]}...")
        print(f"Model: {result.get('model')}")
        print(f"Cost: ${result.get('cost'):.3f}")

        # Check if custom prompt was used
        prompt_used = result.get('prompt_used', '')
        if 'boardroom' in prompt_used.lower() or 'shaking hands' in prompt_used.lower():
            print("\n🎉 CUSTOM PROMPT WAS USED!")
            return True
        else:
            print("\n❌ CUSTOM PROMPT WAS NOT USED - fallback was generated instead")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_without_custom_prompt():
    """Test video generation without custom prompt (fallback)"""
    print("\n" + "=" * 70)
    print("TEST 2: Without Custom Prompt (Fallback)")
    print("=" * 70)

    try:
        result = await generate_article_video(
            title="Placement Notes Issue Report",
            content="<p>Goldman Sachs released 2 million in placement listings...</p>",
            app="placement",
            quality="low",
            duration=3,
            aspect_ratio="16:9",
            video_model="seedance",
            video_prompt=None  # No custom prompt - should use fallback
        )

        print(f"\n✅ SUCCESS")
        print(f"Video URL: {result.get('video_url', 'N/A')[:80]}...")
        print(f"Prompt Used: {result.get('prompt_used', 'N/A')[:100]}...")
        print(f"Model: {result.get('model')}")
        print(f"Cost: ${result.get('cost'):.3f}")

        print("\n✓ Fallback prompt generated successfully")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n🎬 Testing Video Generation Activity\n")

    # Test with custom prompt
    test1_passed = await test_with_custom_prompt()

    # Test without custom prompt
    test2_passed = await test_without_custom_prompt()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Test 1 (Custom Prompt): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Fallback): {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed:
        print("\n🎉 Custom prompts are working correctly!")
    else:
        print("\n⚠️  Custom prompts are NOT being used. Issue is in the activity or workflow parameter passing.")


if __name__ == "__main__":
    asyncio.run(main())
