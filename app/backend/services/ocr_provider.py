"""
OCR Provider abstraction layer

Defines standard interface for different OCR providers.
All providers must implement OcrProvider abstract class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class OcrProviderType(str, Enum):
    """OCR 공급자 타입"""
    GPT_VISION = "gpt_vision"
    CLOVA = "clova"
    TESSERACT = "tesseract"


class OcrConfidenceLevel(str, Enum):
    """신뢰도 레벨"""
    HIGH = "high"      # >= 0.85
    MEDIUM = "medium"  # 0.70 ~ 0.84
    LOW = "low"        # < 0.70


@dataclass
class MenuItem:
    """메뉴 아이템 표준 스키마"""
    name_ko: str                    # 메뉴명 (필수)
    name_en: Optional[str] = None   # 영문명
    description: Optional[str] = None

    # 가격 정보 (확장된 구조)
    price: Optional[int] = None              # 단일 가격 (레거시)
    prices: Optional[List[dict]] = None      # 다중 가격 배열
    # prices 예시:
    # [
    #   {"size": "소", "price": 8000, "label": "소사이즈"},
    #   {"size": "중", "price": 10000, "label": "중사이즈"},
    #   {"size": "대", "price": 12000, "label": "대사이즈"}
    # ]
    is_set: bool = False                     # 세트 여부
    original_price: Optional[int] = None     # 원가 (할인 전)
    discount_price: Optional[int] = None     # 할인가

    # 메타데이터
    ingredients: Optional[List[str]] = field(default_factory=list)
    allergies: Optional[List[str]] = field(default_factory=list)
    category: Optional[str] = None


@dataclass
class OcrResult:
    """OCR 결과 표준 스키마"""
    provider: Optional[OcrProviderType]
    success: bool

    menu_items: List[MenuItem] = field(default_factory=list)
    raw_text: str = ""                       # OCR 원문

    # 신뢰도 및 진단 정보
    confidence: float = 0.0                  # 0.0 ~ 1.0
    confidence_level: Optional[OcrConfidenceLevel] = None

    # 감지 항목
    has_handwriting: bool = False            # 손글씨 감지
    price_parse_errors: List[str] = field(default_factory=list)

    # 캐싱용
    result_hash: str = ""                    # SHA256(image_hash + provider + output)
    processing_time_ms: int = 0

    # 폴백 정보
    triggered_fallback: bool = False
    fallback_reason: Optional[str] = None


class OcrProvider(ABC):
    """OCR 공급자 추상 기본 클래스"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.provider_type: OcrProviderType = None

    @abstractmethod
    async def extract(
        self,
        image_path: str,
        enable_preprocessing: bool = True
    ) -> OcrResult:
        """
        이미지에서 메뉴 정보 추출

        Args:
            image_path: 이미지 파일 경로
            enable_preprocessing: 전처리 활성화 여부

        Returns:
            OcrResult 표준 스키마

        Raises:
            OcrProviderException: 공급자 오류
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """헬스 체크"""
        pass


class OcrProviderException(Exception):
    """OCR 공급자 예외"""
    pass
