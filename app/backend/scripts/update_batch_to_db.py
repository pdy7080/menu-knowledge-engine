"""
Sprint 2 Phase 2 P1: Batch enriched content를 DB에 업데이트
2026-02-19

enriched_batch_N.json 파일을 읽어서 DB에 업데이트
"""
import json
import sys
from pathlib import Path
import argparse
import asyncio
from uuid import UUID

# Path 설정
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from database import AsyncSessionLocal
from models.canonical_menu import CanonicalMenu
from sqlalchemy import select, update


async def update_enriched_to_db(batch_num: int):
    """Batch enriched content를 DB에 업데이트"""

    # enriched_batch_N.json 파일 읽기
    data_file = BASE_DIR.parent.parent / "data" / f"enriched_batch_{batch_num}.json"

    if not data_file.exists():
        print(f"❌ 파일 없음: {data_file}")
        return

    with open(data_file, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)

    menus = batch_data['menus']
    print(f"\nBatch {batch_num}: {len(menus)}개 메뉴 DB 업데이트")
    print("="*60)

    # DB 연결
    async with AsyncSessionLocal() as session:
        update_count = 0

        for menu_data in menus:
            menu_id = UUID(menu_data['menu_id'])
            content = menu_data['content']

            try:
                # UPDATE 쿼리 실행
                stmt = (
                    update(CanonicalMenu)
                    .where(CanonicalMenu.id == menu_id)
                    .values(
                        description_long_ko=content.get('description_ko'),
                        description_long_en=content.get('description_en'),
                        regional_variants=content.get('regional_variants', []),
                        preparation_steps=content.get('preparation_steps', []),
                        nutrition_detail=content.get('nutrition', {}),
                        flavor_profile=content.get('flavor_profile', {}),
                        visitor_tips=content.get('visitor_tips', {}),
                        similar_dishes=content.get('similar_dishes', [])
                    )
                )

                await session.execute(stmt)
                update_count += 1
                print(f"  ✅ [{update_count:2d}] {menu_data['name_ko']}")

            except Exception as e:
                print(f"  ❌ {menu_data['name_ko']}: {str(e)[:50]}")

        # 커밋
        await session.commit()

        print("="*60)
        print(f"완료: {update_count}개 메뉴 업데이트")

        # 검증
        await verify_update(session, batch_num, update_count)


async def verify_update(session, batch_num: int, expected_count: int):
    """DB 업데이트 검증"""
    print("\n검증 중...")

    # enriched content가 있는 메뉴 수 확인
    stmt = select(CanonicalMenu).where(
        CanonicalMenu.description_long_ko.is_not(None)
    )
    result = await session.execute(stmt)
    total_enriched = len(result.scalars().all())

    print(f"  - 총 enriched 메뉴: {total_enriched}개")
    print(f"  - Batch {batch_num} 업데이트: {expected_count}개")

    print("✅ DB 업데이트 완료\n")


async def main():
    parser = argparse.ArgumentParser(description='Batch enriched content를 DB에 업데이트')
    parser.add_argument('--batch', type=int, required=True, choices=[1, 2, 3],
                        help='배치 번호 (1, 2, 3)')
    args = parser.parse_args()

    print("="*60)
    print(f"Sprint 2 Phase 2 P1: Batch {args.batch} DB 업데이트")
    print("2026-02-19")
    print("="*60)

    await update_enriched_to_db(args.batch)


if __name__ == "__main__":
    asyncio.run(main())
