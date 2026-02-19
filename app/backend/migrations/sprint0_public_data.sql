-- Sprint 0: 공공데이터 연동 필드 추가
-- Target: FastComet PostgreSQL 16
-- Date: 2026-02-19
-- Author: Claude (Senior Developer)

-- 1. canonical_menus 테이블에 공공데이터 필드 추가
ALTER TABLE canonical_menus
    ADD COLUMN IF NOT EXISTS standard_code VARCHAR(10),
    ADD COLUMN IF NOT EXISTS category_1 VARCHAR(50),
    ADD COLUMN IF NOT EXISTS category_2 VARCHAR(50),
    ADD COLUMN IF NOT EXISTS serving_size VARCHAR(20),
    ADD COLUMN IF NOT EXISTS nutrition_info JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS last_nutrition_updated TIMESTAMPTZ;

-- 2. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_cm_standard_code ON canonical_menus(standard_code);
CREATE INDEX IF NOT EXISTS idx_cm_category ON canonical_menus(category_1, category_2);

-- 3. 검증
DO $$
BEGIN
    RAISE NOTICE 'Sprint 0 migration completed successfully';
    RAISE NOTICE 'Added columns: standard_code, category_1, category_2, serving_size, nutrition_info, last_nutrition_updated';
END $$;
