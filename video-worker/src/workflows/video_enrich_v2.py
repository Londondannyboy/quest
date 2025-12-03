"""
Video Enrichment V2 - FRESH CODE

Simple workflow:
1. Get hub/article from database
2. Generate video with Seedance
3. Upload to MUX with descriptive name
4. Inject video into article hero section
5. Generate MUX thumbnails for other sections
"""

from temporalio import workflow
from datetime import timedelta
from typing import Dict, Any

with workflow.unsafe.imports_passed_through():
    from src.activities.storage.neon_database import (
        get_article_by_slug,
        get_hub_by_slug,
    )
    from src.activities.generation.article_generation import (
        generate_simple_video_prompt,
    )
    from src.activities.media.simple_video_generation import (
        generate_video_simple,
    )
    from src.activities.media.mux_client import (
        upload_video_to_mux,
    )


@workflow.defn
class VideoEnrichmentV2:
    """
    Clean video enrichment workflow.

    Flow:
    1. Fetch content (article or hub)
    2. Generate simple video prompt
    3. Generate 12s video with Seedance
    4. Upload to MUX with title as name
    5. Update database with playback_id
    """

    @workflow.run
    async def run(
        self,
        slug: str,
        app: str = "relocation",
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Args:
            slug: Article/hub slug
            app: App context
            force_regenerate: Regenerate even if video exists

        Returns:
            Success result with playback_id
        """

        workflow.logger.info(f"▶️  Video enrichment V2 for: {slug}")

        # STEP 1: Get content
        workflow.logger.info("1/4: Fetching content...")
        article = await workflow.execute_activity(
            get_article_by_slug,
            slug,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not article:
            article = await workflow.execute_activity(
                get_hub_by_slug,
                slug,
                start_to_close_timeout=timedelta(seconds=30),
            )

        if not article:
            raise ValueError(f"❌ Content not found: {slug}")

        article_id = article.get("id")
        title = article.get("title", "Untitled")
        is_hub = article.get("is_hub", False)

        workflow.logger.info(f"✅ Found {'hub' if is_hub else 'article'}: {title}")

        # Check existing video
        existing = article.get("video_playback_id")
        if existing and not force_regenerate:
            workflow.logger.info(f"⏭️  Video already exists: {existing}")
            return {
                "success": True,
                "playback_id": existing,
                "skipped": True,
                "message": f"Video already exists: {existing}"
            }

        # STEP 2: Generate prompt
        workflow.logger.info("2/4: Generating video prompt...")
        prompt_result = await workflow.execute_activity(
            generate_simple_video_prompt,
            args=[article, app, "seedance"],
            start_to_close_timeout=timedelta(seconds=10),
        )

        video_prompt = prompt_result.get("prompt", "")
        workflow.logger.info(f"✅ Prompt ready: {len(video_prompt)} chars")

        # STEP 3: Generate video - FRESH ACTIVITY, NO VALIDATION!
        workflow.logger.info("3/4: Generating video with Seedance (1-3 min)...")
        video_result = await workflow.execute_activity(
            generate_video_simple,
            args=[video_prompt],
            kwargs={
                "duration": 12,
                "resolution": "720p",
                "aspect_ratio": "16:9",
            },
            start_to_close_timeout=timedelta(minutes=5),
        )

        video_url = video_result.get("video_url")
        if not video_url:
            raise ValueError("❌ Video generation failed - no URL")

        workflow.logger.info(f"✅ Video generated: {video_url[:50]}...")

        # STEP 4: Upload to MUX with proper naming
        workflow.logger.info("4/4: Uploading to MUX...")
        mux_result = await workflow.execute_activity(
            upload_video_to_mux,
            args=[video_url],
            kwargs={
                "article_id": article_id,
                "title": title,  # This names the video in MUX
                "app": app,
            },
            start_to_close_timeout=timedelta(minutes=3),
        )

        playback_id = mux_result.get("playback_id")
        if not playback_id:
            raise ValueError("❌ MUX upload failed - no playback_id")

        workflow.logger.info(f"✅ Uploaded to MUX: {playback_id}")

        # STEP 5: Update database
        workflow.logger.info("5/5: Updating database...")

        # Import here to avoid circular imports
        if is_hub:
            from src.activities.storage.neon_database import update_hub_video
            await workflow.execute_activity(
                update_hub_video,
                args=[article_id, playback_id, []],
                start_to_close_timeout=timedelta(seconds=30),
            )
        else:
            from src.activities.storage.neon_database import update_article_four_act_content
            await workflow.execute_activity(
                update_article_four_act_content,
                args=[article_id, [], video_prompt],
                start_to_close_timeout=timedelta(seconds=30),
            )

        workflow.logger.info("✅ Database updated!")

        return {
            "success": True,
            "playback_id": playback_id,
            "article_id": article_id,
            "title": title,
            "video_url": f"https://stream.mux.com/{playback_id}.m3u8",
            "thumbnail_url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.5",
            "message": f"✅ Video enrichment complete: {playback_id}"
        }
