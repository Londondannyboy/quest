"""
FFmpeg utilities for video processing with text overlays.
"""

import os
import subprocess
import tempfile
import requests
from temporalio import activity
from typing import Dict, Any, Optional


# App branding - Simple "Q" logo that can't be misread
APP_BRANDS = {
    "placement": "Q",
    "relocation": "Q",
    "rainmaker": "Rainmaker",
    "chief-of-staff": "Chief of Staff",
}


@activity.defn
async def add_video_text_overlay(
    video_url: str,
    title: Optional[str] = None,
    brand: Optional[str] = None,
    app: str = "placement",
    title_position: str = "top_center",
    brand_position: str = "bottom_left",
) -> str:
    """
    Add text overlay to video using FFmpeg.

    Args:
        video_url: URL of input video
        title: Article title to display (optional)
        brand: Brand text override (optional, defaults to app brand)
        app: App name for default branding
        title_position: Position for title text
        brand_position: Position for brand text

    Returns:
        Path to processed video file
    """
    activity.logger.info(f"Adding text overlay to video...")

    # Get brand text
    if brand is None:
        brand = APP_BRANDS.get(app, "Q")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Download video
        input_path = os.path.join(tmpdir, "input.mp4")
        output_path = os.path.join(tmpdir, "output.mp4")

        activity.logger.info("Downloading video...")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Build filter string
        filters = []

        # Add title text if provided
        if title:
            title_filter = build_text_filter(
                text=title,
                position=title_position,
                fontsize=28,
                fontcolor="white",
                borderw=3,
                bordercolor="black"
            )
            filters.append(title_filter)

        # Add brand text
        if brand:
            brand_filter = build_text_filter(
                text=brand,
                position=brand_position,
                fontsize=20,
                fontcolor="white",
                borderw=2,
                bordercolor="black"
            )
            filters.append(brand_filter)

        if not filters:
            activity.logger.info("No text to add, returning original video")
            return video_url

        # Combine filters
        filter_string = ",".join(filters)

        # Run FFmpeg
        ffmpeg_path = os.environ.get("FFMPEG_PATH", "ffmpeg")

        cmd = [
            ffmpeg_path,
            "-i", input_path,
            "-vf", filter_string,
            "-codec:a", "copy",
            "-y",
            output_path
        ]

        activity.logger.info(f"Running FFmpeg with filters: {filter_string[:100]}...")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            activity.logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed: {result.returncode}")

        activity.logger.info("Text overlay added successfully")

        # Return the output path - caller should upload to Mux
        # For now, we need to upload to a temporary location
        # In production, this would upload to cloud storage
        return output_path


def build_text_filter(
    text: str,
    position: str,
    fontsize: int = 24,
    fontcolor: str = "white",
    borderw: int = 2,
    bordercolor: str = "black",
) -> str:
    """
    Build FFmpeg drawtext filter string.

    Args:
        text: Text to display
        position: Position name (top_center, bottom_left, etc.)
        fontsize: Font size in pixels
        fontcolor: Font color
        borderw: Border width for outline
        bordercolor: Border color for outline

    Returns:
        FFmpeg drawtext filter string
    """
    # Position mappings
    positions = {
        "top_left": "x=20:y=20",
        "top_center": "x=(w-tw)/2:y=30",
        "top_right": "x=w-tw-20:y=20",
        "center": "x=(w-tw)/2:y=(h-th)/2",
        "bottom_left": "x=20:y=h-th-20",
        "bottom_center": "x=(w-tw)/2:y=h-th-30",
        "bottom_right": "x=w-tw-20:y=h-th-20",
    }

    pos = positions.get(position, positions["bottom_left"])

    # Escape special characters for FFmpeg
    escaped_text = escape_ffmpeg_text(text)

    return (
        f"drawtext=text='{escaped_text}':"
        f"{pos}:"
        f"fontsize={fontsize}:"
        f"fontcolor={fontcolor}:"
        f"borderw={borderw}:"
        f"bordercolor={bordercolor}"
    )


def escape_ffmpeg_text(text: str) -> str:
    """
    Escape special characters for FFmpeg drawtext filter.

    Args:
        text: Raw text

    Returns:
        Escaped text safe for FFmpeg
    """
    # Escape characters that have special meaning in FFmpeg
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    text = text.replace(":", "\\:")
    text = text.replace("%", "\\%")

    # Truncate long titles
    max_length = 50
    if len(text) > max_length:
        text = text[:max_length-3] + "..."

    return text


def get_video_with_overlay_url(
    video_url: str,
    title: str,
    app: str = "placement"
) -> Dict[str, Any]:
    """
    Synchronous helper for testing - adds overlay and returns info.

    This is used by the test script, not as a Temporal activity.
    """
    import tempfile

    brand = APP_BRANDS.get(app, "Q")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Download
        input_path = os.path.join(tmpdir, "input.mp4")
        output_path = os.path.join(tmpdir, "output.mp4")

        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Build filters
        filters = []

        # Title at top center
        if title:
            filters.append(build_text_filter(
                text=title,
                position="top_center",
                fontsize=28,
                fontcolor="white",
                borderw=3,
                bordercolor="black"
            ))

        # Brand at bottom left
        filters.append(build_text_filter(
            text=brand,
            position="bottom_left",
            fontsize=20,
            fontcolor="white",
            borderw=2,
            bordercolor="black"
        ))

        filter_string = ",".join(filters)

        # Run FFmpeg
        ffmpeg_path = os.environ.get("FFMPEG_PATH", "/tmp/ffmpeg")

        cmd = [
            ffmpeg_path,
            "-i", input_path,
            "-vf", filter_string,
            "-codec:a", "copy",
            "-y",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        return {
            "output_path": output_path,
            "title": title,
            "brand": brand,
            "filter": filter_string
        }
