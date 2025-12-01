"""
Topic Cluster Article Workflow

Child workflow for creating SEO-targeted topic cluster articles.
Called by CountryGuideCreationWorkflow for each high-value keyword discovered.

Each topic cluster article:
- Targets a specific keyword (e.g., "slovakia cost of living")
- Has its own slug (e.g., /slovakia-cost-of-living)
- REUSES parent video (no new video generation - cost efficient)
- Links to parent guide article
- Is separately indexable by search engines

Examples:
- /slovakia-cost-of-living (targeting "slovakia cost of living" - 70 vol)
- /slovakia-visa-requirements (targeting "slovakia visa requirements" - 40 vol)
- /slovakia-golden-visa (targeting "slovakia golden visa" - 10 vol)

Video Strategy:
- Uses parent's video_playback_id for thumbnails
- Extracts alt_text from parent's four_act_content visual hints
- No new video generation (saves $1-2 per article)
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import Dict, Any, Optional, List
from slugify import slugify


@workflow.defn
class TopicClusterWorkflow:
    """
    Create a topic-specific cluster article targeting a high-value keyword.

    Unlike mode-based articles (Story/Guide/YOLO/Voices), these target
    SPECIFIC keywords discovered through SEO research.

    Timeline: 2-5 minutes per article
    """

    @workflow.run
    async def run(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute topic cluster workflow.

        Args:
            input_dict: {
                "country_name": "Slovakia",
                "country_code": "SK",
                "cluster_id": "uuid-string",
                "parent_id": 106,  # Parent guide article ID
                "parent_slug": "slovakia-relocation-guide",
                "parent_playback_id": "V2XIwkq...",  # Reuse parent video
                "parent_four_act_content": [...],  # For alt text
                "target_keyword": "slovakia cost of living",
                "keyword_volume": 70,
                "keyword_difficulty": 35.5,
                "keyword_cpc": 0.0,
                "planning_type": "housing",  # visa, tax, housing, etc.
                "research_context": {...},  # Shared research from parent
                "app": "relocation",
            }

        Returns:
            Dict with article_id, slug, video info, success status
        """
        country_name = input_dict["country_name"]
        country_code = input_dict["country_code"]
        cluster_id = input_dict["cluster_id"]
        parent_id = input_dict["parent_id"]
        parent_slug = input_dict["parent_slug"]
        target_keyword = input_dict["target_keyword"]
        keyword_volume = input_dict.get("keyword_volume", 0)
        keyword_difficulty = input_dict.get("keyword_difficulty")
        keyword_cpc = input_dict.get("keyword_cpc", 0)
        planning_type = input_dict.get("planning_type", "general")
        research_context = input_dict.get("research_context", {})
        app = input_dict.get("app", "relocation")

        # Parent video data - reuse instead of generating new
        parent_playback_id = input_dict.get("parent_playback_id")
        parent_four_act_content = input_dict.get("parent_four_act_content", [])

        workflow.logger.info(
            f"TopicClusterWorkflow: '{target_keyword}' for {country_name} "
            f"(vol={keyword_volume}, cluster={cluster_id[:8]}...)"
        )

        # ===== PHASE 1: GENERATE SLUG AND TITLE =====
        # Create SEO-optimized slug from keyword
        slug = slugify(target_keyword)

        # Build compelling title
        title_templates = {
            "housing": f"{country_name} Cost of Living 2025: Complete Expat Guide",
            "visa": f"{country_name} Visa Requirements 2025: Step-by-Step Guide",
            "tax": f"{country_name} Tax Guide 2025: What Expats Need to Know",
            "retirement": f"Retiring in {country_name} 2025: Complete Guide",
            "general": f"{target_keyword.title()} - Complete Guide 2025",
        }
        title = title_templates.get(planning_type, title_templates["general"])

        # If keyword contains specific terms, use those
        if "golden visa" in target_keyword.lower():
            title = f"{country_name} Golden Visa 2025: Requirements, Costs & Process"
        elif "work permit" in target_keyword.lower():
            title = f"{country_name} Work Permit 2025: How to Apply & Requirements"
        elif "residence permit" in target_keyword.lower():
            title = f"{country_name} Residence Permit 2025: Complete Application Guide"

        workflow.logger.info(f"Topic: {target_keyword} -> Slug: {slug}, Title: {title}")

        # ===== PHASE 2: GENERATE TOPIC-SPECIFIC CONTENT =====
        workflow.logger.info(f"Phase 2: Generate content for '{target_keyword}'")

        content_result = await workflow.execute_activity(
            "generate_topic_cluster_content",
            args=[
                country_name,
                country_code,
                target_keyword,
                keyword_volume,
                planning_type,
                research_context,
                parent_slug
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )

        content = content_result.get("content", "")
        excerpt = content_result.get("excerpt", "")
        meta_description = content_result.get("meta_description", "")
        faq = content_result.get("faq", [])
        word_count = content_result.get("word_count", 0)

        workflow.logger.info(f"Generated {word_count} words for '{target_keyword}'")

        # Inject section images if parent video exists
        if parent_playback_id and content:
            workflow.logger.info("Injecting section images with AI matching into topic cluster...")
            from src.utils.inject_section_images import inject_section_images

            content = inject_section_images(
                content,
                parent_playback_id,  # Reuse parent video for thumbnails
                image_width=1200,
                max_sections=None,  # Unlimited - inject for ALL H2 sections
                four_act_content=parent_four_act_content  # For semantic matching
            )
            workflow.logger.info("Section images injected successfully")

        # Build payload
        payload = {
            "title": title,
            "slug": slug,
            "content": content,
            "excerpt": excerpt,
            "meta_description": meta_description,
            "faq": faq,
            "word_count": word_count,
            "target_keyword": target_keyword,
            "keyword_volume": keyword_volume,
            "keyword_difficulty": keyword_difficulty,
            "keyword_cpc": keyword_cpc,
            "planning_type": planning_type,
            "parent_slug": parent_slug,
            "cluster_id": cluster_id,
            "article_mode": "topic",  # Distinct from story/guide/yolo/voices
            "article_type": "topic_cluster",
        }

        # ===== PHASE 3: SAVE ARTICLE =====
        workflow.logger.info(f"Phase 3: Save topic cluster article")

        article_id = await workflow.execute_activity(
            "save_article_to_neon",
            args=[
                None,  # article_id (new)
                slug,
                title,
                app,
                "topic_cluster",  # article_type
                payload,  # payload
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
                target_keyword,  # target_keyword - KEY!
                keyword_volume,  # keyword_volume - KEY!
                keyword_difficulty,  # keyword_difficulty - KEY!
                None,  # secondary_keywords
                None,  # content_story
                None,  # content_guide
                None,  # content_yolo
                None,  # content_voices
                cluster_id,  # cluster_id
                parent_id,  # parent_id
                "topic"  # article_mode
            ],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )

        workflow.logger.info(f"Topic cluster article saved: ID {article_id}")

        # ===== PHASE 4: LINK TO COUNTRY =====
        workflow.logger.info(f"Phase 4: Link topic cluster to country")

        await workflow.execute_activity(
            "link_article_to_country",
            args=[str(article_id), country_code, f"topic_{planning_type}"],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # ===== PHASE 5: REUSE PARENT VIDEO (No new generation) =====
        workflow.logger.info(f"Phase 5: Reuse parent video {parent_playback_id}")

        video_playback_id = parent_playback_id
        video_asset_id = None  # We only have playback_id from parent
        video_url = None

        # Build alt_text from parent's four_act_content visual hints
        alt_text = None
        if parent_four_act_content and isinstance(parent_four_act_content, list):
            visual_hints = []
            for act in parent_four_act_content:
                if isinstance(act, dict):
                    hint = act.get("four_act_visual_hint", "")
                    if hint:
                        # Take first sentence of each visual hint
                        first_sentence = hint.split('.')[0] if '.' in hint else hint
                        visual_hints.append(first_sentence[:100])
            if visual_hints:
                alt_text = f"Video for {target_keyword}: " + ". ".join(visual_hints[:2])

        workflow.logger.info(f"Reusing parent video: {video_playback_id}, alt_text: {alt_text[:50] if alt_text else 'None'}...")

        # ===== PHASE 6: FINAL UPDATE WITH VIDEO =====
        workflow.logger.info(f"Phase 6: Final update with parent video")

        featured_asset_url = None
        if video_playback_id:
            featured_asset_url = f"https://image.mux.com/{video_playback_id}/animated.gif?start=8&end=12&width=640&fps=12"

        video_narrative = None
        if video_playback_id:
            video_narrative = {
                "playback_id": video_playback_id,
                "duration": 12,
                "mode": "topic",
                "planning_type": planning_type,
                "reused_from_parent": True,
                "alt_text": alt_text,
            }

        # Final update
        await workflow.execute_activity(
            "save_article_to_neon",
            args=[
                article_id,
                slug,
                title,
                app,
                "topic_cluster",
                payload,
                featured_asset_url,
                None,  # hero_asset_url
                None,  # mentioned_companies
                "published",  # Publish
                video_url,
                video_playback_id,
                video_asset_id,
                None,  # raw_research
                video_narrative,
                None,  # zep_facts
                target_keyword,
                keyword_volume,
                keyword_difficulty,
                None,  # secondary_keywords
                None,  # content_story
                None,  # content_guide
                None,  # content_yolo
                None,  # content_voices
                cluster_id,
                parent_id,
                "topic"
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(
            f"TopicClusterWorkflow complete: '{target_keyword}' "
            f"(article_id: {article_id}, slug: {slug})"
        )

        return {
            "success": True,
            "article_id": int(article_id),
            "slug": slug,
            "title": title,
            "target_keyword": target_keyword,
            "keyword_volume": keyword_volume,
            "planning_type": planning_type,
            "cluster_id": cluster_id,
            "parent_id": parent_id,
            "video_playback_id": video_playback_id,
        }
