"""
자동화 시스템 통합 테스트
각 모듈을 순차적으로 테스트
"""
import sys
import asyncio
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, r'c:\project\menu\app\backend\scripts')


async def test_ollama_enrichment():
    """Test 1: Ollama로 메뉴 콘텐츠 생성"""
    print("=" * 60)
    print("TEST 1: Ollama Content Generation")
    print("=" * 60)

    from automation.ollama_client import OllamaClient
    from automation.content_generator import ContentGenerator

    ollama = OllamaClient()
    generator = ContentGenerator(ollama)

    # Ollama 확인
    available = await generator.check_ollama()
    print(f"  Ollama available: {available}")
    if not available:
        print("  SKIP: Ollama not running")
        return False

    # 김치찌개 테스트
    menu = {"name_ko": "김치찌개", "name_en": "Kimchi Jjigae"}
    print(f"  Enriching: {menu['name_ko']}...")

    result = await generator.enrich_menu(menu)
    if result:
        print(f"  SUCCESS: Got {len(result)} fields")
        for key in sorted(result.keys()):
            val = result[key]
            if isinstance(val, str):
                print(f"    {key}: {val[:80]}...")
            elif isinstance(val, list):
                print(f"    {key}: [{len(val)} items]")
            else:
                print(f"    {key}: {val}")
        return True
    else:
        print("  FAILED: No result")
        return False


async def test_menu_discovery():
    """Test 2: 메뉴 수집 (public data 소스만)"""
    print("\n" + "=" * 60)
    print("TEST 2: Menu Discovery (Public Data only)")
    print("=" * 60)

    from automation.collectors.public_data_collector import PublicDataCollector

    collector = PublicDataCollector()
    result = await collector.collect(limit=10)
    print(f"  Discovered: {result.discovered} menus")
    print(f"  New: {result.new_items}")

    if result.menus:
        for m in result.menus[:5]:
            print(f"    - {m.name_ko} ({m.name_en or 'no EN'})")
        return True
    else:
        print("  No menus found (data files may not exist)")
        return False


async def test_image_search():
    """Test 3: 이미지 검색 (Wikimedia만, API 키 불필요)"""
    print("\n" + "=" * 60)
    print("TEST 3: Image Search (Wikimedia Commons)")
    print("=" * 60)

    from automation.image_collectors.wikimedia_collector import WikimediaCollector, HEADERS
    import httpx

    print(f"  User-Agent: {HEADERS.get('User-Agent', 'MISSING')[:60]}...")

    # 직접 API 호출 테스트
    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
        r = await client.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query",
            "generator": "search",
            "gsrnamespace": "6",
            "gsrsearch": "Kimchi jjigae korean food",
            "gsrlimit": "3",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": "800",
            "format": "json",
        })
        print(f"  Direct API: status={r.status_code}, len={len(r.content)}")

    collector = WikimediaCollector()
    images = await collector.search_images(
        query="Kimchi jjigae",
        menu_name_ko="김치찌개",
        per_page=3,
    )
    print(f"  Found: {len(images)} images")

    for img in images:
        print(f"    - {img.source}: {img.url[:80]}...")
        print(f"      License: {img.license}")

    return len(images) > 0


async def test_health_endpoint():
    """Test 4: Health endpoint 생성 확인"""
    print("\n" + "=" * 60)
    print("TEST 4: Health App Creation")
    print("=" * 60)

    from automation.health import create_health_app
    app = create_health_app()
    if app:
        print(f"  SUCCESS: FastAPI app created")
        print(f"  Routes: {[r.path for r in app.routes]}")
        return True
    else:
        print("  FAILED: Could not create health app")
        return False


async def main():
    print("Menu Automation System - Integration Test")
    print("=" * 60)

    results = {}

    # Test 1: Ollama
    try:
        results["ollama"] = await test_ollama_enrichment()
    except Exception as e:
        print(f"  ERROR: {e}")
        results["ollama"] = False

    # Test 2: Menu Discovery
    try:
        results["discovery"] = await test_menu_discovery()
    except Exception as e:
        print(f"  ERROR: {e}")
        results["discovery"] = False

    # Test 3: Image Search
    try:
        results["images"] = await test_image_search()
    except Exception as e:
        print(f"  ERROR: {e}")
        results["images"] = False

    # Test 4: Health
    try:
        results["health"] = await test_health_endpoint()
    except Exception as e:
        print(f"  ERROR: {e}")
        results["health"] = False

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n  {passed}/{total} tests passed")


if __name__ == "__main__":
    asyncio.run(main())
