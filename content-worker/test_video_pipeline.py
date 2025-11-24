#!/usr/bin/env python3
"""
Test script for video generation pipeline.
Tests: Seedance video generation -> FFmpeg text overlay -> Mux upload -> GIF/thumbnail URLs
"""

import os
import sys
import time
import tempfile
import subprocess
import requests
import replicate
import mux_python
from mux_python.rest import ApiException

# Configuration
MUX_TOKEN_ID = os.environ.get("MUX_TOKEN_ID", "0d4004d7-d75a-4c93-9be9-cdfd619e0923")
MUX_TOKEN_SECRET = os.environ.get("MUX_TOKEN_SECRET", "dBYI5CpCAp0JeV/YcPSC/6K0iIg9qlwmpl0XK1dqzyHpFjy3yPUOmMqFpV7uAsg+RfCHu7QJuCN")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")

# Test parameters
TEST_PROMPT = "A modern office space with natural light streaming through large windows, plants on desks, cinematic"
VIDEO_DURATION = 3
VIDEO_RESOLUTION = "480p"
TEXT_OVERLAY = "Relocation Quest"
TEXT_POSITION = "bottom_left"  # bottom_left, bottom_center, top_left
SKIP_TEXT_OVERLAY = False  # FFmpeg now available at /tmp/ffmpeg
FFMPEG_PATH = "/tmp/ffmpeg"  # Path to FFmpeg binary


def generate_video_with_seedance(prompt: str, duration: int = 3, resolution: str = "480p") -> str:
    """Generate video using Seedance on Replicate."""
    print(f"\n1. Generating video with Seedance ({resolution}, {duration}s)...")

    if not REPLICATE_API_TOKEN:
        raise ValueError("REPLICATE_API_TOKEN environment variable not set")

    output = replicate.run(
        "bytedance/seedance-1-pro-fast",
        input={
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "aspect_ratio": "16:9",
            "camera_fixed": True,  # Reduces text warping if we try text in prompt
        }
    )

    video_url = output
    print(f"   Video generated: {video_url}")
    return video_url


