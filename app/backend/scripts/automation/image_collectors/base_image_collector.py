"""
Base Image Collector - 이미지 수집기 추상 클래스
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ImageResult:
    """수집된 이미지 데이터"""
    menu_name_ko: str                    # 매칭된 메뉴명
    url: str                             # 원본 이미지 URL
    source: str = ""                     # "unsplash", "pixabay", "wikimedia"
    license: str = ""                    # 라이선스 유형
    attribution: str = ""               # 저작자 정보
    width: int = 0
    height: int = 0
    local_path: Optional[str] = None    # 다운로드된 로컬 경로


@dataclass
class ImageCollectionResult:
    """이미지 수집 결과"""
    source: str
    found: int = 0
    downloaded: int = 0
    errors: int = 0
    images: List[ImageResult] = field(default_factory=list)


class BaseImageCollector(ABC):
    """이미지 수집기 추상 클래스"""

    source_name: str = "unknown"

    @abstractmethod
    async def search_images(
        self, query: str, menu_name_ko: str, per_page: int = 3
    ) -> List[ImageResult]:
        """
        이미지 검색

        Args:
            query: 검색어 (영문 메뉴명)
            menu_name_ko: 한국어 메뉴명 (매칭용)
            per_page: 결과 수

        Returns:
            검색된 이미지 리스트
        """
        ...

    @abstractmethod
    async def download_image(
        self, image: ImageResult, save_dir: str
    ) -> Optional[str]:
        """
        이미지 다운로드

        Args:
            image: 이미지 정보
            save_dir: 저장 디렉토리

        Returns:
            저장된 파일 경로 또는 None
        """
        ...
