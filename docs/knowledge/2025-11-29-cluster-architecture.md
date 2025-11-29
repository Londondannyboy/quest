# Cluster Architecture for Relocation.Quest

**Date:** 2025-11-29
**Status:** Implemented and Committed

---

## Overview

This document captures the comprehensive cluster architecture implementation for country guide articles on relocation.quest. The system creates SEO-optimized content with multiple presentation modes and topic-specific cluster articles.

---

## Architecture Summary

```
CountryGuideCreationWorkflow
│
├── Phase 1: Research & SEO Keywords (DataForSEO)
│   └── Saves to countries.seo_keywords JSONB
│
├── Phase 2: Generate Content for All Modes
│   ├── Story (primary - 4-act narrative)
│   ├── Guide (practical information)
│   ├── YOLO (adventure-focused)
│   └── Voices (expat perspectives from Reddit)
│
├── Phase A: Create Parent Article
│   └── Saves content_story, content_guide, content_yolo, content_voices
│
├── Phase B: Cluster Articles (Child Workflows)
│   ├── ClusterArticleWorkflow (story) → generates video
│   ├── ClusterArticleWorkflow (guide) → generates video
│   ├── ClusterArticleWorkflow (yolo) → generates video
│   └── ClusterArticleWorkflow (voices) → generates video
│
└── Phase C: Topic Clusters (SEO-Targeted)
    └── TopicClusterWorkflow × N keywords
        ├── Reuses parent video (no new generation)
        ├── Builds alt_text from four_act_visual_hint
        └── Targets specific keywords from DataForSEO
```

---

## Database Schema

### Articles Table - Key Columns

| Column | Type | Description |
|--------|------|-------------|
| `content_story` | TEXT | Story mode HTML content |
| `content_guide` | TEXT | Guide mode HTML content |
| `content_yolo` | TEXT | YOLO mode HTML content |
| `content_voices` | JSONB | Voices mode (structured data) |
| `article_mode` | TEXT | Current mode: story/guide/yolo/voices/topic |
| `cluster_id` | UUID | Links all cluster articles together |
| `parent_id` | INT | References parent guide article |
| `target_keyword` | TEXT | SEO target keyword |
| `keyword_volume` | INT | Monthly search volume |
| `keyword_difficulty` | FLOAT | SEO difficulty score |

### Countries Table

| Column | Type | Description |
|--------|------|-------------|
| `seo_keywords` | JSONB | DataForSEO keyword research results |
| `facts` | JSONB | Extracted country facts for quick reference |

### Video Tags Table

| Column | Type | Description |
|--------|------|-------------|
| `playback_id` | TEXT | Mux playback ID |
| `asset_id` | TEXT | Mux asset ID |
| `cluster_id` | UUID | Links to cluster |
| `article_id` | INT | Associated article |
| `country` | TEXT | Country name |
| `mode` | TEXT | story/guide/yolo/voices/topic |
| `tags` | JSONB | Search tags array |

---

## URL Structure

### Mode-Based Articles (4 constant modes)
```
/slovakia-relocation-guide           → Default (story mode)
/slovakia-relocation-guide-story     → Story mode
/slovakia-relocation-guide-guide     → Guide mode
/slovakia-relocation-guide-yolo      → YOLO mode
/slovakia-relocation-guide-voices    → Voices mode
```

### Topic Cluster Articles (Dynamic from SEO)
```
/slovakia-cost-of-living             → Targeting "slovakia cost of living" (70 vol)
/slovakia-visa-requirements          → Targeting "slovakia visa requirements" (40 vol)
/slovakia-golden-visa                → Targeting "slovakia golden visa" (10 vol)
```

---

## Content Generation

### Mode Templates

Each mode generates content with specific focus:

| Mode | Focus | Tone | Key Elements |
|------|-------|------|--------------|
| Story | Emotional journey | Narrative | 4-act structure, transformation arc |
| Guide | Practical info | Informative | Checklists, steps, requirements |
| YOLO | Adventure | Exciting | Experiences, unique opportunities |
| Voices | Social proof | Authentic | Reddit quotes, real experiences |

### Topic Cluster Content

- Uses inline CSS (not Tailwind - purging issues)
- Requires 8-12 keyword mentions for SEO
- Links back to parent guide: `"See our comprehensive /{parent_slug} for more"`
- Generated via `generate_topic_cluster_content` activity

---

## Video Architecture

### Video Generation Strategy

| Article Type | Video Strategy | Cost |
|--------------|----------------|------|
| Parent Article | Generates hero video | $1-2 |
| Cluster Articles | Each generates segment video | $1-2 each |
| Topic Clusters | **Reuses parent video** | $0 |

### Video Metadata

