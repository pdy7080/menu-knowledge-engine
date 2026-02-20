"""
Public Data Collector
data.go.kr 및 기존 수집 데이터에서 새 메뉴명 발견

Sources:
1. highway_food_canonical_candidates.json (351 candidates)
2. data.go.kr Nutrition DB (food names)
3. 메뉴젠 API (식품 코드)

패턴: public_data_client.py의 httpx async 패턴을 따름

Author: terminal-developer
Date: 2026-02-20
"""
import json
import logging
from pathlib import Path
from typing import List, Set

from .base_collector import BaseCollector, CollectionResult, DiscoveredMenu
from ..config_auto import BACKEND_DIR

logger = logging.getLogger("automation.collector.public_data")

# 기존 수집 데이터 경로
DATA_DIR = BACKEND_DIR / "data"
HIGHWAY_CANDIDATES = DATA_DIR / "highway_food_canonical_candidates.json"
HIGHWAY_RAW = DATA_DIR / "highway_food_raw.json"


class PublicDataCollector(BaseCollector):
    """공공데이터 기반 메뉴 수집기"""

    source_name = "data_go_kr"

    def __init__(self):
        self._used_names: Set[str] = set()

    async def collect(self, limit: int = 50) -> CollectionResult:
        """공공데이터에서 새 메뉴 수집"""
        result = CollectionResult(source=self.source_name)
        all_menus: List[DiscoveredMenu] = []

        # Source 1: 기존 highway food candidates (이미 수집됨)
        highway_menus = self._load_highway_candidates(limit)
        all_menus.extend(highway_menus)

        # Source 2: highway_food_raw.json에서 추가 메뉴 발견
        if len(all_menus) < limit:
            remaining = limit - len(all_menus)
            raw_menus = self._extract_from_raw_highway(remaining)
            all_menus.extend(raw_menus)

        result.discovered = len(all_menus)
        result.menus = all_menus[:limit]
        result.new_items = len(result.menus)
        logger.info(f"Public data: collected {result.discovered} food items")

        return result

    def _load_highway_candidates(self, limit: int) -> List[DiscoveredMenu]:
        """highway_food_canonical_candidates.json에서 메뉴 로드"""
        menus = []

        if not HIGHWAY_CANDIDATES.exists():
            logger.warning(f"File not found: {HIGHWAY_CANDIDATES}")
            return menus

        try:
            with open(HIGHWAY_CANDIDATES, 'r', encoding='utf-8') as f:
                candidates = json.load(f)

            for item in candidates[:limit]:
                name_ko = item.get("name", item.get("food_name", ""))
                if not name_ko or name_ko in self._used_names:
                    continue

                self._used_names.add(name_ko)
                menus.append(DiscoveredMenu(
                    name_ko=name_ko,
                    source=self.source_name,
                    category_hint=item.get("category", ""),
                    raw_data=item,
                ))

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load highway candidates: {e}")

        return menus

    def _extract_from_raw_highway(self, limit: int) -> List[DiscoveredMenu]:
        """highway_food_raw.json에서 고유 메뉴명 추출"""
        menus = []

        if not HIGHWAY_RAW.exists():
            logger.warning(f"File not found: {HIGHWAY_RAW}")
            return menus

        try:
            with open(HIGHWAY_RAW, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            # 데이터 구조: list of items with foodNm field
            items = raw_data if isinstance(raw_data, list) else raw_data.get("items", [])

            seen_names: Set[str] = set()
            for item in items:
                name_ko = item.get("foodNm", item.get("food_name", ""))
                if not name_ko:
                    continue

                # 정규화 (공백 제거, 특수문자 정리)
                name_ko = name_ko.strip()
                name_ko = name_ko.lstrip("★※● ")

                # 중복 및 이미 사용된 이름 건너뛰기
                if name_ko in seen_names or name_ko in self._used_names:
                    continue
                if len(name_ko) < 2:
                    continue

                seen_names.add(name_ko)
                self._used_names.add(name_ko)

                menus.append(DiscoveredMenu(
                    name_ko=name_ko,
                    source=self.source_name,
                    raw_data={
                        "rest_area": item.get("stdRestNm", ""),
                        "price": item.get("foodCost", ""),
                    },
                ))

                if len(menus) >= limit:
                    break

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load highway raw data: {e}")

        return menus

    async def get_remaining_count(self) -> int:
        """추정 남은 수"""
        total = 0

        if HIGHWAY_CANDIDATES.exists():
            try:
                with open(HIGHWAY_CANDIDATES, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total += len(data)
            except Exception:
                pass

        return max(0, total - len(self._used_names))
