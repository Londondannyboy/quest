-- Migration: create_user_profiles.sql
-- Description: User profile facts storage for voice-extracted data
-- Date: 2024-12-01

-- ============================================================================
-- USER PROFILES TABLE (Stack Auth integration)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,

    -- Stack Auth user ID
    stack_user_id VARCHAR(255) NOT NULL UNIQUE,

    -- Profile metadata
    email VARCHAR(255),
    display_name VARCHAR(255),

    -- Aggregated profile facts (denormalized for quick access in voice prompts)
    profile_snapshot JSONB DEFAULT '{}'::jsonb,

    -- Session tracking
    total_sessions INTEGER DEFAULT 0,
    last_session_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_stack_user_id ON user_profiles(stack_user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);

-- ============================================================================
-- USER PROFILE FACTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_profile_facts (
    id SERIAL PRIMARY KEY,

    -- Foreign key to user_profiles
    user_profile_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,

    -- Fact categorization
    fact_type VARCHAR(50) NOT NULL,  -- destination, origin, family, profession, employer, work_type, budget, timeline

    -- Fact value (structured JSONB for flexibility)
    fact_value JSONB NOT NULL,  -- {"value": "Cyprus", "city": "Limassol", "confidence": 0.95}

    -- Source tracking
    source VARCHAR(50) DEFAULT 'voice',  -- voice, user_edit, llm_refined
    confidence DECIMAL(3,2) DEFAULT 0.5,

    -- Session reference for audit
    session_id VARCHAR(100),
    extracted_from_message TEXT,

    -- User verification
    is_user_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    verified_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_user_profile_facts_user_id ON user_profile_facts(user_profile_id);
CREATE INDEX IF NOT EXISTS idx_user_profile_facts_type ON user_profile_facts(fact_type);
CREATE INDEX IF NOT EXISTS idx_user_profile_facts_active ON user_profile_facts(user_profile_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_profile_facts_session ON user_profile_facts(session_id);
CREATE INDEX IF NOT EXISTS idx_user_profile_facts_value_gin ON user_profile_facts USING GIN (fact_value);

-- ============================================================================
-- VOICE SESSIONS TABLE (for audit trail and message storage)
-- ============================================================================

CREATE TABLE IF NOT EXISTS voice_sessions (
    id SERIAL PRIMARY KEY,

    session_id VARCHAR(100) NOT NULL UNIQUE,
    user_profile_id INTEGER REFERENCES user_profiles(id) ON DELETE SET NULL,
    stack_user_id VARCHAR(255),  -- Denormalized for queries before profile exists

    status VARCHAR(20) DEFAULT 'active',  -- active, ended, abandoned

    -- Raw conversation storage
    messages JSONB DEFAULT '[]'::jsonb,

    -- Extraction results
    quick_extraction JSONB DEFAULT '{}'::jsonb,  -- Per-message regex extraction
    llm_refined_facts JSONB DEFAULT '{}'::jsonb,  -- End-of-session LLM refinement

    -- Metadata
    message_count INTEGER DEFAULT 0,
    duration_seconds INTEGER,

    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_voice_sessions_user_id ON voice_sessions(user_profile_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_stack_user ON voice_sessions(stack_user_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_status ON voice_sessions(status);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_session_id ON voice_sessions(session_id);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE user_profiles IS 'User profiles linked to Stack Auth for personalization';
COMMENT ON TABLE user_profile_facts IS 'Individual facts extracted from voice conversations, editable by users';
COMMENT ON TABLE voice_sessions IS 'Voice sessions with raw messages and extraction results for audit';

COMMENT ON COLUMN user_profiles.profile_snapshot IS 'Denormalized JSONB of active facts for quick loading into voice prompts';
COMMENT ON COLUMN user_profile_facts.fact_type IS 'One of: destination, origin, family, profession, employer, work_type, budget, timeline, visa_interest';
COMMENT ON COLUMN user_profile_facts.source IS 'How the fact was captured: voice (regex), llm_refined (end-of-session), user_edit (manual)';
COMMENT ON COLUMN user_profile_facts.is_user_verified IS 'True if user explicitly confirmed or edited this fact';
