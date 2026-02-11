-- Migration: Add Critical ScanLog Columns (Bug #1 Fix)
-- Date: 2026-02-11
-- Purpose: Add missing columns referenced by Admin API

-- Add matching result columns
ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS menu_name_ko VARCHAR(200);
ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS confidence FLOAT;
ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS evidences JSONB;

-- Add admin review columns
ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS review_notes TEXT;

-- Add comments for documentation
COMMENT ON COLUMN scan_logs.menu_name_ko IS '인식된 메뉴명';
COMMENT ON COLUMN scan_logs.confidence IS '매칭 신뢰도 (0.0-1.0)';
COMMENT ON COLUMN scan_logs.evidences IS '매칭 상세 정보 (JSONB: decomposition, ai_called 등)';
COMMENT ON COLUMN scan_logs.reviewed_at IS '관리자 검토 시간';
COMMENT ON COLUMN scan_logs.review_notes IS '관리자 메모';
