"""
공공데이터 API 연결 테스트 (DB 불필요)
3개 API를 직접 호출하여 응답 확인

Author: Claude (Senior Developer)
Date: 2026-02-19
"""
import sys
import io
import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# .env에서 API 키 로드
from dotenv import load_dotenv
import os
load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("PUBLIC_DATA_API_KEY", "")
BASE_URL = "https://apis.data.go.kr"

# 테스트 메뉴 목록
TEST_MENUS = ["김치찌개", "불고기", "비빔밥", "삼겹살", "된장찌개"]


async def test_nutrition_api(food_name: str) -> dict:
    """식품영양성분DB API 테스트 (15127578)"""
    url = f"{BASE_URL}/1471000/FoodNtrIrdntInfoService1/getFoodNtrItdntList1"
    params = {
        "serviceKey": API_KEY,
        "type": "json",
        "FOOD_NM_KR": food_name,
        "pageNo": 1,
        "numOfRows": 3,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        return {"status": response.status_code, "data": response.text[:2000]}


async def test_menuzen_api(food_name: str) -> dict:
    """메뉴젠 API 테스트 (15101046)"""
    url = f"{BASE_URL}/1471000/FoodNtrCpService/getFoodNtrCpInfo"
    params = {
        "serviceKey": API_KEY,
        "type": "json",
        "food_name": food_name,
        "pageNo": 1,
        "numOfRows": 3,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        return {"status": response.status_code, "data": response.text[:2000]}


async def test_seoul_restaurant_api(menu_name: str) -> dict:
    """서울 식당정보 API 테스트 (15098046)"""
    url = f"{BASE_URL}/6260000/FoodService/getFoodKr"
    params = {
        "serviceKey": API_KEY,
        "type": "json",
        "MENU": menu_name,
        "pageNo": 1,
        "numOfRows": 3,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        return {"status": response.status_code, "data": response.text[:2000]}


async def main():
    print("=" * 60)
    print("공공데이터 API 연결 테스트")
    print(f"시간: {datetime.now().isoformat()}")
    print(f"API 키: {API_KEY[:4]}...{API_KEY[-4:]}" if len(API_KEY) > 8 else f"API 키: {API_KEY}")
    print("=" * 60)

    if not API_KEY:
        print("[ERROR] PUBLIC_DATA_API_KEY가 .env에 설정되지 않았습니다!")
        return

    # ========== Test 1: 식품영양성분DB ==========
    print("\n[TEST 1] 식품영양성분DB API (15127578)")
    print("-" * 40)
    for menu in TEST_MENUS[:3]:
        try:
            result = await test_nutrition_api(menu)
            status = result["status"]
            data = result["data"]

            # JSON 파싱 시도
            try:
                parsed = json.loads(data)
                # 응답 구조 확인
                if "header" in parsed:
                    header = parsed["header"]
                    result_code = header.get("resultCode", "N/A")
                    result_msg = header.get("resultMsg", "N/A")
                    print(f"  {menu}: HTTP {status} | code={result_code} | msg={result_msg}")
                elif "response" in parsed:
                    header = parsed["response"].get("header", {})
                    body = parsed["response"].get("body", {})
                    result_code = header.get("resultCode", "N/A")
                    total = body.get("totalCount", 0)
                    print(f"  {menu}: HTTP {status} | code={result_code} | total={total}")
                    if total > 0:
                        items = body.get("items", {})
                        if isinstance(items, dict):
                            items = items.get("item", [])
                        if isinstance(items, list) and items:
                            first = items[0]
                            energy = first.get("AMT_NUM1", "N/A")
                            protein = first.get("AMT_NUM3", "N/A")
                            print(f"         energy={energy}kcal, protein={protein}g")
                else:
                    print(f"  {menu}: HTTP {status} | 응답: {data[:200]}")
            except json.JSONDecodeError:
                print(f"  {menu}: HTTP {status} | 응답(text): {data[:200]}")

        except Exception as e:
            print(f"  {menu}: ERROR - {e}")

        await asyncio.sleep(0.3)

    # ========== Test 2: 메뉴젠 API ==========
    print("\n[TEST 2] 메뉴젠 API (15101046)")
    print("-" * 40)
    for menu in TEST_MENUS[:3]:
        try:
            result = await test_menuzen_api(menu)
            status = result["status"]
            data = result["data"]

            try:
                parsed = json.loads(data)
                if "header" in parsed:
                    header = parsed["header"]
                    print(f"  {menu}: HTTP {status} | code={header.get('resultCode')} | msg={header.get('resultMsg')}")
                elif "response" in parsed:
                    header = parsed["response"].get("header", {})
                    body = parsed["response"].get("body", {})
                    total = body.get("totalCount", 0)
                    print(f"  {menu}: HTTP {status} | code={header.get('resultCode')} | total={total}")
                    if total > 0:
                        items = body.get("items", {})
                        if isinstance(items, dict):
                            items = items.get("item", [])
                        if isinstance(items, list) and items:
                            first = items[0]
                            food_cd = first.get("FOOD_CD", "N/A")
                            cat1 = first.get("FOOD_CAT1_NM", "N/A")
                            print(f"         code={food_cd}, category={cat1}")
                else:
                    print(f"  {menu}: HTTP {status} | 응답: {data[:200]}")
            except json.JSONDecodeError:
                print(f"  {menu}: HTTP {status} | 응답(text): {data[:200]}")

        except Exception as e:
            print(f"  {menu}: ERROR - {e}")

        await asyncio.sleep(0.3)

    # ========== Test 3: 서울 식당정보 ==========
    print("\n[TEST 3] 서울 식당정보 API (15098046)")
    print("-" * 40)
    for menu in TEST_MENUS[:2]:
        try:
            result = await test_seoul_restaurant_api(menu)
            status = result["status"]
            data = result["data"]

            try:
                parsed = json.loads(data)
                if "header" in parsed:
                    header = parsed["header"]
                    print(f"  {menu}: HTTP {status} | code={header.get('resultCode')} | msg={header.get('resultMsg')}")
                elif "response" in parsed:
                    header = parsed["response"].get("header", {})
                    body = parsed["response"].get("body", {})
                    total = body.get("totalCount", 0)
                    print(f"  {menu}: HTTP {status} | code={header.get('resultCode')} | total={total}")
                else:
                    # 다른 구조일 수 있음
                    keys = list(parsed.keys())[:5]
                    print(f"  {menu}: HTTP {status} | keys={keys}")
                    print(f"         data: {data[:300]}")
            except json.JSONDecodeError:
                # XML일 수 있음
                if "SERVICE_KEY_IS_NOT_REGISTERED_ERROR" in data:
                    print(f"  {menu}: HTTP {status} | API 키 미등록 (이 API에 별도 신청 필요)")
                elif "UNREGISTERED_SERVICE" in data:
                    print(f"  {menu}: HTTP {status} | 서비스 미등록 (이 API에 별도 신청 필요)")
                else:
                    print(f"  {menu}: HTTP {status} | 응답: {data[:300]}")

        except Exception as e:
            print(f"  {menu}: ERROR - {e}")

        await asyncio.sleep(0.3)

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
