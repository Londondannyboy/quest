#!/usr/bin/env python3
"""
Test dual text overlay - Article title + Brand
"""

import os
import sys
import time
import tempfile
import subprocess
import requests
import replicate
import mux_python

# Config
MUX_TOKEN_ID = "0d4004d7-d75a-4c93-9be9-cdfd619e0923"
MUX_TOKEN_SECRET = "dBYI5CpCAp0JeV/YcPSC/6K0iIg9qlwmpl0XK1dqzyHpFjy3yPUOmMqFpV7uAsg+RfCHu7QJuCN"
FFMPEG_PATH = "/tmp/ffmpeg"

# Test content
TEST_PROMPT = "Professional office with city skyline view, modern interior design, cinematic lighting"
ARTICLE_TITLE = "Latvia Startup Visa Guide"
BRAND = "Relocation Quest"


def main():
    print("=" * 60)
    print("DUAL TEXT OVERLAY TEST")
    print(f"Title: {ARTICLE_TITLE}")
    print(f"Brand: {BRAND}")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Generate video
        print("\n1. Generating video with Seedance...")
        output = replicate.run(
            "bytedance/seedance-1-pro-fast",
            input={
                "prompt": TEST_PROMPT,
                "duration": 3,
                "resolution": "480p",
                "aspect_ratio": "16:9",
            }
        )
        video_url = output
        print(f"   Video: {video_url}")

        # 2. Download
        print("\n2. Downloading video...")
        input_path = os.path.join(tmpdir, "input.mp4")
        response = requests.get(video_url, stream=True)
        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 3. Add dual text overlay
        print("\n3. Adding dual text overlay...")
        output_path = os.path.join(tmpdir, "output.mp4")

        # Escape text for FFmpeg
        def escape(text):
            return text.replace("'", "\\'").replace(":", "\\:")

        # Title at top center, Brand at bottom left
        filter_str = (
            f"drawtext=text='{escape(ARTICLE_TITLE)}':"
            f"x=(w-tw)/2:y=30:"
            f"fontsize=28:fontcolor=white:borderw=3:bordercolor=black,"
            f"drawtext=text='{escape(BRAND)}':"
            f"x=20:y=h-th-20:"
            f"fontsize=20:fontcolor=white:borderw=2:bordercolor=black"
        )

        cmd = [FFMPEG_PATH, "-i", input_path, "-vf", filter_str, "-codec:a", "copy", "-y", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"   FFmpeg error: {result.stderr}")
            return 1

        print("   Text overlay added!")

        # 4. Upload to Mux
        print("\n4. Uploading to Mux...")
        config = mux_python.Configuration()
        config.username = MUX_TOKEN_ID
        config.password = MUX_TOKEN_SECRET

        uploads_api = mux_python.DirectUploadsApi(mux_python.ApiClient(config))
        assets_api = mux_python.AssetsApi(mux_python.ApiClient(config))

        upload = uploads_api.create_direct_upload(
            mux_python.CreateUploadRequest(
                new_asset_settings=mux_python.CreateAssetRequest(
                    playback_policy=[mux_python.PlaybackPolicy.PUBLIC],
                ),
                cors_origin="*"
            )
        )

        with open(output_path, 'rb') as f:
            requests.put(upload.data.url, data=f, headers={'Content-Type': 'video/mp4'})

        # Wait for processing
        for _ in range(30):
            status = uploads_api.get_direct_upload(upload.data.id)
            if status.data.asset_id:
                asset = assets_api.get_asset(status.data.asset_id)
                if asset.data.status == "ready":
                    playback_id = asset.data.playback_ids[0].id
                    break
            time.sleep(2)
        else:
            print("   Timeout waiting for Mux")
            return 1

        # 5. Output URLs
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)

        print(f"\nPlayback ID: {playback_id}")

        gif_url = f"https://image.mux.com/{playback_id}/animated.gif?start=0&end=3&width=480&fps=15"
        thumb_url = f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=1.5&width=640"

        print(f"\nGIF (with title + brand):")
        print(f"  {gif_url}")

        print(f"\nThumbnail:")
        print(f"  {thumb_url}")

        print("\n--- Layout ---")
        print("┌────────────────────────────┐")
        print("│   Latvia Startup Visa Guide│  ← Title (top center)")
        print("│                            │")
        print("│    [AI Generated Video]    │")
        print("│                            │")
        print("│ Relocation Quest           │  ← Brand (bottom left)")
        print("└────────────────────────────┘")

        return 0


if __name__ == "__main__":
    sys.exit(main())
