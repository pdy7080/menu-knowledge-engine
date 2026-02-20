"""
Menu Discovery - 수집 오케스트레이터
여러 소스에서 수집 → 정규화 → 중복 제거 → DB 삽입

패턴: normalize.py의 정규화 로직 재사용

Author: terminal-developer
Date: 2026-02-20
"""
import asyncio
import json
import logging
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Any

from .collectors.base_collector import BaseCollector, DiscoveredMenu, CollectionResult
from .collectors.wikipedia_collector import WikipediaCollector
from .collectors.public_data_collector import PublicDataCollector
from .collectors.recipe_collector import RecipeCollector
from .menu_name_filter import filter_menu_name
from .state_manager import StateManager
from .config_auto import auto_settings, BACKEND_DIR

logger = logging.getLogger("automation.discovery")


def normalize_name(name: str) -> str:
    """
    메뉴명 정규화 (services/normalize.py 패턴)
    공백, 특수문자 제거
    """
    s = name.strip()
    # 메뉴 번호 제거
    s = re.sub(r'^\d+[\.\)\-\s]+', '', s)
    # 괄호 내용 제거
    s = re.sub(r'\(.*?\)', '', s)
    s = re.sub(r'\[.*?\]', '', s)
    # 공백 제거
    s = re.sub(r'\s+', '', s)
    # 특수문자 제거
    s = re.sub(r'[~!@#$%^&*_+=|\\<>?/:;"\',.\-★※●]', '', s)
    return s.strip()


def is_valid_menu_name(name: str) -> bool:
    """메뉴명 유효성 검사"""
    if not name or len(name) < 2:
        return False
    if len(name) > 30:
        return False
    # 한글이 최소 1자 포함
    if not re.search(r'[가-힣]', name):
        return False
    # 숫자만으로 구성되지 않음
    if re.match(r'^[\d\s]+$', name):
        return False
    return True


class MenuDiscovery:
    """메뉴 수집 오케스트레이터"""

    def __init__(self, existing_names: Set[str] = None):
        """
        Args:
            existing_names: DB에 이미 있는 메뉴명 세트 (중복 방지)
        """
        self.existing_names = existing_names or set()
        self.state = StateManager("collection")
        self.collectors: List[BaseCollector] = [
            PublicDataCollector(),   # 우선: 공공데이터 (가장 안전)
            WikipediaCollector(),    # 2순위: Wikipedia (CC 라이선스)
            RecipeCollector(),       # 3순위: 레시피 사이트
        ]

    async def load_existing_names_from_file(self):
        """기존 메뉴명을 시드 파일에서 로드"""
        seed_files = [
            BACKEND_DIR / "data" / "canonical_seed_data.json",
            BACKEND_DIR / "data" / "canonical_seed_enriched.json",
        ]

        for seed_file in seed_files:
            if seed_file.exists():
                try:
                    with open(seed_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    items = data if isinstance(data, list) else data.get("menus", [])
                    for item in items:
                        name = item.get("name_ko", "")
                        if name:
                            self.existing_names.add(normalize_name(name))
                except Exception as e:
                    logger.warning(f"Failed to load {seed_file}: {e}")

        logger.info(f"Loaded {len(self.existing_names)} existing menu names")

    async def discover_daily(self, target: int = 0) -> Dict[str, Any]:
        """
        일일 메뉴 수집 실행

        Args:
            target: 수집 목표 수 (기본: DAILY_MENU_TARGET)

        Returns:
            수집 결과 요약
        """
        target = target or auto_settings.DAILY_MENU_TARGET
        self.state.start_run()

        logger.info(f"Menu Discovery started (target: {target})")
        logger.info(f"Existing menus: {len(self.existing_names)}")
        logger.info("=" * 60)

        all_new_menus: List[DiscoveredMenu] = []
        source_stats: Dict[str, int] = {}
        total_discovered = 0
        total_duplicates = 0

        # 라운드 로빈으로 각 소스에서 수집
        for collector in self.collectors:
            if len(all_new_menus) >= target:
                break

            remaining = target - len(all_new_menus)
            logger.info(f"\nCollecting from: {collector.source_name} (need {remaining})")

            try:
                result = await collector.collect(limit=remaining)
                total_discovered += result.discovered

                # 정규화 + 품질 필터 + 중복 제거
                new_items = 0
                filtered_count = 0
                for menu in result.menus:
                    # 1단계: 기본 정규화
                    normalized = normalize_name(menu.name_ko)

                    # 2단계: 품질 필터 (브랜드/매장/개념/레시피 제거)
                    filtered = filter_menu_name(normalized)
                    if not filtered:
                        filtered_count += 1
                        continue

                    # 3단계: 중복 확인
                    if filtered in self.existing_names:
                        total_duplicates += 1
                        continue

                    # 신규 유효 메뉴!
                    menu.name_ko = filtered  # 필터링된 이름으로 업데이트
                    all_new_menus.append(menu)
                    self.existing_names.add(filtered)
                    new_items += 1

                if filtered_count > 0:
                    logger.info(f"  {collector.source_name}: {filtered_count} filtered by quality")

                source_stats[collector.source_name] = new_items
                logger.info(f"  {collector.source_name}: {new_items} new menus")

            except Exception as e:
                logger.error(f"Collector error ({collector.source_name}): {e}")
                source_stats[collector.source_name] = 0

        # 결과 저장
        staging_dir = Path(auto_settings.AUTOMATION_STAGING_DIR) / "new_menus"
        staging_dir.mkdir(parents=True, exist_ok=True)

        output_data = {
            "discovered_at": datetime.now().isoformat(),
            "total_discovered": total_discovered,
            "total_new": len(all_new_menus),
            "total_duplicates": total_duplicates,
            "sources": source_stats,
            "menus": [
                {
                    "name_ko": m.name_ko,
                    "name_en": m.name_en,
                    "source": m.source,
                    "category_hint": m.category_hint,
                    "description_ko": m.description_ko,
                    "description_en": m.description_en,
                    "ingredients": m.ingredients,
                }
                for m in all_new_menus
            ],
        }

        output_file = staging_dir / f"discovery_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        self.state.end_run(len(all_new_menus), total_duplicates)

        logger.info("\n" + "=" * 60)
        logger.info(f"Discovery complete:")
        logger.info(f"  Total discovered: {total_discovered}")
        logger.info(f"  New menus: {len(all_new_menus)}")
        logger.info(f"  Duplicates filtered: {total_duplicates}")
        logger.info(f"  Sources: {source_stats}")
        logger.info(f"  Saved to: {output_file}")

        return output_data


async def main():
    """단독 실행용"""
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    from .logging_config import setup_logging
    setup_logging()

    discovery = MenuDiscovery()
    await discovery.load_existing_names_from_file()
    result = await discovery.discover_daily(target=10)

    print(f"\nResult: {result['total_new']} new menus discovered")


if __name__ == "__main__":
    asyncio.run(main())
