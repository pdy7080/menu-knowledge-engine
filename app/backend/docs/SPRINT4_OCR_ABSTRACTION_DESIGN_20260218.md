# Sprint 4: OCR Provider Abstraction + Tier Router 설계 문서

**작성일**: 2026-02-18
**목표**: CLOVA 기존 구현을 유지하면서 OCR Provider 추상화 + Tier 라우팅 시스템 구축
**패턴**: Layering (교체 X, 추상화 O)
**참고**: Sprint 3B CLOVA 구현 기반 (app/backend/services/ocr_service.py)

---

## 개요

### 핵심 결정사항
- **CLOVA 유지**: 기존 구현(Sprint 3B) 완전 보존
- **Tier 재구성**: CLOVA는 Tier 2 fallback으로 격하, GPT-4o mini Vision을 Tier 1 primary로 추가
- **추상화 우선**: 구현이 아니라 인터페이스 설계부터 시작
- **레이어링**: OCR Provider 인터페이스 + Orchestrator + Tier Router 3계층

### 기존 vs 신규 아키텍처

```
[기존 Sprint 3B]
Application
  ↓
ocr_service.recognize_menu_image()
  ↓
CLOVA OCR API (하드코딩)

[신규 Sprint 4]
Application
  ↓
OrchestratorService.extract_menu()  ← 새로운 진입점
  ↓
TierRouter (Tier 1 → Tier 2 → fallback)
  ├── Tier 1: OcrProviderGpt (GPT-4o mini Vision) ← 새로운
  └── Tier 2: OcrProviderClova (CLOVA) ← 기존 코드 래핑
      ↓
      recognize_menu_image() [기존 코드]
```

---

## 1단계: OCR Provider 인터페이스 설계

### 1-1. OcrProvider 기본 인터페이스

**파일**: `app/backend/services/ocr_provider.py` (신규 생성)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class OcrProviderType(str, Enum):
    """OCR 공급자 타입"""
    GPT_VISION = "gpt_vision"
    CLOVA = "clova"
    TESSERACT = "tesseract"  # 미래용

class OcrConfidenceLevel(str, Enum):
    """신뢰도 레벨"""
    HIGH = "high"      # >= 0.85
    MEDIUM = "medium"  # 0.70 ~ 0.84
    LOW = "low"        # < 0.70

@dataclass
class MenuItem:
    """메뉴 아이템 표준 스키마"""
    name_ko: str                    # 메뉴명
    name_en: Optional[str] = None   # 영문명
    description: Optional[str] = None

    # 가격 정보 (확장된 구조)
    price: Optional[int] = None              # 단일 가격
    prices: Optional[List[dict]] = None      # 다중 가격 배열
    # prices 예시:
    # [
    #   {"size": "소", "price": 8000},
    #   {"size": "중", "price": 10000},
    #   {"size": "대", "price": 12000}
    # ]
    is_set: bool = False                     # 세트 여부
    original_price: Optional[int] = None     # 원가 (할인 전)
    discount_price: Optional[int] = None     # 할인가

    # 메타데이터
    ingredients: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    category: Optional[str] = None

@dataclass
class OcrResult:
    """OCR 결과 표준 스키마"""
    provider: OcrProviderType
    success: bool

    menu_items: List[MenuItem]
    raw_text: str                       # OCR 원문

    # 신뢰도 및 진단 정보
    confidence: float                   # 0.0 ~ 1.0
    confidence_level: OcrConfidenceLevel

    # 감지 항목
    has_handwriting: bool = False      # 손글씨 감지
    price_parse_errors: List[str] = None  # 가격 파싱 에러

    # 캐싱용
    result_hash: str = ""              # SHA256(image_hash + provider + output)
    processing_time_ms: int = 0

    # 폴백 정보
    triggered_fallback: bool = False
    fallback_reason: Optional[str] = None

class OcrProvider(ABC):
    """OCR 공급자 추상 기본 클래스"""

    def __init__(self, config: dict):
        self.config = config
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
            ImageProcessingException: 이미지 처리 오류
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """헬스 체크"""
        pass

class OcrProviderException(Exception):
    """OCR 공급자 예외"""
    pass
```

---

### 1-2. GPT-4o mini Vision Provider 구현

**파일**: `app/backend/services/ocr_provider_gpt.py` (신규 생성)

```python
import logging
import hashlib
import time
from typing import Optional
import json
import base64
from pathlib import Path

from openai import AsyncOpenAI
from services.ocr_provider import (
    OcrProvider,
    OcrResult,
    MenuItem,
    OcrProviderType,
    OcrConfidenceLevel,
    OcrProviderException,
)
from config import settings

logger = logging.getLogger(__name__)

