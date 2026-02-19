-- Sprint 2 Phase 1: 누락된 컬럼 추가
-- 생성일: 2026-02-19
-- 작성자: terminal-developer
--
-- 목적: Sprint 2 Phase 1 enriched content 필드 추가
-- 확인된 문제: 10개 컬럼 중 1개(cultural_context)만 존재, 9개 누락

BEGIN;

-- 1. description_long_ko
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS description_long_ko TEXT DEFAULT NULL;

-- 2. description_long_en
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS description_long_en TEXT DEFAULT NULL;

-- 3. regional_variants (JSONB)
-- 구조: [{"region": "전라도", "differences": "...", "local_name": "..."}]
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS regional_variants JSONB DEFAULT NULL;

-- 4. preparation_steps (JSONB)
-- 구조: {"steps": [...], "serving_suggestions": [...], "etiquette": [...]}
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS preparation_steps JSONB DEFAULT NULL;

-- 5. nutrition_detail (JSONB)
-- 구조: {"calories": 500, "protein": 20, "carbs": 70, "fat": 15, "sodium": 0, "serving_size": "1인분"}
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS nutrition_detail JSONB DEFAULT NULL;

-- 6. flavor_profile (JSONB)
-- 구조: {"primary": [...], "balance": {"sweet": 1, "salty": 3, "sour": 0, "bitter": 0, "umami": 4}}
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS flavor_profile JSONB DEFAULT NULL;

-- 7. visitor_tips (JSONB)
-- 구조: {"common_mistakes": [...], "ordering_tips": [...], "pairing": [...], "eating_method": "..."}
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS visitor_tips JSONB DEFAULT NULL;

-- 8. similar_dishes (JSONB[])
-- 구조: [{"name_ko": "...", "name_en": "...", "similarity_reason": "...", "difference": "..."}]
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS similar_dishes JSONB[] DEFAULT NULL;

-- 9. content_completeness (NUMERIC(5,2))
-- 콘텐츠 완성도 점수 (0-100)
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS content_completeness NUMERIC(5, 2) DEFAULT 0.00;

-- 10. cultural_context는 이미 존재 (확인됨)
-- 별도 추가 불필요

-- 인덱스 추가 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_canonical_completeness
ON canonical_menus(content_completeness DESC);

CREATE INDEX IF NOT EXISTS idx_canonical_regional_variants
ON canonical_menus USING GIN(regional_variants);

CREATE INDEX IF NOT EXISTS idx_canonical_flavor_profile
ON canonical_menus USING GIN(flavor_profile);

COMMIT;

-- 검증 쿼리
SELECT
    'Sprint 2 Phase 1 마이그레이션 완료' AS status,
    COUNT(*) FILTER (WHERE description_long_ko IS NOT NULL) AS has_long_desc_ko,
    COUNT(*) FILTER (WHERE regional_variants IS NOT NULL) AS has_variants,
    COUNT(*) FILTER (WHERE content_completeness > 0) AS has_completeness,
    COUNT(*) AS total_menus
FROM canonical_menus;
