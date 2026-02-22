"""
data.go.kr 식품영양성분DB API 디버그 테스트
- serviceKey를 URL에 직접 삽입하여 인코딩 문제 확인
- 여러 serviceKey 전달 방식 시도

Author: Claude (Senior Developer)
Date: 2026-02-19
"""

import sys
import io
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

# Windows UTF-8 인코딩 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("PUBLIC_DATA_API_KEY", "")


async def main():
    print("=" * 60)
    print("data.go.kr API 디버그 테스트")
    print(f"시간: {datetime.now().isoformat()}")
    print(f"API 키: {API_KEY} (길이: {len(API_KEY)})")
    print("=" * 60)

    base_url = (
        "https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02"
    )
    food = "김치찌개"

    # 방법 1: params로 전달 (httpx 자동 인코딩)
    print("\n[방법 1] httpx params 전달")
    print("-" * 40)
    async with httpx.AsyncClient(timeout=15.0) as client:
        params = {
            "serviceKey": API_KEY,
            "pageNo": 1,
            "numOfRows": 3,
            "type": "json",
            "FOOD_NM_KR": food,
        }
        response = await client.get(base_url, params=params)
        print(f"  URL: {response.url}")
        print(f"  HTTP {response.status_code}")
        print(f"  응답: {response.text[:300]}")

    await asyncio.sleep(0.5)

    # 방법 2: serviceKey를 URL에 직접 삽입 (인코딩 우회)
    print("\n[방법 2] serviceKey URL 직접 삽입")
    print("-" * 40)
    from urllib.parse import quote

    direct_url = f"{base_url}?serviceKey={API_KEY}&pageNo=1&numOfRows=3&type=json&FOOD_NM_KR={quote(food)}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(direct_url)
        print(f"  URL: {response.url}")
        print(f"  HTTP {response.status_code}")
        print(f"  응답: {response.text[:300]}")

    await asyncio.sleep(0.5)

    # 방법 3: serviceKey만 params에서 제외
    print("\n[방법 3] serviceKey URL 삽입 + 나머지 params")
    print("-" * 40)
    url_with_key = f"{base_url}?serviceKey={API_KEY}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        params = {
            "pageNo": 1,
            "numOfRows": 3,
            "type": "json",
            "FOOD_NM_KR": food,
        }
        response = await client.get(url_with_key, params=params)
        print(f"  URL: {response.url}")
        print(f"  HTTP {response.status_code}")
        print(f"  응답: {response.text[:300]}")

    await asyncio.sleep(0.5)

    # 방법 4: returnType 대신 type, perPage 대신 numOfRows (GW 방식)
    print("\n[방법 4] GW 방식 파라미터 (perPage, returnType)")
    print("-" * 40)
    async with httpx.AsyncClient(timeout=15.0) as client:
        params = {
            "serviceKey": API_KEY,
            "page": 1,
            "perPage": 3,
            "returnType": "JSON",
            "FOOD_NM_KR": food,
        }
        response = await client.get(base_url, params=params)
        print(f"  URL: {response.url}")
        print(f"  HTTP {response.status_code}")
        print(f"  응답: {response.text[:300]}")

    await asyncio.sleep(0.5)

    # 방법 5: 키 없이 요청 (에러 메시지 확인)
    print("\n[방법 5] 키 없이 요청 (에러 패턴 확인)")
    print("-" * 40)
    async with httpx.AsyncClient(timeout=15.0) as client:
        params = {
            "pageNo": 1,
            "numOfRows": 3,
            "type": "json",
            "FOOD_NM_KR": food,
        }
        response = await client.get(base_url, params=params)
        print(f"  HTTP {response.status_code}")
        print(f"  응답: {response.text[:300]}")

    print("\n" + "=" * 60)
    print("디버그 완료")
    print("=" * 60)
    print("\n[참고] data.go.kr 인증키는 보통 Base64 인코딩된 긴 문자열입니다.")
    print("  예: 'AbCdEfGhIjKlMnOpQrStUvWxYz1234567890+/=='")
    print(f"  현재 키: '{API_KEY}' (숫자 10자리)")
    print("  → 마이페이지에서 '일반 인증키(Encoding)' 값을 확인해주세요.")


if __name__ == "__main__":
    asyncio.run(main())
