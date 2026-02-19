"""
고속도로 휴게소 음식 메뉴 전체 수집 + 분석
7,009개 메뉴 → 고유 음식명 추출 → JSON 저장

Author: Claude (Senior Developer)
Date: 2026-02-19
"""
import sys
import io
import asyncio
import httpx
import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv
import os
load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("PUBLIC_DATA_API_KEY", "")
BASE_URL = "https://data.ex.co.kr/openapi/restinfo/restBestfoodList"
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def clean_food_name(name: str) -> str:
    """음식명 정규화 (휴게소 메뉴 특수 패턴 처리)"""
    s = name.strip()

    # 특수문자 접두사 제거: ★, ※, ◎
    s = re.sub(r'^[★※◎●◆▶▷\s]+', '', s)

    # 언더스코어 분리: "라면_EX라면" → "EX라면"
    if '_' in s:
        parts = s.split('_')
        s = parts[-1]  # 마지막 부분 사용

    # 괄호 접두사 제거: "(실속)바지락미역국" → "바지락미역국"
    s = re.sub(r'^\([^)]+\)\s*', '', s)

    # 꼬리 괄호 제거: "순두부찌개(매운)" → "순두부찌개"
    s = re.sub(r'\([^)]+\)$', '', s)

    # 공백 정리
    s = re.sub(r'\s+', ' ', s).strip()

    return s


async def fetch_all_pages() -> list:
    """전체 페이지 수집"""
    all_items = []
    page = 1
    per_page = 100

    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            params = {
                "key": API_KEY,
                "type": "json",
                "numOfRows": per_page,
                "pageNo": page,
            }

            response = await client.get(BASE_URL, params=params)
            if response.status_code != 200:
                print(f"  [ERROR] Page {page}: HTTP {response.status_code}")
                break

            data = response.json()
            if data.get("code") != "SUCCESS":
                print(f"  [ERROR] Page {page}: {data.get('message')}")
                break

            items = data.get("list", [])
            if not items:
                break

            all_items.extend(items)
            total = data.get("count", 0)

            if page % 10 == 0 or page == 1:
                print(f"  [Page {page:3d}] {len(all_items):,}/{total:,}개 수집됨")

            if len(all_items) >= total:
                break

            page += 1
            await asyncio.sleep(0.3)

    return all_items


