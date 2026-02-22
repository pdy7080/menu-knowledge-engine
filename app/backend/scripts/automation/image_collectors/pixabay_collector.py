"""
Pixabay Image Collector
무료 API로 한식 이미지 검색/다운로드

API: https://pixabay.com/api/
- 무료: 100 req/min (5000/day with key)
- CC0 License: 상업용 가능, attribution 불필요

Author: terminal-developer
Date: 2026-02-20
"""

import logging
import re
from pathlib import Path
from typing import List, Optional
import httpx

from .base_image_collector import BaseImageCollector, ImageResult
from ..config_auto import auto_settings

logger = logging.getLogger("automation.image.pixabay")

PIXABAY_API = "https://pixabay.com/api/"


class PixabayCollector(BaseImageCollector):
    """Pixabay 이미지 수집기"""

    source_name = "pixabay"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or auto_settings.PIXABAY_API_KEY

    async def search_images(
        self, query: str, menu_name_ko: str, per_page: int = 3
    ) -> List[ImageResult]:
        """Pixabay에서 이미지 검색"""
        if not self.api_key:
            logger.warning("Pixabay API key not configured")
            return []

        images = []
        search_query = f"korean food {query}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    PIXABAY_API,
                    params={
                        "key": self.api_key,
                        "q": search_query,
                        "per_page": per_page,
                        "image_type": "photo",
                        "category": "food",
                        "safesearch": "true",
                    },
                )

                if response.status_code == 429:
                    logger.warning("Pixabay rate limit reached")
                    return []
                if response.status_code != 200:
                    logger.warning(f"Pixabay API error: {response.status_code}")
                    return []

                data = response.json()
                hits = data.get("hits", [])

                for hit in hits:
                    images.append(
                        ImageResult(
                            menu_name_ko=menu_name_ko,
                            url=hit.get("webformatURL", ""),
                            source=self.source_name,
                            license="Pixabay License (CC0)",
                            attribution=f"Image by {hit.get('user', 'Unknown')} on Pixabay",
                            width=hit.get("webformatWidth", 0),
                            height=hit.get("webformatHeight", 0),
                        )
                    )

        except Exception as e:
            logger.error(f"Pixabay search error: {e}")

        return images

    async def download_image(self, image: ImageResult, save_dir: str) -> Optional[str]:
        """이미지 다운로드"""
        if not image.url:
            return None

        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        safe_name = re.sub(r"[^\w가-힣]", "_", image.menu_name_ko)
        filename = f"{safe_name}_{self.source_name}.jpg"
        filepath = save_path / filename

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image.url)
                if response.status_code == 200:
                    filepath.write_bytes(response.content)
                    image.local_path = str(filepath)
                    logger.info(
                        f"Downloaded: {filename} ({len(response.content) // 1024}KB)"
                    )
                    return str(filepath)
        except Exception as e:
            logger.error(f"Download error: {e}")

        return None