```python
video_narrative = {
    "playback_id": "V2XIwkq...",
    "duration": 12,
    "mode": "topic",
    "planning_type": "housing",
    "reused_from_parent": True,
    "alt_text": "Video for slovakia cost of living: A rainy window..."
}
```

### four_act_content Structure

```python
four_act_content = [
    {
        "act": 1,
        "title": "The Grey Realization",
        "factoid": "Rent in Slovakia is 61.3% lower than US",
        "four_act_visual_hint": "A rainy window in a cramped London apartment..."
    },
    # ... acts 2-4
]
```

---

## Frontend Rendering

### [slug].astro Page Logic

```javascript
// Mode detection
const urlMode = Astro.url.pathname.split('-').pop();
const modes = ['story', 'guide', 'yolo', 'voices'];
const requestedMode = modes.includes(urlMode) ? urlMode : 'story';

// Content source selection
const hasContentModes = article.content_story || article.content_guide ||
                        article.content_yolo || article.content_voices;
const isClusterMode = hasContentModes;

// Render appropriate content
if (isClusterMode) {
    // Use content_story/guide/yolo/voices columns
} else {
    // Use article.content (legacy)
}
```

### CSS Strategy

**Problem:** Tailwind purges dynamic class names in SSR content.

**Solution:** Use `.prose` wrapper class which inherits all typography styles:

```html
<div id="cluster-content" class="cluster-mode-content">
  <div class="prose prose-lg max-w-none">
    {content from database}
  </div>
</div>
```

---

## Workflow Files

### Key Files Modified/Created

| File | Purpose |
|------|---------|
| `content-worker/src/workflows/topic_cluster_workflow.py` | **NEW** - SEO topic cluster workflow |
| `content-worker/src/workflows/country_guide_creation.py` | Added Phase C for topic clusters |
| `content-worker/src/workflows/cluster_article_workflow.py` | Mode-based cluster articles |
| `content-worker/src/activities/generation/country_guide_generation.py` | Added `generate_topic_cluster_content` |
| `content-worker/worker.py` | Registered new workflow and activity |
| `relocation/src/pages/[slug].astro` | Frontend mode switching |

---

## Git Commits Today

```
4027ab5 feat: TopicClusterWorkflow reuses parent video for SEO articles
1fe043c Add content_story/guide/yolo/voices columns to save_article_to_neon
3796229 Replace crawl4ai_batch with individual CrawlUrlWorkflow child workflows
f1ea220 fix: crawl4ai_batch needs topic parameter + correct response key
2fe189d feat: Cyprus-style video prompts + segment child workflows + character consistency
```

---

## Known Issues & TODO

### Display Issue (PENDING FIX)
- Cluster content may not render properly on some article pages
- Related to CSS class purging or content column detection
- Needs investigation on live deployment

### Future Enhancements
- Add video_tags metadata (title, description, alt_text columns)
- Pre/post link validation (404 cleansing)
- Sitemap generation for topic clusters

---

## Testing

### Slovakia Test Case

```sql
-- Check Slovakia articles
SELECT slug, article_mode, video_playback_id,
       content_story IS NOT NULL as has_story,
       content_guide IS NOT NULL as has_guide
FROM articles
WHERE slug LIKE '%slovakia%' AND app = 'relocation';

-- Check SEO keywords
SELECT seo_keywords->'long_tail' as keywords
FROM countries WHERE code = 'SK';
```

### Live URLs to Test
- https://relocation.quest/slovakia-relocation-guide
- https://relocation.quest/slovakia-relocation-guide-story
- https://relocation.quest/slovakia-relocation-guide-yolo

---

## Architecture Diagram

```
                    ┌─────────────────────────────────┐
                    │  CountryGuideCreationWorkflow   │
                    └────────────────┬────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │  ClusterArticle │   │  ClusterArticle │   │ TopicCluster    │
    │  (story/guide/  │   │  (yolo/voices)  │   │ Workflow × N    │
    │   generates vid)│   │  (generates vid)│   │ (reuses vid)    │
    └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
             │                     │                     │
             ▼                     ▼                     ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                     Neon PostgreSQL                          │
    │  articles: content_story, content_guide, content_yolo, etc  │
    │  video_tags: playback_id, cluster_id, mode, tags            │
    │  countries: seo_keywords, facts                             │
    └─────────────────────────────────────────────────────────────┘
             │                     │                     │
             ▼                     ▼                     ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   Astro Frontend                             │
    │  [slug].astro: Detects mode from URL, renders content       │
    │  Uses .prose class for consistent typography                │
    └─────────────────────────────────────────────────────────────┘
```

---

*Document auto-generated by Claude Code on 2025-11-29*
