"""
DB에 Sprint 2 Phase 1 컬럼이 존재하는지 확인
"""
import asyncio
from sqlalchemy import text
import sys
from pathlib import Path

# Path 설정
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "app" / "backend"))

from database import engine


async def check_columns():
    """Sprint 2 Phase 1 컬럼 존재 여부 확인"""
    columns_to_check = [
        'description_long_ko',
        'description_long_en',
        'regional_variants',
        'preparation_steps',
        'nutrition_detail',
        'flavor_profile',
        'visitor_tips',
        'similar_dishes',
        'cultural_context',
        'content_completeness'
    ]

    # IN 절을 문자열로 직접 구성
    col_list = "', '".join(columns_to_check)
    query = text(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'canonical_menus'
        AND column_name IN ('{col_list}')
        ORDER BY column_name
    """)

    async with engine.begin() as conn:
        result = await conn.execute(query)
        existing = [row[0] for row in result]

    print("=" * 60)
    print("Sprint 2 Phase 1 컬럼 확인")
    print("=" * 60)
    print(f"\n확인할 컬럼 수: {len(columns_to_check)}")
    print(f"존재하는 컬럼 수: {len(existing)}")
    print(f"\n존재하는 컬럼:")
    for col in existing:
        print(f"  ✅ {col}")

    missing = set(columns_to_check) - set(existing)
    if missing:
        print(f"\n누락된 컬럼:")
        for col in sorted(missing):
            print(f"  ❌ {col}")

    return len(existing) == len(columns_to_check)


if __name__ == "__main__":
    result = asyncio.run(check_columns())
    sys.exit(0 if result else 1)
