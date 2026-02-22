"""
공공데이터 일괄 임포트 스크립트
DB의 canonical_menus에 공공데이터 (표준코드, 분류, 영양정보) 적용

실행: python scripts/ingest_public_data.py
옵션:
  --limit N    처리할 메뉴 수 (기본: 전체)
  --dry-run    실제 DB 업데이트 없이 테스트
  --force      이미 영양정보가 있는 메뉴도 재처리

Author: Claude (Senior Developer)
Date: 2026-02-19
"""

import sys
import io
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Windows UTF-8 인코딩 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Path 설정
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import select, update
from database import AsyncSessionLocal
from models.canonical_menu import CanonicalMenu
from services.public_data_client import PublicDataClient
from services.normalize import generate_search_variants


async def ingest_public_data(
    limit: int = 0, dry_run: bool = False, force: bool = False
):
    """공공데이터 일괄 임포트"""
    print("[START] 공공데이터 일괄 임포트")
    print(f"[TIME] {datetime.now().isoformat()}")
    print(f"[OPTIONS] limit={limit or 'ALL'}, dry_run={dry_run}, force={force}")
    print("-" * 60)

    client = PublicDataClient()

    async with AsyncSessionLocal() as session:
        # 메뉴 목록 조회
        query = select(CanonicalMenu).order_by(CanonicalMenu.name_ko)

        if not force:
            # 영양정보가 없는 메뉴만 대상
            query = query.where(
                (CanonicalMenu.nutrition_info == None)
                | (CanonicalMenu.nutrition_info == {})
            )

        if limit > 0:
            query = query.limit(limit)

        result = await session.execute(query)
        menus = result.scalars().all()

        print(f"[INFO] 대상 메뉴: {len(menus)}개\n")

        success = 0
        failed = 0
        skipped = 0
        failed_names = []

        for idx, menu in enumerate(menus, 1):
            print(f"[{idx:3d}/{len(menus)}] {menu.name_ko}...", end=" ", flush=True)

            # 메뉴명 변형 생성
            variants = generate_search_variants(menu.name_ko)

            # 각 변형으로 검색 시도
            enriched = None
            for variant in variants:
                try:
                    enriched = await client.enrich_menu(variant)
                    if enriched and (
                        enriched.get("nutrition_info") or enriched.get("standard_code")
                    ):
                        break
                except Exception as e:
                    print(f"\n  [WARN] API error for '{variant}': {e}")
                    continue

            if not enriched or (
                not enriched.get("nutrition_info") and not enriched.get("standard_code")
            ):
                failed += 1
                failed_names.append(menu.name_ko)
                print("X (no data)")
                continue

            if dry_run:
                print(f"OK (dry-run) code={enriched.get('standard_code')}")
                success += 1
                continue

            # DB 업데이트
            try:
                now = datetime.now(timezone.utc)
                update_values = {}

                if enriched.get("standard_code"):
                    update_values["standard_code"] = enriched["standard_code"]
                if enriched.get("category_1"):
                    update_values["category_1"] = enriched["category_1"]
                if enriched.get("category_2"):
                    update_values["category_2"] = enriched["category_2"]
                if enriched.get("serving_size"):
                    update_values["serving_size"] = enriched["serving_size"]
                if enriched.get("nutrition_info"):
                    update_values["nutrition_info"] = enriched["nutrition_info"]
                    update_values["last_nutrition_updated"] = now

                if update_values:
                    await session.execute(
                        update(CanonicalMenu)
                        .where(CanonicalMenu.id == menu.id)
                        .values(**update_values)
                    )
                    await session.commit()
                    success += 1
                    print(f"OK code={enriched.get('standard_code', 'N/A')}")
                else:
                    skipped += 1
                    print("SKIP (no update)")

            except Exception as e:
                failed += 1
                failed_names.append(menu.name_ko)
                print(f"ERROR ({e})")
                await session.rollback()

            # 10개마다 진행 상황 출력
            if idx % 10 == 0:
                print(
                    f"\n  [PROGRESS] {idx}/{len(menus)} - OK:{success} FAIL:{failed} SKIP:{skipped}\n"
                )

            # Rate limiting (공공데이터 API 1000건/일 제한 대비)
            await asyncio.sleep(0.5)

    print("-" * 60)
    print("[COMPLETE] 처리 완료")
    print(f"[RESULT] OK={success}, FAIL={failed}, SKIP={skipped}")
    if failed_names:
        print(
            f"[FAILED] {', '.join(failed_names[:10])}{'...' if len(failed_names) > 10 else ''}"
        )
    print(f"[TIME] {datetime.now().isoformat()}")


def main():
    parser = argparse.ArgumentParser(description="공공데이터 일괄 임포트")
    parser.add_argument("--limit", type=int, default=0, help="처리할 메뉴 수 (0=전체)")
    parser.add_argument(
        "--dry-run", action="store_true", help="테스트 모드 (DB 변경 없음)"
    )
    parser.add_argument(
        "--force", action="store_true", help="이미 데이터 있는 메뉴도 재처리"
    )
    args = parser.parse_args()

    asyncio.run(
        ingest_public_data(
            limit=args.limit,
            dry_run=args.dry_run,
            force=args.force,
        )
    )


if __name__ == "__main__":
    main()
