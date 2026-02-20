-- ============================================================================
-- Sprint 2 Phase 1 Rollback Script
-- ============================================================================
-- Purpose: Safely rollback all changes from sprint2_phase1_images.sql
-- Date: 2026-02-19
-- Author: backend-dev
--
-- WARNING: This will DROP columns and their data permanently
-- Make sure you have a backup before running this!
-- ============================================================================

BEGIN;

-- Verification check before rollback
DO $$
DECLARE
  menu_count INT;
BEGIN
  SELECT COUNT(*) INTO menu_count FROM canonical_menus;
  RAISE NOTICE 'About to rollback Sprint 2 Phase 1 migration';
  RAISE NOTICE 'Current menu count: %', menu_count;
  RAISE NOTICE 'This will DROP 11 columns permanently';
  RAISE WARNING 'Make sure you have a backup!';
END $$;

-- ============================================================================
-- PART 1: Drop Trigger and Functions (must drop before dropping columns)
-- ============================================================================

DROP TRIGGER IF EXISTS trg_update_completeness ON canonical_menus;
DROP FUNCTION IF EXISTS update_content_completeness();
DROP FUNCTION IF EXISTS calculate_content_completeness(canonical_menus);

RAISE NOTICE 'Dropped trigger and 2 functions';

-- ============================================================================
-- PART 2: Drop Indexes (must drop before dropping columns)
-- ============================================================================

DROP INDEX IF EXISTS idx_cm_primary_image_gin;
DROP INDEX IF EXISTS idx_cm_images_gin;
DROP INDEX IF EXISTS idx_cm_regional_variants_gin;
DROP INDEX IF EXISTS idx_cm_content_completeness;
DROP INDEX IF EXISTS idx_cm_content_complete;

RAISE NOTICE 'Dropped 5 indexes';

-- ============================================================================
-- PART 3: Drop New Columns (in reverse order of creation)
-- ============================================================================

ALTER TABLE canonical_menus
  DROP COLUMN IF EXISTS content_completeness CASCADE;

ALTER TABLE canonical_menus
  DROP COLUMN IF EXISTS similar_dishes CASCADE;

ALTER TABLE canonical_menus
  DROP COLUMN IF EXISTS visitor_tips CASCADE;

ALTER TABLE canonical_menus
  DROP COLUMN IF EXISTS flavor_profile CASCADE;

ALTER TABLE canonical_menus
  DROP COLUMN IF EXISTS nutrition_detail CASCADE;

ALTER TABLE canonical_menus
  DROP COLUMN IF EXISTS preparation_steps CASCADE;

ALTER TABLE canonical_menus
  DROP COLUMN IF EXISTS regional_variants CASCADE;

ALTER TABLE canonical_menus
  DROP COLUMN IF EXISTS description_long_en CASCADE;

ALTER TABLE canonical_menus
  DROP COLUMN IF EXISTS description_long_ko CASCADE;

ALTER TABLE canonical_menus
  DROP COLUMN IF EXISTS images CASCADE;

ALTER TABLE canonical_menus
  DROP COLUMN IF EXISTS primary_image CASCADE;

RAISE NOTICE 'Dropped 11 columns from canonical_menus';

-- ============================================================================
-- PART 4: Verification
-- ============================================================================

DO $$
DECLARE
  remaining_columns TEXT[];
BEGIN
  SELECT ARRAY_AGG(column_name) INTO remaining_columns
  FROM information_schema.columns
  WHERE table_name = 'canonical_menus'
    AND column_name IN (
      'primary_image', 'images', 'description_long_ko', 'description_long_en',
      'regional_variants', 'preparation_steps', 'nutrition_detail',
      'flavor_profile', 'visitor_tips', 'similar_dishes', 'content_completeness'
    );

  IF remaining_columns IS NULL THEN
    RAISE NOTICE 'Rollback successful - all Sprint 2 Phase 1 columns removed';
  ELSE
    RAISE WARNING 'Some columns still exist: %', remaining_columns;
  END IF;
END $$;

COMMIT;

-- ============================================================================
-- Post-Rollback Manual Checks
-- ============================================================================

-- Verify columns are gone
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'canonical_menus'
ORDER BY ordinal_position;

-- Verify indexes are gone
SELECT indexname
FROM pg_indexes
WHERE tablename = 'canonical_menus'
ORDER BY indexname;

-- Note: image_url column remains unchanged (not touched by migration)
