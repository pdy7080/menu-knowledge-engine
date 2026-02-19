"""
Sprint 2 Phase 1 DB 마이그레이션 실행
"""
import asyncio
import sys
import re
from pathlib import Path

# Path 설정
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "app" / "backend"))

from database import engine
from sqlalchemy import text


async def run_migration():
    """마이그레이션 SQL 실행"""
    sql_file = BASE_DIR / "sprint2_phase1_add_columns.sql"

    print("=" * 60)
    print("Sprint 2 Phase 1 DB 마이그레이션 시작")
    print("=" * 60)
    print(f"\nSQL 파일: {sql_file}")

    # SQL 파일 읽기
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 주석 제거 (-- 로 시작하는 줄)
    lines = []
    for line in sql_content.split('\n'):
        if not line.strip().startswith('--'):
            lines.append(line)
    cleaned = '\n'.join(lines)

    # SQL 문을 세미콜론으로 분할
    statements = []
    for stmt in cleaned.split(';'):
        stmt = stmt.strip()
        # 빈 줄, BEGIN, COMMIT 제외
        if stmt and stmt not in ('BEGIN', 'COMMIT'):
            statements.append(stmt)

    print(f"  ✅ {len(statements)}개 SQL 문 로드 완료\n")

    # 각 SQL 문을 개별 실행
    async with engine.begin() as conn:
        for i, stmt in enumerate(statements, 1):
            preview = stmt.replace('\n', ' ')[:80]
            print(f"[{i}/{len(statements)}] {preview}...")

            try:
                result = await conn.execute(text(stmt))

                # SELECT 문이면 결과 출력
                if stmt.strip().upper().startswith('SELECT'):
                    rows = result.fetchall()
                    if rows:
                        print(f"  📊 결과:")
                        for row in rows:
                            print(f"      {dict(row._mapping)}")
                else:
                    print(f"  ✅ 실행 완료")

            except Exception as e:
                print(f"  ❌ 오류: {str(e)}")
                # 컬럼이 이미 존재하는 경우는 무시
                if "already exists" in str(e).lower():
                    print(f"  ℹ️  컬럼 이미 존재 - 계속 진행")
                else:
                    raise
            print()

    print("=" * 60)
    print("✅ 마이그레이션 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_migration())
