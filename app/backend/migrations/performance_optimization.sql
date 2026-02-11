-- Performance Optimization - Sprint 3 P2-2
-- DB Indexing for faster queries

-- ===========================
-- 1. Canonical Menus Indexing
-- ===========================

-- Index for exact match queries (most frequent)
CREATE INDEX IF NOT EXISTS idx_canonical_menus_name_ko
ON canonical_menus(name_ko);

-- pg_trgm index for similarity search
CREATE INDEX IF NOT EXISTS idx_canonical_menus_name_ko_trgm
ON canonical_menus USING gin (name_ko gin_trgm_ops);

-- Index for concept lookup
CREATE INDEX IF NOT EXISTS idx_canonical_menus_concept_id
ON canonical_menus(concept_id);

-- ===========================
-- 2. Modifiers Indexing
-- ===========================

-- Index for modifier text lookup (used in decomposition)
CREATE INDEX IF NOT EXISTS idx_modifiers_text_ko
ON modifiers(text_ko);

-- Index for type-based filtering
CREATE INDEX IF NOT EXISTS idx_modifiers_type
ON modifiers(type);

-- Composite index for priority sorting
CREATE INDEX IF NOT EXISTS idx_modifiers_type_priority
ON modifiers(type, priority DESC);

-- ===========================
-- 3. Scan Logs Indexing
-- ===========================

-- Index for admin queue queries (status + created_at)
CREATE INDEX IF NOT EXISTS idx_scan_logs_status_created
ON scan_logs(status, created_at DESC);

-- Index for shop-based queries
CREATE INDEX IF NOT EXISTS idx_scan_logs_shop_id
ON scan_logs(shop_id) WHERE shop_id IS NOT NULL;

-- Index for 7-day stats queries
CREATE INDEX IF NOT EXISTS idx_scan_logs_created_at
ON scan_logs(created_at DESC);

-- Index for canonical matching
CREATE INDEX IF NOT EXISTS idx_scan_logs_canonical_id
ON scan_logs(matched_canonical_id) WHERE matched_canonical_id IS NOT NULL;

-- ===========================
-- 4. Menu Variants Indexing
-- ===========================

-- Index for shop menu lookup
CREATE INDEX IF NOT EXISTS idx_menu_variants_shop_id
ON menu_variants(shop_id, is_active) WHERE is_active = true;

-- Index for canonical menu reference
CREATE INDEX IF NOT EXISTS idx_menu_variants_canonical_id
ON menu_variants(canonical_menu_id);

-- Index for display order (QR menu page)
CREATE INDEX IF NOT EXISTS idx_menu_variants_shop_display
ON menu_variants(shop_id, display_order) WHERE is_active = true;

-- ===========================
-- 5. Shops Indexing
-- ===========================

-- Index for shop code lookup (QR menu)
CREATE INDEX IF NOT EXISTS idx_shops_shop_code
ON shops(shop_code);

-- ===========================
-- 6. Statistics and Monitoring
-- ===========================

-- Analyze tables for query planner
ANALYZE canonical_menus;
ANALYZE modifiers;
ANALYZE scan_logs;
ANALYZE menu_variants;
ANALYZE shops;

-- ===========================
-- 7. Vacuum for space reclaim
-- ===========================

-- Remove dead tuples
VACUUM ANALYZE canonical_menus;
VACUUM ANALYZE modifiers;
VACUUM ANALYZE scan_logs;

-- ===========================
-- Performance Verification
-- ===========================

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Estimated query performance improvement:
-- - Exact match: 0.5ms → 0.1ms (5x faster)
-- - Similarity search: 50ms → 5ms (10x faster)
-- - Admin queue: 20ms → 2ms (10x faster)
-- - QR menu page: 100ms → 10ms (10x faster)
