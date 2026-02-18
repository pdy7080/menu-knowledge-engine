#!/usr/bin/env python3
"""
Task #4: 브랜드명 패턴 50개 추가 마이그레이션
2026-02-18
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from dotenv import load_dotenv


async def run_migration():
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

    # PostgreSQL async engine 생성
    engine = create_async_engine(database_url, echo=False)

    try:
        # SQL 마이그레이션 파일 읽기
        migration_file = Path(__file__).parent / "add_brand_names_20260218.sql"
        with open(migration_file, "r", encoding="utf-8") as f:
            sql_content = f.read()

        print("📝 마이그레이션 파일 읽기 완료")
        print(f"📄 파일: {migration_file}")

        # 데이터베이스 연결 및 마이그레이션 실행
        async with engine.begin() as conn:
            print("🔗 데이터베이스 연결 성공")

            # 마이그레이션 실행 (BEGIN/COMMIT 포함)
            await conn.execute(text(sql_content))

            print("✅ 마이그레이션 완료!")

        # 검증: 추가된 데이터 확인
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            # 전체 modifier 개수 확인
            result = await session.execute(
                text("SELECT COUNT(*) as cnt FROM modifiers")
            )
            total_count = result.scalar()
            print(f"📊 현재 Modifier 총 개수: {total_count}개")

            # emotion 타입 modifier 개수 확인
            result = await session.execute(
                text("SELECT COUNT(*) as cnt FROM modifiers WHERE type = 'emotion'")
            )
            emotion_count = result.scalar()
            print(f"📊 emotion 타입 Modifier: {emotion_count}개")

            # "고씨네" 존재 여부 확인 (TC-10용)
            result = await session.execute(
                text("SELECT text_ko, type FROM modifiers WHERE text_ko = '고씨네'")
            )
            gho = result.first()
            if gho:
                print(f"✅ '고씨네' 추가됨: type={gho[1]}")
            else:
                print("❌ '고씨네'를 찾을 수 없습니다")

            # "할머니" 존재 여부 확인 (TC-02용)
            result = await session.execute(
                text("SELECT text_ko, type FROM modifiers WHERE text_ko = '할머니'")
            )
            grandma = result.first()
            if grandma:
                print(f"✅ '할머니' 존재: type={grandma[1]}")
            else:
                print("❌ '할머니'를 찾을 수 없습니다")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        await engine.dispose()
        return False


async def main():
    """메인 함수"""
    print("=" * 60)
    print("Task #4: 브랜드명 패턴 50개 추가")
    print("=" * 60)
    print()

    success = await run_migration()

    print()
    print("=" * 60)
    if success:
        print("🎉 마이그레이션 성공!")
        sys.exit(0)
    else:
        print("😞 마이그레이션 실패!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