class OcrProviderGpt(OcrProvider):
    """GPT-4o mini Vision을 사용한 OCR 공급자"""

    def __init__(self, config: dict = None):
        super().__init__(config or {})
        self.provider_type = OcrProviderType.GPT_VISION
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
        self.temperature = 0  # 결정론성 확보 (매번 같은 결과)

    async def extract(
        self,
        image_path: str,
        enable_preprocessing: bool = True
    ) -> OcrResult:
        """
        GPT-4o mini Vision으로 메뉴 이미지 분석

        3단계:
        1. 이미지 인코딩 (base64)
        2. GPT API 호출 (vision + JSON schema)
        3. 결과 파싱 및 신뢰도 계산
        """
        start_time = time.time()

        try:
            # Step 1: 이미지 로드 및 전처리
            image_bytes = self._load_and_preprocess(image_path, enable_preprocessing)
            image_b64 = base64.b64encode(image_bytes).decode()

            # Step 2: GPT Vision 호출
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=self.temperature,  # 결정론적 출력
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": self._build_prompt(),
                            }
                        ],
                    }
                ],
            )

            # Step 3: 응답 파싱
            raw_text = response.content[0].text
            menu_items, parse_errors = self._parse_response(raw_text)

            # Step 4: 신뢰도 계산
            confidence = self._calculate_confidence(
                menu_items=menu_items,
                parse_errors=parse_errors,
                response_tokens=response.usage.output_tokens,
            )

            # Step 5: 결과 해시 생성
            result_hash = self._compute_result_hash(image_path, raw_text)

            processing_time = int((time.time() - start_time) * 1000)

            return OcrResult(
                provider=self.provider_type,
                success=len(menu_items) > 0,
                menu_items=menu_items,
                raw_text=raw_text,
                confidence=confidence,
                confidence_level=self._get_confidence_level(confidence),
                has_handwriting=self._detect_handwriting(raw_text),
                price_parse_errors=parse_errors,
                result_hash=result_hash,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"GPT OCR 실패: {str(e)}")
            raise OcrProviderException(f"GPT Vision OCR 실패: {str(e)}")

    async def health_check(self) -> bool:
        """OpenAI API 헬스 체크"""
        try:
            # 매우 작은 요청으로 API 접근성 확인
            await self.client.models.retrieve(self.model)
            return True
        except Exception as e:
            logger.error(f"GPT API 헬스 체크 실패: {str(e)}")
            return False

    def _build_prompt(self) -> str:
        """GPT Vision 프롬프트 (JSON Schema 강제)"""
        return """음식점 메뉴판 이미지를 분석하여 다음 JSON 형식으로 반환하세요.

필수 조건:
- 손글씨 여부를 반드시 표기
- 각 메뉴의 신뢰도(0~1)를 개별 기록
- 가격은 다중값(배열) 또는 단일값으로 반환
- 세트상품은 is_set: true로 표기

JSON Schema:
{
  "has_handwriting": bool,
  "menu_items": [
    {
      "name_ko": "메뉴명",
      "name_en": "메뉴명 영문 (선택)",
      "description": "설명 (선택)",
      "price": 단일가격 또는 null,
      "prices": [
        {"size": "소", "price": 8000},
        {"size": "중", "price": 10000}
      ] 또는 null,
      "is_set": false,
      "confidence": 0.95,
      "ingredients": ["재료1", "재료2"] 선택,
      "category": "카테고리"
    }
  ]
}

주의:
- 데이터 없음 필드는 null 사용
- 가격은 숫자형 (문자열 아님)
- 신뢰도 0.85 이상만 반환 권장
"""

    def _parse_response(self, raw_text: str) -> tuple[list[MenuItem], list[str]]:
        """GPT 응답을 MenuItem 리스트로 파싱"""
        menu_items = []
        parse_errors = []

        try:
            # JSON 추출
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1
            json_str = raw_text[json_start:json_end]
            data = json.loads(json_str)

            # 메뉴 아이템 변환
            for item in data.get('menu_items', []):
                try:
                    menu_item = MenuItem(
                        name_ko=item.get('name_ko'),
                        name_en=item.get('name_en'),
                        description=item.get('description'),
                        price=item.get('price'),
                        prices=item.get('prices'),
                        is_set=item.get('is_set', False),
                        original_price=item.get('original_price'),
                        discount_price=item.get('discount_price'),
                        ingredients=item.get('ingredients'),
                        category=item.get('category'),
                    )
                    menu_items.append(menu_item)
                except Exception as e:
                    parse_errors.append(f"메뉴 파싱 오류: {str(e)}")

        except json.JSONDecodeError as e:
            parse_errors.append(f"JSON 파싱 실패: {str(e)}")
        except Exception as e:
            parse_errors.append(f"응답 처리 오류: {str(e)}")

        return menu_items, parse_errors

    def _calculate_confidence(
        self,
        menu_items: list[MenuItem],
        parse_errors: list[str],
        response_tokens: int,
    ) -> float:
        """신뢰도 계산 로직"""
        base_confidence = 0.75

        # 메뉴 아이템 수 (0개 = 신뢰도 0, 많을수록 증가)
        if not menu_items:
            return 0.0

        item_count_bonus = min(len(menu_items) * 0.02, 0.15)  # 최대 +0.15

        # 파싱 에러 페널티
        error_penalty = len(parse_errors) * 0.05  # 에러당 -0.05

        # 응답 토큰 (너무 적으면 신뢰도 낮음)
        if response_tokens < 100:
            token_penalty = 0.1
        else:
            token_penalty = 0

        confidence = base_confidence + item_count_bonus - error_penalty - token_penalty
        return max(0.0, min(1.0, confidence))  # 0~1 범위로 제한

    def _detect_handwriting(self, raw_text: str) -> bool:
        """손글씨 감지 (응답 텍스트에 'handwriting' 키워드 포함 여부)"""
        return "handwriting" in raw_text.lower() and "true" in raw_text.lower()

    def _get_confidence_level(self, confidence: float) -> OcrConfidenceLevel:
        """신뢰도 점수를 레벨로 변환"""
        if confidence >= 0.85:
            return OcrConfidenceLevel.HIGH
        elif confidence >= 0.70:
            return OcrConfidenceLevel.MEDIUM
        else:
            return OcrConfidenceLevel.LOW

    def _compute_result_hash(self, image_path: str, raw_text: str) -> str:
        """결과 해시 계산 (캐싱용)"""
        # 이미지 파일의 MD5
        with open(image_path, 'rb') as f:
            image_hash = hashlib.md5(f.read()).hexdigest()

        # 이미지 해시 + 출력 텍스트 해시
        combined = f"{image_hash}:{raw_text}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _load_and_preprocess(self, image_path: str, enable_preprocessing: bool) -> bytes:
        """이미지 로드 및 전처리"""
        if enable_preprocessing:
            from utils.image_preprocessing import preprocess_menu_image
            preprocessed_path = preprocess_menu_image(image_path)
            image_path = preprocessed_path

        with open(image_path, 'rb') as f:
            return f.read()
