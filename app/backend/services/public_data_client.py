"""
공공데이터 API 클라이언트
2개 포털 통합: data.go.kr (식품영양성분DB) + data.ex.co.kr (고속도로 휴게소)

API 목록:
- 식품영양성분DB (data.go.kr/15127578): 영양정보 (에너지, 단백질 등)
  URL: apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02
  인증: serviceKey (data.go.kr 포털 발급)
- 고속도로 휴게소 음식 (data.ex.co.kr): 메뉴명, 가격, 휴게소 정보
  URL: data.ex.co.kr/openapi/restinfo/restBestfoodList
  인증: key (data.ex.co.kr 포털 발급)

주의: 두 포털의 인증키는 별도 발급 필요
- data.go.kr: Base64 인코딩된 긴 문자열 (serviceKey)
- data.ex.co.kr: 숫자 10자리 (key)

Author: Claude (Senior Developer)
Date: 2026-02-19
"""
import httpx
import logging
from typing import Dict, List, Any, Optional
from config import settings

logger = logging.getLogger(__name__)

# API 키 (config.py → .env에서 로드)
PUBLIC_DATA_API_KEY = getattr(settings, 'PUBLIC_DATA_API_KEY', '')
# data.go.kr 별도 키가 설정되지 않으면 PUBLIC_DATA_API_KEY 사용
DATA_GO_KR_API_KEY = getattr(settings, 'DATA_GO_KR_API_KEY', '') or PUBLIC_DATA_API_KEY


