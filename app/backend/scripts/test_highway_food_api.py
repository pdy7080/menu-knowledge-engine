"""
한국도로공사 고속도로 휴게소 음식 메뉴 API 테스트
https://data.ex.co.kr/openapi/basicinfo/openApiInfoM?apiId=0502

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


async def test_rest_area_food(unit_code: str = "", menu_name: str = ""):
    """휴게소 음식 메뉴 조회"""
    url = "https://data.ex.co.kr/openapi/restinfo/restBestfoodList"
    params = {
        "key": API_KEY,
        "type": "json",
        "numOfRows": 10,
        "pageNo": 1,
    }
    if unit_code:
        params["unitCode"] = unit_code
    if menu_name:
        params["foodNm"] = menu_name

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        return response.status_code, response.text


async def test_rest_area_list():
    """휴게소 목록 조회"""
    url = "https://data.ex.co.kr/openapi/restinfo/restAreaList"
    params = {
        "key": API_KEY,
        "type": "json",
        "numOfRows": 5,
        "pageNo": 1,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        return response.status_code, response.text


async def test_food_menu_list():
    """음식 메뉴 전체 목록 조회"""
    url = "https://data.ex.co.kr/openapi/restinfo/restFoodList"
    params = {
        "key": API_KEY,
        "type": "json",
        "numOfRows": 20,
        "pageNo": 1,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        return response.status_code, response.text


async def main():
    print("=" * 60)
    print("한국도로공사 고속도로 휴게소 음식 메뉴 API 테스트")
    print(f"시간: {datetime.now().isoformat()}")
    print(f"API 키: {API_KEY}")
    print("=" * 60)

    # Test 1: 휴게소 목록
    print("\n[TEST 1] 휴게소 목록 조회")
    print("-" * 40)
    try:
        status, data = await test_rest_area_list()
        print(f"  HTTP {status}")
        if status == 200:
            try:
                parsed = json.loads(data)
                print(f"  응답 키: {list(parsed.keys())}")
                # 데이터 구조 탐색
                if "list" in parsed:
                    items = parsed["list"]
                    print(f"  휴게소 수: {len(items)}개")
                    for item in items[:3]:
                        print(f"    - {item.get('unitName', 'N/A')} ({item.get('routeName', 'N/A')})")
                elif "count" in parsed:
                    print(f"  총 건수: {parsed.get('count')}")
                else:
                    print(f"  데이터: {json.dumps(parsed, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                print(f"  응답(raw): {data[:500]}")
        else:
            print(f"  응답: {data[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")

    await asyncio.sleep(0.5)

    # Test 2: 대표 음식 메뉴 조회
    print("\n[TEST 2] 대표 음식 메뉴 (Best Food)")
    print("-" * 40)
    try:
        status, data = await test_rest_area_food()
        print(f"  HTTP {status}")
        if status == 200:
            try:
                parsed = json.loads(data)
                print(f"  응답 키: {list(parsed.keys())}")
                if "list" in parsed:
                    items = parsed["list"]
                    print(f"  메뉴 수: {len(items)}개")
                    for item in items[:5]:
                        print(f"    - {item.get('foodNm', 'N/A')} | {item.get('unitNm', 'N/A')} | {item.get('foodCost', 'N/A')}원")
                elif "count" in parsed:
                    print(f"  총 건수: {parsed.get('count')}")
                else:
                    print(f"  데이터: {json.dumps(parsed, ensure_ascii=False, indent=2)[:500]}")
            except json.JSONDecodeError:
                print(f"  응답(raw): {data[:500]}")
        else:
            print(f"  응답: {data[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")

    await asyncio.sleep(0.5)

    # Test 3: 전체 음식 메뉴 목록
    print("\n[TEST 3] 전체 음식 메뉴 목록 (Food List)")
    print("-" * 40)
    try:
        status, data = await test_food_menu_list()
        print(f"  HTTP {status}")
        if status == 200:
            try:
                parsed = json.loads(data)
                print(f"  응답 키: {list(parsed.keys())}")
                if "list" in parsed:
                    items = parsed["list"]
                    print(f"  메뉴 수: {len(items)}개")
                    for item in items[:10]:
                        name = item.get('foodNm', item.get('menuNm', 'N/A'))
                        rest_area = item.get('unitNm', item.get('stdRestNm', 'N/A'))
                        price = item.get('foodCost', item.get('price', 'N/A'))
                        print(f"    - {name} | {rest_area} | {price}원")
                elif "count" in parsed:
                    print(f"  총 건수: {parsed.get('count')}")
                    if "list" not in parsed:
                        print(f"  전체 응답: {json.dumps(parsed, ensure_ascii=False, indent=2)[:800]}")
                else:
                    print(f"  데이터: {json.dumps(parsed, ensure_ascii=False, indent=2)[:800]}")
            except json.JSONDecodeError:
                print(f"  응답(raw): {data[:500]}")
        else:
            print(f"  응답: {data[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
