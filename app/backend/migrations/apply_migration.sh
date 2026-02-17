#!/bin/bash
# Task #4: 브랜드명 패턴 50개 추가 마이그레이션
# FastComet 서버에서 실행할 스크립트

set -e

echo "=================================================="
echo "Task #4: 브랜드명 패턴 50개 추가"
echo "=================================================="
echo ""

# 데이터베이스 정보
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="chargeap_menu_knowledge"
DB_USER="chargeap_dcclab2022"
DB_PASS="eromlab!1228"

# 마이그레이션 파일
MIGRATION_FILE="/home/chargeap/menu-knowledge/app/backend/migrations/add_brand_names_20260218.sql"

echo "🔍 마이그레이션 파일 확인: $MIGRATION_FILE"
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ 파일을 찾을 수 없습니다: $MIGRATION_FILE"
    exit 1
fi

echo "✅ 파일 존재 확인"
echo ""

# PostgreSQL 연결 테스트
echo "🔗 데이터베이스 연결 테스트..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 데이터베이스 연결 성공"
else
    echo "❌ 데이터베이스 연결 실패"
    exit 1
fi

echo ""
echo "⚙️  마이그레이션 실행 중..."
echo ""

# SQL 마이그레이션 실행
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 마이그레이션 완료!"
else
    echo ""
    echo "❌ 마이그레이션 실패!"
    exit 1
fi

echo ""
echo "🔍 검증 중..."
echo ""

# 1. 전체 modifier 개수 확인
echo "📊 현재 Modifier 총 개수:"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) as total FROM modifiers;"

echo ""
echo "📊 emotion 타입 Modifier 개수:"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) as emotion_count FROM modifiers WHERE type = 'emotion';"

echo ""
echo "✅ '고씨네' 확인 (TC-10용):"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT text_ko, type, priority FROM modifiers WHERE text_ko = '고씨네';"

echo ""
echo "✅ '할머니' 확인 (TC-02용):"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT text_ko, type, priority FROM modifiers WHERE text_ko = '할머니';"

echo ""
echo "📋 최근 추가된 emotion 항목 (상위 10개):"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT text_ko, semantic_key FROM modifiers WHERE type = 'emotion' ORDER BY created_at DESC LIMIT 10;"

echo ""
echo "=================================================="
echo "🎉 마이그레이션 성공!"
echo "=================================================="
