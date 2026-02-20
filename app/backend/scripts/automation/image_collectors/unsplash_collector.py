"""
Unsplash Image Collector
무료 API로 한식 이미지 검색/다운로드

API: https://api.unsplash.com
- 무료: 50 req/hr (demo), 5000 req/hr (production)
- Unsplash License: 상업용 가능, attribution 불필요

Author: terminal-developer
Date: 2026-02-20
"""
import asyncio
import logging
import re
from pathlib import Path
from typing import List, Optional
import httpx

from .base_image_collector import BaseImageCollector, ImageResult, ImageCollectionResult
from ..config_auto import auto_settings

logger = logging.getLogger("automation.image.unsplash")

UNSPLASH_API = "https://api.unsplash.com"


class UnsplashCollector(BaseImageCollector):
    """Unsplash 이미지 수집기"""

    source_name = "unsplash"

    def __init__(self, access_key: str = ""):
        self.access_key = access_key or auto_settings.UNSPLASH_ACCESS_KEY

    async def search_images(
        self, query: str, menu_name_ko: str, per_page: int = 3
    ) -> List[ImageResult]:
        """Unsplash에서 이미지 검색"""
        if not self.access_key:
            logger.warning("Unsplash API key not configured")
            return []

        images = []
        search_query = query  # 메뉴 영문명 그대로 사용

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{UNSPLASH_API}/search/photos",
                    params={
                        "query": search_query,
                        "per_page": per_page,
                    },
                    headers={
                        "Authorization": f"Client-ID {self.access_key}",
                    },
                )

                if response.status_code == 403:
                    logger.warning("Unsplash rate limit reached")
                    return []
                if response.status_code != 200:
                    logger.warning(f"Unsplash API error: {response.status_code}")
                    return []

                data = response.json()
                results = data.get("results", [])

                for photo in results:
                    images.append(ImageResult(
                        menu_name_ko=menu_name_ko,
                        url=photo.get("urls", {}).get("regular", ""),
                        source=self.source_name,
                        license="Unsplash License",
                        attribution=f"Photo by {photo.get('user', {}).get('name', 'Unknown')} on Unsplash",
                        width=photo.get("width", 0),
                        height=photo.get("height", 0),
                    ))

        except Exception as e:
            logger.error(f"Unsplash search error: {e}")

        return images

    async def download_image(
        self, image: ImageResult, save_dir: str
    ) -> Optional[str]:
        """이미지 다운로드"""
        if not image.url:
            return None

        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        # 파일명: menu_name_unsplash_1.jpg
        safe_name = re.sub(r'[^\w가-힣]', '_', image.menu_name_ko)
        filename = f"{safe_name}_{self.source_name}.jpg"
        filepath = save_path / filename

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image.url)
                if response.status_code == 200:
                    filepath.write_bytes(response.content)
                    image.local_path = str(filepath)
                    logger.info(f"Downloaded: {filename} ({len(response.content) // 1024}KB)")
                    return str(filepath)
        except Exception as e:
            logger.error(f"Download error: {e}")

        return None
