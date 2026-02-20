-- Add translation status tracking columns to canonical_menus
-- Created: 2026-02-20
-- Purpose: Track auto-translation status for multi-language support

-- Add translation status column
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS translation_status VARCHAR(20) DEFAULT 'pending';

-- Add translation attempted timestamp
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS translation_attempted_at TIMESTAMPTZ;

-- Add translation error message
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS translation_error TEXT;

-- Add CHECK constraint for valid status values
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_translation_status'
    ) THEN
        ALTER TABLE canonical_menus
        ADD CONSTRAINT check_translation_status
        CHECK (translation_status IN ('pending', 'completed', 'failed', 'partial', 'disabled'));
    END IF;
END$$;

-- Create index for status queries
CREATE INDEX IF NOT EXISTS idx_canonical_translation_status
ON canonical_menus(translation_status);

-- Comment for documentation
COMMENT ON COLUMN canonical_menus.translation_status IS 'Auto-translation status: pending, completed, failed, partial, disabled';
COMMENT ON COLUMN canonical_menus.translation_attempted_at IS 'Timestamp of last translation attempt';
COMMENT ON COLUMN canonical_menus.translation_error IS 'Error message if translation failed';

-- Set existing menus to 'completed' if they have translations, otherwise 'pending'
UPDATE canonical_menus
SET translation_status = CASE
    WHEN (name_ja IS NOT NULL AND name_ja != '') OR
         (name_zh_cn IS NOT NULL AND name_zh_cn != '') OR
         (explanation_short ? 'ja') OR
         (explanation_short ? 'zh')
    THEN 'completed'
    ELSE 'pending'
END
WHERE translation_status IS NULL OR translation_status = 'pending';

-- Output summary
DO $$
DECLARE
    pending_count INT;
    completed_count INT;
BEGIN
    SELECT COUNT(*) INTO pending_count FROM canonical_menus WHERE translation_status = 'pending';
    SELECT COUNT(*) INTO completed_count FROM canonical_menus WHERE translation_status = 'completed';

    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Translation Status Migration Complete';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Pending translations: %', pending_count;
    RAISE NOTICE 'Completed translations: %', completed_count;
    RAISE NOTICE '==============================================';
END$$;
