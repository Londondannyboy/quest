"""
Segment Video Workflow

Child workflow for generating individual segment videos.
Called by CountryGuideCreationWorkflow for each video segment.

Benefits of separate workflows:
- Each video has its own execution context
- Failures are isolated (one video failing doesn't block others)
- Can be retried independently
- Clearer monitoring in Temporal UI
- Each video gets its own optimized prompt
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import Dict, Any


@workflow.defn
class SegmentVideoWorkflow:
    """
    Generate a single segment video for a country guide.

    Segments: hero, family, finance, daily, yolo
    Each segment has its own optimized 4-act prompt template.

    Timeline: 3-5 minutes per video
    Cost: ~$0.30 (Seedance) per video
    """

    @workflow.run
    async def run(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute segment video workflow.

        Args:
            input_dict: {
                "country_name": "Portugal",
                "country_code": "PT",
                "segment": "hero",  # hero, family, finance, daily, yolo
                "video_quality": "low",
                "article_id": "uuid",  # For linking
                "four_act_content": [...],  # Optional, for hero video customization
            }

        Returns:
            Dict with video_url, playback_id, asset_id, segment_video object
        """
        country_name = input_dict["country_name"]
        country_code = input_dict["country_code"]
        segment = input_dict["segment"]
        video_quality = input_dict.get("video_quality", "low")
        article_id = input_dict.get("article_id")
        four_act_content = input_dict.get("four_act_content")

        workflow.logger.info(f"SegmentVideoWorkflow: {segment.upper()} video for {country_name}")

        # ===== PHASE 1: GENERATE VIDEO PROMPT =====
        workflow.logger.info(f"Phase 1: Generate {segment} video prompt")

        prompt_result = await workflow.execute_activity(
            "generate_segment_video_prompt",
            args=[
                country_name,
                segment,
                four_act_content if segment == "hero" else None
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        video_prompt = prompt_result.get("video_prompt", "")
        segment_title = prompt_result.get("title", f"{segment.title()} Video")
        cluster = prompt_result.get("cluster", "story")

        workflow.logger.info(f"Prompt generated: {len(video_prompt)} chars")
        workflow.logger.info(f"Prompt preview: {video_prompt[:150]}...")

        # ===== PHASE 2: GENERATE VIDEO =====
        # For non-hero videos, use character reference image from hero video
        # This helps maintain visual consistency (same character throughout)
        character_reference_url = input_dict.get("character_reference_url")

        if character_reference_url and segment != "hero":
            workflow.logger.info(f"Phase 2: Generate {segment} video via Seedance (with character reference)")
            workflow.logger.info(f"Character reference: {character_reference_url[:60]}...")
        else:
            workflow.logger.info(f"Phase 2: Generate {segment} video via Seedance")

        video_result = await workflow.execute_activity(
            "generate_four_act_video",
            args=[
                segment_title,              # title
                "",                         # content (not needed, prompt is complete)
                "relocation",               # app
                video_quality,              # quality
                12,                         # duration (4-act = 12s)
                "16:9",                     # aspect_ratio
                "seedance",                 # video_model
                video_prompt,               # video_prompt
                character_reference_url     # reference_image (for character consistency)
            ],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )

        raw_video_url = video_result.get("video_url")

        if not raw_video_url:
            workflow.logger.error(f"{segment.upper()} video generation failed")
            return {
                "success": False,
                "segment": segment,
                "error": "Video generation returned no URL",
                "video_result": video_result
            }

        workflow.logger.info(f"Video generated: {raw_video_url[:60]}...")

        # ===== PHASE 3: UPLOAD TO MUX =====
        workflow.logger.info(f"Phase 3: Upload {segment} video to Mux")

        mux_result = await workflow.execute_activity(
            "upload_video_to_mux",
            args=[raw_video_url],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )

        playback_id = mux_result.get("playback_id")
        asset_id = mux_result.get("asset_id")
        stream_url = mux_result.get("playback_url")

        if not playback_id:
            workflow.logger.error(f"Mux upload failed for {segment}")
            return {
                "success": False,
                "segment": segment,
                "error": "Mux upload failed",
                "raw_video_url": raw_video_url
            }

        workflow.logger.info(f"Uploaded to Mux: {playback_id}")

        # ===== BUILD SEGMENT VIDEO OBJECT =====
        # Position is set by parent workflow based on segment order
        position_map = {"hero": 1, "family": 2, "finance": 3, "daily": 4, "yolo": 5}

        segment_video = {
            "id": segment,
            "title": segment_title,
            "video_url": stream_url,
            "playback_id": playback_id,
            "asset_id": asset_id,
            "position": position_map.get(segment, 1),
            "cluster": cluster,
            "thumbnail_hero": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time=10.5&width=1200",
            "animated_gif": f"https://image.mux.com/{playback_id}/animated.gif?start=8&end=12&width=640&fps=12",
            "thumbnails": [
                {
                    "act": act_num + 1,
                    "time": act_num * 3 + 1.5,
                    "url": f"https://image.mux.com/{playback_id}/thumbnail.jpg?time={act_num * 3 + 1.5}&width=800"
                }
                for act_num in range(4)
            ]
        }

        workflow.logger.info(f"SegmentVideoWorkflow complete: {segment} for {country_name}")

        return {
            "success": True,
            "segment": segment,
            "country_code": country_code,
            "article_id": article_id,
            "video_url": stream_url,
            "playback_id": playback_id,
            "asset_id": asset_id,
            "segment_video": segment_video,
            "cost": video_result.get("cost", 0.30)
        }
