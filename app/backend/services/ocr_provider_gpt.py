"""
GPT-4o mini Vision OCR Provider

Tier 1 primary provider for menu image analysis.
Uses GPT-4o mini Vision with temperature=0 for deterministic output.
"""

import logging
import hashlib
import time
import json
import base64
from typing import Optional, List

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

        if not settings.OPENAI_API_KEY:
            raise OcrProviderException("OPENAI_API_KEY not configured")

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
            image_bytes = await self._load_and_preprocess(
                image_path, enable_preprocessing
            )
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
      "ingredients": ["재료1", "재료2"] 또는 [],
      "category": "카테고리"
    }
  ]
}

주의:
- 데이터 없음 필드는 null 사용
- 가격은 숫자형 (문자열 아님)
- 신뢰도 0.85 이상만 반환 권장
- 메뉴가 없으면 빈 배열 [] 반환
"""

    def _parse_response(self, raw_text: str) -> tuple[List[MenuItem], List[str]]:
        """GPT 응답을 MenuItem 리스트로 파싱"""
        menu_items = []
        parse_errors = []

        try:
            # JSON 추출
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                parse_errors.append("JSON 시작/종료 태그 없음")
                return menu_items, parse_errors

            json_str = raw_text[json_start:json_end]
            data = json.loads(json_str)

            # 메뉴 아이템 변환
            for item in data.get('menu_items', []):
                try:
                    menu_item = MenuItem(
                        name_ko=item.get('name_ko', ''),
                        name_en=item.get('name_en'),
                        description=item.get('description'),
                        price=item.get('price'),
                        prices=item.get('prices'),
                        is_set=item.get('is_set', False),
                        original_price=item.get('original_price'),
                        discount_price=item.get('discount_price'),
                        ingredients=item.get('ingredients', []),
                        category=item.get('category'),
                    )

                    # 메뉴명 검증 (필수)
                    if menu_item.name_ko:
                        menu_items.append(menu_item)
                    else:
                        parse_errors.append("메뉴명 누락")

                except Exception as e:
                    parse_errors.append(f"메뉴 파싱 오류: {str(e)}")

        except json.JSONDecodeError as e:
            parse_errors.append(f"JSON 파싱 실패: {str(e)}")
        except Exception as e:
            parse_errors.append(f"응답 처리 오류: {str(e)}")

        return menu_items, parse_errors

    def _calculate_confidence(
        self,
        menu_items: List[MenuItem],
        parse_errors: List[str],
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
        token_penalty = 0.1 if response_tokens < 100 else 0

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
        try:
            # 이미지 파일의 MD5
            with open(image_path, 'rb') as f:
                image_hash = hashlib.md5(f.read()).hexdigest()

            # 이미지 해시 + 출력 텍스트 해시
            combined = f"{image_hash}:{raw_text}"
            return hashlib.sha256(combined.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"해시 계산 실패: {str(e)}")
            return ""

    async def _load_and_preprocess(
        self,
        image_path: str,
        enable_preprocessing: bool
    ) -> bytes:
        """이미지 로드 및 전처리"""
        if enable_preprocessing:
            try:
                from utils.image_preprocessing import preprocess_menu_image
                preprocessed_path = preprocess_menu_image(image_path)
                image_path = preprocessed_path
            except Exception as e:
                logger.warning(f"이미지 전처리 실패: {str(e)}, 원본 이미지 사용")

        with open(image_path, 'rb') as f:
            return f.read()
