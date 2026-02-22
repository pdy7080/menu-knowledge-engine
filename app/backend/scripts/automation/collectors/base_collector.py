"""
Base Collector - 메뉴 데이터 수집기 추상 클래스
모든 수집기는 이 클래스를 상속받아 구현
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DiscoveredMenu:
    """수집된 메뉴 데이터"""

    name_ko: str  # 한국어 메뉴명 (필수)
    name_en: Optional[str] = None  # 영문 메뉴명
    source: str = ""  # 수집 소스 ("wikipedia", "data_go_kr", "recipe")
    category_hint: Optional[str] = None  # 카테고리 힌트
    description_ko: Optional[str] = None  # 간단 설명
    description_en: Optional[str] = None  # 영문 설명
    ingredients: List[str] = field(default_factory=list)  # 재료 목록
    raw_data: dict = field(default_factory=dict)  # 원본 데이터


@dataclass
class CollectionResult:
    """수집 결과"""

    source: str
    discovered: int = 0
    new_items: int = 0
    duplicates: int = 0
    errors: int = 0
    menus: List[DiscoveredMenu] = field(default_factory=list)


class BaseCollector(ABC):
    """메뉴 데이터 수집기 추상 클래스"""

    source_name: str = "unknown"

    @abstractmethod
    async def collect(self, limit: int = 50) -> CollectionResult:
        """
        메뉴 데이터 수집

        Args:
            limit: 최대 수집 수

        Returns:
            CollectionResult
        """
        ...

    @abstractmethod
    async def get_remaining_count(self) -> int:
        """
        이 소스에서 추가 수집 가능한 메뉴 수

        Returns:
            남은 메뉴 수 (추정)
        """
        ...