```

---

### 1-3. CLOVA Provider 래핑

**파일**: `app/backend/services/ocr_provider_clova.py` (신규 생성)

```python
import logging
import hashlib
import time
from services.ocr_provider import (
    OcrProvider,
    OcrResult,
    MenuItem,
    OcrProviderType,
    OcrConfidenceLevel,
    OcrProviderException,
)
from services.ocr_service import ocr_service  # 기존 CLOVA 구현

logger = logging.getLogger(__name__)

class OcrProviderClova(OcrProvider):
    """CLOVA OCR을 추상화된 OcrProvider로 래핑"""

    def __init__(self, config: dict = None):
        super().__init__(config or {})
        self.provider_type = OcrProviderType.CLOVA
        # 기존 ocr_service 사용

    async def extract(
        self,
        image_path: str,
        enable_preprocessing: bool = True
    ) -> OcrResult:
        """
        CLOVA OCR로 메뉴 이미지 분석
        기존 recognize_menu_image() 함수를 래핑
        """
        start_time = time.time()

        try:
            # 기존 CLOVA 함수 호출
            clova_result = await ocr_service.recognize_menu_image(
                image_path=image_path,
                enable_preprocessing=enable_preprocessing,
            )

            # CLOVA 응답을 OcrResult로 변환
            menu_items = self._convert_clova_response(clova_result)

            # 신뢰도 계산
            confidence = self._calculate_confidence(
                clova_result=clova_result,
                menu_items=menu_items,
            )

            # 결과 해시
            result_hash = self._compute_result_hash(image_path, clova_result)

            processing_time = int((time.time() - start_time) * 1000)

            return OcrResult(
                provider=self.provider_type,
                success=clova_result.get('success', False),
                menu_items=menu_items,
                raw_text=clova_result.get('raw_text', ''),
                confidence=confidence,
                confidence_level=self._get_confidence_level(confidence),
                has_handwriting=clova_result.get('has_handwriting', False),
                price_parse_errors=[],  # CLOVA는 에러 목록 미제공
                result_hash=result_hash,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"CLOVA OCR 실패: {str(e)}")
            raise OcrProviderException(f"CLOVA OCR 실패: {str(e)}")

    async def health_check(self) -> bool:
        """CLOVA API 헬스 체크"""
        try:
            # 기존 CLOVA 서비스의 헬스 체크 구현 필요
            return await ocr_service.health_check()
        except Exception as e:
            logger.error(f"CLOVA 헬스 체크 실패: {str(e)}")
            return False

    def _convert_clova_response(self, clova_result: dict) -> list[MenuItem]:
        """CLOVA 응답을 MenuItem 리스트로 변환"""
        menu_items = []

        for item in clova_result.get('menu_items', []):
            try:
                # CLOVA 응답 필드를 MenuItem으로 매핑
                menu_item = MenuItem(
                    name_ko=item.get('name_ko'),
                    name_en=item.get('name_en'),
                    description=item.get('description'),
                    price=item.get('price'),
                    prices=item.get('prices'),
                    is_set=item.get('is_set', False),
                    ingredients=item.get('ingredients'),
                    category=item.get('category'),
                )
                menu_items.append(menu_item)
            except Exception as e:
                logger.warning(f"CLOVA 메뉴 변환 실패: {str(e)}")

        return menu_items

    def _calculate_confidence(
        self,
        clova_result: dict,
        menu_items: list[MenuItem],
    ) -> float:
        """신뢰도 계산"""
        # CLOVA는 신뢰도 점수를 제공하지 않으므로 휴리스틱 사용
        base_confidence = 0.80  # CLOVA는 한글 95%+ 정확도

        # 메뉴 아이템 수 기반 조정
        if not menu_items:
            return 0.0

        # CLOVA 응답 필드 확인
        if 'confidence' in clova_result:
            return clova_result['confidence']

        # 기본값 반환
        return min(base_confidence, 0.90)

    def _get_confidence_level(self, confidence: float) -> OcrConfidenceLevel:
        """신뢰도 점수를 레벨로 변환"""
        if confidence >= 0.85:
            return OcrConfidenceLevel.HIGH
        elif confidence >= 0.70:
            return OcrConfidenceLevel.MEDIUM
        else:
            return OcrConfidenceLevel.LOW

    def _compute_result_hash(self, image_path: str, clova_result: dict) -> str:
        """결과 해시 계산"""
        with open(image_path, 'rb') as f:
            image_hash = hashlib.md5(f.read()).hexdigest()

        result_text = str(clova_result)
        combined = f"{image_hash}:{result_text}"
        return hashlib.sha256(combined.encode()).hexdigest()