class PublicDataClient:
    """공공데이터 API 통합 클라이언트"""

    def __init__(self, api_key: str = "", data_go_kr_key: str = ""):
        self.api_key = api_key or PUBLIC_DATA_API_KEY  # data.ex.co.kr
        self.data_go_kr_key = data_go_kr_key or DATA_GO_KR_API_KEY  # data.go.kr
        self.timeout = 10.0

    async def _request_ex(self, url: str, params: Dict[str, Any]) -> Optional[Dict]:
        """data.ex.co.kr 전용 HTTP GET 요청"""
        params["key"] = self.api_key
        params["type"] = "json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error(f"[ExData] Timeout: {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"[ExData] HTTP {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"[ExData] Error: {e}")
            return None

    async def _request_go(self, url: str, params: Dict[str, Any]) -> Optional[Dict]:
        """data.go.kr 전용 HTTP GET 요청"""
        params["serviceKey"] = self.data_go_kr_key
        params["type"] = "json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error(f"[GoData] Timeout: {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"[GoData] HTTP {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"[GoData] Error: {e}")
            return None

    # ========== 1. 고속도로 휴게소 음식 API (data.ex.co.kr) ==========

    async def search_highway_food(
        self,
        food_name: str = "",
        page: int = 1,
        per_page: int = 20,
    ) -> Optional[Dict]:
        """
        고속도로 휴게소 음식 메뉴 검색 (확인됨, 작동 중)

        Args:
            food_name: 음식명 검색 (선택)
            page: 페이지 번호
            per_page: 페이지당 결과 수

        Returns:
            {"total": int, "items": [{"food_name": str, "price": int, ...}]}
        """
        url = "https://data.ex.co.kr/openapi/restinfo/restBestfoodList"

        params = {
            "numOfRows": per_page,
            "pageNo": page,
        }
        if food_name:
            params["foodNm"] = food_name

        data = await self._request_ex(url, params)
        if not data or data.get("code") != "SUCCESS":
            return None

        items = data.get("list", [])
        return {
            "total": data.get("count", 0),
            "items": [
                {
                    "food_name": item.get("foodNm", ""),
                    "price": int(item.get("foodCost", "0") or "0"),
                    "rest_area": item.get("stdRestNm", ""),
                    "route": item.get("routeNm", ""),
                    "is_best": item.get("bestfoodyn") == "Y",
                    "is_recommend": item.get("recommendyn") == "Y",
                }
                for item in items
            ],
        }

    # ========== 2. 식품영양성분DB API (data.go.kr) ==========

    async def get_nutrition_info(self, food_name: str, page: int = 1, per_page: int = 5) -> Optional[Dict]:
        """
        식품영양성분DB API - 음식명으로 영양정보 조회
        URL: apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02

        주의: data.go.kr 인증키 필요 (data.ex.co.kr 키와 별도)

        Args:
            food_name: 음식명 (한글)
            page: 페이지 번호
            per_page: 결과 수

        Returns:
            {"total": int, "items": [{"food_name": str, "nutrition": {...}}]}
        """
        url = "https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02"

        params = {
            "FOOD_NM_KR": food_name,
            "pageNo": page,
            "numOfRows": per_page,
        }

        data = await self._request_go(url, params)
        if not data:
            return None

        try:
            # 응답 구조: header + body 또는 response > header + body
            body = data.get("body", {})
            if not body and "response" in data:
                body = data["response"].get("body", {})
            if not body and "header" in data:
                body = data.get("body", {})

            items = body.get("items", [])
            if isinstance(items, dict):
                items = items.get("item", [])
            if isinstance(items, dict):
                items = [items]

            return {
                "total": body.get("totalCount", 0),
                "items": [
                    {
                        "food_name": item.get("FOOD_NM_KR", ""),
                        "food_code": item.get("FOOD_CD", ""),
                        "category_1": item.get("FOOD_CAT1_NM", ""),
                        "category_2": item.get("FOOD_CAT2_NM", ""),
                        "serving_size": item.get("SERVING_SIZE", ""),
                        "nutrition": self._parse_nutrition(item),
                    }
                    for item in items
                ],
            }
        except Exception as e:
            logger.error(f"[NutritionDB] Parse error: {e}")
            return None

    def _parse_nutrition(self, item: Dict) -> Dict[str, Any]:
        """
        API 응답에서 영양정보 JSONB 형식으로 변환

        Returns:
            {"energy": float, "protein": float, "fat": float, ...}
        """
        def safe_float(val) -> Optional[float]:
            if val is None or val == "" or val == "-":
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        return {
            "energy": safe_float(item.get("AMT_NUM1")),
            "protein": safe_float(item.get("AMT_NUM3")),
            "fat": safe_float(item.get("AMT_NUM4")),
            "carbohydrate": safe_float(item.get("AMT_NUM7")),
            "fiber": safe_float(item.get("AMT_NUM8")),
            "calcium": safe_float(item.get("AMT_NUM9")),
            "iron": safe_float(item.get("AMT_NUM10")),
            "sodium": safe_float(item.get("AMT_NUM13")),
            "potassium": safe_float(item.get("AMT_NUM14")),
            "vitamin_a": safe_float(item.get("AMT_NUM15")),
            "vitamin_c": safe_float(item.get("AMT_NUM18")),
            "cholesterol": safe_float(item.get("AMT_NUM24")),
            "saturated_fat": safe_float(item.get("AMT_NUM25")),
        }

    # ========== 통합 검색 ==========

    async def enrich_menu(self, menu_name_ko: str) -> Dict[str, Any]:
        """
        메뉴명으로 공공데이터 통합 조회
        1. 고속도로 휴게소 API (가격, 인기도)
        2. 식품영양성분DB (영양정보) — data.go.kr 키 필요

        Args:
            menu_name_ko: 한글 메뉴명

        Returns:
            {
                "category_1": str,
                "category_2": str,
                "serving_size": str,
                "nutrition_info": dict,
                "avg_price": int,
                "is_popular": bool,
                "source": str,
            }
        """
        result = {
            "category_1": None,
            "category_2": None,
            "serving_size": None,
            "nutrition_info": {},
            "avg_price": 0,
            "is_popular": False,
            "source": "public_data",
        }

        # Step 1: 고속도로 휴게소에서 가격/인기도 조회 (항상 작동)
        highway = await self.search_highway_food(food_name=menu_name_ko)
        if highway and highway["items"]:
            prices = [i["price"] for i in highway["items"] if i["price"] > 0]
            if prices:
                result["avg_price"] = sum(prices) // len(prices)
            result["is_popular"] = any(i.get("is_best") for i in highway["items"])

        # Step 2: 영양정보 조회 (data.go.kr 키 필요)
        if self.data_go_kr_key:
            nutrition = await self.get_nutrition_info(menu_name_ko)
            if nutrition and nutrition["items"]:
                first = nutrition["items"][0]
                result["nutrition_info"] = first.get("nutrition", {})
                result["serving_size"] = first.get("serving_size")
                result["category_1"] = first.get("category_1")
                result["category_2"] = first.get("category_2")

        return result


# Global client instance
public_data_client = PublicDataClient()
