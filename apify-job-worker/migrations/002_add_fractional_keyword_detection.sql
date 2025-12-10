-- Migration: Add automatic fractional keyword detection via trigger
-- Purpose: Automatically mark jobs as is_fractional=TRUE if they contain
--          fractional-related keywords in title or description
--
-- This migration:
-- 1. Creates a trigger function that checks for keywords on INSERT
-- 2. Creates a BEFORE INSERT trigger on jobs table
-- 3. Backfills all existing jobs with the keyword check
--
-- Keywords checked: 'fractional', 'part-time', 'part time'

-- Step 1: Create the trigger function
CREATE OR REPLACE FUNCTION check_fractional_keywords()
RETURNS TRIGGER AS $$
BEGIN
  -- Check if title or description contains fractional-related keywords (case-insensitive)
  IF (
    LOWER(COALESCE(NEW.title, '')) LIKE '%fractional%' OR
    LOWER(COALESCE(NEW.title, '')) LIKE '%part-time%' OR
    LOWER(COALESCE(NEW.title, '')) LIKE '%part time%' OR
    LOWER(COALESCE(NEW.full_description, '')) LIKE '%fractional%' OR
    LOWER(COALESCE(NEW.full_description, '')) LIKE '%part-time%' OR
    LOWER(COALESCE(NEW.full_description, '')) LIKE '%part time%'
  ) THEN
    NEW.is_fractional := TRUE;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 2: Create the trigger on INSERT (fires before each row is inserted)
DROP TRIGGER IF EXISTS detect_fractional_on_insert ON jobs;
CREATE TRIGGER detect_fractional_on_insert
BEFORE INSERT ON jobs
FOR EACH ROW
EXECUTE FUNCTION check_fractional_keywords();

-- Step 3: Backfill existing jobs that contain fractional keywords but are not yet marked
UPDATE jobs
SET is_fractional = TRUE
WHERE is_fractional = FALSE
  AND (
    LOWER(COALESCE(title, '')) LIKE '%fractional%' OR
    LOWER(COALESCE(title, '')) LIKE '%part-time%' OR
    LOWER(COALESCE(title, '')) LIKE '%part time%' OR
    LOWER(COALESCE(full_description, '')) LIKE '%fractional%' OR
    LOWER(COALESCE(full_description, '')) LIKE '%part-time%' OR
    LOWER(COALESCE(full_description, '')) LIKE '%part time%'
  );
