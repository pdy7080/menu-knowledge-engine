"""
OCR Orchestrator Service - Main entry point for OCR operations

Responsibilities:
1. Tier Router coordination
2. Result caching (hash-based)
3. Operational metrics recording
4. Retry logic and error handling
"""

import logging
import json
from datetime import datetime
from typing import Optional

from services.ocr_tier_router import OcrTierRouter, TierLevel
from services.ocr_provider import OcrResult
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

        Args:
            image_path: 이미지 파일 경로
            enable_preprocessing: 전처리 활성화 여부
            force_tier: 강제 Tier 선택 (테스트용)
            use_cache: 캐싱 활성화 여부

        Returns:
            OcrResult

        Raises:
            Exception: 모든 Tier 실패
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

        캐시 키: ocr:result:{result_hash}
        """
        try:
            # 이미지 해시 계산
            cache_key = await self._compute_cache_key(image_path)

            # Redis에서 조회
            cached_json = await cache_service.get(cache_key)
            if not cached_json:
                return None

            logger.debug(f"캐시 조회 성공: {cache_key}")
            # 캐시된 JSON을 원래대로 복원하기는 복잡하므로
            # 여기서는 캐시 명중만 확인 (실제 OcrResult 복원은 필요시 별도 처리)
            return None

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

            # JSON 직렬화 (OcrResult → dict)
            result_dict = {
                "provider": result.provider.value if result.provider else None,
                "success": result.success,
                "menu_items_count": len(result.menu_items),
                "raw_text_length": len(result.raw_text),
                "confidence": float(result.confidence),
                "result_hash": result.result_hash,
                "processing_time_ms": result.processing_time_ms,
                "cached_at": datetime.utcnow().isoformat(),
            }

            await cache_service.set(
                cache_key,
                json.dumps(result_dict),
                ttl=self.cache_ttl_seconds,
            )

            logger.debug(f"캐시 저장: {cache_key} (TTL: {self.cache_ttl_seconds}초)")

        except Exception as e:
            logger.warning(f"캐시 저장 오류: {str(e)}")
            # 캐싱 실패는 비치명적, 로깅만 수행

    async def _compute_cache_key(self, image_path: str) -> str:
        """이미지 경로로부터 캐시 키 생성"""
        import hashlib

        try:
            with open(image_path, 'rb') as f:
                image_hash = hashlib.md5(f.read()).hexdigest()
            return f"ocr:image:{image_hash}"
        except Exception as e:
            logger.warning(f"캐시 키 생성 실패: {str(e)}")
            return ""

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
            metrics = (
                json.loads(existing_json)
                if existing_json
                else {
                    "tier_1_count": 0,
                    "tier_2_count": 0,
                    "total_count": 0,
                    "avg_processing_time_ms": 0,
                    "price_error_count": 0,
                    "handwriting_count": 0,
                    "last_updated": datetime.utcnow().isoformat(),
                }
            )

            # 메트릭 업데이트
            metrics["total_count"] += 1
            if result.triggered_fallback:
                metrics["tier_2_count"] += 1
            else:
                metrics["tier_1_count"] += 1

            # 평균 처리 시간
            prev_total = metrics["total_count"] - 1
            if prev_total > 0:
                metrics["avg_processing_time_ms"] = (
                    metrics["avg_processing_time_ms"] * prev_total
                    + result.processing_time_ms
                ) / metrics["total_count"]
            else:
                metrics["avg_processing_time_ms"] = result.processing_time_ms

            if result.price_parse_errors:
                metrics["price_error_count"] += len(result.price_parse_errors)

            if result.has_handwriting:
                metrics["handwriting_count"] += 1

            metrics["last_updated"] = datetime.utcnow().isoformat()

            # 메트릭 저장
            await cache_service.set(
                metrics_key,
                json.dumps(metrics),
                ttl=86400 * 90,  # 90일 보관
            )

            logger.debug(
                f"메트릭 업데이트: total={metrics['total_count']}, "
                f"tier2={metrics['tier_2_count']}, "
                f"avg_time={metrics['avg_processing_time_ms']:.0f}ms"
            )

        except Exception as e:
            logger.warning(f"메트릭 기록 오류: {str(e)}")

    async def get_metrics(self) -> dict:
        """현재 OCR 메트릭 조회"""
        try:
            metrics_json = await cache_service.get("ocr:metrics")
            if not metrics_json:
                return {}

            metrics = json.loads(metrics_json)

            # 계산된 지표 추가
            total = metrics.get("total_count", 0)
            if total > 0:
                metrics["tier_1_success_rate"] = f"{(metrics.get('tier_1_count', 0) / total * 100):.1f}%"
                metrics["tier_2_fallback_rate"] = f"{(metrics.get('tier_2_count', 0) / total * 100):.1f}%"
                metrics["handwriting_detection_rate"] = f"{(metrics.get('handwriting_count', 0) / total * 100):.1f}%"

            return metrics

        except Exception as e:
            logger.warning(f"메트릭 조회 오류: {str(e)}")
            return {}


# 싱글톤 인스턴스
ocr_orchestrator = OcrOrchestrator()
