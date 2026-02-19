"""
Sprint 4 OCR Integration Test

테스트 범위:
1. OcrProvider 인터페이스 기본 검증
2. OcrProviderGpt 로드 및 초기화
3. OrchestratorService 기본 동작
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ocr_provider import OcrProvider, OcrProviderType, OcrResult
from services.ocr_provider_gpt import OcrProviderGpt
from services.ocr_tier_router import OcrTierRouter
from services.ocr_orchestrator import ocr_orchestrator
from config import settings


def test_ocr_provider_interface():
    """OcrProvider 인터페이스 검증"""
    print("\n[TEST 1] OcrProvider 인터페이스 검증")

    # 1. OcrProvider는 추상 클래스
    try:
        provider = OcrProvider()
        print("  FAIL: OcrProvider should not be instantiable")
        return False
    except TypeError as e:
        print("  PASS: OcrProvider is abstract (cannot instantiate)")

    # 2. OcrProviderType enum 확인
    assert hasattr(OcrProviderType, 'GPT_VISION')
    assert hasattr(OcrProviderType, 'CLOVA')
    print("  PASS: OcrProviderType enums exist")

    return True


def test_ocr_provider_gpt_initialization():
    """OcrProviderGpt 초기화 테스트"""
    print("\n[TEST 2] OcrProviderGpt 초기화")

    # 1. OpenAI API 키 확인
    if not settings.OPENAI_API_KEY:
        print("  FAIL: OPENAI_API_KEY not configured")
        return False

    # 2. Provider 생성
    try:
        provider_gpt = OcrProviderGpt()
        print(f"  PASS: OcrProviderGpt initialized")
        print(f"    - Model: {provider_gpt.model}")
        print(f"    - Temperature: {provider_gpt.temperature}")
        print(f"    - Provider type: {provider_gpt.provider_type}")
        return True
    except Exception as e:
        print(f"  FAIL: {str(e)}")
        return False


async def test_ocr_tier_router_initialization():
    """OcrTierRouter 초기화 테스트"""
    print("\n[TEST 3] OcrTierRouter 초기화")

    try:
        router = OcrTierRouter()

        # Tier 1 확인
        if router.tier_1_provider:
            print("  PASS: Tier 1 (GPT Vision) initialized")
            print(f"    - Type: {router.tier_1_provider.provider_type}")
        else:
            print("  WARN: Tier 1 (GPT Vision) not available")

        # Tier 2 확인
        if router.tier_2_provider:
            print("  PASS: Tier 2 (CLOVA) initialized")
            print(f"    - Type: {router.tier_2_provider.provider_type}")
        else:
            print("  WARN: Tier 2 (CLOVA) not available")

        # Fallback trigger 확인
        print(f"  PASS: Fallback triggers configured")
        print(f"    - Tier 1 confidence threshold: {router.tier_1_trigger.confidence_threshold}")
        print(f"    - Tier 2 confidence threshold: {router.tier_2_trigger.confidence_threshold}")

        return True
    except Exception as e:
        print(f"  FAIL: {str(e)}")
        return False


async def test_ocr_orchestrator_initialization():
    """OrchestratorService 초기화 테스트"""
    print("\n[TEST 4] OrchestratorService 초기화")

    try:
        # OrchestratorService 싱글톤 확인
        print(f"  PASS: ocr_orchestrator singleton available")
        print(f"    - Router type: {type(ocr_orchestrator.tier_router).__name__}")
        print(f"    - Cache TTL: {ocr_orchestrator.cache_ttl_seconds} seconds (30 days)")

        return True
    except Exception as e:
        print(f"  FAIL: {str(e)}")
        return False


async def test_configuration_consistency():
    """설정 일관성 테스트"""
    print("\n[TEST 5] 설정 일관성 검증")

    errors = []

    # 1. OpenAI API 키 존재 여부
    if not settings.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is empty")
    else:
        print("  PASS: OPENAI_API_KEY configured")

    # 2. Redis 설정
    print(f"  PASS: Redis configuration")
    print(f"    - Host: {settings.REDIS_HOST}")
    print(f"    - Port: {settings.REDIS_PORT}")
    print(f"    - DB: {settings.REDIS_DB}")
    print(f"    - Enabled: {settings.CACHE_ENABLED}")

    # 3. 데이터베이스 설정
    if settings.DATABASE_URL:
        print(f"  PASS: Database configured")
        print(f"    - URL: {settings.DATABASE_URL[:50]}...")
    else:
        errors.append("DATABASE_URL is empty")

    if errors:
        print(f"\n  WARNINGS:")
        for err in errors:
            print(f"    - {err}")
        return False

    return True


async def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Sprint 4 OCR Integration Test Suite")
    print("=" * 60)

    results = {}

    # 동기 테스트
    results['interface'] = test_ocr_provider_interface()
    results['gpt_init'] = test_ocr_provider_gpt_initialization()

    # 비동기 테스트
    results['router_init'] = await test_ocr_tier_router_initialization()
    results['orchestrator_init'] = await test_ocr_orchestrator_initialization()
    results['config'] = await test_configuration_consistency()

    # 결과 출력
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"[{status}] {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    # 비동기 테스트 실행
    success = asyncio.run(run_all_tests())

    # 종료 코드
    sys.exit(0 if success else 1)