```

---

## 2단계: OCR Orchestrator + Tier Router 설계

### 2-1. Tier Router 구현

**파일**: `app/backend/services/ocr_tier_router.py` (신규 생성)

```python
import logging
from typing import Optional
from enum import Enum
from dataclasses import dataclass

from services.ocr_provider import (
    OcrProvider,
    OcrResult,
    OcrProviderType,
    OcrProviderException,
)
from services.ocr_provider_gpt import OcrProviderGpt
from services.ocr_provider_clova import OcrProviderClova

logger = logging.getLogger(__name__)

class TierLevel(str, Enum):
    """Tier 레벨"""
    TIER_1 = "tier_1"  # Primary
    TIER_2 = "tier_2"  # Fallback
    TIER_3 = "tier_3"  # Growth (미래용)

@dataclass
class FallbackTrigger:
    """Tier 폴백 트리거 조건"""
    confidence_threshold: float = 0.75
    min_menu_items: int = 1
    allow_on_handwriting: bool = False
    allow_on_price_error: bool = True
    allow_on_item_count_anomaly: bool = True

class OcrTierRouter:
    """
    Tier 기반 OCR 라우팅 시스템

    Tier 1: GPT-4o mini Vision (빠르고, 구조화된 출력)
    Tier 2: CLOVA OCR (Tier 1 실패 시 fallback, 한글 특화)
    Tier 3: Tesseract (미래용, 로컬)
    """

    def __init__(self):
        self.tier_1_provider: Optional[OcrProvider] = OcrProviderGpt()
        self.tier_2_provider: Optional[OcrProvider] = OcrProviderClova()
        self.tier_3_provider: Optional[OcrProvider] = None

        self.tier_1_trigger = FallbackTrigger(
            confidence_threshold=0.75,
            min_menu_items=1,
            allow_on_handwriting=False,  # 손글씨 감지 시 폴백
            allow_on_price_error=True,
            allow_on_item_count_anomaly=True,
        )

        self.tier_2_trigger = FallbackTrigger(
            confidence_threshold=0.70,
            min_menu_items=1,
            allow_on_handwriting=True,  # 손글씨도 처리
            allow_on_price_error=False,  # 가격 에러 시 실패 반환
            allow_on_item_count_anomaly=False,
        )

    async def route(
        self,
        image_path: str,
        enable_preprocessing: bool = True,
        force_tier: Optional[TierLevel] = None,  # 강제 Tier 선택 (테스트용)
    ) -> OcrResult:
        """
        Tier 라우팅 로직

        1. Tier 1 (GPT Vision) 시도
        2. Tier 1 실패 또는 폴백 조건 만족 시 Tier 2 (CLOVA) 시도
        3. Tier 2 실패 시 최후의 결과 반환 또는 예외 발생
        """

        # 강제 Tier 선택 (디버깅용)
        if force_tier:
            return await self._execute_tier(force_tier, image_path, enable_preprocessing)

        # Tier 1: GPT Vision
        logger.info("Tier 1 (GPT Vision) 시도...")
        result_tier_1 = await self._execute_tier(TierLevel.TIER_1, image_path, enable_preprocessing)

        # Tier 1 결과 평가
        if self._should_fallback(result_tier_1, self.tier_1_trigger):
            logger.warning(
                f"Tier 1 폴백 트리거: confidence={result_tier_1.confidence:.2f}, "
                f"handwriting={result_tier_1.has_handwriting}, "
                f"errors={len(result_tier_1.price_parse_errors)}"
            )

            # Tier 2: CLOVA
            logger.info("Tier 2 (CLOVA) 시도...")
            result_tier_2 = await self._execute_tier(TierLevel.TIER_2, image_path, enable_preprocessing)
            result_tier_2.triggered_fallback = True
            result_tier_2.fallback_reason = f"Tier 1 폴백: {self._get_fallback_reason(result_tier_1, self.tier_1_trigger)}"

            return result_tier_2

        logger.info(f"Tier 1 성공: confidence={result_tier_1.confidence:.2f}")
        return result_tier_1

    async def _execute_tier(
        self,
        tier_level: TierLevel,
        image_path: str,
        enable_preprocessing: bool,
    ) -> OcrResult:
        """특정 Tier 실행"""
        try:
            if tier_level == TierLevel.TIER_1:
                provider = self.tier_1_provider
            elif tier_level == TierLevel.TIER_2:
                provider = self.tier_2_provider
            elif tier_level == TierLevel.TIER_3:
                provider = self.tier_3_provider
            else:
                raise ValueError(f"알 수 없는 Tier: {tier_level}")

            if not provider:
                raise OcrProviderException(f"{tier_level}은 활성화되지 않았습니다")

            result = await provider.extract(image_path, enable_preprocessing)
            return result

        except OcrProviderException as e:
            logger.error(f"{tier_level} 실행 오류: {str(e)}")
            # 공급자 오류 시 빈 결과 반환 (폴백 가능하도록)
            return OcrResult(
                provider=None,
                success=False,
                menu_items=[],
                raw_text=str(e),
                confidence=0.0,
                confidence_level=None,
            )

    def _should_fallback(self, result: OcrResult, trigger: FallbackTrigger) -> bool:
        """폴백 조건 평가"""

        # Tier 1 완전 실패
        if not result.success:
            logger.info("폴백 이유: OCR 실패")
            return True

        # 신뢰도 미달
        if result.confidence < trigger.confidence_threshold:
            logger.info(f"폴백 이유: 신뢰도 미달 ({result.confidence:.2f} < {trigger.confidence_threshold})")
            return True

        # 메뉴 아이템 부족
        if len(result.menu_items) < trigger.min_menu_items:
            logger.info(f"폴백 이유: 메뉴 부족 ({len(result.menu_items)} < {trigger.min_menu_items})")
            return True

        # 손글씨 감지
        if result.has_handwriting and not trigger.allow_on_handwriting:
            logger.info("폴백 이유: 손글씨 감지")
            return True

        # 가격 파싱 에러
        if result.price_parse_errors and trigger.allow_on_price_error:
            logger.info(f"폴백 이유: 가격 파싱 에러 ({len(result.price_parse_errors)}건)")
            return True

        # 아이템 수 이상 감지
        if self._detect_item_count_anomaly(result) and trigger.allow_on_item_count_anomaly:
            logger.info(f"폴백 이유: 메뉴 개수 이상 (>{len(result.menu_items)})")
            return True

        return False

    def _detect_item_count_anomaly(self, result: OcrResult) -> bool:
        """메뉴 개수 이상 감지 (100개 이상 = 비정상)"""
        return len(result.menu_items) > 100

    def _get_fallback_reason(self, result: OcrResult, trigger: FallbackTrigger) -> str:
        """폴백 사유 텍스트 생성"""
        reasons = []

        if not result.success:
            reasons.append("OCR 실패")
        if result.confidence < trigger.confidence_threshold:
            reasons.append(f"신뢰도 {result.confidence:.2f}")
        if result.has_handwriting:
            reasons.append("손글씨 감지")
        if result.price_parse_errors:
            reasons.append(f"가격 에러 {len(result.price_parse_errors)}건")
        if self._detect_item_count_anomaly(result):
            reasons.append(f"메뉴 개수 이상 {len(result.menu_items)}개")

        return ", ".join(reasons) if reasons else "기타"
