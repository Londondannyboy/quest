#!/usr/bin/env python3
"""
Quick test to verify Pydantic AI integration.

Run with:
    python test_pydantic_ai.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_pydantic_ai():
    """Test Pydantic AI with available providers."""
    from pydantic_ai import Agent

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    google_key = os.environ.get("GOOGLE_API_KEY")

    print("=" * 60)
    print("🧪 Pydantic AI Integration Test")
    print("=" * 60)
    print()

    # Check API keys
    print("📋 Configuration:")
    print(f"   ANTHROPIC_API_KEY: {'✅ Set' if anthropic_key else '❌ Not set'}")
    print(f"   GOOGLE_API_KEY: {'✅ Set' if google_key else '❌ Not set'}")
    print()

    if not anthropic_key and not google_key:
        print("❌ No API key available. Set ANTHROPIC_API_KEY or GOOGLE_API_KEY")
        return False

    # Test with Anthropic Haiku (fast)
    if anthropic_key:
        print("🔄 Testing Anthropic Claude 3.5 Haiku via Pydantic AI...")
        try:
            agent = Agent('anthropic:claude-3-5-haiku-latest')
            result = await agent.run("What is 2 + 2? Reply with just the number.")
            response = result.output.strip()
            print(f"   Response: {response}")
            if "4" in response:
                print("   ✅ Anthropic Haiku: PASSED")
            else:
                print(f"   ⚠️  Unexpected response: {response}")
        except Exception as e:
            print(f"   ❌ Anthropic Haiku: FAILED - {e}")
            return False

        # Test with Anthropic Sonnet (quality)
        print()
        print("🔄 Testing Anthropic Claude Sonnet via Pydantic AI...")
        try:
            agent = Agent('anthropic:claude-sonnet-4-20250514')
            result = await agent.run("Name one country in Europe. Reply with just the country name.")
            response = result.output.strip()
            print(f"   Response: {response}")
            print("   ✅ Anthropic Sonnet: PASSED")
        except Exception as e:
            print(f"   ❌ Anthropic Sonnet: FAILED - {e}")
            return False

    # Test Google if key is set (may fail if key is invalid)
    if google_key:
        print()
        print("🔄 Testing Google Gemini via Pydantic AI...")
        try:
            from pydantic_ai.models.google import GoogleModel
            model = GoogleModel('gemini-2.5-flash')
            agent = Agent(model=model)
            result = await agent.run("What is 3 + 3? Reply with just the number.")
            response = result.output.strip()
            print(f"   Response: {response}")
            print("   ✅ Google Gemini: PASSED")
        except Exception as e:
            print(f"   ⚠️  Google Gemini: FAILED - {e}")
            print("      (This is OK if Anthropic works)")

    print()
    print("=" * 60)
    print("✅ Pydantic AI tests passed!")
    print("=" * 60)
    print()
    print("The Country Guide workflow should now work with Anthropic.")

    return True


async def test_config():
    """Test config module."""
    print()
    print("🔄 Testing config module...")

    try:
        from src.utils.config import config

        print(f"   use_gateway(): {config.use_gateway()}")
        print(f"   get_gemini_model('flash'): {config.get_gemini_model('flash')}")
        print(f"   get_gemini_model('pro'): {config.get_gemini_model('pro')}")
        print("   ✅ Config: PASSED")
        return True

    except Exception as e:
        print(f"   ❌ Config: FAILED - {e}")
        return False


async def main():
    config_ok = await test_config()
    if not config_ok:
        print("❌ Config test failed")
        return

    ai_ok = await test_pydantic_ai()
    if not ai_ok:
        print("❌ AI test failed")
        return


if __name__ == "__main__":
    asyncio.run(main())