async def main():
    print("=" * 60)
    print("고속도로 휴게소 음식 메뉴 전체 수집")
    print(f"시간: {datetime.now().isoformat()}")
    print("=" * 60)

    # 1. 전체 데이터 수집
    print("\n[1] 전체 데이터 수집 중...")
    items = await fetch_all_pages()
    print(f"  수집 완료: {len(items):,}개")

    # 2. 전체 데이터 저장 (raw)
    OUTPUT_DIR.mkdir(exist_ok=True)
    raw_file = OUTPUT_DIR / "highway_food_raw.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {raw_file.name} ({len(items):,}건)")

    # 3. 고유 음식명 추출 + 정규화
    print(f"\n[2] 고유 음식명 추출 및 정규화")
    print("-" * 40)

    food_counter = Counter()
    food_details = {}

    for item in items:
        raw_name = item.get("foodNm", "").strip()
        if not raw_name:
            continue

        clean_name = clean_food_name(raw_name)
        if not clean_name or len(clean_name) < 2:
            continue

        food_counter[clean_name] += 1

        # 가격 정보 누적
        if clean_name not in food_details:
            food_details[clean_name] = {
                "name_ko": clean_name,
                "raw_names": [],
                "prices": [],
                "rest_areas": set(),
                "routes": set(),
                "is_best": False,
                "is_recommend": False,
                "is_premium": False,
            }

        detail = food_details[clean_name]
        if raw_name not in detail["raw_names"]:
            detail["raw_names"].append(raw_name)

        try:
            price = int(item.get("foodCost", "0"))
            if price > 0:
                detail["prices"].append(price)
        except ValueError:
            pass

        detail["rest_areas"].add(item.get("stdRestNm", ""))
        detail["routes"].add(item.get("routeNm", ""))

        if item.get("bestfoodyn") == "Y":
            detail["is_best"] = True
        if item.get("recommendyn") == "Y":
            detail["is_recommend"] = True
        if item.get("premiumyn") == "Y":
            detail["is_premium"] = True

    unique_foods = len(food_counter)
    print(f"  고유 음식명: {unique_foods}개")
    print(f"  가장 많은 메뉴 (전국 인기):")
    for name, count in food_counter.most_common(15):
        detail = food_details[name]
        avg_price = sum(detail["prices"]) // len(detail["prices"]) if detail["prices"] else 0
        rest_count = len(detail["rest_areas"])
        flags = ""
        if detail["is_best"]:
            flags += "[BEST]"
        if detail["is_recommend"]:
            flags += "[REC]"
        if detail["is_premium"]:
            flags += "[PREM]"
        print(f"    {name:<20} {count:3d}곳 | avg {avg_price:>6,}원 | {rest_count:3d}개 휴게소 {flags}")

    # 4. 카테고리 분류
    print(f"\n[3] 카테고리 분류")
    print("-" * 40)
    categories = Counter()
    for name in food_counter:
        if any(k in name for k in ["우동", "국수", "라면", "면", "소바", "파스타", "냉면"]):
            categories["면류"] += 1
        elif any(k in name for k in ["찌개", "국", "탕", "해장"]):
            categories["국/찌개/탕"] += 1
        elif any(k in name for k in ["밥", "덮밥", "비빔", "볶음밥", "김밥"]):
            categories["밥류"] += 1
        elif any(k in name for k in ["돈까스", "돈가스", "까스", "커틀릿"]):
            categories["돈까스"] += 1
        elif any(k in name for k in ["불고기", "갈비", "삼겹", "구이", "숯불"]):
            categories["구이/고기"] += 1
        elif any(k in name for k in ["커피", "아메", "라떼", "음료", "주스", "차"]):
            categories["음료"] += 1
        elif any(k in name for k in ["빵", "호떡", "토스트", "와플"]):
            categories["빵/간식"] += 1
        elif any(k in name for k in ["떡볶이", "순대", "튀김", "어묵"]):
            categories["분식"] += 1
        else:
            categories["기타"] += 1

    for cat, count in categories.most_common():
        print(f"  {cat:<15} {count:4d}개 ({count/unique_foods*100:.1f}%)")

    # 5. canonical_menus 시드 데이터 생성
    print(f"\n[4] canonical_menus 시드 데이터 생성")
    print("-" * 40)

    # 3곳 이상 휴게소에서 판매하는 메뉴만 (보편적 메뉴)
    canonical_candidates = []
    for name, count in food_counter.most_common():
        detail = food_details[name]
        rest_count = len(detail["rest_areas"])

        if rest_count >= 3 and len(name) >= 2:
            avg_price = sum(detail["prices"]) // len(detail["prices"]) if detail["prices"] else 0
            min_price = min(detail["prices"]) if detail["prices"] else 0
            max_price = max(detail["prices"]) if detail["prices"] else 0

            canonical_candidates.append({
                "name_ko": name,
                "occurrence_count": count,
                "rest_area_count": rest_count,
                "avg_price": avg_price,
                "min_price": min_price,
                "max_price": max_price,
                "routes": sorted(r for r in detail["routes"] if r),
                "is_best": detail["is_best"],
                "is_recommend": detail["is_recommend"],
                "raw_names": detail["raw_names"][:3],
            })

    print(f"  3곳 이상 판매 메뉴: {len(canonical_candidates)}개 (전체 {unique_foods}개 중)")

    # 시드 데이터 저장
    seed_file = OUTPUT_DIR / "highway_food_canonical_candidates.json"
    with open(seed_file, 'w', encoding='utf-8') as f:
        json.dump(canonical_candidates, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {seed_file.name}")

    # 6. 전체 고유 음식 목록 저장
    all_unique_file = OUTPUT_DIR / "highway_food_unique_names.json"
    unique_list = [
        {
            "name_ko": name,
            "count": count,
            "rest_area_count": len(food_details[name]["rest_areas"]),
            "avg_price": sum(food_details[name]["prices"]) // len(food_details[name]["prices"]) if food_details[name]["prices"] else 0,
        }
        for name, count in food_counter.most_common()
    ]
    with open(all_unique_file, 'w', encoding='utf-8') as f:
        json.dump(unique_list, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {all_unique_file.name} ({len(unique_list)}개)")

    # 7. 통계 요약
    print(f"\n[5] 최종 통계")
    print("=" * 60)
    print(f"  총 수집 메뉴: {len(items):,}개")
    print(f"  고유 음식명: {unique_foods}개")
    print(f"  canonical 후보 (3곳+): {len(canonical_candidates)}개")
    print(f"  휴게소 수: {len(set(item.get('stdRestNm', '') for item in items))}곳")
    print(f"  노선 수: {len(set(item.get('routeNm', '') for item in items))}개")
    print(f"  저장 파일:")
    print(f"    - {raw_file.name} (전체 raw 데이터)")
    print(f"    - {seed_file.name} (canonical 후보)")
    print(f"    - {all_unique_file.name} (고유 음식명)")
    print(f"  시간: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
