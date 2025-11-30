-- Add video metadata columns to articles table
-- These enable intelligent video-to-section matching in hub creation

-- video_topics: Array of topic tags for matching (e.g., ["adventure", "lifestyle", "beaches"])
-- video_description: Human-readable description of what the video covers

ALTER TABLE articles
ADD COLUMN IF NOT EXISTS video_topics JSONB DEFAULT '[]'::jsonb;

ALTER TABLE articles
ADD COLUMN IF NOT EXISTS video_description TEXT;

-- Create index for topic-based queries
CREATE INDEX IF NOT EXISTS idx_articles_video_topics
ON articles USING GIN (video_topics);

-- Add comment for documentation
COMMENT ON COLUMN articles.video_topics IS 'Array of topic tags for video content matching (e.g., ["visa", "permits", "legal"])';
COMMENT ON COLUMN articles.video_description IS 'Human-readable description of video content for hub section matching';

-- Update existing articles with topics based on article_mode
-- This gives us initial data to work with

UPDATE articles
SET video_topics = CASE article_mode
    WHEN 'story' THEN '["narrative", "journey", "overview", "introduction", "lifestyle"]'::jsonb
    WHEN 'guide' THEN '["practical", "steps", "visa", "permits", "legal", "process", "how-to"]'::jsonb
    WHEN 'yolo' THEN '["adventure", "lifestyle", "beaches", "nightlife", "exploration", "fun"]'::jsonb
    WHEN 'voices' THEN '["expat", "community", "experiences", "testimonials", "real-life", "stories"]'::jsonb
    ELSE '[]'::jsonb
END
WHERE video_playback_id IS NOT NULL
  AND (video_topics IS NULL OR video_topics = '[]'::jsonb);

-- Set descriptions based on mode and country
UPDATE articles
SET video_description = CASE article_mode
    WHEN 'story' THEN 'Narrative journey through relocation - the draw, opportunity, journey, and new life'
    WHEN 'guide' THEN 'Step-by-step practical guide - visas, permits, processes, and requirements'
    WHEN 'yolo' THEN 'Adventure and lifestyle - beaches, nightlife, exploration, and fun experiences'
    WHEN 'voices' THEN 'Real expat experiences - community stories, testimonials, and lived experiences'
    ELSE NULL
END
WHERE video_playback_id IS NOT NULL
  AND video_description IS NULL;
