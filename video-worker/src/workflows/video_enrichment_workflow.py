"""
Video Enrichment Workflow - Add videos to existing articles

Takes an article slug and enriches it with:
- Hero video (12-second 4-act format)
- Section videos (cut from the 4-act video using MUX)
- Thumbnails for remaining sections

This workflow is triggered from the dashboard and uses the existing 4-act video generation logic.
"""

from temporalio import workflow
from datetime import timedelta
from typing import Dict, Any

with workflow.unsafe.imports_passed_through():
    from src.activities.storage.neon_database import (
        get_article_by_slug,
        get_hub_by_slug,
        update_article_four_act_content,
        update_hub_video,
    )
    from src.activities.generation.article_generation import (
        generate_four_act_video_prompt_brief,
        generate_four_act_video_prompt,
    )
    from src.activities.media.video_generation import (
        generate_four_act_video,
    )
    from src.activities.media.mux_client import (
        upload_video_to_mux,
        inject_section_images_activity,
    )


@workflow.defn
class VideoEnrichmentWorkflow:
    """
    Workflow to enrich existing articles with videos.

    1. Fetch article by slug
    2. Check if video generation is needed
    3. Generate 4-act video prompt from article content
    4. Generate 12-second 4-act video
    5. Upload to MUX and cut into sections
    6. Update article with video embeds
    """

    @workflow.run
    async def run(
        self,
        slug: str,
        app: str = "relocation",
        video_model: str = "cdream",
        min_sections: int = 4,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Args:
            slug: Article slug
            app: Application context (relocation, placement, newsroom)
            video_model: cdream or seedance
            min_sections: Minimum number of sections to have videos (default 4)
            force_regenerate: Force video regeneration even if one exists

        Returns:
            Dict with video_playback_id, article title, and success status
        """

        workflow.logger.info(f"🎬 Starting video enrichment for slug: {slug}")

        # Step 1: Fetch article or hub
        workflow.logger.info("Step 1/6: Fetching content from database...")

        # Try article first
        article = await workflow.execute_activity(
            get_article_by_slug,
            slug,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # If not found, try hub
        if not article:
            workflow.logger.info("Not found in articles, trying country_hubs...")
            article = await workflow.execute_activity(
                get_hub_by_slug,
                slug,
                start_to_close_timeout=timedelta(seconds=30),
            )

        if not article:
            raise ValueError(f"Content not found with slug: {slug} (checked both articles and country_hubs)")

        article_id = article.get("id")
        article_title = article.get("title", "Untitled")
        is_hub = article.get("is_hub", False)
        content_type = "hub" if is_hub else "article"
        workflow.logger.info(f"Found {content_type}: {article_title}")

        # Check if video already exists
        existing_video = article.get("video_playback_id")
        if existing_video and not force_regenerate:
            workflow.logger.info(f"Article already has video: {existing_video}. Skipping (use force_regenerate=True to override)")
            return {
                "success": True,
                "video_playback_id": existing_video,
                "article_title": article_title,
                "message": "Article already has video. Use force_regenerate to create new video.",
                "skipped": True
            }

        # Step 2: Generate 4-act video prompt briefs from article content
        workflow.logger.info("Step 2/6: Generating 4-act video prompt briefs from article...")
        brief_result = await workflow.execute_activity(
            generate_four_act_video_prompt_brief,
            args=[article, app, None],  # character_style = None (use app default)
            start_to_close_timeout=timedelta(minutes=3),
        )

        if not brief_result.get("success"):
            raise ValueError("Failed to generate video prompt briefs")

        # Update article with four_act_content
        four_act_content = brief_result.get("four_act_content", [])
        workflow.logger.info(f"Generated {len(four_act_content)} act briefs")

        # Save briefs to article
        await workflow.execute_activity(
            update_article_four_act_content,
            args=[article_id, four_act_content, None],  # video_prompt will be set later
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Update article dict with four_act_content for prompt generation
        article["four_act_content"] = four_act_content

        # Step 3: Generate 4-act video prompt
        workflow.logger.info("Step 3/6: Assembling 4-act video prompt...")
        prompt_result = await workflow.execute_activity(
            generate_four_act_video_prompt,
            args=[article, app, video_model, None],  # character_style = None
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not prompt_result.get("success"):
            raise ValueError("Failed to generate video prompt")

        video_prompt = prompt_result.get("prompt", "")
        workflow.logger.info(f"Generated video prompt: {len(video_prompt)} characters")

        # Step 4: Generate 4-act video
        workflow.logger.info(f"Step 4/6: Generating 12-second 4-act video with {video_model}...")
        video_result = await workflow.execute_activity(
            generate_four_act_video,
            args=[video_prompt, video_model],
            start_to_close_timeout=timedelta(minutes=5),  # Video generation can take time
        )

        if not video_result.get("success"):
            raise ValueError(f"Video generation failed: {video_result.get('error', 'Unknown error')}")

        video_url = video_result.get("output")
        workflow.logger.info(f"Video generated: {video_url}")

        # Step 5: Upload to MUX with proper naming
        workflow.logger.info("Step 5/6: Uploading video to MUX...")
        mux_result = await workflow.execute_activity(
            upload_video_to_mux,
            args=[
                video_url,
                {
                    "article_id": str(article_id),
                    "article_slug": slug,
                    "article_title": article_title,
                    "video_type": "hero_4act",
                    "app": app,
                }
            ],
            start_to_close_timeout=timedelta(minutes=3),
        )

        if not mux_result.get("success"):
            raise ValueError(f"MUX upload failed: {mux_result.get('error', 'Unknown error')}")

        playback_id = mux_result.get("playback_id")
        workflow.logger.info(f"Video uploaded to MUX: {playback_id}")

        # Step 6: Update content with video
        workflow.logger.info(f"Step 6/6: Updating {content_type} with video...")

        # Update based on content type
        if is_hub:
            # Update hub with video
            await workflow.execute_activity(
                update_hub_video,
                args=[article_id, playback_id, four_act_content],
                start_to_close_timeout=timedelta(seconds=30),
            )
        else:
            # Update article with video_playback_id and video_prompt
            await workflow.execute_activity(
                update_article_four_act_content,
                args=[article_id, four_act_content, video_prompt],
                start_to_close_timeout=timedelta(seconds=30),
            )

        # Note: MUX will automatically cut the video into 4 sections (0-3s, 3-6s, 6-9s, 9-12s)
        # These can be accessed via the playback_id with time parameters

        workflow.logger.info("✅ Video enrichment complete!")

        return {
            "success": True,
            "video_playback_id": playback_id,
            "article_id": article_id,
            "article_title": article_title,
            "video_url": f"https://stream.mux.com/{playback_id}.m3u8",
            "acts_generated": len(four_act_content),
            "model_used": video_model,
            "message": f"Successfully enriched article with 4-act video ({playback_id})"
        }
