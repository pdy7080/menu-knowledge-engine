"""
한국도로공사 고속도로 휴게소 음식 메뉴 API - 상세 테스트
총 7,009개 메뉴 데이터 확인됨

Author: Claude (Senior Developer)
Date: 2026-02-19
"""

import sys
import io
import asyncio
import httpx
from pathlib import Path
from datetime import datetime
from collections import Counter

# Windows UTF-8 인코딩 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# .env에서 API 키 로드
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("PUBLIC_DATA_API_KEY", "")
BASE_URL = "https://data.ex.co.kr/openapi/restinfo/restBestfoodList"


async def fetch_page(page: int, per_page: int = 100) -> dict:
    """한 페이지 조회"""
    params = {
        "key": API_KEY,
        "type": "json",
        "numOfRows": per_page,
        "pageNo": page,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(BASE_URL, params=params)
        if response.status_code == 200:
            return response.json()
        return None


async def main():
    print("=" * 60)
    print("고속도로 휴게소 음식 메뉴 API - 데이터 분석")
    print(f"시간: {datetime.now().isoformat()}")
    print("=" * 60)

    # 1. 첫 페이지로 총 건수 확인
    print("\n[1] 데이터 규모 확인...")
    data = await fetch_page(1, 100)
    if not data or data.get("code") != "SUCCESS":
        print(f"  ERROR: {data}")
        return

    total = data.get("count", 0)
    print(f"  총 메뉴 수: {total:,}개")
    print(f"  메시지: {data.get('message')}")

    # 2. 처음 100개 메뉴 분석
    items = data.get("list", [])
    print(f"\n[2] 처음 {len(items)}개 메뉴 분석")
    print("-" * 40)

    # 음식명 분석
    food_names = [item.get("foodNm", "") for item in items]
    print(f"  고유 음식명: {len(set(food_names))}개")

    # 가격 분석
    prices = []
    for item in items:
        try:
            p = int(item.get("foodCost", "0"))
            if p > 0:
                prices.append(p)
        except ValueError:
            pass

    if prices:
        print(f"  가격 범위: {min(prices):,}원 ~ {max(prices):,}원")
        print(f"  평균 가격: {sum(prices)//len(prices):,}원")

    # 추천/베스트 메뉴
    recommend = sum(1 for item in items if item.get("recommendyn") == "Y")
    best = sum(1 for item in items if item.get("bestfoodyn") == "Y")
    premium = sum(1 for item in items if item.get("premiumyn") == "Y")
    print(f"  추천 메뉴: {recommend}개")
    print(f"  베스트 메뉴: {best}개")
    print(f"  프리미엄: {premium}개")

    # 휴게소 분석
    rest_areas = set(item.get("stdRestNm", "") for item in items)
    routes = Counter(item.get("routeNm", "") for item in items)
    print(f"  휴게소: {len(rest_areas)}곳")
    print(f"  노선: {dict(routes.most_common(5))}")

    # 3. 샘플 메뉴 출력
    print("\n[3] 샘플 메뉴 (처음 20개)")
    print("-" * 40)
    print(f"  {'음식명':<20} {'가격':>8} {'휴게소':<25} {'노선':<10}")
    print(f"  {'-'*20} {'-'*8} {'-'*25} {'-'*10}")

    for item in items[:20]:
        name = item.get("foodNm", "N/A")[:18]
        price = item.get("foodCost", "N/A")
        rest = item.get("stdRestNm", "N/A")[:23]
        route = item.get("routeNm", "N/A")[:8]
        print(f"  {name:<20} {price:>8} {rest:<25} {route:<10}")

    # 4. 2페이지도 가져와서 더 다양한 메뉴 확인
    print("\n[4] 2페이지 추가 확인...")
    data2 = await fetch_page(2, 100)
    if data2 and data2.get("code") == "SUCCESS":
        items2 = data2.get("list", [])
        # 1+2페이지 합쳐서 고유 음식명 분석
        all_items = items + items2
        all_food_names = set(item.get("foodNm", "") for item in all_items)
        print(f"  200개 중 고유 음식명: {len(all_food_names)}개")

        # 음식 카테고리 추정 (이름 기반)
        categories = Counter()
        for name in all_food_names:
            if any(k in name for k in ["우동", "국수", "라면", "면"]):
                categories["면류"] += 1
            elif any(k in name for k in ["찌개", "국", "탕"]):
                categories["국/찌개"] += 1
            elif any(k in name for k in ["밥", "덮밥", "비빔"]):
                categories["밥류"] += 1
            elif any(k in name for k in ["돈까스", "커틀릿"]):
                categories["돈까스"] += 1
            elif any(k in name for k in ["커피", "음료", "주스", "차"]):
                categories["음료"] += 1
            elif any(k in name for k in ["빵", "호떡", "토스트"]):
                categories["빵/간식"] += 1
            else:
                categories["기타"] += 1

        print(f"  카테고리 분포: {dict(categories.most_common(10))}")

    # 5. 전체 데이터 수집 가능성 분석
    print("\n[5] 전체 데이터 수집 분석")
    print("-" * 40)
    pages_needed = (total + 99) // 100
    print(f"  총 메뉴: {total:,}개")
    print(f"  필요 페이지: {pages_needed}페이지 (100개/페이지)")
    print(f"  예상 수집 시간: ~{pages_needed * 0.5:.0f}초 (0.5초/페이지)")
    print("  활용: canonical_menus 시드 데이터 + 가격 정보 + 휴게소 메뉴 매핑")

    print("\n" + "=" * 60)
    print("분석 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
