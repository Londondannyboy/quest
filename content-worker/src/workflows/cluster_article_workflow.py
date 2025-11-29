"""
Cluster Article Workflow

Child workflow for creating individual articles within a cluster.
Called by CountryGuideCreationWorkflow for each content mode (Story/Guide/YOLO/Voices).

Each cluster article:
- Has its own slug (parent: country-relocation-guide, children: -guide, -yolo, -voices)
- Has its own video with mode-specific styling
- Links to other articles via cluster_id and parent_id
- Is separately indexable by search engines (SEO benefit)

Benefits of separate workflows:
- Each article has its own execution context
- Failures are isolated (one mode failing doesn't block others)
- Can be retried independently
- Clearer monitoring in Temporal UI
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import Dict, Any, Optional, List
import uuid


@workflow.defn
class ClusterArticleWorkflow:
    """
    Create a single article within a content cluster.

    Modes:
    - story: Narrative, cinematic - PARENT article (no suffix)
    - guide: Practical, methodical - slug-guide
    - yolo: Adventurous, energetic - slug-yolo
    - voices: Testimonials, intimate - slug-voices

    Timeline: 2-5 minutes per article (depends on video generation)
    """

    @workflow.run
    async def run(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute cluster article workflow.

        Args:
            input_dict: {
                "country_name": "Portugal",
                "country_code": "PT",
                "cluster_id": "uuid-string",
                "article_mode": "story",  # story, guide, yolo, voices
                "parent_id": None,  # None for story (parent), article_id for children
                "base_slug": "portugal-relocation-guide",
                "title": "Portugal Relocation Guide",
                "content": "Full markdown content...",
                "meta_description": "SEO description...",
                "excerpt": "Short excerpt...",
                "payload": {...},  # Full article payload
                "app": "relocation",
                "video_quality": "medium",
                "character_reference_url": None,  # For video consistency
                "research_context": {...},  # For voices generation
            }

        Returns:
            Dict with article_id, slug, video info, success status
        """
        country_name = input_dict["country_name"]
        country_code = input_dict["country_code"]
        cluster_id = input_dict["cluster_id"]
        article_mode = input_dict["article_mode"]
        parent_id = input_dict.get("parent_id")
        base_slug = input_dict["base_slug"]
        title = input_dict["title"]
        content = input_dict["content"]
        meta_description = input_dict.get("meta_description", "")
        excerpt = input_dict.get("excerpt", "")
        payload = input_dict.get("payload", {})
        app = input_dict.get("app", "relocation")
        video_quality = input_dict.get("video_quality", "medium")
        character_reference_url = input_dict.get("character_reference_url")
        research_context = input_dict.get("research_context", {})

        workflow.logger.info(
            f"ClusterArticleWorkflow: {article_mode.upper()} for {country_name} "
            f"(cluster: {cluster_id[:8]}...)"
        )

        # ===== PHASE 1: DETERMINE SLUG AND TITLE =====
        # Parent (story) uses base slug, children add suffix
        if article_mode == "story":
            slug = base_slug
            article_title = title
        else:
            slug = f"{base_slug}-{article_mode}"
            # Adjust title for mode
            mode_titles = {
                "guide": f"{title} - Practical Guide",
                "yolo": f"{title} - YOLO Edition",
                "voices": f"{title} - Expat Voices"
            }
            article_title = mode_titles.get(article_mode, title)

        workflow.logger.info(f"Slug: {slug}, Title: {article_title}")

        # ===== PHASE 2: PREPARE ARTICLE PAYLOAD =====
        # Add cluster metadata to payload
        article_payload = {
            **payload,
            "cluster_id": cluster_id,
            "article_mode": article_mode,
            "parent_slug": base_slug if article_mode != "story" else None,
            "content": content,
            "excerpt": excerpt,
            "meta_description": meta_description,
        }

        # For voices mode, add testimonials from research context
        if article_mode == "voices":
            voices = research_context.get("voices", [])
            article_payload["voices"] = voices
            article_payload["voice_count"] = len(voices)
            workflow.logger.info(f"Voices mode: {len(voices)} testimonials")

        # ===== PHASE 3: SAVE ARTICLE =====
        workflow.logger.info(f"Phase 3: Save {article_mode} article")

        # Determine which content_* column to populate based on article_mode
        # This ensures the frontend can detect the mode even without cluster siblings
        # Note: content_voices is JSONB for testimonials, not HTML - handled separately
        initial_content_story = content if article_mode == "story" else None
        initial_content_guide = content if article_mode == "guide" else None
        initial_content_yolo = content if article_mode == "yolo" else None
        # For voices mode, pass the voices array (JSONB), not HTML content
        initial_content_voices = research_context.get("voices", []) if article_mode == "voices" else None

        article_id = await workflow.execute_activity(
            "save_article_to_neon",
            args=[
                None,  # article_id (new)
                slug,
                article_title,
                app,
                "country_guide",  # article_type
                article_payload,  # payload
                None,  # featured_asset_url (added after video)
                None,  # hero_asset_url
                None,  # mentioned_companies
                "draft",  # status - will be published after video
                None,  # video_url
                None,  # video_playback_id
                None,  # video_asset_id
                None,  # raw_research
                None,  # video_narrative
                None,  # zep_facts
                None,  # target_keyword
                None,  # keyword_volume
                None,  # keyword_difficulty
                None,  # secondary_keywords
                initial_content_story,
                initial_content_guide,
                initial_content_yolo,
                initial_content_voices,
                cluster_id,  # cluster_id
                parent_id,  # parent_id
                article_mode  # article_mode
            ],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )

        workflow.logger.info(f"Article saved: ID {article_id}")

        # ===== PHASE 4: LINK TO COUNTRY =====
        workflow.logger.info(f"Phase 4: Link {article_mode} article to country")

        await workflow.execute_activity(
            "link_article_to_country",
            args=[str(article_id), country_code, f"country_{article_mode}"],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # ===== PHASE 5: GENERATE VIDEO =====
        video_url = None
        video_playback_id = None
        video_asset_id = None
        new_character_reference_url = None

        if video_quality:
            workflow.logger.info(f"Phase 5: Generate {article_mode} video")

            # Map article_mode to video segment for prompt generation
            # story -> hero, guide -> guide, yolo -> yolo, voices -> voices
            segment_map = {
                "story": "hero",
                "guide": "guide",
                "yolo": "yolo",
                "voices": "voices"
            }
            video_segment = segment_map.get(article_mode, "hero")

            try:
                # Execute segment video child workflow
                child_result = await workflow.execute_child_workflow(
                    "SegmentVideoWorkflow",
                    {
                        "country_name": country_name,
                        "country_code": country_code,
                        "segment": video_segment,
                        "video_quality": video_quality,
                        "article_id": article_id,
                        "four_act_content": payload.get("four_act_content") if article_mode == "story" else None,
                        "character_reference_url": character_reference_url
                    },
                    id=f"cluster-video-{country_code.lower()}-{article_mode}-{workflow.uuid4().hex[:8]}",
                    task_queue="quest-content-queue",
                    execution_timeout=timedelta(minutes=15)
                )

                if child_result.get("success"):
                    video_url = child_result.get("video_url")
                    video_playback_id = child_result.get("playback_id")
                    video_asset_id = child_result.get("asset_id")
                    workflow.logger.info(f"Video generated: {video_playback_id}")

                    # Save video tags to Neon for queryability
                    await workflow.execute_activity(
                        "save_video_tags",
                        args=[
                            str(video_playback_id) if video_playback_id else "",
                            str(video_asset_id) if video_asset_id else "",
                            cluster_id,
                            int(article_id),
                            country_name,
                            article_mode,
                            ["relocation", country_name.lower(), article_mode, "quest"]
                        ],
                        start_to_close_timeout=timedelta(seconds=30)
                    )
                    workflow.logger.info(f"Video tags saved for {article_mode}")

                    # For story mode, extract character reference for other modes
                    if article_mode == "story" and video_playback_id:
                        new_character_reference_url = f"https://image.mux.com/{video_playback_id}/thumbnail.jpg?time=1.5&width=1024"
                        workflow.logger.info(f"Character reference extracted: {new_character_reference_url[:60]}...")
                else:
                    workflow.logger.warning(f"Video generation failed: {child_result.get('error')}")

            except Exception as e:
                workflow.logger.error(f"Video workflow failed: {e}")
                # Continue without video - article is still valid

        # ===== PHASE 6: FINAL UPDATE WITH VIDEO =====
        workflow.logger.info(f"Phase 6: Final update with video")

        # GIF for featured asset
        featured_asset_url = None
        if video_playback_id:
            featured_asset_url = f"https://image.mux.com/{video_playback_id}/animated.gif?start=8&end=12&width=640&fps=12"

        # Build video narrative
        video_narrative = None
        if video_playback_id:
            video_narrative = {
                "playback_id": video_playback_id,
                "duration": 12,
                "mode": article_mode,
                "thumbnails": {
                    "hero": f"https://image.mux.com/{video_playback_id}/thumbnail.jpg?time=10.5&width=1200",
                }
            }

        # Determine which content_* column to populate based on article_mode
        # This ensures the frontend can detect the mode even without cluster siblings
        # Note: content_voices is JSONB for testimonials, not HTML - handled separately
        content_story = content if article_mode == "story" else None
        content_guide = content if article_mode == "guide" else None
        content_yolo = content if article_mode == "yolo" else None
        # For voices mode, pass the voices array (JSONB), not HTML content
        content_voices = research_context.get("voices", []) if article_mode == "voices" else None

        # Final update with video and publish
        await workflow.execute_activity(
            "save_article_to_neon",
            args=[
                article_id,
                slug,
                article_title,
                app,
                "country_guide",
                article_payload,
                featured_asset_url,
                None,  # hero_asset_url
                None,  # mentioned_companies
                "published",  # Publish the article
                video_url,
                video_playback_id,
                video_asset_id,
                None,  # raw_research
                video_narrative,
                None,  # zep_facts
                None,  # target_keyword
                None,  # keyword_volume
                None,  # keyword_difficulty
                None,  # secondary_keywords
                content_story,
                content_guide,
                content_yolo,
                content_voices,
                cluster_id,
                parent_id,
                article_mode
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(
            f"ClusterArticleWorkflow complete: {article_mode} for {country_name} "
            f"(article_id: {article_id})"
        )

        return {
            "success": True,
            "article_id": int(article_id),
            "slug": slug,
            "title": article_title,
            "article_mode": article_mode,
            "cluster_id": cluster_id,
            "parent_id": parent_id,
            "video_playback_id": video_playback_id,
            "video_url": video_url,
            "character_reference_url": new_character_reference_url,  # Only set for story mode
        }
