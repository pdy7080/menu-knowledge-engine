#!/usr/bin/env python3
"""
번역 API 진단 스크립트
OpenAI API 인증 및 번역 기능 테스트
"""

import asyncio
import json
from services.auto_translate_service import auto_translate_service
from config import settings

async def test_openai_auth():
    """OpenAI API 인증 테스트"""
    print("\n[1] OpenAI API 인증 테스트")
    print("-" * 50)

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=5
        )
        print("[OK] OpenAI API 인증 성공")
        print(f"    - Model: {response.model}")
        print(f"    - Usage: {response.usage.prompt_tokens} input, {response.usage.completion_tokens} output")
        return True
    except Exception as e:
        print(f"[FAIL] OpenAI API 인증 실패: {e}")
        return False

async def test_translation():
    """번역 기능 테스트"""
    print("\n[2] 번역 기능 테스트")
    print("-" * 50)

    try:
        result = await auto_translate_service._translate_with_gpt4o(
            menu_name_ko="김치찌개",
            description_en="Spicy fermented cabbage stew with kimchi, tofu, Korean vegetables"
        )

        if result.get("ja") and result.get("zh"):
            print("[OK] 번역 성공")
            print(f"    - Japanese length: {len(result['ja'])} chars")
            print(f"    - Chinese length: {len(result['zh'])} chars")
            # Save to file to avoid encoding issues
            with open("test_translation_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"    - 결과 저장: test_translation_result.json")
            return True
        else:
            print("[FAIL] 번역 결과가 비어있음")
            return False
    except Exception as e:
        print(f"[FAIL] 번역 실패: {e}")
        return False

async def main():
    print("=" * 50)
    print("번역 시스템 진단 보고서")
    print("=" * 50)

    # Test 1: API 인증
    auth_ok = await test_openai_auth()

    # Test 2: 번역 기능
    translation_ok = await test_translation()

    # Summary
    print("\n" + "=" * 50)
    print("진단 결과 요약")
    print("=" * 50)
    print(f"[{'PASS' if auth_ok else 'FAIL'}] OpenAI API 인증")
    print(f"[{'PASS' if translation_ok else 'FAIL'}] 번역 기능")

    if auth_ok and translation_ok:
        print("\n[결론] 모든 시스템이 정상 작동합니다.")
        print("      이제 배치 번역을 실행할 수 있습니다:")
        print("      python scripts/translate_canonical_menus_gpt4o.py --language ja,zh --batch-size 10")
    else:
        print("\n[결론] 문제가 있습니다. 위의 진단 결과를 확인하세요.")

if __name__ == "__main__":
    asyncio.run(main())