```

---

### 2-2. Orchestrator 서비스 구현

**파일**: `app/backend/services/ocr_orchestrator.py` (신규 생성)

```python
import logging
import json
from datetime import datetime, timedelta
from typing import Optional

from services.ocr_tier_router import OcrTierRouter, TierLevel
from services.ocr_provider import OcrResult, OcrProviderException
from services.cache_service import cache_service

logger = logging.getLogger(__name__)

class OcrOrchestrator:
    """
    OCR 오케스트레이션 서비스

    역할:
    1. Tier Router 조율
    2. 결과 캐싱 (결과 해시 기반)
    3. 연산 메트릭 기록
    4. 재시도 로직
    """

    def __init__(self):
        self.tier_router = OcrTierRouter()
        self.cache_ttl_seconds = 86400 * 30  # 30일

    async def extract_menu(
        self,
        image_path: str,
        enable_preprocessing: bool = True,
        force_tier: Optional[TierLevel] = None,  # 테스트용
        use_cache: bool = True,  # 캐싱 활성화
    ) -> OcrResult:
        """
        메뉴 이미지 분석 (메인 진입점)

        프로세스:
        1. 캐시 확인 (결과 해시 매칭)
        2. 캐시 미스 시 Tier 라우팅
        3. 결과 캐싱
        4. 메트릭 기록
        """

        # 1. 캐시 조회
        if use_cache:
            cached_result = await self._get_cached_result(image_path)
            if cached_result:
                logger.info(f"캐시 히트: {image_path}")
                return cached_result

        # 2. Tier 라우팅
        logger.info(f"OCR 분석 시작: {image_path}")
        try:
            result = await self.tier_router.route(
                image_path=image_path,
                enable_preprocessing=enable_preprocessing,
                force_tier=force_tier,
            )
        except Exception as e:
            logger.error(f"OCR 라우팅 오류: {str(e)}")
            raise

        # 3. 결과 캐싱
        if use_cache and result.success:
            await self._cache_result(image_path, result)

        # 4. 메트릭 기록
        await self._record_metrics(result)

        return result

    async def _get_cached_result(self, image_path: str) -> Optional[OcrResult]:
        """
        캐시에서 결과 조회

        캐시 키: ocr:result:{image_hash}
        """
        try:
            # 이미지 해시 계산
            cache_key = await self._compute_cache_key(image_path)

            # Redis에서 조회
            cached_json = await cache_service.get(cache_key)
            if not cached_json:
                return None

            # JSON 역직렬화
            result_dict = json.loads(cached_json)
            # OcrResult 객체로 재구성 (생략: 복잡한 데이터 구조로 인해 필요시 별도 처리)
            logger.debug(f"캐시 복원: {cache_key}")
            return None  # TODO: 직렬화 로직 구현

        except Exception as e:
            logger.warning(f"캐시 조회 오류: {str(e)}")
            return None

    async def _cache_result(self, image_path: str, result: OcrResult) -> None:
        """
        결과를 캐시에 저장

        캐시 구조:
        - 키: ocr:result:{result_hash}
        - 값: OcrResult JSON
        - TTL: 30일
        """
        try:
            cache_key = f"ocr:result:{result.result_hash}"

            # JSON 직렬화 (데이터클래스 → dict)
            result_dict = {
                "provider": result.provider.value if result.provider else None,
                "success": result.success,
                "raw_text": result.raw_text,
                "confidence": result.confidence,
                "menu_items_count": len(result.menu_items),
                "result_hash": result.result_hash,
                "processing_time_ms": result.processing_time_ms,
                "cached_at": datetime.utcnow().isoformat(),
            }

            await cache_service.set(
                cache_key,
                json.dumps(result_dict),
                expire=self.cache_ttl_seconds,
            )

            logger.debug(f"캐시 저장: {cache_key}")

        except Exception as e:
            logger.warning(f"캐시 저장 오류: {str(e)}")
            # 캐싱 실패는 비치명적, 로깅만 수행

    async def _compute_cache_key(self, image_path: str) -> str:
        """이미지 경로로부터 캐시 키 생성"""
        import hashlib

        with open(image_path, 'rb') as f:
            image_hash = hashlib.md5(f.read()).hexdigest()

        return f"ocr:image:{image_hash}"

    async def _record_metrics(self, result: OcrResult) -> None:
        """
        OCR 메트릭 기록

        수집 지표:
        - Tier 1 성공률
        - Tier 2 폴백 비율
        - 평균 처리 시간
        - 가격 파싱 에러율
        - 손글씨 감지율
        """
        try:
            metrics_key = "ocr:metrics"

            # 기존 메트릭 조회
            existing_json = await cache_service.get(metrics_key)
            metrics = json.loads(existing_json) if existing_json else {
                "tier_1_count": 0,
                "tier_2_count": 0,
                "total_count": 0,
                "avg_processing_time_ms": 0,
                "price_error_count": 0,
                "handwriting_count": 0,
                "last_updated": datetime.utcnow().isoformat(),
            }

            # 메트릭 업데이트
            metrics["total_count"] += 1
            if result.triggered_fallback:
                metrics["tier_2_count"] += 1
            else:
                metrics["tier_1_count"] += 1

            metrics["avg_processing_time_ms"] = (
                (metrics["avg_processing_time_ms"] * (metrics["total_count"] - 1) + result.processing_time_ms)
                / metrics["total_count"]
            )

            if result.price_parse_errors:
                metrics["price_error_count"] += len(result.price_parse_errors)

            if result.has_handwriting:
                metrics["handwriting_count"] += 1

            metrics["last_updated"] = datetime.utcnow().isoformat()

            # 메트릭 저장
            await cache_service.set(
                metrics_key,
                json.dumps(metrics),
                expire=86400 * 90,  # 90일 보관
            )

            logger.debug(f"메트릭 업데이트: {metrics}")

        except Exception as e:
            logger.warning(f"메트릭 기록 오류: {str(e)}")

    async def get_metrics(self) -> dict:
        """현재 OCR 메트릭 조회"""
        try:
            metrics_json = await cache_service.get("ocr:metrics")
            return json.loads(metrics_json) if metrics_json else {}
        except Exception as e:
            logger.warning(f"메트릭 조회 오류: {str(e)}")
            return {}

