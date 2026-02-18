"""
매칭 정확도 테스트 스위트
Sprint 3A: Knowledge Graph 강화 검증
"""
import pytest
import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import AsyncSessionLocal, init_db
from services.matching_engine import MenuMatchingEngine
from tests.test_cases.exact_match import EXACT_MATCH_CASES
from tests.test_cases.normalization import NORMALIZATION_CASES
from tests.test_cases.suffix_patterns import SUFFIX_CASES
from tests.test_cases.modifier_decomposition import MODIFIER_CASES
from tests.test_cases.similarity_match import SIMILARITY_CASES


# 전체 테스트 케이스 합치기
ALL_TEST_CASES = (
    EXACT_MATCH_CASES +           # 50개
    NORMALIZATION_CASES +         # 20개
    SUFFIX_CASES +                # 15개
    MODIFIER_CASES +              # 30개
    SIMILARITY_CASES              # 15개
)  # 총 130개


@pytest.fixture(scope="module")
def event_loop():
    """이벤트 루프 fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def db_session():
    """DB 세션 fixture"""
    # DB 초기화
    await init_db()

    # 세션 생성
    async with AsyncSessionLocal() as session:
        yield session


@pytest.mark.asyncio
async def test_matching_accuracy(db_session: AsyncSession):
    """매칭 정확도 테스트 (목표: 80%+)"""
    engine = MenuMatchingEngine(db_session)

    passed = 0
    failed_cases = []
    skipped_cases = []

    for input_text, expected_canonical, expected_type in ALL_TEST_CASES:
        # expected_type이 None이면 매칭 실패를 기대 (skip)
        if expected_type is None:
            skipped_cases.append({
                "input": input_text,
                "reason": "Expected to fail (length diff too large)",
            })
            continue

        try:
            result = await engine.match_menu(input_text)

            # 매칭 타입 확인
            if result.match_type in [expected_type, "exact", "similarity", "modifier_decomposition"]:
                # canonical 이름 확인
                if expected_canonical:
                    actual_name = result.canonical.get("name_ko", "") if result.canonical else None

                    if actual_name == expected_canonical:
                        passed += 1
                    else:
                        failed_cases.append({
                            "input": input_text,
                            "expected_canonical": expected_canonical,
                            "actual_canonical": actual_name,
                            "expected_type": expected_type,
                            "actual_type": result.match_type,
                            "confidence": result.confidence,
                        })
                else:
                    # canonical이 없어도 되는 경우 (AI discovery 등)
                    passed += 1
            else:
                failed_cases.append({
                    "input": input_text,
                    "expected_canonical": expected_canonical,
                    "expected_type": expected_type,
                    "actual_type": result.match_type,
                    "actual_canonical": result.canonical.get("name_ko") if result.canonical else None,
                    "confidence": result.confidence,
                })

        except Exception as e:
            failed_cases.append({
                "input": input_text,
                "expected_canonical": expected_canonical,
                "expected_type": expected_type,
                "error": str(e),
            })

    total = len(ALL_TEST_CASES) - len(skipped_cases)
    accuracy = (passed / total * 100) if total > 0 else 0

    # 결과 출력
    print(f"\n{'='*60}")
    print(f"매칭 정확도 테스트 결과")
    print(f"{'='*60}")
    print(f"총 테스트: {len(ALL_TEST_CASES)}개")
    print(f"  ✅ 통과: {passed}개")
    print(f"  ❌ 실패: {len(failed_cases)}개")
    print(f"  ⏭️  스킵: {len(skipped_cases)}개")
    print(f"🎯 정확도: {accuracy:.1f}% ({passed}/{total})")
    print(f"{'='*60}\n")

    # 실패 케이스 상세 출력 (최대 20개)
    if failed_cases:
        print(f"실패 케이스 ({len(failed_cases)}개):")
        for i, case in enumerate(failed_cases[:20], 1):
            print(f"\n  {i}. 입력: '{case['input']}'")
            print(f"     기대: {case['expected_type']} → {case['expected_canonical']}")

            if 'error' in case:
                print(f"     오류: {case['error']}")
            else:
                print(f"     실제: {case.get('actual_type', 'N/A')} → {case.get('actual_canonical', 'N/A')}")
                if 'confidence' in case:
                    print(f"     신뢰도: {case['confidence']:.2f}")

        if len(failed_cases) > 20:
            print(f"\n  ... 외 {len(failed_cases) - 20}개 실패 케이스 생략")

    # 80% 이상 통과 확인
    assert accuracy >= 80.0, f"정확도 {accuracy:.1f}%: 목표 80% 미달"


@pytest.mark.asyncio
async def test_individual_exact_match(db_session: AsyncSession):
    """개별 테스트: 정확 매칭"""
    engine = MenuMatchingEngine(db_session)

    passed = 0
    for input_text, expected_canonical, expected_type in EXACT_MATCH_CASES:
        result = await engine.match_menu(input_text)
        if result.canonical and result.canonical.get("name_ko") == expected_canonical:
            passed += 1

    accuracy = (passed / len(EXACT_MATCH_CASES) * 100) if EXACT_MATCH_CASES else 0
    print(f"\n[정확 매칭] {passed}/{len(EXACT_MATCH_CASES)} = {accuracy:.1f}%")
    assert accuracy >= 90.0, f"정확 매칭 정확도 {accuracy:.1f}%: 목표 90% 미달"


@pytest.mark.asyncio
async def test_individual_normalization(db_session: AsyncSession):
    """개별 테스트: 정규화"""
    engine = MenuMatchingEngine(db_session)

    passed = 0
    for input_text, expected_canonical, expected_type in NORMALIZATION_CASES:
        result = await engine.match_menu(input_text)
        if result.canonical and result.canonical.get("name_ko") == expected_canonical:
            passed += 1

    accuracy = (passed / len(NORMALIZATION_CASES) * 100) if NORMALIZATION_CASES else 0
    print(f"\n[정규화] {passed}/{len(NORMALIZATION_CASES)} = {accuracy:.1f}%")
    assert accuracy >= 80.0, f"정규화 정확도 {accuracy:.1f}%: 목표 80% 미달"


@pytest.mark.asyncio
async def test_individual_modifier_decomposition(db_session: AsyncSession):
    """개별 테스트: 수식어 분해"""
    engine = MenuMatchingEngine(db_session)

    passed = 0
    for input_text, expected_canonical, expected_type in MODIFIER_CASES:
        result = await engine.match_menu(input_text)
        if result.canonical and result.canonical.get("name_ko") == expected_canonical:
            passed += 1

    accuracy = (passed / len(MODIFIER_CASES) * 100) if MODIFIER_CASES else 0
    print(f"\n[수식어 분해] {passed}/{len(MODIFIER_CASES)} = {accuracy:.1f}%")
    assert accuracy >= 70.0, f"수식어 분해 정확도 {accuracy:.1f}%: 목표 70% 미달"


if __name__ == "__main__":
    # 직접 실행 시
    asyncio.run(test_matching_accuracy(AsyncSessionLocal()))
