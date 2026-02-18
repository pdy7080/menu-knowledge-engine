"""
Menu Matching Engine - 3단계 매칭 파이프라인
Step 1: Exact Match (DB 직접 매칭)
Step 2: Modifier Decomposition (수식어 분해)
Step 3: AI Discovery (GPT-4o fallback)
"""
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models import CanonicalMenu, Modifier
from services.cache_service import cache_service, TTL_MENU_TRANSLATION
from openai import OpenAI
import asyncio
import json
import os


class MatchResult:
    """매칭 결과 데이터 클래스"""
    def __init__(
        self,
        input_text: str,
        match_type: str,  # "exact", "similarity", "modifier_decomposition", "ai_discovery_needed"
        canonical: Optional[Dict[str, Any]] = None,
        modifiers: List[Dict[str, Any]] = None,
        confidence: float = 0.0,
        ai_called: bool = False,
    ):
        self.input_text = input_text
        self.match_type = match_type
        self.canonical = canonical
        self.modifiers = modifiers or []
        self.confidence = confidence
        self.ai_called = ai_called

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "input": self.input_text,
            "match_type": self.match_type,
            "canonical": self.canonical,
            "modifiers": self.modifiers,
            "confidence": self.confidence,
            "ai_called": self.ai_called,
        }


class MenuMatchingEngine:
    """메뉴 매칭 엔진"""

    # 클래스 레벨 AI Discovery 캐시 (인메모리, thread-safe)
    _ai_cache: Dict[str, Dict[str, Any]] = {}
    _cache_lock: asyncio.Lock = None  # Lazy initialization

    def __init__(self, db: AsyncSession):
        self.db = db
        # Lazy init Lock (클래스 레벨로 공유)
        if MenuMatchingEngine._cache_lock is None:
            MenuMatchingEngine._cache_lock = asyncio.Lock()

    async def match_menu(self, menu_name: str) -> MatchResult:
        """
        메뉴명 매칭 메인 함수
        3단계 파이프라인: Exact Match → Modifier Decomposition → AI Discovery
        Redis 캐싱 적용 (TTL: 24시간)
        """
        # Check Redis cache first
        cache_key = f"menu:identify:{menu_name}"
        cached_result = await cache_service.get(cache_key)
        if cached_result is not None:
            # Convert cached dict back to MatchResult
            return MatchResult(
                input_text=cached_result["input"],
                match_type=cached_result["match_type"],
                canonical=cached_result["canonical"],
                modifiers=cached_result["modifiers"],
                confidence=cached_result["confidence"],
                ai_called=False,  # 캐시에서 가져왔으므로 False
            )

        # Step 1: Exact Match
        result = await self._exact_match(menu_name)
        if result:
            await cache_service.set(cache_key, result.to_dict(), TTL_MENU_TRANSLATION)
            return result

        # Step 2: Modifier Decomposition
        result = await self._modifier_decomposition(menu_name)
        if result:
            await cache_service.set(cache_key, result.to_dict(), TTL_MENU_TRANSLATION)
            return result

        # Step 3: AI Discovery
        result = await self._ai_discovery(menu_name)
        await cache_service.set(cache_key, result.to_dict(), TTL_MENU_TRANSLATION)
        return result

    async def _exact_match(self, menu_name: str) -> Optional[MatchResult]:
        """
        Step 1: Exact Match
        - DB에서 정확히 일치하는 메뉴 찾기
        - pg_trgm 유사도 검색 (similarity >= 0.6)
        """
        # 1-1. 정확한 일치 검색
        result = await self.db.execute(
            select(CanonicalMenu).where(CanonicalMenu.name_ko == menu_name)
        )
        canonical = result.scalars().first()

        if canonical:
            return MatchResult(
                input_text=menu_name,
                match_type="exact",
                canonical=self._canonical_to_dict(canonical),
                modifiers=[],
                confidence=1.0,
                ai_called=False,
            )

        # 1-2. pg_trgm 유사도 검색 (similarity >= 0.35)
        # PostgreSQL의 pg_trgm extension을 사용한 유사도 검색
        # 한글 오타 감지를 위해 threshold를 낮춤
        #   - 김치찌개 vs 김치찌게 = 0.43 (ㅐ vs ㅔ)
        #   - 떡볶이 vs 떡복이 = ~0.38 (ㄲ vs ㄱ)
        # 길이 차이 제한: 오타 보정용이므로 길이가 동일한 경우만 허용
        similarity_threshold = 0.35  # 0.4 → 0.35로 낮춤 (떡볶이/떡복이 커버)
        max_length_diff = 0  # 길이가 동일한 경우만 (김치찌개 4글자 vs 김치찌게 4글자)

        result = await self.db.execute(
            select(
                CanonicalMenu,
                func.similarity(CanonicalMenu.name_ko, menu_name).label("sim"),
                func.length(CanonicalMenu.name_ko).label("len"),
            )
            .where(func.similarity(CanonicalMenu.name_ko, menu_name) >= similarity_threshold)
            .where(func.abs(func.length(CanonicalMenu.name_ko) - len(menu_name)) <= max_length_diff)
            .order_by(func.similarity(CanonicalMenu.name_ko, menu_name).desc())
            .limit(1)
        )
        row = result.first()

        if row:
            canonical, similarity, length = row
            return MatchResult(
                input_text=menu_name,
                match_type="similarity",
                canonical=self._canonical_to_dict(canonical),
                modifiers=[],
                confidence=float(similarity),
                ai_called=False,
            )

        return None

    async def _modifier_decomposition(self, menu_name: str) -> Optional[MatchResult]:
        """
        Step 2: Modifier Decomposition (개선됨)
        - 먼저 입력 문자열의 부분 문자열이 canonical과 매칭되는지 확인 (NEW!)
        - modifiers 테이블에서 수식어 찾아서 제거
        - 타입별 우선순위 적용
        - 수식어를 누적해서 제거하면서 canonical 매칭 시도
        - 매칭 성공하는 조합만 유효
        """
        # 2-0. Canonical 우선 매칭 (NEW!)
        # 입력 문자열의 모든 연속 부분 문자열이 canonical과 매칭되는지 확인
        # 예: "한우불고기" → "불고기"가 canonical과 매칭되면, "한우"는 modifier
        for length in range(len(menu_name), 1, -1):  # 긴 것부터 시도
            for start in range(len(menu_name) - length + 1):
                substring = menu_name[start:start + length]

                # 이 부분 문자열이 canonical과 매칭되는가?
                canonical = await self._try_canonical_match(substring)

                if canonical:
                    # 나머지 부분 추출
                    prefix = menu_name[:start]
                    suffix = menu_name[start + length:]
                    remaining_text = (prefix + suffix).strip()

                    # 나머지가 없으면 (전체가 canonical) 이미 Step 1에서 잡혔을 것
                    if not remaining_text:
                        continue

                    # 나머지 부분이 modifier인지 확인
                    result_mod = await self.db.execute(select(Modifier))
                    all_mods = result_mod.scalars().all()

                    found_modifiers = []
                    temp_remaining = remaining_text

                    for mod in all_mods:
                        if mod.text_ko in temp_remaining:
                            found_modifiers.append({
                                "text_ko": mod.text_ko,
                                "type": mod.type,
                                "translation_en": mod.translation_en,
                                "semantic_key": mod.semantic_key,
                            })
                            temp_remaining = temp_remaining.replace(mod.text_ko, "", 1).strip()

                    # 모든 나머지 텍스트가 modifier로 설명되면 성공
                    if not temp_remaining or temp_remaining == "":
                        confidence = 0.95 - (len(found_modifiers) * 0.05)
                        confidence = max(confidence, 0.7)

                        return MatchResult(
                            input_text=menu_name,
                            match_type="modifier_decomposition",
                            canonical=self._canonical_to_dict(canonical),
                            modifiers=found_modifiers,
                            confidence=confidence,
                            ai_called=False,
                        )

        # 2-1. 모든 수식어 조회 (기존 알고리즘 폴백)
        result = await self.db.execute(select(Modifier))
        all_modifiers = result.scalars().all()

        # 2-1-1. 타입별 우선순위 정의 (숫자가 낮을수록 높은 우선순위)
        # emotion/cooking/grade/origin: 메뉴 외부 수식어 (브랜드, 감성) - 최우선
        # ingredient: 재료 강조 - cooking 다음 (한우불고기, 해물짬뽕 등)
        # taste/size: 메뉴 내부 속성 - 그 다음
        type_priority = {
            "emotion": 1,   # 최우선 (원조, 할매 등)
            "cooking": 2,
            "ingredient": 3,  # cooking 다음 (한우, 해물 등)
            "grade": 4,
            "origin": 5,
            "taste": 6,
            "size": 7,
        }

        # 2-1-2. 타입 우선순위 → 길이 순 → priority 순으로 정렬
        all_modifiers = sorted(
            all_modifiers,
            key=lambda m: (
                type_priority.get(m.type, 50),  # 타입 우선순위
                -len(m.text_ko),  # 길이 (긴 것부터, 그래서 음수)
                -m.priority,  # priority (높은 것부터, 그래서 음수)
            )
        )

        # 2-2. 메뉴명에서 발견 가능한 수식어 목록 추출
        # 모든 타입의 수식어를 포함 (ingredient 포함)
        # 이유: "한우불고기" = "한우"(ingredient) + "불고기"(canonical)와 같은 경우를 처리하기 위함
        potential_modifiers = []
        for modifier in all_modifiers:
            if modifier.text_ko in menu_name:
                potential_modifiers.append(modifier)

        # 수식어가 하나도 없으면 실패
        if not potential_modifiers:
            return None

        # 2-3. Greedy accumulative matching
        # 수식어를 하나씩 누적해서 제거하면서 canonical 매칭을 시도
        found_modifiers = []
        remaining_text = menu_name

        for modifier in potential_modifiers:
            # 현재 남은 텍스트에 이 수식어가 있는지 확인
            if modifier.text_ko not in remaining_text:
                continue

            # 수식어를 제거
            new_remaining = remaining_text.replace(modifier.text_ko, "", 1).strip()

            # 수식어를 제거한 후에도 텍스트가 남아있는지 확인
            if not new_remaining:
                # 남은 텍스트가 없으면 이 수식어는 건너뛰기
                continue

            # 이 수식어를 누적 목록에 추가
            found_modifiers.append({
                "text_ko": modifier.text_ko,
                "type": modifier.type,
                "translation_en": modifier.translation_en,
                "semantic_key": modifier.semantic_key,
            })
            remaining_text = new_remaining

            # 매번 canonical 매칭 시도
            canonical = await self._try_canonical_match(remaining_text)

            if canonical:
                # 매칭 성공! 즉시 반환
                confidence = 0.95 - (len(found_modifiers) * 0.05)
                confidence = max(confidence, 0.7)

                return MatchResult(
                    input_text=menu_name,
                    match_type="modifier_decomposition",
                    canonical=self._canonical_to_dict(canonical),
                    modifiers=found_modifiers,
                    confidence=confidence,
                    ai_called=False,
                )

        # 모든 수식어를 제거했지만 매칭 실패
        return None

    async def _try_canonical_match(self, text: str) -> Optional[CanonicalMenu]:
        """
        텍스트가 canonical_menus와 매칭되는지 확인
        Exact match 또는 Similarity match 시도
        """
        if not text or not text.strip():
            return None

        text = text.strip()

        # Exact match 시도
        result = await self.db.execute(
            select(CanonicalMenu).where(CanonicalMenu.name_ko == text)
        )
        canonical = result.scalars().first()

        if canonical:
            return canonical

        # Similarity match 시도 (threshold 0.7)
        similarity_threshold = 0.7
        result = await self.db.execute(
            select(
                CanonicalMenu,
                func.similarity(CanonicalMenu.name_ko, text).label("sim"),
            )
            .where(func.similarity(CanonicalMenu.name_ko, text) >= similarity_threshold)
            .order_by(func.similarity(CanonicalMenu.name_ko, text).desc())
            .limit(1)
        )
        row = result.first()

        if row:
            canonical, similarity = row
            return canonical

        return None

    async def _ai_discovery(self, menu_name: str) -> MatchResult:
        """
        Step 3: AI Discovery (GPT-4o)
        - OpenAI API로 새로운 메뉴 분석
        - 영문 번역 + 간단한 설명 생성
        - modifiers 추출 시도
        - 인메모리 캐시 사용 (성능 최적화, thread-safe)
        """
        # Fast path: Read cache without lock
        if menu_name in self._ai_cache:
            cached = self._ai_cache[menu_name]
            return MatchResult(
                input_text=menu_name,
                match_type=cached["match_type"],
                canonical=cached["canonical"],
                modifiers=cached["modifiers"],
                confidence=cached["confidence"],
                ai_called=False,  # 캐시에서 가져왔으므로 False
            )

        # 먼저 수식어 추출 시도
        result = await self.db.execute(
            select(Modifier).order_by(func.length(Modifier.text_ko).desc())
        )
        modifiers = result.scalars().all()

        found_modifiers = []
        remaining_text = menu_name

        for modifier in modifiers:
            if modifier.text_ko in remaining_text:
                found_modifiers.append({
                    "text_ko": modifier.text_ko,
                    "type": modifier.type,
                    "translation_en": modifier.translation_en,
                })
                remaining_text = remaining_text.replace(modifier.text_ko, "", 1)

        # OpenAI API 호출 (환경변수 확인)
        openai_api_key = os.getenv("OPENAI_API_KEY")

        if not openai_api_key:
            # API 키가 없으면 기본 응답 반환
            return MatchResult(
                input_text=menu_name,
                match_type="ai_discovery_needed",
                canonical=None,
                modifiers=found_modifiers,
                confidence=0.0,
                ai_called=False,
            )

        try:
            client = OpenAI(api_key=openai_api_key)

            # GPT-4o로 메뉴 분석
            prompt = f"""You are a Korean food expert. Analyze this Korean menu name and provide information.

Menu name (Korean): {menu_name}

Please provide:
1. English translation (simple, readable for tourists)
2. Brief explanation (1-2 sentences, what is it?)
3. Main ingredients (list)
4. Allergens (if any: peanut, tree nuts, soy, wheat, milk, egg, fish, shellfish, beef, pork, chicken)
5. Spice level (0-5, where 0=not spicy, 5=very spicy)
6. Adventure level (1-3, where 1=familiar, 2=somewhat unusual, 3=very adventurous)

Return JSON only:
{{
  "name_en": "...",
  "explanation_short_en": "...",
  "main_ingredients": ["...", "..."],
  "allergens": ["...", "..."],
  "spice_level": 0-5,
  "difficulty_score": 1-3
}}"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective
                messages=[
                    {"role": "system", "content": "You are a Korean food expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON from markdown code block
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            ai_result = json.loads(content)

            # AI가 분석한 내용을 canonical 형태로 구성
            ai_canonical = {
                "id": None,  # AI Discovery는 DB에 아직 없음
                "name_ko": menu_name,
                "name_en": ai_result.get("name_en", menu_name),
                "explanation_short": {
                    "en": ai_result.get("explanation_short_en", "No description available")
                },
                "main_ingredients": ai_result.get("main_ingredients", []),
                "allergens": ai_result.get("allergens", []),
                "spice_level": ai_result.get("spice_level", 0),
                "difficulty_score": ai_result.get("difficulty_score", 1),
                "image_url": None,
            }

            result = MatchResult(
                input_text=menu_name,
                match_type="ai_discovery",
                canonical=ai_canonical,
                modifiers=found_modifiers,
                confidence=0.6,  # AI 추론이므로 중간 신뢰도
                ai_called=True,
            )

            # 캐시에 저장 (다음 요청에서 재사용, thread-safe)
            async with self._cache_lock:
                # Double-check: 다른 태스크가 이미 캐싱했을 수 있음
                if menu_name not in self._ai_cache:
                    self._ai_cache[menu_name] = {
                        "match_type": "ai_discovery",
                        "canonical": ai_canonical,
                        "modifiers": found_modifiers,
                        "confidence": 0.6,
                    }

            return result

        except Exception as e:
            print(f"AI Discovery error: {e}")
            # AI 호출 실패 시 기본 응답
            return MatchResult(
                input_text=menu_name,
                match_type="ai_discovery_needed",
                canonical=None,
                modifiers=found_modifiers,
                confidence=0.0,
                ai_called=False,
            )

    def _canonical_to_dict(self, canonical: CanonicalMenu) -> Dict[str, Any]:
        """CanonicalMenu 모델을 딕셔너리로 변환"""
        return {
            "id": str(canonical.id),
            "name_ko": canonical.name_ko,
            "name_en": canonical.name_en,
            "explanation_short": canonical.explanation_short,
            "main_ingredients": canonical.main_ingredients,
            "allergens": canonical.allergens,
            "spice_level": canonical.spice_level,
            "difficulty_score": canonical.difficulty_score,
            "image_url": canonical.image_url,
        }
