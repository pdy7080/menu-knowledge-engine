"""
canonical_menus 169개에 식품영양성분 정보 자동 매핑
data.go.kr API를 사용하여 각 메뉴의 영양정보를 조회하고 시드 데이터에 추가

사용법:
  python scripts/enrich_canonical_nutrition.py              # 전체 실행
  python scripts/enrich_canonical_nutrition.py --dry-run    # 테스트 (API 호출만, 저장 안함)
  python scripts/enrich_canonical_nutrition.py --limit 10   # 10개만 처리

Author: Claude (Senior Developer)
Date: 2026-02-19
"""
import sys
import io
import asyncio
import httpx
import json
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv
import os
load_dotenv(Path(__file__).parent.parent / ".env")

DATA_GO_KR_KEY = os.getenv("DATA_GO_KR_API_KEY", "")
DATA_DIR = Path(__file__).parent.parent / "data"

# 식품영양성분DB API
NUTRITION_API_URL = "https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02"


def parse_nutrition(item: dict) -> dict:
    """API 응답 항목에서 영양정보 추출"""
    def safe_float(val):
        if val is None or val == "" or val == "-":
            return None
        try:
            return round(float(val), 2)
        except (ValueError, TypeError):
            return None

    return {
        "energy_kcal": safe_float(item.get("AMT_NUM1")),
        "water_g": safe_float(item.get("AMT_NUM2")),
        "protein_g": safe_float(item.get("AMT_NUM3")),
        "fat_g": safe_float(item.get("AMT_NUM4")),
        "ash_g": safe_float(item.get("AMT_NUM5")),
        "carbohydrate_g": safe_float(item.get("AMT_NUM7")),
        "fiber_g": safe_float(item.get("AMT_NUM8")),
        "calcium_mg": safe_float(item.get("AMT_NUM9")),
        "iron_mg": safe_float(item.get("AMT_NUM10")),
        "phosphorus_mg": safe_float(item.get("AMT_NUM11")),
        "potassium_mg": safe_float(item.get("AMT_NUM14")),
        "sodium_mg": safe_float(item.get("AMT_NUM13")),
        "vitamin_a_ug": safe_float(item.get("AMT_NUM15")),
        "vitamin_c_mg": safe_float(item.get("AMT_NUM18")),
        "cholesterol_mg": safe_float(item.get("AMT_NUM24")),
        "saturated_fat_g": safe_float(item.get("AMT_NUM25")),
    }


async def search_nutrition(client: httpx.AsyncClient, food_name: str) -> dict | None:
    """API에서 음식명으로 영양정보 검색"""
    # 직접 검색
    result = await _fetch_nutrition(client, food_name)
    if result:
        return result

    # 검색어 변형: 마지막 글자 제거 (예: "유부우동" → "유부우동" 안 되면 "우동")
    # 일반적 매칭: 핵심 키워드로 재검색
    base_words = _extract_base_word(food_name)
    if base_words and base_words != food_name:
        result = await _fetch_nutrition(client, base_words)
        if result:
            return result

    return None


async def _fetch_nutrition(client: httpx.AsyncClient, food_name: str) -> dict | None:
    """실제 API 호출"""
    params = {
        "serviceKey": DATA_GO_KR_KEY,
        "pageNo": 1,
        "numOfRows": 5,
        "type": "json",
        "FOOD_NM_KR": food_name,
    }

    try:
        response = await client.get(NUTRITION_API_URL, params=params)
        if response.status_code != 200:
            return None

        data = response.json()

        # 응답 구조 파싱 (header+body 또는 response>header+body)
        body = data.get("body", {})
        if not body and "response" in data:
            body = data["response"].get("body", {})
        if not body and "header" in data:
            body = data.get("body", {})

        total = body.get("totalCount", 0)
        if total == 0:
            return None

        items = body.get("items", [])
        if isinstance(items, dict):
            items = items.get("item", [])
        if isinstance(items, dict):
            items = [items]
        if not items:
            return None

        # 가장 관련성 높은 항목 선택 (이름 일치도)
        best_item = items[0]
        for item in items:
            if item.get("FOOD_NM_KR", "") == food_name:
                best_item = item
                break

        return {
            "food_name_api": best_item.get("FOOD_NM_KR", ""),
            "food_code": best_item.get("FOOD_CD", ""),
            "category_1": best_item.get("FOOD_CAT1_NM", ""),
            "category_2": best_item.get("FOOD_CAT2_NM", ""),
            "serving_size": best_item.get("SERVING_SIZE", ""),
            "nutrition": parse_nutrition(best_item),
            "total_results": total,
        }

    except Exception as e:
        return None


def _extract_base_word(name: str) -> str:
    """복합 메뉴명에서 핵심 키워드 추출"""
    # 수식어 제거
    prefixes = ["왕", "특", "대", "매운", "얼큰", "해물", "치즈", "새우", "야채",
                 "등심", "돌솥", "뚝배기", "숯불", "차돌", "통", "옛날"]
    result = name
    for prefix in prefixes:
        if result.startswith(prefix) and len(result) > len(prefix) + 1:
            result = result[len(prefix):]
    return result


