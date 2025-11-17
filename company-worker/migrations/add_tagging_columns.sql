-- Migration: Add tagging columns for geographic, specializations, and deals
-- Date: 2025-11-17
-- Description: Add array columns to support filtering and categorization

ALTER TABLE companies
  ADD COLUMN IF NOT EXISTS geographic_tags TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS specialization_tags TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS deal_tags TEXT[] DEFAULT '{}';

-- Create indexes for array searching
CREATE INDEX IF NOT EXISTS idx_companies_geographic_tags ON companies USING GIN (geographic_tags);
CREATE INDEX IF NOT EXISTS idx_companies_specialization_tags ON companies USING GIN (specialization_tags);
CREATE INDEX IF NOT EXISTS idx_companies_deal_tags ON companies USING GIN (deal_tags);

-- Example usage:
-- UPDATE companies SET geographic_tags = '{UK, Europe, London}' WHERE slug = 'evercore';
-- UPDATE companies SET specialization_tags = '{Private Equity, M&A, Advisory}' WHERE slug = 'evercore';
-- SELECT * FROM companies WHERE 'UK' = ANY(geographic_tags);
