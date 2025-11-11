"""
Insert Images Activity

Embeds generated images into article content at strategic points.
"""

import re
from temporalio import activity
from typing import Dict


@activity.defn(name="insert_images_into_content")
async def insert_images_into_content(
    content: str,
    images: Dict[str, str]
) -> str:
    """
    Insert content images into article markdown at strategic points

    Rules:
    - Only insert content images (content, content2, content3, content4)
    - NO hero, featured images
    - Insert after long sentences or two short sentences
    - Add two line breaks before and after each image for clear spacing

    Args:
        content: Original article markdown content
        images: Dict with image URLs (hero, featured, content, content2, content3, content4)

    Returns:
        Updated content with embedded images
    """
    activity.logger.info("📸 Inserting images into article content")

    # Get only content images (skip hero and featured)
    content_images = []
    for key in ['content', 'content2', 'content3', 'content4']:
        if images.get(key):
            content_images.append(images[key])

    if not content_images:
        activity.logger.warning("⚠️  No content images to insert")
        return content

    activity.logger.info(f"   Found {len(content_images)} content images to insert")

    # Split content into sections (by ## headers)
    sections = re.split(r'(^##\s+.*$)', content, flags=re.MULTILINE)

    # Sections will be: [intro, header1, section1_content, header2, section2_content, ...]
    # We want to insert images into the section content, not headers

    updated_sections = []
    image_index = 0

    for i, section in enumerate(sections):
        updated_sections.append(section)

        # Only process content sections (not headers or intro)
        if i > 0 and not section.strip().startswith('##'):
            # Insert image if we have more images and this is a substantial section
            if image_index < len(content_images) and len(section.strip()) > 300:
                # Find a good insertion point: after 1-2 sentences
                # Split by sentence endings
                sentences = re.split(r'([.!?]\s+)', section)

                # Try to insert after 2-3 sentences (around 1/3 into the section)
                insert_point = min(4, len(sentences) // 2)

                if insert_point < len(sentences):
                    # Reconstruct section with image inserted
                    before = ''.join(sentences[:insert_point])
                    after = ''.join(sentences[insert_point:])

                    # Create image markdown with proper spacing
                    image_url = content_images[image_index]
                    image_markdown = f"\n\n![Chief of Staff content image]({image_url})\n\n"

                    updated_sections[-1] = before + image_markdown + after
                    image_index += 1
                    activity.logger.info(f"   ✅ Inserted image {image_index} into section")

    # Rejoin all sections
    updated_content = ''.join(updated_sections)

    activity.logger.info(f"✅ Inserted {image_index} images into content")
    return updated_content
