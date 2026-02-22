"""
Wikimedia Commons Image Collector
기존 collect_wikipedia_images.py 로직을 리팩토링

CC 라이선스 이미지만 수집 (합법)
Wikimedia API 정책 준수 (User-Agent, rate limit)

Author: terminal-developer
Date: 2026-02-20
"""

import logging
import re
from pathlib import Path
from typing import List, Optional
import httpx

from .base_image_collector import BaseImageCollector, ImageResult

logger = logging.getLogger("automation.image.wikimedia")

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "MenuKnowledgeBot/2.0 "
        "(https://github.com/user/menu-knowledge-engine; "
        "menu-knowledge-bot@chargeapp.net) "
        "python-httpx/0.28"
    ),
    "Accept": "application/json",
}

# CC 라이선스 허용 키워드 (공백/하이픈 모두 매칭)
ALLOWED_LICENSE_KEYWORDS = {"cc by", "cc-by", "cc0", "pd", "public domain"}


class WikimediaCollector(BaseImageCollector):
    """Wikimedia Commons 이미지 수집기"""

    source_name = "wikimedia"

    async def search_images(
        self, query: str, menu_name_ko: str, per_page: int = 3
    ) -> List[ImageResult]:
        """Wikimedia Commons에서 이미지 검색"""
        images = []
        search_query = f"{query} korean food"

        try:
            async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
                # Step 1: 이미지 검색
                response = await client.get(
                    WIKIMEDIA_API,
                    params={
                        "action": "query",
                        "generator": "search",
                        "gsrnamespace": "6",  # File namespace
                        "gsrsearch": search_query,
                        "gsrlimit": per_page,
                        "prop": "imageinfo",
                        "iiprop": "url|size|extmetadata",
                        "iiurlwidth": 800,
                        "format": "json",
                    },
                )

                if response.status_code != 200:
                    logger.warning(f"Wikimedia API error: {response.status_code}")
                    return images

                data = response.json()
                pages = data.get("query", {}).get("pages", {})

                for page_data in pages.values():
                    imageinfo = page_data.get("imageinfo", [{}])
                    if not imageinfo:
                        continue

                    info = imageinfo[0]
                    ext_meta = info.get("extmetadata", {})

                    # 라이선스 확인
                    license_short = (
                        ext_meta.get("LicenseShortName", {}).get("value", "").lower()
                    )
                    if not any(kw in license_short for kw in ALLOWED_LICENSE_KEYWORDS):
                        continue

                    thumb_url = info.get("thumburl", info.get("url", ""))
                    if not thumb_url:
                        continue

                    artist = ext_meta.get("Artist", {}).get("value", "Unknown")
                    # HTML 태그 제거
                    artist = re.sub(r"<[^>]+>", "", artist).strip()

                    images.append(
                        ImageResult(
                            menu_name_ko=menu_name_ko,
                            url=thumb_url,
                            source=self.source_name,
                            license=license_short,
                            attribution=f"{artist} via Wikimedia Commons",
                            width=info.get("thumbwidth", info.get("width", 0)),
                            height=info.get("thumbheight", info.get("height", 0)),
                        )
                    )

        except Exception as e:
            logger.error(f"Wikimedia search error: {e}")

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
            async with httpx.AsyncClient(timeout=30.0, headers=HEADERS) as client:
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
