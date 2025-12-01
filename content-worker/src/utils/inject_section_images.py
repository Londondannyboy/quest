"""
Inject Mux video thumbnails into article content at section breaks.

This utility:
1. Splits HTML content by H2 sections
2. Injects an <img> tag after each H2 using Mux thumbnail URLs
3. Returns the modified HTML with visual breaks

Usage in workflow:
    content_with_images = inject_section_images(content, video_playback_id)
"""

import re
from typing import Optional, List, Tuple


# Generate diverse time points across 12-second video for unlimited sections
# Instead of being limited to 4 acts, we can use any time point
def get_video_time_points(num_sections: int, video_duration: float = 12.0) -> list:
    """
    Generate evenly distributed time points across the video duration.

    For unlimited sections, we interpolate time points across the full video.
    Examples:
    - 4 sections: 1.5s, 4.5s, 7.5s, 10.5s (original 4-act midpoints)
    - 8 sections: 1.0s, 2.5s, 4.0s, 5.5s, 7.0s, 8.5s, 10.0s, 11.5s
    - 12 sections: 0.75s, 1.75s, 2.75s, ... 11.25s
    """
    if num_sections <= 0:
        return []

    # Distribute evenly across video with small margin at start/end
    margin = 0.5  # Don't use very first/last frames
    usable_duration = video_duration - (2 * margin)
    step = usable_duration / num_sections

    return [margin + (step * i) + (step / 2) for i in range(num_sections)]


# Legacy constant for backward compatibility
ACT_TIMESTAMPS = [
    {"start": 0, "end": 3, "mid": 1.5},   # Act 1
    {"start": 3, "end": 6, "mid": 4.5},   # Act 2
    {"start": 6, "end": 9, "mid": 7.5},   # Act 3
    {"start": 9, "end": 12, "mid": 10.5}, # Act 4
]


def get_mux_thumbnail_url(playback_id: str, time: float, width: int = 800) -> str:
    """Generate a Mux thumbnail URL for a specific time."""
    return f"https://image.mux.com/{playback_id}/thumbnail.jpg?time={time}&width={width}"


def split_content_by_h2(html: str) -> List[Tuple[str, str]]:
    """
    Split HTML content by H2 headers.

    Returns list of tuples: (h2_tag, content_after_h2)
    First element may be (None, preamble_content) if content starts before first H2.
    """
    # Pattern to match H2 tags (with any attributes)
    h2_pattern = r'(<h2[^>]*>.*?</h2>)'

    parts = re.split(h2_pattern, html, flags=re.IGNORECASE | re.DOTALL)

    sections = []
    i = 0

    # Handle preamble (content before first H2)
    if parts and not re.match(r'<h2', parts[0], re.IGNORECASE):
        preamble = parts[0].strip()
        if preamble:
            sections.append((None, preamble))
        i = 1

    # Process H2 + content pairs
    while i < len(parts):
        h2_tag = parts[i] if i < len(parts) else None
        content = parts[i + 1] if i + 1 < len(parts) else ""

        if h2_tag:
            sections.append((h2_tag, content.strip()))

        i += 2

    return sections


def inject_section_images(
    content: str,
    video_playback_id: Optional[str],
    image_width: int = 800,
    add_caption: bool = False,
    max_sections: int = None  # None = unlimited (inject for ALL H2 sections)
) -> str:
    """
    Inject Mux thumbnail images after each H2 section header.

    Uses video thumbnails from evenly distributed time points across the 12-second video.
    Supports unlimited sections by interpolating time points.

    Args:
        content: HTML content to process
        video_playback_id: Mux video playback ID for thumbnails
        image_width: Width of thumbnail images
        add_caption: Whether to add a caption under images
        max_sections: Maximum number of sections to add images to (None = unlimited)

    Returns:
        HTML content with injected images
    """
    if not video_playback_id or not content:
        return content

    sections = split_content_by_h2(content)

    if not sections:
        return content

    # Count H2 sections (exclude preamble)
    h2_count = sum(1 for h2_tag, _ in sections if h2_tag is not None)

    if h2_count == 0:
        return content

    # Determine how many images to inject
    num_images = h2_count if max_sections is None else min(h2_count, max_sections)

    # Generate time points for all sections
    time_points = get_video_time_points(num_images, video_duration=12.0)

    result_parts = []
    section_index = 0

    for h2_tag, section_content in sections:
        if h2_tag is None:
            # Preamble - no image
            result_parts.append(section_content)
            continue

        # Add H2 tag
        result_parts.append(h2_tag)

        # Add image after H2 if we have a time point for this section
        if section_index < len(time_points):
            time = time_points[section_index]
            img_url = get_mux_thumbnail_url(video_playback_id, time, image_width)

            # Image with styling - rounded corners, full width, subtle shadow
            img_html = f'''
<figure class="section-image my-6">
  <img
    src="{img_url}"
    alt="Section visual"
    class="w-full aspect-[21/9] object-cover rounded-xl shadow-md"
    loading="lazy"
  />
</figure>
'''
            result_parts.append(img_html)

        # Add section content
        result_parts.append(section_content)
        section_index += 1

    return "\n".join(result_parts)


def inject_images_for_article(
    article: dict,
    content_field: str = "content"
) -> str:
    """
    Helper to inject images into an article dict.

    Args:
        article: Article dict with content and video_playback_id
        content_field: Which content field to process (content, content_story, etc.)

    Returns:
        Modified content with images
    """
    content = article.get(content_field, "")
    playback_id = article.get("video_playback_id")

    if not playback_id:
        return content

    return inject_section_images(content, playback_id)


# Test
if __name__ == "__main__":
    test_content = """
<p>Intro paragraph here.</p>

<h2>First Section</h2>
<p>Content for first section...</p>

<h2>Second Section</h2>
<p>Content for second section...</p>

<h2>Third Section</h2>
<p>Content for third section...</p>

<h2>Fourth Section</h2>
<p>Content for fourth section...</p>
"""

    result = inject_section_images(test_content, "test123playbackid")
    print(result)
