"""
OCR Tier Router - Automatic fallback orchestration

Implements Tier-based routing with automatic fallback:
- Tier 1: GPT-4o mini Vision (primary, fast)
- Tier 2: CLOVA OCR (fallback, Korean specialized)
- Tier 3: Tesseract (future)
"""

import logging
from typing import Optional
from enum import Enum

from services.ocr_provider import (
    OcrProvider,
    OcrResult,
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


class FallbackTrigger:
    """Tier 폴백 트리거 조건"""

    def __init__(
        self,
        confidence_threshold: float = 0.75,
        min_menu_items: int = 1,
        allow_on_handwriting: bool = False,
        allow_on_price_error: bool = True,
        allow_on_item_count_anomaly: bool = True,
    ):
        self.confidence_threshold = confidence_threshold
        self.min_menu_items = min_menu_items
        self.allow_on_handwriting = allow_on_handwriting
        self.allow_on_price_error = allow_on_price_error
        self.allow_on_item_count_anomaly = allow_on_item_count_anomaly


class OcrTierRouter:
    """
    Tier 기반 OCR 라우팅 시스템

    Tier 1: GPT-4o mini Vision (빠르고, 구조화된 출력)
    Tier 2: CLOVA OCR (Tier 1 실패 시 fallback, 한글 특화)
    Tier 3: Tesseract (미래용, 로컬)
    """

    def __init__(self):
        # Provider 초기화
        self.tier_1_provider: Optional[OcrProvider] = None
        self.tier_2_provider: Optional[OcrProvider] = None
        self.tier_3_provider: Optional[OcrProvider] = None

        # Tier 1 (GPT Vision) 초기화
        try:
            self.tier_1_provider = OcrProviderGpt()
            logger.info("Tier 1 (GPT Vision) 초기화 완료")
        except Exception as e:
            logger.warning(f"Tier 1 (GPT Vision) 초기화 실패: {str(e)}")

        # Tier 2 (CLOVA) 초기화
        try:
            self.tier_2_provider = OcrProviderClova()
            logger.info("Tier 2 (CLOVA) 초기화 완료")
        except Exception as e:
            logger.warning(f"Tier 2 (CLOVA) 초기화 실패: {str(e)}")

        # Tier별 폴백 조건
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

        프로세스:
        1. Tier 1 (GPT Vision) 시도
        2. Tier 1 실패 또는 폴백 조건 만족 시 Tier 2 (CLOVA) 시도
        3. Tier 2 실패 시 최후의 결과 반환

        Args:
            image_path: 이미지 파일 경로
            enable_preprocessing: 전처리 활성화 여부
            force_tier: 강제 Tier 선택 (테스트용)

        Returns:
            OcrResult

        Raises:
            OcrProviderException: 모든 Tier 실패
        """

        # 강제 Tier 선택 (디버깅용)
        if force_tier:
            logger.info(f"강제 Tier 선택: {force_tier}")
            return await self._execute_tier(
                force_tier, image_path, enable_preprocessing
            )

        # Tier 1: GPT Vision
        logger.info(f"Tier 1 (GPT Vision) 시도: {image_path}")
        result_tier_1 = await self._execute_tier(
            TierLevel.TIER_1, image_path, enable_preprocessing
        )

        # Tier 1 결과 평가
        if self._should_fallback(result_tier_1, self.tier_1_trigger):
            fallback_reason = self._get_fallback_reason(
                result_tier_1, self.tier_1_trigger
            )
            logger.warning(f"Tier 1 폴백 트리거: {fallback_reason}")

            # Tier 2: CLOVA
            logger.info(f"Tier 2 (CLOVA) 시도: {image_path}")
            result_tier_2 = await self._execute_tier(
                TierLevel.TIER_2, image_path, enable_preprocessing
            )

            result_tier_2.triggered_fallback = True
            result_tier_2.fallback_reason = fallback_reason

            return result_tier_2

        logger.info(
            f"Tier 1 성공: confidence={result_tier_1.confidence:.2f}, "
            f"items={len(result_tier_1.menu_items)}"
        )
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
        except Exception as e:
            logger.error(f"{tier_level} 예상치 못한 오류: {str(e)}")
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
            logger.debug("폴백 이유: OCR 실패")
            return True

        # 신뢰도 미달
        if result.confidence < trigger.confidence_threshold:
            logger.debug(
                f"폴백 이유: 신뢰도 미달 ({result.confidence:.2f} < {trigger.confidence_threshold})"
            )
            return True

        # 메뉴 아이템 부족
        if len(result.menu_items) < trigger.min_menu_items:
            logger.debug(
                f"폴백 이유: 메뉴 부족 ({len(result.menu_items)} < {trigger.min_menu_items})"
            )
            return True

        # 손글씨 감지
        if result.has_handwriting and not trigger.allow_on_handwriting:
            logger.debug("폴백 이유: 손글씨 감지")
            return True

        # 가격 파싱 에러
        if result.price_parse_errors and trigger.allow_on_price_error:
            logger.debug(
                f"폴백 이유: 가격 파싱 에러 ({len(result.price_parse_errors)}건)"
            )
            return True

        # 아이템 수 이상 감지
        if (
            self._detect_item_count_anomaly(result)
            and trigger.allow_on_item_count_anomaly
        ):
            logger.debug(f"폴백 이유: 메뉴 개수 이상 ({len(result.menu_items)}개)")
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
        if len(result.menu_items) < trigger.min_menu_items:
            reasons.append("메뉴 부족")
        if result.has_handwriting and not trigger.allow_on_handwriting:
            reasons.append("손글씨 감지")
        if result.price_parse_errors and trigger.allow_on_price_error:
            reasons.append(f"가격 에러 {len(result.price_parse_errors)}건")
        if self._detect_item_count_anomaly(result):
            reasons.append("메뉴 개수 이상")

        return ", ".join(reasons) if reasons else "기타 이유로 폴백"
