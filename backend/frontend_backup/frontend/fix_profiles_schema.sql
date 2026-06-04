-- ================================================================
-- FIX: Add missing columns to the 'profiles' table
-- Run this in the Supabase SQL Editor:
--   https://supabase.com/dashboard/project/<your-project>/sql/new
-- It is safe to re-run — each statement uses "IF NOT EXISTS"
-- ================================================================

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS city      TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS address   TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS photo_url TEXT;

-- Verify the columns were added:
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'profiles'
ORDER BY ordinal_position;