async def main():
    parser = argparse.ArgumentParser(description="canonical 메뉴 영양정보 매핑")
    parser.add_argument("--dry-run", action="store_true", help="API 호출만, 저장 안함")
    parser.add_argument("--limit", type=int, default=0, help="처리할 메뉴 수 제한")
    args = parser.parse_args()

    print("=" * 60)
    print("canonical_menus 영양정보 자동 매핑")
    print(f"시간: {datetime.now().isoformat()}")
    print(f"API 키: {DATA_GO_KR_KEY[:10]}...{DATA_GO_KR_KEY[-10:]}" if len(DATA_GO_KR_KEY) > 20 else f"API 키: {DATA_GO_KR_KEY}")
    print(f"모드: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("=" * 60)

    if not DATA_GO_KR_KEY:
        print("\n[ERROR] DATA_GO_KR_API_KEY가 .env에 설정되지 않았습니다.")
        print("  → data.go.kr에서 식품영양성분DB API 활용신청 후 인증키를 .env에 추가하세요.")
        return

    # 1. canonical 시드 데이터 로드
    seed_file = DATA_DIR / "canonical_seed_data.json"
    if not seed_file.exists():
        print(f"\n[ERROR] {seed_file} 파일이 없습니다. generate_canonical_seed.py를 먼저 실행하세요.")
        return

    with open(seed_file, 'r', encoding='utf-8') as f:
        seed_data = json.load(f)

    total_menus = len(seed_data)
    if args.limit > 0:
        seed_data = seed_data[:args.limit]
    print(f"\n[1] 시드 데이터: {total_menus}개 (처리 대상: {len(seed_data)}개)")

    # 2. API로 영양정보 조회
    print(f"\n[2] 영양정보 API 조회 시작...")
    print("-" * 40)

    matched = 0
    failed = 0
    errors = 0

    async with httpx.AsyncClient(timeout=15.0) as client:
        for i, menu in enumerate(seed_data, 1):
            name = menu["name_ko"]

            result = await search_nutrition(client, name)

            if result:
                matched += 1
                menu["nutrition_info"] = result["nutrition"]
                menu["serving_size"] = result["serving_size"]
                menu["food_code"] = result["food_code"]
                menu["nutrition_source"] = "data.go.kr"
                menu["nutrition_api_name"] = result["food_name_api"]

                # 카테고리 업데이트 (API 카테고리가 더 정확)
                if result["category_1"]:
                    menu["api_category_1"] = result["category_1"]
                if result["category_2"]:
                    menu["api_category_2"] = result["category_2"]

                energy = result["nutrition"].get("energy_kcal", "N/A")
                protein = result["nutrition"].get("protein_g", "N/A")
                print(f"  [{i:3d}/{len(seed_data)}] {name:<20} ✓ {result['food_name_api']} | {energy}kcal | {protein}g protein")
            else:
                failed += 1
                print(f"  [{i:3d}/{len(seed_data)}] {name:<20} ✗ 매칭 실패")

            # Rate limiting (일일 10,000건)
            await asyncio.sleep(0.3)

            # 진행률 표시
            if i % 20 == 0:
                print(f"  --- 진행: {i}/{len(seed_data)} ({matched}건 매칭, {failed}건 실패) ---")

    # 3. 결과 저장
    print(f"\n[3] 결과")
    print("=" * 40)
    print(f"  총 메뉴: {len(seed_data)}개")
    print(f"  매칭 성공: {matched}개 ({matched/len(seed_data)*100:.1f}%)")
    print(f"  매칭 실패: {failed}개")
    print(f"  에러: {errors}개")

    if not args.dry_run:
        # 영양정보 포함된 시드 데이터 저장
        enriched_file = DATA_DIR / "canonical_seed_enriched.json"
        with open(enriched_file, 'w', encoding='utf-8') as f:
            json.dump(seed_data, f, ensure_ascii=False, indent=2)
        print(f"\n  [SAVED] {enriched_file.name}")

        # 영양정보 UPDATE SQL 생성
        sql_file = Path(__file__).parent.parent / "migrations" / "sprint0_update_nutrition.sql"
        sql_lines = [
            f"-- canonical_menus 영양정보 UPDATE",
            f"-- 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"-- 매칭: {matched}/{len(seed_data)}개\n",
        ]
        for menu in seed_data:
            if "nutrition_info" in menu and menu.get("nutrition_source"):
                nutrition_json = json.dumps(menu["nutrition_info"], ensure_ascii=False)
                serving = menu.get("serving_size", "")
                sql_lines.append(
                    f"UPDATE canonical_menus SET "
                    f"nutrition_info = '{nutrition_json}'::jsonb, "
                    f"serving_size = '{serving}', "
                    f"last_nutrition_updated = NOW() "
                    f"WHERE name_ko = '{menu['name_ko']}';"
                )

        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_lines))
        print(f"  [SAVED] {sql_file.name}")
    else:
        print("\n  [DRY RUN] 파일 저장 생략")

    print(f"\n  시간: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
