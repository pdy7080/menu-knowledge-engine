"""
Recipe Site Collector
만개의레시피 등 레시피 사이트에서 메뉴명 수집 (robots.txt 준수)

Strategy:
1. robots.txt 확인 (크롤링 허용 여부)
2. 카테고리 페이지에서 레시피 제목 추출
3. Polite crawling (5초 간격)

Author: terminal-developer
Date: 2026-02-20
"""
import asyncio
import logging
import re
import httpx
from typing import List, Set, Optional

from .base_collector import BaseCollector, CollectionResult, DiscoveredMenu

logger = logging.getLogger("automation.collector.recipe")

# 만개의레시피 설정
MANGAE_BASE_URL = "https://www.10000recipe.com"
MANGAE_CATEGORY_URL = f"{MANGAE_BASE_URL}/recipe/list.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; MenuKnowledgeBot/2.0; "
        "+educational; respectful-crawling)"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 레시피 제목 → 음식명 추출용 키워드 (제거 대상)
RECIPE_TITLE_NOISE = [
    "만들기", "만드는법", "만드는방법", "레시피", "황금레시피",
    "초간단", "간단한", "간단", "쉬운", "간편", "자취생",
    "백종원의", "백종원", "이보은의",
    "밑반찬", "반찬",
]

# 특수문자 패턴
RECIPE_SPECIAL_CHARS = re.compile(r'[♪♫♬♩~!@#$%^&*]')


class RecipeCollector(BaseCollector):
    """만개의레시피 크롤러 (robots.txt 준수)"""

    source_name = "recipe"

    def __init__(self):
        self._collected_names: Set[str] = set()
        self._robots_checked = False
        self._allowed = False

    async def _check_robots(self) -> bool:
        """robots.txt 확인"""
        if self._robots_checked:
            return self._allowed

        try:
            async with httpx.AsyncClient(timeout=10.0, headers=HEADERS) as client:
                response = await client.get(f"{MANGAE_BASE_URL}/robots.txt")
                if response.status_code == 200:
                    robots_text = response.text
                    # /recipe/list.html 경로가 Disallow에 없는지 확인
                    self._allowed = "Disallow: /recipe/list" not in robots_text
                    if not self._allowed:
                        logger.warning("robots.txt disallows /recipe/list crawling")
                else:
                    # robots.txt 없으면 허용으로 간주
                    self._allowed = True
        except Exception as e:
            logger.warning(f"robots.txt check failed: {e}")
            self._allowed = False

        self._robots_checked = True
        return self._allowed

    async def collect(self, limit: int = 50) -> CollectionResult:
        """레시피 사이트에서 메뉴명 수집"""
        result = CollectionResult(source=self.source_name)

        # robots.txt 확인
        if not await self._check_robots():
            logger.info("Recipe collection skipped (robots.txt)")
            return result

        all_menus: List[DiscoveredMenu] = []

        # 카테고리별 수집 (한식 카테고리)
        # 만개의레시피 카테고리: cat4=63 (한식)
        categories = [
            ("63", "한식"),    # Korean
            ("56", "반찬"),    # Side dishes
            ("54", "국/탕"),   # Soups
            ("55", "찌개"),    # Stews
        ]

        for cat_id, cat_name in categories:
            if len(all_menus) >= limit:
                break

            remaining = limit - len(all_menus)
            menus = await self._collect_from_category(cat_id, cat_name, remaining)
            all_menus.extend(menus)

            # Polite delay (5초)
            await asyncio.sleep(5.0)

        result.discovered = len(all_menus)
        result.menus = all_menus[:limit]
        result.new_items = len(result.menus)
        logger.info(f"Recipe sites: collected {result.discovered} food items")

        return result

    async def _collect_from_category(
        self, cat_id: str, cat_name: str, limit: int
    ) -> List[DiscoveredMenu]:
        """카테고리 페이지에서 레시피 제목 추출"""
        menus = []

        try:
            params = {"cat4": cat_id, "order": "reco", "page": "1"}
            async with httpx.AsyncClient(
                timeout=15.0, headers=HEADERS, follow_redirects=True
            ) as client:
                response = await client.get(MANGAE_CATEGORY_URL, params=params)
                if response.status_code != 200:
                    logger.warning(f"Recipe page error: {response.status_code}")
                    return menus

                html = response.text

                # BeautifulSoup 없이 간단한 regex 추출
                # <div class="common_sp_caption_tit">레시피 제목</div>
                titles = re.findall(
                    r'class="common_sp_caption_tit[^"]*"[^>]*>([^<]+)<',
                    html,
                )

                if not titles:
                    # 대체 패턴
                    titles = re.findall(
                        r'<div class="common_sp_caption_tit(?:le)?">([^<]+)</div>',
                        html,
                    )

                for title in titles:
                    name_ko = title.strip()
                    if not name_ko or len(name_ko) < 2:
                        continue

                    # 레시피 제목 → 핵심 음식명 추출
                    name_ko = self._extract_food_name(name_ko)

                    if not name_ko or len(name_ko) < 2 or len(name_ko) > 20:
                        continue
                    if name_ko in self._collected_names:
                        continue

                    self._collected_names.add(name_ko)
                    menus.append(DiscoveredMenu(
                        name_ko=name_ko,
                        source=self.source_name,
                        category_hint=cat_name,
                    ))

                    if len(menus) >= limit:
                        break

        except Exception as e:
            logger.error(f"Recipe collection error ({cat_name}): {e}")

        return menus

    @staticmethod
    def _extract_food_name(title: str) -> str:
        """
        레시피 제목에서 핵심 음식명 추출

        예시:
        - "백종원의감자전만들기♪♪" → "감자전"
        - "소시지볶음레시피간장비엔나소시지반찬만들기" → "소시지볶음"
        - "단무지무침레시피밑반찬만들기치자단무지무침" → "단무지무침"
        - "청포묵무침만드는법" → "청포묵무침"
        """
        name = title.strip()

        # 특수문자 제거
        name = RECIPE_SPECIAL_CHARS.sub('', name)

        # 괄호 내용 제거
        name = re.sub(r'\(.*?\)', '', name)
        name = re.sub(r'\[.*?\]', '', name)

        # 레시피 노이즈 키워드 제거
        for noise in RECIPE_TITLE_NOISE:
            name = name.replace(noise, '')

        name = name.strip()

        # 남은 텍스트에서 음식 이름 패턴 추출
        # 일반적으로 한국 음식명은 2~8자
        # 긴 텍스트가 남으면 앞부분만 (보통 핵심 음식명이 앞에 위치)
        if len(name) > 10:
            # 조리법 키워드로 분할하여 첫 번째 부분 취하기
            cooking_words = ["볶음", "무침", "조림", "구이", "찜", "전", "탕", "국"]
            for cw in cooking_words:
                idx = name.find(cw)
                if idx > 0 and idx + len(cw) <= 10:
                    name = name[:idx + len(cw)]
                    break
            else:
                # 조리법 키워드 없으면 처음 8자까지
                name = name[:8]

        return name.strip()

    async def get_remaining_count(self) -> int:
        """추정 남은 수 (만개의레시피에 약 3,000-5,000개 한식 레시피)"""
        return max(0, 3000 - len(self._collected_names))
