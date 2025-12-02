"""
Mux client activity for video upload and URL generation.
"""

import os
import time
import tempfile
import requests
import mux_python
from temporalio import activity
from typing import Dict, Any, Optional


def get_mux_client():
    """Get configured Mux API client."""
    configuration = mux_python.Configuration()
    configuration.username = os.environ.get("MUX_TOKEN_ID")
    configuration.password = os.environ.get("MUX_TOKEN_SECRET")

    if not configuration.username or not configuration.password:
        raise ValueError("MUX_TOKEN_ID and MUX_TOKEN_SECRET must be set")

    return mux_python.ApiClient(configuration)


@activity.defn
async def upload_video_to_mux(
    video_url: str,
    public: bool = True,
    # Passthrough metadata for tagging
    cluster_id: Optional[str] = None,
    article_id: Optional[int] = None,
    country: Optional[str] = None,
    article_mode: Optional[str] = None,
    tags: Optional[list] = None,
    # Human-readable identifiers
    title: Optional[str] = None,
    app: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a video to Mux from a URL with optional passthrough metadata.

    Args:
        video_url: URL of the video file to upload
        public: Whether the video should be publicly accessible
        cluster_id: UUID grouping related videos (for cluster architecture)
        article_id: Associated article ID
        country: Country name for the video
        article_mode: Content mode (story, guide, yolo, voices)
        tags: List of tags for categorization
        title: Human-readable title for the video (shown in Mux dashboard)
        app: Application name (e.g., 'relocation', 'quest')

    Returns:
        Dict with asset_id, playback_id, duration, and all generated URLs
    """
    activity.logger.info(f"Uploading video to Mux: {video_url[:50]}...")

    client = get_mux_client()
    assets_api = mux_python.AssetsApi(client)

    # Create asset from URL
    playback_policy = [mux_python.PlaybackPolicy.PUBLIC] if public else [mux_python.PlaybackPolicy.SIGNED]

    # Build human-readable passthrough string for Mux dashboard
    # Format: "Title | Mode | Country | App | cluster:xxx"
    passthrough_parts = []

    # Start with title if available (most visible in Mux dashboard)
    if title:
        # Truncate title to leave room for other metadata
        passthrough_parts.append(title[:80])

    # Add mode and country for quick identification
    if article_mode:
        passthrough_parts.append(article_mode.upper())
    if country:
        passthrough_parts.append(country[:20])
    if app:
        passthrough_parts.append(f"app:{app}")
    if cluster_id:
        passthrough_parts.append(f"cluster:{cluster_id[:8]}")
    if article_id:
        passthrough_parts.append(f"id:{article_id}")

    passthrough = " | ".join(passthrough_parts)[:255] if passthrough_parts else None

    if passthrough:
        activity.logger.info(f"Mux video label: {passthrough}")

    create_asset_request = mux_python.CreateAssetRequest(
        input=[mux_python.InputSettings(url=video_url)],
        playback_policy=playback_policy,
        passthrough=passthrough,
    )

    asset = assets_api.create_asset(create_asset_request)
    asset_id = asset.data.id

    activity.logger.info(f"Asset created: {asset_id}, waiting for processing...")

    # Wait for asset to be ready
    max_attempts = 60  # 2 minutes max
    for attempt in range(max_attempts):
        asset_status = assets_api.get_asset(asset_id)

        if asset_status.data.status == "ready":
            playback_id = asset_status.data.playback_ids[0].id
            duration = asset_status.data.duration

            activity.logger.info(f"Asset ready! Playback ID: {playback_id}")

            # Generate all URLs
            urls = generate_mux_urls(playback_id, duration)

            return {
                "asset_id": asset_id,
                "playback_id": playback_id,
                "duration": duration,
                "status": "ready",
                "passthrough": passthrough,
                **urls
            }
        elif asset_status.data.status == "errored":
            errors = asset_status.data.errors
            raise RuntimeError(f"Mux asset processing failed: {errors}")

        activity.heartbeat()
        time.sleep(2)

    raise TimeoutError(f"Mux asset processing timed out after {max_attempts * 2} seconds")


@activity.defn
async def upload_video_file_to_mux(
    video_path: str,
    public: bool = True
) -> Dict[str, Any]:
    """
    Upload a local video file to Mux using direct upload.

    Args:
        video_path: Local path to video file
        public: Whether the video should be publicly accessible

    Returns:
        Dict with asset_id, playback_id, duration, and all generated URLs
    """
    activity.logger.info(f"Uploading local file to Mux: {video_path}")

    client = get_mux_client()
    uploads_api = mux_python.DirectUploadsApi(client)
    assets_api = mux_python.AssetsApi(client)

    # Create direct upload
    playback_policy = [mux_python.PlaybackPolicy.PUBLIC] if public else [mux_python.PlaybackPolicy.SIGNED]

    create_upload_request = mux_python.CreateUploadRequest(
        new_asset_settings=mux_python.CreateAssetRequest(
            playback_policy=playback_policy,
        ),
        cors_origin="*"
    )

    upload = uploads_api.create_direct_upload(create_upload_request)
    upload_url = upload.data.url
    upload_id = upload.data.id

    # Upload file
    with open(video_path, 'rb') as f:
        response = requests.put(
            upload_url,
            data=f,
            headers={'Content-Type': 'video/mp4'}
        )
        response.raise_for_status()

    activity.logger.info("File uploaded, waiting for processing...")

    # Wait for asset to be ready
    max_attempts = 60
    for attempt in range(max_attempts):
        upload_status = uploads_api.get_direct_upload(upload_id)

        if upload_status.data.asset_id:
            asset_id = upload_status.data.asset_id
            asset = assets_api.get_asset(asset_id)

            if asset.data.status == "ready":
                playback_id = asset.data.playback_ids[0].id
                duration = asset.data.duration

                urls = generate_mux_urls(playback_id, duration)

                return {
                    "asset_id": asset_id,
                    "playback_id": playback_id,
                    "duration": duration,
                    "status": "ready",
                    **urls
                }
            elif asset.data.status == "errored":
                raise RuntimeError(f"Mux processing failed: {asset.data.errors}")

        activity.heartbeat()
        time.sleep(2)

    raise TimeoutError("Mux processing timed out")


def generate_mux_urls(playback_id: str, duration: float = 3.0) -> Dict[str, str]:
    """
    Generate all useful Mux URLs from a playback ID.

    Args:
        playback_id: Mux playback ID
        duration: Video duration in seconds

    Returns:
        Dict with stream, gif, thumbnail URLs
    """
    image_base = f"https://image.mux.com/{playback_id}"
    stream_base = f"https://stream.mux.com/{playback_id}"

    # Calculate GIF end time (use full duration up to 5s)
    gif_end = min(duration, 5.0)

    return {
        # Streaming URL (HLS)
        "stream_url": f"{stream_base}.m3u8",

        # Animated previews
        "gif_url": f"{image_base}/animated.gif?start=0&end={gif_end:.1f}&width=480&fps=15",
        "gif_webp_url": f"{image_base}/animated.webp?start=0&end={gif_end:.1f}&width=480&fps=15",

        # Thumbnails at different times
        "thumbnail_url": f"{image_base}/thumbnail.jpg?time=0&width=640",
        "thumbnail_start": f"{image_base}/thumbnail.jpg?time=0&width=640",
        "thumbnail_middle": f"{image_base}/thumbnail.jpg?time={duration/2:.1f}&width=640",
        "thumbnail_end": f"{image_base}/thumbnail.jpg?time={duration-0.5:.1f}&width=640",

        # High-res versions for article hero
        "thumbnail_hero": f"{image_base}/thumbnail.jpg?time={duration/2:.1f}&width=1920&height=1080&fit_mode=smartcrop",

        # Featured image (1200x630 for social sharing)
        "thumbnail_featured": f"{image_base}/thumbnail.jpg?time={duration/2:.1f}&width=1200&height=630&fit_mode=smartcrop",
    }


@activity.defn
async def delete_mux_asset(asset_id: str) -> bool:
    """
    Delete a Mux asset.

    Args:
        asset_id: Mux asset ID to delete

    Returns:
        True if deleted successfully
    """
    activity.logger.info(f"Deleting Mux asset: {asset_id}")

    client = get_mux_client()
    assets_api = mux_python.AssetsApi(client)

    try:
        assets_api.delete_asset(asset_id)
        activity.logger.info(f"Asset {asset_id} deleted")
        return True
    except mux_python.rest.ApiException as e:
        activity.logger.error(f"Failed to delete asset: {e}")
        return False


@activity.defn
async def get_mux_asset_info(asset_id: str) -> Dict[str, Any]:
    """
    Get information about a Mux asset.

    Args:
        asset_id: Mux asset ID

    Returns:
        Dict with asset information
    """
    client = get_mux_client()
    assets_api = mux_python.AssetsApi(client)

    asset = assets_api.get_asset(asset_id)

    return {
        "asset_id": asset.data.id,
        "status": asset.data.status,
        "duration": asset.data.duration,
        "playback_ids": [p.id for p in asset.data.playback_ids] if asset.data.playback_ids else [],
        "created_at": str(asset.data.created_at) if asset.data.created_at else None,
    }


@activity.defn(name="inject_section_images")
async def inject_section_images_activity(
    content: str,
    video_playback_id: Optional[str],
    image_width: int = 800,
    max_sections: Optional[int] = None,
    four_act_content: Optional[list] = None
) -> str:
    """
    Inject Mux thumbnail images into article content at section breaks.

    This activity wraps the inject_section_images utility function to make it
    safe for use from Temporal workflows (avoids sandbox restrictions).

    Args:
        content: HTML content to process
        video_playback_id: Mux video playback ID for thumbnails
        image_width: Width of thumbnail images
        max_sections: Maximum number of sections to add images to (None = unlimited)
        four_act_content: Video act descriptions for AI matching (optional)

    Returns:
        HTML content with injected images
    """
    activity.logger.info(f"Injecting section images for video {video_playback_id}")

    # Import here (inside activity) to avoid Temporal workflow sandbox restrictions
    from src.utils.inject_section_images import inject_section_images

    result = inject_section_images(
        content,
        video_playback_id,
        image_width=image_width,
        max_sections=max_sections,
        four_act_content=four_act_content
    )

    activity.logger.info("Section images injected successfully")
    return result
