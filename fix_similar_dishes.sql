-- Fix similar_dishes column type
-- Change from JSONB to JSONB[]

BEGIN;

-- Drop existing column
ALTER TABLE canonical_menus DROP COLUMN IF EXISTS similar_dishes;

-- Recreate as JSONB array
ALTER TABLE canonical_menus ADD COLUMN similar_dishes JSONB[] DEFAULT NULL;

COMMIT;

-- Verify
SELECT data_type, udt_name
FROM information_schema.columns
WHERE table_name = 'canonical_menus' AND column_name = 'similar_dishes';
