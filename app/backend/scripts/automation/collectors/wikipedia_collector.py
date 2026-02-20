"""
Wikipedia Korean Food Collector
Wikipedia API로 한식 카테고리의 음식명 수집 (CC 라이선스, 합법)

Sources:
- en.wikipedia.org: Category:Korean_cuisine
- ko.wikipedia.org: 분류:한국_음식

Author: terminal-developer
Date: 2026-02-20
"""
import asyncio
import logging
import httpx
from typing import List, Set

from .base_collector import BaseCollector, CollectionResult, DiscoveredMenu

logger = logging.getLogger("automation.collector.wikipedia")

# Wikipedia API endpoints
EN_WIKI_API = "https://en.wikipedia.org/w/api.php"
KO_WIKI_API = "https://ko.wikipedia.org/w/api.php"

# Korean cuisine categories to crawl (음식 카테고리만 — 개념/문화 카테고리 제외)
KOREAN_FOOD_CATEGORIES = [
    "Korean_soups_and_stews",
    "Korean_rice_dishes",
    "Korean_noodle_dishes",
    "Korean_side_dishes",
    "Korean_street_food",
    "Korean_grilled_dishes",
    "Korean_stews",
    "Korean_desserts_and_confections",
]

# 제외할 기사 제목 키워드 (개념/재료/문화 페이지)
EXCLUDED_TITLE_KEYWORDS = [
    "cuisine", "culture", "wheat", "bean", "rice (grain)",
    "agriculture", "condiment", "ingredient", "adzuki",
    "fermentation", "history of", "regional",
]

# User-Agent (Wikimedia 정책 준수)
HEADERS = {
    "User-Agent": (
        "MenuKnowledgeBot/2.0 "
        "(Contact: educational.research@example.com; "
        "Educational Korean food knowledge engine) "
        "Python-httpx/0.28"
    )
}


class WikipediaCollector(BaseCollector):
    """Wikipedia 한식 카테고리 크롤러"""

    source_name = "wikipedia"

    def __init__(self):
        self._collected_titles: Set[str] = set()

    async def collect(self, limit: int = 50) -> CollectionResult:
        """Wikipedia에서 한식 메뉴명 수집"""
        result = CollectionResult(source=self.source_name)
        all_menus: List[DiscoveredMenu] = []

        for category in KOREAN_FOOD_CATEGORIES:
            if len(all_menus) >= limit:
                break

            remaining = limit - len(all_menus)
            menus = await self._collect_from_category(category, remaining)
            all_menus.extend(menus)

            # Rate limit (Wikimedia: 200 req/s but be polite)
            await asyncio.sleep(1.0)

        result.discovered = len(all_menus)
        result.menus = all_menus[:limit]
        result.new_items = len(result.menus)
        logger.info(f"Wikipedia: collected {result.discovered} food items")

        return result

    async def _collect_from_category(
        self, category: str, limit: int
    ) -> List[DiscoveredMenu]:
        """단일 카테고리에서 음식 기사 수집"""
        menus = []

        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmtype": "page",
            "cmlimit": min(limit, 50),
            "format": "json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, headers=HEADERS) as client:
                response = await client.get(EN_WIKI_API, params=params)
                if response.status_code != 200:
                    logger.warning(f"Wikipedia API error: {response.status_code}")
                    return menus

                data = response.json()
                members = data.get("query", {}).get("categorymembers", [])

                for member in members:
                    title = member.get("title", "")
                    # 카테고리/목록 페이지 건너뛰기
                    if title.startswith("Category:") or title.startswith("List of"):
                        continue
                    # 개념/재료/문화 페이지 건너뛰기
                    title_lower = title.lower()
                    if any(kw in title_lower for kw in EXCLUDED_TITLE_KEYWORDS):
                        logger.debug(f"Excluded (non-food): {title}")
                        continue
                    # 중복 건너뛰기
                    if title in self._collected_titles:
                        continue

                    self._collected_titles.add(title)

                    # 한국어 이름 가져오기
                    ko_name = await self._get_korean_name(title, client)

                    # 간단 설명 가져오기
                    extract = await self._get_extract(title, client)

                    if ko_name:
                        menus.append(DiscoveredMenu(
                            name_ko=ko_name,
                            name_en=title,
                            source=self.source_name,
                            category_hint=category.replace("Korean_", "").replace("_", " "),
                            description_en=extract,
                            raw_data={"wiki_title": title, "category": category},
                        ))

                    await asyncio.sleep(0.5)  # Polite rate limiting

        except Exception as e:
            logger.error(f"Wikipedia collection error ({category}): {e}")

        return menus

    async def _get_korean_name(
        self, en_title: str, client: httpx.AsyncClient
    ) -> str:
        """영문 Wikipedia 기사의 한국어 이름 가져오기 (interlanguage link)"""
        params = {
            "action": "query",
            "titles": en_title,
            "prop": "langlinks",
            "lllang": "ko",
            "format": "json",
        }

        try:
            response = await client.get(EN_WIKI_API, params=params)
            if response.status_code == 200:
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                for page_data in pages.values():
                    langlinks = page_data.get("langlinks", [])
                    for ll in langlinks:
                        if ll.get("lang") == "ko":
                            return ll.get("*", "")
        except Exception:
            pass

        # Fallback: 영문 제목에서 한국어 유추 불가
        return ""

    async def _get_extract(
        self, title: str, client: httpx.AsyncClient
    ) -> str:
        """Wikipedia 기사의 첫 문단 추출"""
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "exsentences": 2,
            "format": "json",
        }

        try:
            response = await client.get(EN_WIKI_API, params=params)
            if response.status_code == 200:
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                for page_data in pages.values():
                    return page_data.get("extract", "")[:300]
        except Exception:
            pass

        return ""

    async def get_remaining_count(self) -> int:
        """추정 남은 수 (Wikipedia 한식 카테고리 전체 약 500-800개)"""
        return max(0, 800 - len(self._collected_titles))
