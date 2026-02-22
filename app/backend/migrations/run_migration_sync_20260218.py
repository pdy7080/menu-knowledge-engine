#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #4: 브랜드명 패턴 50개 추가 마이그레이션 (동기 방식)
2026-02-18
"""
import sys
import io

# Windows에서 UTF-8 출력 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pathlib import Path
import psycopg2
import os
from dotenv import load_dotenv
from urllib.parse import urlparse


def parse_database_url(url: str):
    """PostgreSQL URL 파싱"""
    parsed = urlparse(url)

    # postgresql+asyncpg://user:pass@host:port/database
    # → host, port, user, password, database 추출
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path.lstrip("/"),
    }


def run_migration():
    """브랜드명 패턴 마이그레이션 실행"""

    # 환경변수 로드
    env_file = Path(__file__).parent.parent / ".env.production"
    if not env_file.exists():
        env_file = Path(__file__).parent.parent / ".env"

    load_dotenv(env_file)

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL 환경변수가 설정되지 않았습니다")
        return False

    # URL에서 postgresql+ 접두사 제거 (psycopg2는 postgresql://만 지원)
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    # 데이터베이스 정보 파싱
    db_config = parse_database_url(database_url)

    try:
        print("=" * 60)
        print("Task #4: 브랜드명 패턴 50개 추가")
        print("=" * 60)
        print()

        # PostgreSQL 연결
        print("🔗 데이터베이스 연결 중...")
        print(f"   Host: {db_config['host']}:{db_config['port']}")
        print(f"   Database: {db_config['database']}")

        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
        )

        cursor = conn.cursor()
        print("✅ 데이터베이스 연결 성공!")
        print()

        # SQL 마이그레이션 파일 읽기
        migration_file = Path(__file__).parent / "add_brand_names_20260218.sql"
        with open(migration_file, "r", encoding="utf-8") as f:
            sql_content = f.read()

        print("📝 마이그레이션 파일 읽기 완료")
        print(f"📄 파일: {migration_file}")
        print()

        # 마이그레이션 실행
        print("⚙️  마이그레이션 실행 중...")
        cursor.execute(sql_content)
        conn.commit()
        print("✅ 마이그레이션 완료!")
        print()

        # 검증: 추가된 데이터 확인
        print("🔍 검증 중...")

        # 1. 전체 modifier 개수 확인
        cursor.execute("SELECT COUNT(*) FROM modifiers")
        total_count = cursor.fetchone()[0]
        print(f"📊 현재 Modifier 총 개수: {total_count}개")

        # 2. emotion 타입 modifier 개수 확인
        cursor.execute("SELECT COUNT(*) FROM modifiers WHERE type = 'emotion'")
        emotion_count = cursor.fetchone()[0]
        print(f"📊 emotion 타입 Modifier: {emotion_count}개")

        # 3. "고씨네" 존재 여부 확인 (TC-10용)
        cursor.execute(
            "SELECT text_ko, type FROM modifiers WHERE text_ko = %s", ("고씨네",)
        )
        gho = cursor.fetchone()
        if gho:
            print(f"✅ '고씨네' 추가됨: type={gho[1]}")
        else:
            print("❌ '고씨네'를 찾을 수 없습니다")

        # 4. "할머니" 존재 여부 확인 (TC-02용)
        cursor.execute(
            "SELECT text_ko, type FROM modifiers WHERE text_ko = %s", ("할머니",)
        )
        grandma = cursor.fetchone()
        if grandma:
            print(f"✅ '할머니' 존재: type={grandma[1]}")
        else:
            print("❌ '할머니'를 찾을 수 없습니다")

        # 5. 최근 추가된 5개 항목 샘플
        cursor.execute(
            "SELECT text_ko, semantic_key FROM modifiers WHERE type = 'emotion' ORDER BY created_at DESC LIMIT 5"
        )
        samples = cursor.fetchall()
        print()
        print("📋 최근 추가된 emotion 항목 (상위 5개):")
        for text_ko, semantic_key in samples:
            print(f"   - {text_ko} ({semantic_key})")

        cursor.close()
        conn.close()

        print()
        print("=" * 60)
        print("🎉 마이그레이션 성공!")
        print("=" * 60)
        return True

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 마이그레이션 실패!")
        print(f"오류: {e}")
        print("=" * 60)
        if "conn" in locals():
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
