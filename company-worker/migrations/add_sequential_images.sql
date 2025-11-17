-- Migration: Add sequential image structure for Flux Kontext
-- Date: 2025-11-17
-- Description: Add 7-image structure (featured, hero, 5 content) with SEO metadata
--              for both articles and companies to support contextual storytelling

-- ============================================================================
-- ARTICLES TABLE - Add Sequential Images
-- ============================================================================

-- Featured Image (social sharing, 1200x630)
ALTER TABLE articles
  ADD COLUMN IF NOT EXISTS featured_image_url TEXT,
  ADD COLUMN IF NOT EXISTS featured_image_alt TEXT,
  ADD COLUMN IF NOT EXISTS featured_image_description TEXT,
  ADD COLUMN IF NOT EXISTS featured_image_title TEXT;

-- Hero Image (article header, 16:9)
ALTER TABLE articles
  ADD COLUMN IF NOT EXISTS hero_image_url TEXT,
  ADD COLUMN IF NOT EXISTS hero_image_alt TEXT,
  ADD COLUMN IF NOT EXISTS hero_image_description TEXT,
  ADD COLUMN IF NOT EXISTS hero_image_title TEXT;

-- Content Images 1-5 (in-article, 4:3 or 1:1)
ALTER TABLE articles
  ADD COLUMN IF NOT EXISTS content_image1_url TEXT,
  ADD COLUMN IF NOT EXISTS content_image1_alt TEXT,
  ADD COLUMN IF NOT EXISTS content_image1_description TEXT,
  ADD COLUMN IF NOT EXISTS content_image1_title TEXT,

  ADD COLUMN IF NOT EXISTS content_image2_url TEXT,
  ADD COLUMN IF NOT EXISTS content_image2_alt TEXT,
  ADD COLUMN IF NOT EXISTS content_image2_description TEXT,
  ADD COLUMN IF NOT EXISTS content_image2_title TEXT,

  ADD COLUMN IF NOT EXISTS content_image3_url TEXT,
  ADD COLUMN IF NOT EXISTS content_image3_alt TEXT,
  ADD COLUMN IF NOT EXISTS content_image3_description TEXT,
  ADD COLUMN IF NOT EXISTS content_image3_title TEXT,

  ADD COLUMN IF NOT EXISTS content_image4_url TEXT,
  ADD COLUMN IF NOT EXISTS content_image4_alt TEXT,
  ADD COLUMN IF NOT EXISTS content_image4_description TEXT,
  ADD COLUMN IF NOT EXISTS content_image4_title TEXT,

  ADD COLUMN IF NOT EXISTS content_image5_url TEXT,
  ADD COLUMN IF NOT EXISTS content_image5_alt TEXT,
  ADD COLUMN IF NOT EXISTS content_image5_description TEXT,
  ADD COLUMN IF NOT EXISTS content_image5_title TEXT;

-- Content Structure Analysis (H2 sections, sentiment)
ALTER TABLE articles
  ADD COLUMN IF NOT EXISTS sections JSONB DEFAULT '[]'::jsonb;

-- ============================================================================
-- COMPANIES TABLE - Add Sequential Images
-- ============================================================================

-- Featured Image (social sharing, 1200x630)
ALTER TABLE companies
  ADD COLUMN IF NOT EXISTS featured_image_url TEXT,
  ADD COLUMN IF NOT EXISTS featured_image_alt TEXT,
  ADD COLUMN IF NOT EXISTS featured_image_description TEXT,
  ADD COLUMN IF NOT EXISTS featured_image_title TEXT;

-- Hero Image (company header, 16:9)
ALTER TABLE companies
  ADD COLUMN IF NOT EXISTS hero_image_url TEXT,
  ADD COLUMN IF NOT EXISTS hero_image_alt TEXT,
  ADD COLUMN IF NOT EXISTS hero_image_description TEXT,
  ADD COLUMN IF NOT EXISTS hero_image_title TEXT;