# 싱글톤 인스턴스
ocr_orchestrator = OcrOrchestrator()
```

---

## 3단계: API 통합

### 3-1. B2B Bulk Upload 엔드포인트 수정

**파일**: `app/backend/api/b2b.py` (기존 수정)

**변경 전**: `ocr_service.recognize_menu_image()` 직접 호출

**변경 후**: `ocr_orchestrator.extract_menu()` 호출

```python
from services.ocr_orchestrator import ocr_orchestrator

@router.post("/api/v1/b2b/restaurants/{restaurant_id}/menus/upload-images")
async def upload_menu_images(
    restaurant_id: UUID,
    files: List[UploadFile] = File(...),
):
    """메뉴 이미지 일괄 업로드 및 OCR 처리"""

    results = []
    for file in files:
        try:
            # 임시 파일 저장
            temp_path = save_temp_file(file)

            # OCR 처리 (Tier 라우팅 포함)
            ocr_result = await ocr_orchestrator.extract_menu(
                image_path=temp_path,
                enable_preprocessing=True,
                use_cache=True,  # 캐싱 활성화
            )

            # 결과 저장
            results.append({
                "filename": file.filename,
                "success": ocr_result.success,
                "provider": ocr_result.provider.value if ocr_result.provider else None,
                "menu_count": len(ocr_result.menu_items),
                "confidence": ocr_result.confidence,
                "processing_time_ms": ocr_result.processing_time_ms,
                "fallback_triggered": ocr_result.triggered_fallback,
            })

        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e),
            })

    return {"results": results}
