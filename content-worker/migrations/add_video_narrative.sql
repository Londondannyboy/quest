-- Migration: Add video_narrative JSONB column to articles table
-- Date: 2024-11-26
-- Description: Stores 3-act narrative structure for video-first articles
--
-- The video_narrative column stores:
-- {
--   "template": "aspirational|news_deals|company_profile|guide",
--   "acts": [
--     {
--       "act": 1,
--       "title": "The Dream",
--       "timestamp": 0.0,
--       "end_timestamp": 3.33,
--       "visual_description": "...",
--       "key_points": ["...", "..."]
--     },
--     ...
--   ],
--   "chapters": [
--     {"title": "Act 1: ...", "startTime": 0.0},
--     ...
--   ],
--   "mux_urls": {
--     "stream_url": "...",
--     "playback_id": "...",
--     "acts": {
--       "act_1": {"thumbnail": "...", "gif": "...", "start": 0, "end": 3.33},
--       "act_2": {...},
--       "act_3": {...}
--     }
--   },
--   "video_prompt": "..." (truncated)
-- }

-- Add video_narrative JSONB column
ALTER TABLE articles ADD COLUMN IF NOT EXISTS video_narrative JSONB;

-- Add GIN index for JSONB queries (e.g., finding articles by template)
CREATE INDEX IF NOT EXISTS idx_articles_video_narrative_gin
ON articles USING GIN (video_narrative);

-- Add index for template lookups
CREATE INDEX IF NOT EXISTS idx_articles_narrative_template
ON articles ((video_narrative->>'template'))
WHERE video_narrative IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN articles.video_narrative IS 'JSONB containing 3-act narrative structure: template, acts with timestamps/key_points, chapters for player, mux_urls for thumbnails/GIFs';