-- Content Images 1-5 (profile sections, contextual brand imagery)
ALTER TABLE companies
  ADD COLUMN IF NOT EXISTS content_image1_url TEXT,
  ADD COLUMN IF NOT EXISTS content_image1_alt TEXT,
  ADD COLUMN IF NOT EXISTS content_image1_description TEXT,
  ADD COLUMN IF NOT EXISTS content_image1_title TEXT,

  ADD COLUMN IF NOT EXISTS content_image2_url TEXT,
  ADD COLUMN IF NOT EXISTS content_image2_alt TEXT,
  ADD COLUMN IF NOT EXISTS content_image2_description TEXT,
  ADD COLUMN IF NOT EXISTS content_image2_title TEXT,

  ADD COLUMN IF NOT EXISTS content_image3_url TEXT,
  ADD COLUMN IF NOT EXISTS content_image3_alt TEXT,
  ADD COLUMN IF NOT EXISTS content_image3_description TEXT,
  ADD COLUMN IF NOT EXISTS content_image3_title TEXT,

  ADD COLUMN IF NOT EXISTS content_image4_url TEXT,
  ADD COLUMN IF NOT EXISTS content_image4_alt TEXT,
  ADD COLUMN IF NOT EXISTS content_image4_description TEXT,
  ADD COLUMN IF NOT EXISTS content_image4_title TEXT,

  ADD COLUMN IF NOT EXISTS content_image5_url TEXT,
  ADD COLUMN IF NOT EXISTS content_image5_alt TEXT,
  ADD COLUMN IF NOT EXISTS content_image5_description TEXT,
  ADD COLUMN IF NOT EXISTS content_image5_title TEXT;

-- ============================================================================
-- INDEXES for Performance
-- ============================================================================

-- Articles sections JSONB index
CREATE INDEX IF NOT EXISTS idx_articles_sections ON articles USING GIN (sections);

-- Image URL indexes for quick lookups
CREATE INDEX IF NOT EXISTS idx_articles_featured_image ON articles(featured_image_url) WHERE featured_image_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_articles_hero_image ON articles(hero_image_url) WHERE hero_image_url IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_companies_featured_image ON companies(featured_image_url) WHERE featured_image_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_companies_hero_image ON companies(hero_image_url) WHERE hero_image_url IS NOT NULL;

-- ============================================================================
-- COMMENTS for Documentation
-- ============================================================================

COMMENT ON COLUMN articles.featured_image_url IS 'Social sharing image (1200x630), first in Kontext sequence';
COMMENT ON COLUMN articles.hero_image_url IS 'Article header image (16:9), second in Kontext sequence';
COMMENT ON COLUMN articles.content_image1_url IS 'First in-content image, uses hero as context reference';
COMMENT ON COLUMN articles.sections IS 'H2 sections with sentiment analysis for image generation: [{title, content, sentiment, image_index}]';

COMMENT ON COLUMN companies.featured_image_url IS 'Social sharing image with logo (1200x630)';
COMMENT ON COLUMN companies.hero_image_url IS 'Company header image (16:9), consistent brand aesthetic';
COMMENT ON COLUMN companies.content_image1_url IS 'First contextual brand image, maintains logo consistency';

-- ============================================================================
-- EXAMPLE USAGE
-- ============================================================================

-- Example sections structure:
-- UPDATE articles SET sections = '[
--   {"title": "Introduction", "content": "...", "sentiment": "neutral", "image_index": null},
--   {"title": "The Challenge", "content": "...", "sentiment": "negative", "image_index": 1},
--   {"title": "Turning Point", "content": "...", "sentiment": "positive", "image_index": 2},
--   {"title": "Resolution", "content": "...", "sentiment": "positive", "image_index": 3}
-- ]'::jsonb WHERE id = 'article-123';

-- Query articles with images:
-- SELECT id, title, featured_image_url, hero_image_url,
--        jsonb_array_length(sections) as section_count
-- FROM articles
-- WHERE featured_image_url IS NOT NULL;
