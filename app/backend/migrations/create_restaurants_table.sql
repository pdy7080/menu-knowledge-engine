-- Migration: Create Restaurants Table (Sprint 4 Task 1.1)
-- Date: 2026-02-12
-- Purpose: B2B restaurant registration and management

-- ===========================
-- 1. Create ENUM Type
-- ===========================

CREATE TYPE restaurantstatus AS ENUM (
    'pending_approval',
    'active',
    'inactive',
    'rejected'
);

-- ===========================
-- 2. Create Restaurants Table
-- ===========================

CREATE TABLE IF NOT EXISTS restaurants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic Information
    name VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),

    -- Owner Information
    owner_name VARCHAR(100) NOT NULL,
    owner_phone VARCHAR(20) NOT NULL,
    owner_email VARCHAR(100),

    -- Address
    address VARCHAR(500) NOT NULL,
    address_detail VARCHAR(200),
    postal_code VARCHAR(10),

    -- Business Information
    business_license VARCHAR(50) UNIQUE NOT NULL,
    business_type VARCHAR(50),

    -- Status Management
    status restaurantstatus NOT NULL DEFAULT 'pending_approval',

    -- Approval Information
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by VARCHAR(100),
    rejection_reason VARCHAR(500),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- ===========================
-- 2. Create Indexes
-- ===========================

-- Index for business license uniqueness (already enforced by UNIQUE constraint)
CREATE INDEX IF NOT EXISTS idx_restaurants_business_license
ON restaurants(business_license);

-- Index for status filtering (admin queue)
CREATE INDEX IF NOT EXISTS idx_restaurants_status
ON restaurants(status);

-- Index for status + created_at (admin queue sorting)
CREATE INDEX IF NOT EXISTS idx_restaurants_status_created
ON restaurants(status, created_at DESC);

-- Index for approved restaurants
CREATE INDEX IF NOT EXISTS idx_restaurants_approved
ON restaurants(approved_at) WHERE status = 'active';

-- ===========================
-- 3. Column Documentation
-- ===========================

COMMENT ON TABLE restaurants IS 'B2B 식당 등록 및 관리';

-- Basic Information
COMMENT ON COLUMN restaurants.id IS '식당 고유 ID (UUID)';
COMMENT ON COLUMN restaurants.name IS '식당명 (한글)';
COMMENT ON COLUMN restaurants.name_en IS '식당명 (영문)';

-- Owner Information
COMMENT ON COLUMN restaurants.owner_name IS '사장님 성함';
COMMENT ON COLUMN restaurants.owner_phone IS '사장님 연락처';
COMMENT ON COLUMN restaurants.owner_email IS '사장님 이메일';

-- Address
COMMENT ON COLUMN restaurants.address IS '기본 주소';
COMMENT ON COLUMN restaurants.address_detail IS '상세 주소';
COMMENT ON COLUMN restaurants.postal_code IS '우편번호';

-- Business Information
COMMENT ON COLUMN restaurants.business_license IS '사업자 등록번호 (중복 불가)';
COMMENT ON COLUMN restaurants.business_type IS '음식점 유형 (Korean, Japanese, Chinese 등)';

-- Status Management
COMMENT ON COLUMN restaurants.status IS '승인 상태 (pending_approval, active, inactive, rejected)';

-- Approval Information
COMMENT ON COLUMN restaurants.approved_at IS '승인 시각';
COMMENT ON COLUMN restaurants.approved_by IS '승인한 관리자 ID';
COMMENT ON COLUMN restaurants.rejection_reason IS '거부 사유';

-- Metadata
COMMENT ON COLUMN restaurants.created_at IS '등록 시각';
COMMENT ON COLUMN restaurants.updated_at IS '최종 수정 시각';

-- ===========================
-- 4. Performance Optimization
-- ===========================

-- Analyze table for query planner
ANALYZE restaurants;

-- ===========================
-- 5. Verification
-- ===========================

-- Verify table creation
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'restaurants'
ORDER BY ordinal_position;

-- Verify indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'restaurants';

-- Expected indexes:
-- 1. restaurants_pkey (PRIMARY KEY on id)
-- 2. restaurants_business_license_key (UNIQUE on business_license)
-- 3. idx_restaurants_business_license
-- 4. idx_restaurants_status
-- 5. idx_restaurants_status_created
-- 6. idx_restaurants_approved
