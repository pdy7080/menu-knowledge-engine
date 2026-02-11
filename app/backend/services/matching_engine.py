"""
Menu Matching Engine - 3단계 매칭 파이프라인
Step 1: Exact Match (DB 직접 매칭)
Step 2: Modifier Decomposition (수식어 분해)
Step 3: AI Discovery (fallback)
"""
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models import CanonicalMenu, Modifier


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

    def __init__(self, db: AsyncSession):
        self.db = db

    async def match_menu(self, menu_name: str) -> MatchResult:
        """
        메뉴명 매칭 메인 함수
        3단계 파이프라인: Exact Match → Modifier Decomposition → AI Discovery
        """
        # Step 1: Exact Match
        result = await self._exact_match(menu_name)
        if result:
            return result

        # Step 2: Modifier Decomposition
        result = await self._modifier_decomposition(menu_name)
        if result:
            return result

        # Step 3: AI Discovery (placeholder)
        return await self._ai_discovery(menu_name)

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

        # 1-2. pg_trgm 유사도 검색 (similarity >= 0.4)
        # PostgreSQL의 pg_trgm extension을 사용한 유사도 검색
        # 한글 오타 감지를 위해 threshold를 낮춤 (김치찌개 vs 김치찌게 = 0.43)
        # 길이 차이 제한: 오타 보정용이므로 길이가 동일한 경우만 허용
        similarity_threshold = 0.4
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
        - modifiers 테이블에서 수식어 찾아서 제거
        - 타입별 우선순위 적용 (ingredient는 마지막에)
        - 수식어를 누적해서 제거하면서 canonical 매칭 시도
        - 매칭 성공하는 조합만 유효
        """
        # 2-1. 모든 수식어 조회
        result = await self.db.execute(select(Modifier))
        all_modifiers = result.scalars().all()

        # 2-1-1. 타입별 우선순위 정의 (숫자가 낮을수록 높은 우선순위)
        # emotion/cooking/grade/origin: 메뉴 외부 수식어 (브랜드, 감성) - 최우선
        # taste/size: 메뉴 내부 속성 - 그 다음
        # ingredient: 핵심 재료 - 제외
        type_priority = {
            "emotion": 1,   # 최우선 (원조, 할매 등)
            "cooking": 2,
            "grade": 3,
            "origin": 4,
            "taste": 5,
            "size": 6,
            "ingredient": 99,  # 가장 낮은 우선순위 (제외됨)
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
        # ingredient 타입은 제외 (핵심 재료이므로 수식어로 제거하면 안 됨)
        potential_modifiers = []
        for modifier in all_modifiers:
            if modifier.type == "ingredient":
                continue  # ingredient는 Step 2에서 제외
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
        Step 3: AI Discovery (placeholder)
        - 실제 GPT-4o 연동은 Sprint 1 후반에 구현
        - 지금은 ai_discovery_needed 상태로 반환
        """
        # 수식어만 추출 시도 (canonical은 찾지 못했지만 수식어는 기록)
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

        return MatchResult(
            input_text=menu_name,
            match_type="ai_discovery_needed",
            canonical=None,
            modifiers=found_modifiers,
            confidence=0.0,
            ai_called=False,  # placeholder이므로 실제로 호출하지 않음
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
