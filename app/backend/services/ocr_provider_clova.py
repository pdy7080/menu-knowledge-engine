"""
CLOVA OCR Provider Wrapper

Wraps existing OCRService (Sprint 3B) into OcrProvider interface.
Tier 2 fallback provider - specialized for Korean handwriting.
"""

import logging
import hashlib
import time
from typing import List

from services.ocr_provider import (
    OcrProvider,
    OcrResult,
    MenuItem,
    OcrProviderType,
    OcrConfidenceLevel,
    OcrProviderException,
)
from services.ocr_service import ocr_service

logger = logging.getLogger(__name__)


class OcrProviderClova(OcrProvider):
    """CLOVA OCR을 추상화된 OcrProvider로 래핑"""

    def __init__(self, config: dict = None):
        super().__init__(config or {})
        self.provider_type = OcrProviderType.CLOVA

    async def extract(
        self,
        image_path: str,
        enable_preprocessing: bool = True
    ) -> OcrResult:
        """
        CLOVA OCR로 메뉴 이미지 분석

        기존 recognize_menu_image() 함수를 래핑하여
        표준 OcrResult 스키마로 변환합니다.
        """
        start_time = time.time()

        try:
            # 기존 CLOVA 함수 호출 (동기 함수를 비동기로 래핑)
            clova_result = await self._call_clova_sync(
                image_path=image_path,
                enable_preprocessing=enable_preprocessing,
            )

            # CLOVA 응답을 MenuItem 리스트로 변환
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
            # 기존 ocr_service 확인
            if not ocr_service.clova_secret:
                logger.warning("CLOVA_OCR_SECRET not configured")
                return False

            logger.info("CLOVA health check passed")
            return True

        except Exception as e:
            logger.error(f"CLOVA 헬스 체크 실패: {str(e)}")
            return False

    async def _call_clova_sync(
        self,
        image_path: str,
        enable_preprocessing: bool,
    ) -> dict:
        """
        동기 함수인 recognize_menu_image()를 비동기로 래핑

        기존 Sprint 3B 코드와의 호환성 유지
        """
        try:
            # 기존 ocr_service.recognize_menu_image() 호출
            # (현재는 동기 함수, 필요시 asyncio.to_thread로 래핑 가능)
            clova_result = ocr_service.recognize_menu_image(
                image_path=image_path,
                enable_preprocessing=enable_preprocessing,
            )

            # 기존 응답 구조
            # {
            #   "success": bool,
            #   "menu_items": [{"name_ko": str, "price_ko": str}, ...],
            #   "raw_text": str,
            #   "ocr_confidence": float,
            #   "error": str (if failed)
            # }

            return clova_result

        except Exception as e:
            logger.error(f"CLOVA 호출 오류: {str(e)}")
            raise

    def _convert_clova_response(self, clova_result: dict) -> List[MenuItem]:
        """CLOVA 응답을 MenuItem 리스트로 변환"""
        menu_items = []

        try:
            # CLOVA 응답 형식: [{"name_ko": str, "price_ko": str}, ...]
            for item in clova_result.get('menu_items', []):
                try:
                    # price_ko를 정수로 파싱 (예: "8,000" → 8000)
                    price_str = item.get('price_ko', '')
                    price = None

                    if price_str:
                        # 콤마, 원 제거
                        price_clean = price_str.replace(',', '').replace('원', '').strip()
                        try:
                            price = int(price_clean)
                        except ValueError:
                            price = None

                    menu_item = MenuItem(
                        name_ko=item.get('name_ko', ''),
                        price=price,
                        # CLOVA는 추가 필드 미제공
                    )

                    # 메뉴명 검증 (필수)
                    if menu_item.name_ko:
                        menu_items.append(menu_item)

                except Exception as e:
                    logger.warning(f"CLOVA 메뉴 변환 실패: {str(e)}")

        except Exception as e:
            logger.warning(f"CLOVA 응답 처리 오류: {str(e)}")

        return menu_items

    def _calculate_confidence(
        self,
        clova_result: dict,
        menu_items: List[MenuItem],
    ) -> float:
        """신뢰도 계산"""

        # CLOVA 실패
        if not clova_result.get('success', False):
            return 0.0

        # CLOVA 응답에서 신뢰도 점수 추출
        confidence = clova_result.get('ocr_confidence', 0.0)

        # 신뢰도가 없거나 0이면 휴리스틱 사용
        if confidence == 0.0:
            # CLOVA는 한글 95%+ 정확도 (기본값)
            confidence = 0.85 if menu_items else 0.0

        return min(confidence, 1.0)

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
        try:
            with open(image_path, 'rb') as f:
                image_hash = hashlib.md5(f.read()).hexdigest()

            result_text = str(clova_result)
            combined = f"{image_hash}:{result_text}"
            return hashlib.sha256(combined.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"해시 계산 실패: {str(e)}")
            return ""
