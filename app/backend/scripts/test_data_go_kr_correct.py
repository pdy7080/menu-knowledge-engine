"""
data.go.kr 식품영양성분DB API 테스트 - 올바른 URL
확인된 정확한 엔드포인트:
  https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02

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
from urllib.parse import quote, urlencode

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv
import os
load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("DATA_GO_KR_API_KEY", "")

TEST_MENUS = ["김치찌개", "불고기", "비빔밥", "된장찌개", "삼겹살"]


async def test_nutrition_api(food_name: str):
    """식품영양성분DB API - 올바른 URL"""
    url = "https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02"

    params = {
        "serviceKey": API_KEY,
        "pageNo": 1,
        "numOfRows": 5,
        "type": "json",
        "FOOD_NM_KR": food_name,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        return response.status_code, response.text


async def main():
    print("=" * 60)
    print("식품영양성분DB API 테스트 (올바른 URL)")
    print(f"시간: {datetime.now().isoformat()}")
    print(f"API 키: {API_KEY}")
    print(f"URL: apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02")
    print("=" * 60)

    for menu in TEST_MENUS:
        print(f"\n[{menu}]")
        try:
            status, text = await test_nutrition_api(menu)
            print(f"  HTTP {status}")

            if status == 200:
                try:
                    data = json.loads(text)
                    # 응답 구조 탐색
                    if "header" in data:
                        header = data["header"]
                        print(f"  resultCode: {header.get('resultCode')}")
                        print(f"  resultMsg: {header.get('resultMsg')}")

                        if "body" in data:
                            body = data["body"]
                            total = body.get("totalCount", 0)
                            print(f"  totalCount: {total}")
                            items = body.get("items", [])
                            if isinstance(items, dict):
                                items = items.get("item", [])
                            if isinstance(items, list):
                                for item in items[:2]:
                                    name = item.get("FOOD_NM_KR", "N/A")
                                    energy = item.get("AMT_NUM1", item.get("ENERC", "N/A"))
                                    protein = item.get("AMT_NUM3", item.get("PROT", "N/A"))
                                    cat1 = item.get("FOOD_CAT1_NM", "N/A")
                                    print(f"  -> {name} | {cat1} | energy={energy} protein={protein}")

                    elif "response" in data:
                        resp = data["response"]
                        header = resp.get("header", {})
                        body = resp.get("body", {})
                        print(f"  resultCode: {header.get('resultCode')}")
                        print(f"  resultMsg: {header.get('resultMsg')}")
                        total = body.get("totalCount", 0)
                        print(f"  totalCount: {total}")
                        items = body.get("items", {})
                        if isinstance(items, dict):
                            items = items.get("item", [])
                        if isinstance(items, list):
                            for item in items[:2]:
                                print(f"  -> keys: {list(item.keys())[:10]}")
                                name = item.get("FOOD_NM_KR", item.get("foodNmKr", "N/A"))
                                print(f"  -> {name}")

                    else:
                        # 다른 구조
                        keys = list(data.keys())[:10]
                        print(f"  keys: {keys}")
                        print(f"  data: {json.dumps(data, ensure_ascii=False)[:500]}")

                except json.JSONDecodeError:
                    # XML일 수 있음
                    if "<resultCode>" in text:
                        import re
                        code = re.search(r'<resultCode>(\d+)</resultCode>', text)
                        msg = re.search(r'<resultMsg>([^<]+)</resultMsg>', text)
                        print(f"  XML resultCode: {code.group(1) if code else 'N/A'}")
                        print(f"  XML resultMsg: {msg.group(1) if msg else 'N/A'}")

                        # totalCount 확인
                        total = re.search(r'<totalCount>(\d+)</totalCount>', text)
                        if total:
                            print(f"  XML totalCount: {total.group(1)}")
                    else:
                        print(f"  raw: {text[:300]}")
            else:
                print(f"  응답: {text[:300]}")

        except Exception as e:
            print(f"  ERROR: {e}")

        await asyncio.sleep(0.3)

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