```

---

## 4단계: 확장된 가격 파싱 데이터 모델

### 4-1. MenuItem 가격 필드 설명

기존 `MenuItem` dataclass에 다음 필드 추가:

```python
@dataclass
class MenuItem:
    # ... 기존 필드 ...

    # 가격 정보 (확장된 구조)
    price: Optional[int] = None  # 단일 가격 (레거시)

    prices: Optional[List[dict]] = None  # 다중 가격 배열
    # 예시: [
    #   {"size": "소", "price": 8000, "label": "소사이즈"},
    #   {"size": "중", "price": 10000, "label": "중사이즈"},
    #   {"size": "대", "price": 12000, "label": "대사이즈"}
    # ]

    is_set: bool = False  # 세트 여부

    original_price: Optional[int] = None  # 원가 (할인 전)
    discount_price: Optional[int] = None  # 할인가

    # 가격 유효성 검증
    price_unit: str = "원"  # 기본값: 원
    price_currency: str = "KRW"  # 기본값: 한국 원화
```

### 4-2. 가격 유효성 검증 헬퍼

**파일**: `app/backend/utils/price_validator.py` (신규 생성)

```python
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class PriceValidator:
    """
    가격 데이터 유효성 검증

    규칙:
    - 500원 단위 (0, 500, 1000, 1500, ...)
    - 2000원 ~ 50000원 범위
    - 할인가 < 원가
    """

    PRICE_STEP = 500  # 500원 단위
    MIN_PRICE = 2000
    MAX_PRICE = 50000

    @staticmethod
    def validate_price(price: int) -> Tuple[bool, Optional[str]]:
        """단일 가격 검증"""
        if price is None:
            return False, "가격이 없음"

        if not isinstance(price, int):
            return False, f"가격이 정수가 아님: {type(price)}"

        if price % PriceValidator.PRICE_STEP != 0:
            return False, f"가격이 {PriceValidator.PRICE_STEP}원 단위가 아님: {price}"

        if price < PriceValidator.MIN_PRICE or price > PriceValidator.MAX_PRICE:
            return False, f"가격 범위 초과: {price}원 ({PriceValidator.MIN_PRICE}~{PriceValidator.MAX_PRICE})"

        return True, None

    @staticmethod
    def validate_prices_array(prices: List[dict]) -> Tuple[bool, List[str]]:
        """다중 가격 배열 검증"""
        errors = []

        if not prices:
            errors.append("가격 배열이 비어있음")
            return False, errors

        if len(prices) > 5:
            errors.append(f"가격 아이템이 너무 많음: {len(prices)}개 (최대 5개)")

        for i, price_item in enumerate(prices):
            if not isinstance(price_item, dict):
                errors.append(f"가격 아이템 {i}이 dict가 아님")
                continue

            price = price_item.get('price')
            is_valid, error = PriceValidator.validate_price(price)
            if not is_valid:
                errors.append(f"가격 아이템 {i}: {error}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_discount(
        original_price: Optional[int],
        discount_price: Optional[int],
    ) -> Tuple[bool, Optional[str]]:
        """할인 가격 검증"""
        if original_price is None or discount_price is None:
            return True, None

        if discount_price >= original_price:
            return False, f"할인가가 원가 이상: {discount_price}원 >= {original_price}원"

        # 원가 검증
        is_valid, error = PriceValidator.validate_price(original_price)
        if not is_valid:
            return False, f"원가 검증 실패: {error}"

        # 할인가 검증
        is_valid, error = PriceValidator.validate_price(discount_price)
        if not is_valid:
            return False, f"할인가 검증 실패: {error}"

        return True, None
