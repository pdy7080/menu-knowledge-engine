"""
Image Matcher - 메뉴별 이미지 자동 검색 및 다운로드
여러 소스에서 최적 이미지를 찾아 매칭

Author: terminal-developer
Date: 2026-02-20
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .image_collectors.base_image_collector import BaseImageCollector, ImageResult
from .image_collectors.wikimedia_collector import WikimediaCollector
from .image_collectors.unsplash_collector import UnsplashCollector
from .image_collectors.pixabay_collector import PixabayCollector
from .state_manager import StateManager
from .config_auto import auto_settings, BACKEND_DIR

logger = logging.getLogger("automation.image_matcher")

# 기존 image_manifest.json 경로
MANIFEST_PATH = BACKEND_DIR / "data" / "image_manifest.json"


class ImageMatcher:
    """메뉴-이미지 매칭 오케스트레이터"""

    def __init__(self):
        self.state = StateManager("images")
        self.collectors: List[BaseImageCollector] = [
            WikimediaCollector(),   # 1순위: 최고 품질, CC 라이선스
            UnsplashCollector(),    # 2순위: 무료, attribution 불필요
            PixabayCollector(),     # 3순위: CC0, 가장 큰 라이브러리
        ]
        self.save_dir = str(
            Path(auto_settings.AUTOMATION_STAGING_DIR) / "images"
        )

    async def find_images_for_menu(
        self, name_ko: str, name_en: str
    ) -> List[ImageResult]:
        """
        메뉴에 대한 이미지 검색 (우선순위 순서로 소스 탐색)

        name_en이 있으면 "{name_en} Korean food"로 검색 (정확도 높음)
        name_en이 없으면 건너뛰기 (한국어만으로는 무관 이미지 반환)

        Args:
            name_ko: 한국어 메뉴명
            name_en: 영문 메뉴명

        Returns:
            찾은 이미지 리스트 (최대 3개)
        """
        if not name_en:
            logger.info(f"  Skip image search (no name_en): {name_ko}")
            return []

        all_images: List[ImageResult] = []
        query = f"{name_en} Korean food"

        for collector in self.collectors:
            if len(all_images) >= 3:
                break

            try:
                images = await collector.search_images(
                    query=query,
                    menu_name_ko=name_ko,
                    per_page=3,
                )
                # 최소 크기 필터 (300x300)
                for img in images:
                    if img.width >= 300 and img.height >= 300:
                        all_images.append(img)
            except Exception as e:
                logger.warning(f"{collector.source_name} search failed: {e}")

            await asyncio.sleep(0.5)

        return all_images[:3]

    async def batch_collect(
        self, menus_without_images: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        이미지 없는 메뉴에 대해 일괄 이미지 수집

        Args:
            menus_without_images: [{"name_ko": str, "name_en": str}, ...]

        Returns:
            수집 결과 요약
        """
        self.state.start_run()
        results = []
        source_counts: Dict[str, int] = {}
        found = 0
        downloaded = 0

        logger.info(f"Image collection: {len(menus_without_images)} menus")
        logger.info("=" * 60)

        for i, menu in enumerate(menus_without_images):
            name_ko = menu.get("name_ko", "")
            name_en = menu.get("name_en", "")

            # 이미 처리됨
            if self.state.is_processed(name_ko):
                continue

            logger.info(f"[{i + 1}/{len(menus_without_images)}] {name_ko}")

            images = await self.find_images_for_menu(name_ko, name_en)

            if images:
                found += len(images)
                # 첫 번째 이미지 다운로드
                best = images[0]
                for collector in self.collectors:
                    if collector.source_name == best.source:
                        path = await collector.download_image(best, self.save_dir)
                        if path:
                            downloaded += 1
                            src = best.source
                            source_counts[src] = source_counts.get(src, 0) + 1

                            results.append({
                                "name_ko": name_ko,
                                "image": {
                                    "url": best.url,
                                    "source": best.source,
                                    "license": best.license,
                                    "attribution": best.attribution,
                                    "local_path": path,
                                },
                            })
                        break

            self.state.mark_processed(name_ko)

            # Rate limit
            await asyncio.sleep(2.0)

            # 체크포인트
            if (i + 1) % 10 == 0:
                self.state.save_state()

        self.state.end_run(downloaded, len(menus_without_images) - downloaded)

        # manifest 업데이트
        self._update_manifest(results)

        summary = {
            "total_menus": len(menus_without_images),
            "images_found": found,
            "images_downloaded": downloaded,
            "sources": source_counts,
            "completed_at": datetime.now().isoformat(),
        }

        logger.info("\n" + "=" * 60)
        logger.info(f"Image collection complete:")
        logger.info(f"  Found: {found}, Downloaded: {downloaded}")
        logger.info(f"  Sources: {source_counts}")

        return summary

    def _update_manifest(self, results: List[Dict]):
        """image_manifest.json 업데이트 (기존 형식 유지)"""
        manifest = {}
        if MANIFEST_PATH.exists():
            try:
                with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
            except Exception:
                pass

        for item in results:
            name_ko = item["name_ko"]
            img = item["image"]
            manifest[name_ko] = {
                "source": img["source"],
                "public_url": img["url"],
                "local_path": img.get("local_path", ""),
                "license": img["license"],
                "attribution": img["attribution"],
                "collected_at": datetime.now().isoformat(),
            }

        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        logger.info(f"Manifest updated: {len(manifest)} total entries")