def download_video(url: str, output_path: str) -> str:
    """Download video from URL to local file."""
    print(f"\n2. Downloading video...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"   Downloaded to: {output_path}")
    return output_path


def add_text_overlay(input_path: str, output_path: str, text: str, position: str = "bottom_left") -> str:
    """Add text overlay to video using FFmpeg."""
    print(f"\n3. Adding text overlay: '{text}'...")

    # Position mapping
    positions = {
        "bottom_left": "x=20:y=h-th-20",
        "bottom_center": "x=(w-tw)/2:y=h-th-20",
        "top_left": "x=20:y=20",
        "top_center": "x=(w-tw)/2:y=20",
    }

    pos = positions.get(position, positions["bottom_left"])

    # FFmpeg drawtext filter
    # Using a system font - adjust for your system
    filter_str = (
        f"drawtext=text='{text}':"
        f"{pos}:"
        f"fontsize=24:"
        f"fontcolor=white:"
        f"borderw=2:"
        f"bordercolor=black"
    )

    cmd = [
        FFMPEG_PATH,
        "-i", input_path,
        "-vf", filter_str,
        "-codec:a", "copy",
        "-y",  # Overwrite output
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"   FFmpeg stderr: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed: {result.returncode}")

    print(f"   Text overlay added: {output_path}")
    return output_path


def upload_to_mux(video_path: str) -> dict:
    """Upload video to Mux and return asset details."""
    print(f"\n4. Uploading to Mux...")

    # Configure Mux client
    configuration = mux_python.Configuration()
    configuration.username = MUX_TOKEN_ID
    configuration.password = MUX_TOKEN_SECRET

    # Create API clients
    assets_api = mux_python.AssetsApi(mux_python.ApiClient(configuration))

    # For local file upload, we need to use direct upload
    # First, create a direct upload URL
    uploads_api = mux_python.DirectUploadsApi(mux_python.ApiClient(configuration))

    create_upload_request = mux_python.CreateUploadRequest(
        new_asset_settings=mux_python.CreateAssetRequest(
            playback_policy=[mux_python.PlaybackPolicy.PUBLIC],
            # mp4_support not available on free tier
        ),
        cors_origin="*"
    )

    upload = uploads_api.create_direct_upload(create_upload_request)
    upload_url = upload.data.url
    upload_id = upload.data.id

    print(f"   Upload URL obtained, uploading file...")

    # Upload the file
    with open(video_path, 'rb') as f:
        response = requests.put(
            upload_url,
            data=f,
            headers={'Content-Type': 'video/mp4'}
        )
        response.raise_for_status()

    print(f"   File uploaded, waiting for processing...")

    # Wait for asset to be ready
    max_attempts = 30
    for attempt in range(max_attempts):
        upload_status = uploads_api.get_direct_upload(upload_id)

        if upload_status.data.asset_id:
            asset_id = upload_status.data.asset_id

            # Get asset details
            asset = assets_api.get_asset(asset_id)

            if asset.data.status == "ready":
                playback_id = asset.data.playback_ids[0].id
                print(f"   Asset ready! ID: {asset_id}")

                return {
                    "asset_id": asset_id,
                    "playback_id": playback_id,
                    "duration": asset.data.duration,
                    "status": asset.data.status
                }
            elif asset.data.status == "errored":
                raise RuntimeError(f"Asset processing failed: {asset.data.errors}")

        time.sleep(2)
        print(f"   Waiting... ({attempt + 1}/{max_attempts})")

    raise TimeoutError("Asset processing timed out")


def generate_urls(playback_id: str) -> dict:
    """Generate all useful URLs from playback ID."""
    base = f"https://image.mux.com/{playback_id}"
    stream = f"https://stream.mux.com/{playback_id}"

    return {
        "stream_url": f"{stream}.m3u8",
        "mp4_url": f"{stream}/medium.mp4",
        "gif_url": f"{base}/animated.gif?start=0&end=3&width=480&fps=15",
        "gif_webp_url": f"{base}/animated.webp?start=0&end=3&width=480&fps=15",
        "thumbnail_0s": f"{base}/thumbnail.jpg?time=0&width=640",
        "thumbnail_1s": f"{base}/thumbnail.jpg?time=1&width=640",
        "thumbnail_2s": f"{base}/thumbnail.jpg?time=2&width=640",
    }


def main():
    print("=" * 60)
    print("VIDEO PIPELINE TEST")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Step 1: Generate video
            video_url = generate_video_with_seedance(
                TEST_PROMPT,
                duration=VIDEO_DURATION,
                resolution=VIDEO_RESOLUTION
            )

            # Step 2: Download video
            input_path = os.path.join(tmpdir, "input.mp4")
            download_video(video_url, input_path)

            # Step 3: Add text overlay (optional)
            if SKIP_TEXT_OVERLAY:
                print("\n3. Skipping text overlay (FFmpeg not installed)")
                output_path = input_path
            else:
                output_path = os.path.join(tmpdir, "output.mp4")
                add_text_overlay(input_path, output_path, TEXT_OVERLAY, TEXT_POSITION)

            # Step 4: Upload to Mux
            mux_result = upload_to_mux(output_path)

            # Step 5: Generate URLs
            urls = generate_urls(mux_result["playback_id"])

            # Print results
            print("\n" + "=" * 60)
            print("SUCCESS! Video pipeline complete.")
            print("=" * 60)

            print(f"\nMux Asset ID: {mux_result['asset_id']}")
            print(f"Playback ID: {mux_result['playback_id']}")
            print(f"Duration: {mux_result['duration']}s")

            print("\n--- URLs ---")
            for name, url in urls.items():
                print(f"\n{name}:")
                print(f"  {url}")

            print("\n--- Test these URLs ---")
            print(f"\nGIF (paste in browser): {urls['gif_url']}")
            print(f"\nThumbnails for hover effect:")
            print(f"  Default: {urls['thumbnail_0s']}")
            print(f"  Hover:   {urls['thumbnail_1s']}")

            # Calculate cost
            cost_per_second = 0.015  # 480p
            total_cost = cost_per_second * VIDEO_DURATION
            print(f"\n--- Cost ---")
            print(f"Seedance ({VIDEO_RESOLUTION}, {VIDEO_DURATION}s): ${total_cost:.3f}")
            print(f"Mux hosting: Free tier / pay-as-you-go")

            return 0

        except Exception as e:
            print(f"\n ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    sys.exit(main())
