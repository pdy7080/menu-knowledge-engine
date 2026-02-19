-- Sprint 2 Phase 1: 이미지 필드 추가
-- 생성일: 2026-02-19
-- 작성자: terminal-developer
--
-- 목적: primary_image, images 필드 추가 (API 오류 수정)

BEGIN;

-- 1. primary_image (JSONB)
-- 구조: {"url": "...", "source": "...", "license": "...", "attribution": "..."}
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS primary_image JSONB DEFAULT NULL;

-- 2. images (JSONB 배열)
-- 구조: [{"url": "...", "source": "...", "license": "...", "attribution": "..."}, ...]
ALTER TABLE canonical_menus
ADD COLUMN IF NOT EXISTS images JSONB[] DEFAULT NULL;

-- 인덱스 추가 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_canonical_primary_image
ON canonical_menus USING GIN(primary_image);

CREATE INDEX IF NOT EXISTS idx_canonical_images
ON canonical_menus USING GIN(images);

COMMIT;

-- 검증 쿼리
SELECT
    'Sprint 2 Phase 1 이미지 필드 추가 완료' AS status,
    COUNT(*) FILTER (WHERE primary_image IS NOT NULL) AS has_primary_image,
    COUNT(*) FILTER (WHERE images IS NOT NULL) AS has_images,
    COUNT(*) AS total_menus
FROM canonical_menus;
