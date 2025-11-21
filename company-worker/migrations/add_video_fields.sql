-- Migration: Add video fields to articles table
-- Date: 2024-11-21
-- Description: Adds video URL and Mux playback fields for video-first article generation

-- Add video columns
ALTER TABLE articles ADD COLUMN IF NOT EXISTS video_url TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS video_playback_id TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS video_asset_id TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS video_gif_url TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS video_thumbnail_url TEXT;

-- Add index for video lookups
CREATE INDEX IF NOT EXISTS idx_articles_video_playback_id ON articles(video_playback_id);

-- Add comments for documentation
COMMENT ON COLUMN articles.video_url IS 'Mux HLS stream URL (.m3u8)';
COMMENT ON COLUMN articles.video_playback_id IS 'Mux playback ID for generating thumbnails/GIFs';
COMMENT ON COLUMN articles.video_asset_id IS 'Mux asset ID for management';
COMMENT ON COLUMN articles.video_gif_url IS 'Animated GIF URL for collection cards';
COMMENT ON COLUMN articles.video_thumbnail_url IS 'Primary thumbnail URL';
