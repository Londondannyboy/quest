-- Migration: Create country_hubs table for SEO-optimized hub pages
-- Date: 2024-11-30
-- Description: Stores comprehensive hub pages that aggregate all cluster content
--              with SEO-optimized slugs and Conde Nast-style formatting
--
-- Hub pages are:
-- - Separate entities from countries and articles
-- - Aggregated content from all cluster modes (Story/Guide/YOLO/Voices)
-- - SEO slugs up to 10 words (e.g., relocating-to-cyprus-visa-cost-of-living-golden-visa-guide)
-- - Self-contained pillar pages (minimal click-through needed)

-- Create the country_hubs table
CREATE TABLE IF NOT EXISTS country_hubs (
    id SERIAL PRIMARY KEY,

    -- Identity and linking
    country_code VARCHAR(2) NOT NULL,           -- ISO 3166-1 alpha-2 (CY, PT, etc.)
    cluster_id UUID,                             -- Links to article cluster
    location_type VARCHAR(20) DEFAULT 'country', -- 'country' or 'city' for city guides
    location_name VARCHAR(100) NOT NULL,         -- "Cyprus" or "Lisbon" for cities

    -- SEO-optimized routing
    slug VARCHAR(150) NOT NULL UNIQUE,           -- SEO slug (up to 10 words, kebab-case)
    legacy_slug VARCHAR(100),                    -- Old /guides/cyprus path for redirects

    -- Content and metadata
    title VARCHAR(255) NOT NULL,                 -- "Relocating to Cyprus: Visa, Cost of Living & Golden Visa Guide"
    meta_description VARCHAR(320),               -- SEO meta description (155-160 chars ideal)
    hub_content TEXT,                            -- Full aggregated HTML content

    -- Flexible storage for aggregated data
    payload JSONB DEFAULT '{}',                  -- Quick stats, cluster navigation, embedded sections
    seo_data JSONB DEFAULT '{}',                 -- DataForSEO keywords used in slug generation

    -- Primary SEO targeting
    primary_keyword VARCHAR(255),                -- Main keyword (highest volume)
    keyword_volume INTEGER,                      -- Monthly search volume
    keyword_difficulty INTEGER,                  -- Keyword difficulty (0-100)

    -- Video (reuses primary article video)
    video_playback_id VARCHAR(100),              -- Mux playback ID for hero video
    video_thumbnail_url VARCHAR(500),            -- Static thumbnail

    -- Status and timestamps
    status VARCHAR(20) DEFAULT 'draft',          -- draft, published, archived
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_country_hubs_country_code
ON country_hubs(country_code);

CREATE INDEX IF NOT EXISTS idx_country_hubs_cluster_id
ON country_hubs(cluster_id);

CREATE INDEX IF NOT EXISTS idx_country_hubs_status
ON country_hubs(status);

CREATE INDEX IF NOT EXISTS idx_country_hubs_slug
ON country_hubs(slug);

CREATE INDEX IF NOT EXISTS idx_country_hubs_legacy_slug
ON country_hubs(legacy_slug);

-- GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_country_hubs_payload_gin
ON country_hubs USING GIN (payload);

CREATE INDEX IF NOT EXISTS idx_country_hubs_seo_data_gin
ON country_hubs USING GIN (seo_data);

-- Comments for documentation
COMMENT ON TABLE country_hubs IS 'SEO-optimized hub pages aggregating all cluster content for a country/city';
COMMENT ON COLUMN country_hubs.slug IS 'SEO slug up to 10 words: relocating-to-cyprus-visa-cost-of-living-golden-visa-guide';
COMMENT ON COLUMN country_hubs.legacy_slug IS 'Old URL path for 301 redirects (e.g., /guides/cyprus)';
COMMENT ON COLUMN country_hubs.payload IS 'JSONB: quick_stats, cluster_articles, embedded_sections, faq_aggregated, sources_aggregated';
COMMENT ON COLUMN country_hubs.seo_data IS 'JSONB: keywords used for slug generation, volumes, difficulty scores';
