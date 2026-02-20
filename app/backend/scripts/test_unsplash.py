"""Unsplash API 연동 테스트"""
import sys, asyncio
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'c:\project\menu\app\backend\scripts')

async def test():
    import logging
    logging.basicConfig(level=logging.DEBUG)

    from automation.image_collectors.unsplash_collector import UnsplashCollector
    from automation.config_auto import auto_settings

    print(f"Unsplash key: {auto_settings.UNSPLASH_ACCESS_KEY[:10]}...")

    collector = UnsplashCollector()
    images = await collector.search_images(
        query="Kimchi jjigae",
        menu_name_ko="김치찌개",
        per_page=3,
    )
    print(f"Found: {len(images)} images")
    for img in images:
        print(f"  - {img.source}: {img.url[:80]}...")
        print(f"    License: {img.license}, Size: {img.width}x{img.height}")

asyncio.run(test())
