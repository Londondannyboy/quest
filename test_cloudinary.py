#!/usr/bin/env python3
"""Test Cloudinary upload"""
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

print(f"Cloud name: {os.getenv('CLOUDINARY_CLOUD_NAME')}")
print(f"API key: {os.getenv('CLOUDINARY_API_KEY')[:10]}...")

# Use the Replicate URL from the test
test_url = "https://replicate.delivery/xezq/53TRmDGROxLUO5OOUY3eJh6bLKyZ1zWUgygFjcped6R3ECoVA/tmptvl2p1ho.png"

try:
    print(f"\n☁️  Testing Cloudinary upload...")
    result = cloudinary.uploader.upload(
        test_url,
        folder="quest-articles",
        public_id="test_upload",
        overwrite=True,
        resource_type="image"
    )

    print(f"✅ Success!")
    print(f"URL: {result['secure_url']}")
    print(f"Format: {result.get('format')}")
    print(f"Size: {result.get('bytes')} bytes")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
