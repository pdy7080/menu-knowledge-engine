"""
공공데이터 API 클라이언트
3개 API 통합: 메뉴젠, 서울 식당정보, 식품영양성분DB

API 목록:
- 메뉴젠 (15101046): 음식명 표준화, 음식코드 매핑
- 서울 식당정보 (15098046): 서울 소재 식당의 메뉴 데이터
- 식품영양성분DB (15127578): 영양정보 (에너지, 단백질 등 24항목)

Author: Claude (Senior Developer)
Date: 2026-02-19
"""
import httpx
import logging
from typing import Dict, List, Any, Optional
from config import settings

logger = logging.getLogger(__name__)

# 공공데이터 API 기본 설정
BASE_URL = "https://apis.data.go.kr"

# API 서비스 키 (공공데이터포털에서 발급)
# config.py에 PUBLIC_DATA_API_KEY 추가 필요
PUBLIC_DATA_API_KEY = getattr(settings, 'PUBLIC_DATA_API_KEY', '')


class PublicDataClient:
    """공공데이터 API 통합 클라이언트"""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or PUBLIC_DATA_API_KEY
        self.timeout = 10.0

    async def _request(self, url: str, params: Dict[str, Any]) -> Optional[Dict]:
        """공통 HTTP GET 요청"""
        params["serviceKey"] = self.api_key
        params["type"] = "json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                return data

        except httpx.TimeoutException:
            logger.error(f"[PublicData] Timeout: {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"[PublicData] HTTP {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"[PublicData] Error: {e}")
            return None

    # ========== 1. 메뉴젠 API (음식명 표준화) ==========

    async def search_menuzen(self, food_name: str, page: int = 1, per_page: int = 10) -> Optional[Dict]:
        """
        메뉴젠 API - 음식명으로 표준 음식코드 검색

        Args:
            food_name: 검색할 음식명 (한글)
            page: 페이지 번호
            per_page: 페이지당 결과 수

        Returns:
            {"total": int, "items": [{"food_code": str, "food_name": str, "category_1": str, ...}]}
        """
        url = f"{BASE_URL}/1471000/FoodNtrCpService/getFoodNtrCpInfo"

        params = {
            "food_name": food_name,
            "pageNo": page,
            "numOfRows": per_page,
        }

        data = await self._request(url, params)
        if not data:
            return None

        try:
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
                        "food_code": item.get("FOOD_CD", ""),
                        "food_name": item.get("FOOD_NM_KR", ""),
                        "category_1": item.get("FOOD_CAT1_NM", ""),
                        "category_2": item.get("FOOD_CAT2_NM", ""),
                        "serving_size": item.get("SERVING_SIZE", ""),
                        "energy": item.get("AMT_NUM1", ""),
                    }
                    for item in items
                ],
            }
        except Exception as e:
            logger.error(f"[MenuZen] Parse error: {e}")
            return None

    # ========== 2. 서울 식당정보 API ==========

    async def search_seoul_restaurants(
        self,
        menu_name: str = "",
        district: str = "",
        page: int = 1,
        per_page: int = 20,
    ) -> Optional[Dict]:
        """
        서울 식당정보 API - 메뉴명 또는 지역으로 식당 검색

        Args:
            menu_name: 메뉴명 검색 (선택)
            district: 구/동 (선택)
            page: 페이지 번호
            per_page: 페이지당 결과 수

        Returns:
            {"total": int, "items": [{"restaurant_name": str, "menu": str, ...}]}
        """
        url = f"{BASE_URL}/6260000/FoodService/getFoodKr"

        params = {
            "pageNo": page,
            "numOfRows": per_page,
        }

        if menu_name:
            params["MENU"] = menu_name
        if district:
            params["ADDR"] = district

        data = await self._request(url, params)
        if not data:
            return None

        try:
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
                        "restaurant_name": item.get("BIZPLC_NM", ""),
                        "menu": item.get("MENU_NM", ""),
                        "address": item.get("REFINE_ROADNM_ADDR", ""),
                        "district": item.get("SIGUN_NM", ""),
                    }
                    for item in items
                ],
            }
        except Exception as e:
            logger.error(f"[SeoulRestaurant] Parse error: {e}")
            return None

    # ========== 3. 식품영양성분DB API ==========

    async def get_nutrition_info(self, food_name: str, page: int = 1, per_page: int = 5) -> Optional[Dict]:
        """
        식품영양성분DB API - 음식명으로 영양정보 조회

        Args:
            food_name: 음식명 (한글)
            page: 페이지 번호
            per_page: 결과 수

        Returns:
            {"total": int, "items": [{"food_name": str, "nutrition": {...}}]}
        """
        url = f"{BASE_URL}/1471000/FoodNtrIrdntInfoService1/getFoodNtrItdntList1"

        params = {
            "FOOD_NM_KR": food_name,
            "pageNo": page,
            "numOfRows": per_page,
        }

        data = await self._request(url, params)
        if not data:
            return None

        try:
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
        3개 API를 순차적으로 호출하여 메뉴 정보 구축

        Args:
            menu_name_ko: 한글 메뉴명

        Returns:
            {
                "standard_code": str,
                "category_1": str,
                "category_2": str,
                "serving_size": str,
                "nutrition_info": dict,
                "source": str,
            }
        """
        result = {
            "standard_code": None,
            "category_1": None,
            "category_2": None,
            "serving_size": None,
            "nutrition_info": {},
            "source": "public_data",
        }

        # Step 1: 메뉴젠에서 표준코드 + 분류 조회
        menuzen = await self.search_menuzen(menu_name_ko)
        if menuzen and menuzen["items"]:
            first = menuzen["items"][0]
            result["standard_code"] = first.get("food_code")
            result["category_1"] = first.get("category_1")
            result["category_2"] = first.get("category_2")
            result["serving_size"] = first.get("serving_size")

        # Step 2: 영양정보 조회
        nutrition = await self.get_nutrition_info(menu_name_ko)
        if nutrition and nutrition["items"]:
            first = nutrition["items"][0]
            result["nutrition_info"] = first.get("nutrition", {})
            if not result["serving_size"] and first.get("serving_size"):
                result["serving_size"] = first["serving_size"]

        return result


# Global client instance
public_data_client = PublicDataClient()