```

---

## 5단계: 예외 처리 및 Fallback 전략

### 5-1. 커스텀 예외 클래스

**파일**: `app/backend/exceptions.py` (기존 수정 또는 신규 추가)

```python
class OcrException(Exception):
    """OCR 관련 기본 예외"""
    pass

class OcrProviderException(OcrException):
    """OCR 공급자 오류"""
    pass

class OcrExtractionException(OcrException):
    """OCR 추출 실패"""
    pass

class PriceValidationException(OcrException):
    """가격 검증 실패"""
    pass
```

### 5-2. Graceful Fallback 로직

```python
# Tier 1 (GPT Vision) 실패 → Tier 2 (CLOVA) 자동 폴백
# Tier 2 실패 → 부분 결과 반환 (원문 텍스트만이라도)

# 클라이언트는 OcrResult.triggered_fallback 플래그로 폴백 여부 확인 가능
```

---

## 6단계: 배포 및 테스트 체크리스트

### 6-1. 사전 검증

- [ ] OpenAI API 키 `.env` 추가 (OPENAI_API_KEY)
- [ ] CLOVA OCR 설정 완료 (CLOVA_OCR_SECRET, CLOVA_OCR_API_URL)
- [ ] Redis 캐시 연결 확인
- [ ] 이미지 전처리 모듈 정상 작동

### 6-2. 단위 테스트

- [ ] OcrProviderGpt 유닛 테스트
- [ ] OcrProviderClova 유닛 테스트
- [ ] OcrTierRouter 폴백 로직 테스트
- [ ] PriceValidator 검증 로직 테스트

### 6-3. 통합 테스트

- [ ] B2B 벌크 업로드 엔드포인트 Tier 라우팅 확인
- [ ] 캐싱 동작 확인
- [ ] 메트릭 기록 확인

### 6-4. 성능 벤치마크

- [ ] Tier 1 (GPT) 처리 시간: 기준 < 5초
- [ ] Tier 2 (CLOVA) 처리 시간: 기준 < 3초
- [ ] 캐시 히트 시간: < 100ms

---

## 7단계: 운영 모니터링

### 7-1. 메트릭 대시보드

```
OCR 메트릭 엔드포인트: GET /api/v1/admin/ocr/metrics

응답:
{
  "tier_1_count": 1250,
  "tier_2_count": 180,      # 12.6% 폴백률
  "total_count": 1430,
  "tier_1_success_rate": "86.7%",
  "tier_2_success_rate": "97.2%",
  "avg_processing_time_ms": 3420,
  "price_error_count": 45,
  "price_error_rate": "3.1%",
  "handwriting_count": 89,
  "handwriting_detection_rate": "6.2%",
  "last_updated": "2026-02-18T10:30:00Z"
}
```

### 7-2. 알림 규칙

| 조건 | 심각도 | 조치 |
|------|--------|------|
| Tier 1 성공률 < 70% | 🔴 Critical | 자동 조사, GPT API 문제 확인 |
| Tier 2 폴백률 > 20% | 🟡 Warning | 이미지 전처리 로직 재검토 |
| 평균 처리시간 > 5초 | 🟡 Warning | API 성능 모니터링 |
| 가격 에러율 > 10% | 🟢 Info | 파싱 로직 최적화 검토 |

---

## 구현 순서 (권장)

1. **Step 1-1**: OcrProvider 기본 인터페이스 작성
2. **Step 1-2**: OcrProviderGpt 구현
3. **Step 1-3**: OcrProviderClova 래핑
4. **Step 2-1**: OcrTierRouter 구현
5. **Step 2-2**: OcrOrchestrator 구현
6. **Step 3-1**: B2B 엔드포인트 수정
7. **Step 4**: 확장된 가격 파싱 모델
8. **Step 5**: 예외 처리 및 Fallback
9. **Step 6**: 테스트 및 배포

---

## 핵심 설계 원칙

### 추상화 우선 (Abstraction First)
- OCR 공급자는 인터페이스(OcrProvider)로 추상화
- 각 공급자는 독립적으로 구현 및 테스트 가능
- 미래에 새로운 공급자 추가 시 기존 코드 변경 최소화

### 결정론성 (Determinism)
- GPT Vision: `temperature=0` 강제 (매번 동일 결과)
- 결과 해시 캐싱으로 B2B 벌크 업로드 데이터 일관성 보장
- 동일 이미지 = 동일 OCR 결과

### 점진적 폴백 (Graceful Degradation)
- Tier 1 실패 → 자동 Tier 2 호출 (사용자 개입 불필요)
- Tier 2 실패 → 부분 결과 또는 원문 반환
- 최악의 경우도 에러는 던지되, 로깅과 메트릭 기록

### 캐싱 전략
- 결과 해시 기반 캐싱 (이미지 내용 + OCR 출력의 SHA256)
- B2B 벌크 업로드 시 중복 요청 방지 (비용 절감)
- 30일 TTL

---

**최종 업데이트**: 2026-02-18
**상태**: Sprint 4 설계 완료, 구현 대기
