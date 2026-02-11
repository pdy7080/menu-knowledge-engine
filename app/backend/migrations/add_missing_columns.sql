-- Add Missing Columns Migration
-- Fix model-API mismatch from Sprint 3

-- ===========================
-- 1. ScanLog Table
-- ===========================

-- Add status column for admin dashboard
ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';

-- Add matched_canonical_id for admin review
ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS matched_canonical_id UUID REFERENCES canonical_menus(id);

-- Add created_at (alias for scanned_at compatibility)
ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Update created_at from scanned_at for existing rows
UPDATE scan_logs SET created_at = scanned_at WHERE created_at IS NULL;

-- ===========================
-- 2. MenuVariant Table
-- ===========================

-- Add canonical_menu_id (alias for canonical_id)
ALTER TABLE menu_variants ADD COLUMN IF NOT EXISTS canonical_menu_id UUID REFERENCES canonical_menus(id);

-- Copy canonical_id to canonical_menu_id
UPDATE menu_variants SET canonical_menu_id = canonical_id WHERE canonical_menu_id IS NULL;

-- Add menu_name_ko (alias for display_name_ko)
ALTER TABLE menu_variants ADD COLUMN IF NOT EXISTS menu_name_ko VARCHAR(200);

-- Copy display_name_ko to menu_name_ko
UPDATE menu_variants SET menu_name_ko = display_name_ko WHERE menu_name_ko IS NULL;

-- Add price_display for QR menu
ALTER TABLE menu_variants ADD COLUMN IF NOT EXISTS price_display VARCHAR(50);

-- Generate price_display from price
UPDATE menu_variants SET price_display = price::text || '원' WHERE price IS NOT NULL AND price_display IS NULL;

-- Add is_active for QR menu filtering
ALTER TABLE menu_variants ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Add display_order for QR menu sorting
ALTER TABLE menu_variants ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0;

-- ===========================
-- 3. Shop Table
-- ===========================

-- Add shop_code for QR menu
ALTER TABLE shops ADD COLUMN IF NOT EXISTS shop_code VARCHAR(50) UNIQUE;

-- Generate shop_code from name_ko (first 3 chars + random)
UPDATE shops SET shop_code = LOWER(
    REGEXP_REPLACE(
        SUBSTRING(name_ko, 1, 3) || '-' || SUBSTRING(MD5(RANDOM()::text), 1, 6),
        '[^a-z0-9-]',
        '',
        'g'
    )
)
WHERE shop_code IS NULL;

-- ===========================
-- 4. Verify Changes
-- ===========================

-- Show updated schema
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('scan_logs', 'menu_variants', 'shops')
  AND column_name IN (
    'status', 'matched_canonical_id', 'created_at',
    'canonical_menu_id', 'menu_name_ko', 'price_display', 'is_active', 'display_order',
    'shop_code'
  )
ORDER BY table_name, ordinal_position;
