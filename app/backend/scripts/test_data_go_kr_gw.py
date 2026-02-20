"""
data.go.kr GW방식 API 테스트
PDF 가이드 기반 올바른 URL 구조로 테스트

Base URL: api.odcloud.kr/api/{서비스ID}/v1/{엔드포인트}
파라미터: serviceKey, page, perPage, returnType

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
from urllib.parse import quote

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv
import os
load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("PUBLIC_DATA_API_KEY", "")

# 테스트할 API 서비스 ID 목록
SERVICES = {
    "식품영양성분DB": "15127578",
    "메뉴젠": "15101046",
    "서울식당정보": "15098046",
}


async def test_gw_api(service_name: str, service_id: str):
    """GW방식 API 테스트"""
    print(f"\n  [{service_name}] 서비스ID: {service_id}")

    # GW방식 URL 패턴들 시도
    url_patterns = [
        # 패턴 1: api.odcloud.kr (PDF curl 예시)
        f"https://api.odcloud.kr/api/{service_id}/v1/file-data-list",
        # 패턴 2: api.odcloud.kr - open-data-list
        f"https://api.odcloud.kr/api/{service_id}/v1/open-data-list",
        # 패턴 3: api.odcloud.kr - dataset
        f"https://api.odcloud.kr/api/{service_id}/v1/dataset",
        # 패턴 4: apis.data.go.kr GW방식
        f"https://apis.data.go.kr/{service_id}/api/file-data-list",
        # 패턴 5: apis.data.go.kr GW방식 v1
        f"https://apis.data.go.kr/{service_id}/v1/file-data-list",
    ]

    for idx, url in enumerate(url_patterns, 1):
        # GW방식 파라미터
        params = {
            "serviceKey": API_KEY,
            "page": 1,
            "perPage": 5,
            "returnType": "JSON",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                status = response.status_code
                text = response.text[:500]

                if status == 200:
                    try:
                        data = response.json()
                        if "data" in data or "currentCount" in data:
                            print(f"    패턴{idx} OK: {url}")
                            print(f"    응답: {json.dumps(data, ensure_ascii=False, indent=2)[:400]}")
                            return url, data
                        elif "resultCode" in str(data):
                            code = data.get("resultCode", data.get("header", {}).get("resultCode", "N/A"))
                            print(f"    패턴{idx} HTTP 200 but code={code}: {text[:150]}")
                        else:
                            print(f"    패턴{idx} HTTP 200: {text[:150]}")
                    except json.JSONDecodeError:
                        if "SERVICE_KEY" in text or "SERVICE" in text:
                            print(f"    패턴{idx} HTTP {status}: 키 관련 오류 - {text[:150]}")
                        else:
                            print(f"    패턴{idx} HTTP {status}: {text[:150]}")
                elif status == 401:
                    print(f"    패턴{idx} HTTP 401: 인증 실패")
                elif status == 404:
                    print(f"    패턴{idx} HTTP 404: 경로 없음")
                elif status == 500:
                    print(f"    패턴{idx} HTTP 500: {text[:100]}")
                else:
                    print(f"    패턴{idx} HTTP {status}: {text[:100]}")

        except Exception as e:
            print(f"    패턴{idx} ERROR: {e}")

        await asyncio.sleep(0.2)

    return None, None


async def test_direct_api_variations():
    """기존 방식 API도 serviceKey 파라미터로 재시도"""
    print("\n[추가] 기존 URL + serviceKey 파라미터 조합 테스트")
    print("-" * 50)

    # 식품영양성분 API - 여러 경로 시도
    test_urls = [
        # data.go.kr 기존 방식 (serviceKey 파라미터 사용)
        "https://apis.data.go.kr/1471000/FoodNtrIrdntInfoService1/getFoodNtrItdntList1",
        # 대체 경로
        "http://apis.data.go.kr/1471000/FoodNtrIrdntInfoService1/getFoodNtrItdntList1",
        # 식약처 영양성분 API 대체 경로
        "https://apis.data.go.kr/1471000/FoodNtrCpService/getFoodNtrCpInfo",
    ]

    for url in test_urls:
        params = {
            "serviceKey": API_KEY,
            "pageNo": 1,
            "numOfRows": 3,
            "type": "json",
            "FOOD_NM_KR": "김치찌개",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                status = response.status_code
                text = response.text[:300]
                print(f"  {url.split('/')[-1]}: HTTP {status}")

                if status == 200:
                    try:
                        data = response.json()
                        keys = list(data.keys())[:5]
                        print(f"    keys: {keys}")
                        # 응답 구조 확인
                        if "response" in data:
                            header = data["response"].get("header", {})
                            print(f"    resultCode: {header.get('resultCode')}, resultMsg: {header.get('resultMsg')}")
                        elif "header" in data:
                            print(f"    resultCode: {data['header'].get('resultCode')}")
                        else:
                            print(f"    data: {json.dumps(data, ensure_ascii=False)[:200]}")
                    except json.JSONDecodeError:
                        print(f"    text: {text[:200]}")
                else:
                    print(f"    text: {text[:200]}")

        except Exception as e:
            print(f"  ERROR: {e}")

        await asyncio.sleep(0.3)


async def main():
    print("=" * 60)
    print("data.go.kr GW방식 API 테스트")
    print(f"시간: {datetime.now().isoformat()}")
    print(f"API 키: {API_KEY}")
    print("=" * 60)

    # 1. GW방식 테스트
    print("\n[1] GW방식 (api.odcloud.kr) 테스트")
    print("-" * 50)
    for name, sid in SERVICES.items():
        await test_gw_api(name, sid)

    # 2. 기존 방식 재시도
    await test_direct_api_variations()

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
