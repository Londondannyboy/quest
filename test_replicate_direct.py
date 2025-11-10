#!/usr/bin/env python3
"""Test Replicate API directly"""
import os
from dotenv import load_dotenv
import replicate

load_dotenv()

print(f"REPLICATE_API_TOKEN: {os.getenv('REPLICATE_API_TOKEN')[:20]}...")

try:
    print("\n🎨 Testing Replicate API...")
    output = replicate.run(
        "ideogram-ai/ideogram-v3-turbo",
        input={
            "prompt": "Professional financial concept illustration, corporate style, Bloomberg aesthetic",
            "aspect_ratio": "16:9",
            "magic_prompt_option": "Auto",
            "style_type": "General"
        }
    )

    print(f"✅ Success! Output type: {type(output)}")
    print(f"Output: {output}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
