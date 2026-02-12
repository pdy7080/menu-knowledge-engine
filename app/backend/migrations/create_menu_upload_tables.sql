-- Migration: Create Menu Upload Tables (Sprint 4 Task 1.2)
-- Date: 2026-02-12
-- Purpose: B2B menu batch upload tracking

-- ===========================
-- 1. Create ENUM Types
-- ===========================

CREATE TYPE uploadstatus AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed'
);

CREATE TYPE menuitemstatus AS ENUM (
    'success',
    'failed',
    'skipped'
);

-- ===========================
-- 2. Create menu_upload_tasks Table
-- ===========================

CREATE TABLE IF NOT EXISTS menu_upload_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Restaurant 연결
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,

    -- 파일 정보
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_type VARCHAR(10),

    -- 통계
    total_menus INTEGER DEFAULT 0,
    successful INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0,

    -- 상태
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- 에러 로그
    error_log TEXT,

    -- 메타데이터
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ===========================
-- 3. Create menu_upload_details Table
-- ===========================

CREATE TABLE IF NOT EXISTS menu_upload_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Upload Task 연결
    upload_task_id UUID NOT NULL REFERENCES menu_upload_tasks(id) ON DELETE CASCADE,

    -- 메뉴 데이터
    name_ko VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    description_en TEXT,
    price INTEGER,

    -- 상태
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    error_message TEXT,

    -- 생성된 메뉴 ID
    created_menu_id UUID,

    -- 메타데이터
    row_number INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- 4. Create Indexes
-- ===========================

-- menu_upload_tasks 인덱스
CREATE INDEX IF NOT EXISTS idx_menu_upload_tasks_restaurant
ON menu_upload_tasks(restaurant_id);

CREATE INDEX IF NOT EXISTS idx_menu_upload_tasks_status_created
ON menu_upload_tasks(status, created_at DESC);

-- menu_upload_details 인덱스
CREATE INDEX IF NOT EXISTS idx_menu_upload_details_task
ON menu_upload_details(upload_task_id);

CREATE INDEX IF NOT EXISTS idx_menu_upload_details_status
ON menu_upload_details(status);

-- ===========================
-- 5. Column Documentation
-- ===========================

COMMENT ON TABLE menu_upload_tasks IS 'B2B 메뉴 일괄 업로드 작업 추적';
COMMENT ON TABLE menu_upload_details IS '개별 메뉴 업로드 상세';

-- menu_upload_tasks
COMMENT ON COLUMN menu_upload_tasks.id IS '업로드 작업 ID';
COMMENT ON COLUMN menu_upload_tasks.restaurant_id IS '식당 ID (FK)';
COMMENT ON COLUMN menu_upload_tasks.file_name IS '업로드 파일명';
COMMENT ON COLUMN menu_upload_tasks.file_type IS '파일 타입 (csv, json)';
COMMENT ON COLUMN menu_upload_tasks.total_menus IS '전체 메뉴 수';
COMMENT ON COLUMN menu_upload_tasks.successful IS '성공 수';
COMMENT ON COLUMN menu_upload_tasks.failed IS '실패 수';
COMMENT ON COLUMN menu_upload_tasks.skipped IS '중복으로 건너뛴 수';
COMMENT ON COLUMN menu_upload_tasks.status IS '작업 상태';
COMMENT ON COLUMN menu_upload_tasks.error_log IS '에러 로그 (JSON)';

-- menu_upload_details
COMMENT ON COLUMN menu_upload_details.upload_task_id IS '업로드 작업 ID (FK)';
COMMENT ON COLUMN menu_upload_details.name_ko IS '메뉴명 (한글)';
COMMENT ON COLUMN menu_upload_details.status IS '처리 상태 (success, failed, skipped)';
COMMENT ON COLUMN menu_upload_details.created_menu_id IS '생성된 메뉴 ID';
COMMENT ON COLUMN menu_upload_details.row_number IS 'CSV/JSON 행 번호';

-- ===========================
-- 6. Performance Optimization
-- ===========================

ANALYZE menu_upload_tasks;
ANALYZE menu_upload_details;

-- ===========================
-- 7. Verification
-- ===========================

SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN ('menu_upload_tasks', 'menu_upload_details')
ORDER BY table_name, ordinal_position;
