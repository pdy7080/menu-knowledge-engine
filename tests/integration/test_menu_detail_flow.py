"""
Integration Tests - Menu Detail Flow (Sprint 2 Phase 1)

Tests the complete flow:
1. Menu list API → 2. Menu detail API → 3. Image loading → 4. Multi-language support

Success Criteria:
- Image coverage: 280 menus (93%)
- Content completeness: 100 menus at 90%+
- API response time: p95 < 500ms
- Image loading time: < 2s
- Multi-language: 4 languages (ko/en/ja/zh)
"""
import asyncio
import httpx
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app" / "backend"))

BASE_URL = "http://localhost:8000"
IMAGE_LOAD_TIMEOUT = 5.0  # 5 seconds max for image loading


class TestResults:
    """Test results tracker with performance metrics"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.api_response_times: List[float] = []
        self.image_load_times: List[float] = []
        self.menu_stats = {
            "total_menus": 0,
            "menus_with_images": 0,
            "menus_90_percent_complete": 0,
            "total_images": 0,
        }

    def add_pass(self, test_name: str):
        self.total += 1
        self.passed += 1
        print(f"  ✅ [PASS] {test_name}")

    def add_fail(self, test_name: str, reason: str):
        self.total += 1
        self.failed += 1
        print(f"  ❌ [FAIL] {test_name}")
        print(f"      Reason: {reason}")

    def add_api_time(self, duration_ms: float):
        """Record API response time"""
        self.api_response_times.append(duration_ms)

    def add_image_time(self, duration_s: float):
        """Record image loading time"""
        self.image_load_times.append(duration_s)

    def get_p95_api_time(self) -> float:
        """Calculate p95 API response time"""
        if not self.api_response_times:
            return 0.0
        sorted_times = sorted(self.api_response_times)
        p95_index = int(len(sorted_times) * 0.95)
        return sorted_times[p95_index]

    def get_avg_image_time(self) -> float:
        """Calculate average image loading time"""
        return mean(self.image_load_times) if self.image_load_times else 0.0

    def calculate_completeness(self, menu: Dict) -> float:
        """Calculate menu completeness percentage"""
        fields = [
            menu.get("name_ko"),
            menu.get("name_en"),
            menu.get("name_ja"),
            menu.get("name_zh"),
            menu.get("explanation_short"),
            menu.get("explanation_long"),
            menu.get("main_ingredients"),
            menu.get("image_url"),
            menu.get("allergens"),
            menu.get("spice_level"),
        ]
        filled_fields = sum(1 for f in fields if f and (isinstance(f, str) and f.strip() or isinstance(f, (int, float, list))))
        return (filled_fields / len(fields)) * 100

    def summary(self):
        print(f"\n{'=' * 80}")
        print(f"INTEGRATION TEST RESULTS - Sprint 2 Phase 1")
        print(f"{'=' * 80}")
        print(f"\n📊 Test Coverage: {self.passed}/{self.total} passed")

        if self.api_response_times:
            print(f"\n⚡ API Performance:")
            print(f"  - Mean: {mean(self.api_response_times):.2f}ms")
            print(f"  - Median: {median(self.api_response_times):.2f}ms")
            print(f"  - P95: {self.get_p95_api_time():.2f}ms (Target: < 500ms)")
            p95_pass = self.get_p95_api_time() < 500
            print(f"  - Status: {'✅ PASS' if p95_pass else '❌ FAIL'}")

        if self.image_load_times:
            avg_img_time = self.get_avg_image_time()
            print(f"\n🖼️  Image Loading:")
            print(f"  - Average: {avg_img_time:.2f}s (Target: < 2s)")
            print(f"  - Max: {max(self.image_load_times):.2f}s")
            img_pass = avg_img_time < 2.0
            print(f"  - Status: {'✅ PASS' if img_pass else '❌ FAIL'}")

        print(f"\n📈 Menu Data Quality:")
        print(f"  - Total menus: {self.menu_stats['total_menus']}")
        print(f"  - Menus with images: {self.menu_stats['menus_with_images']} ({self.menu_stats['menus_with_images']/max(1, self.menu_stats['total_menus'])*100:.1f}%)")
        print(f"  - Image coverage target: 280 menus (93%)")
        print(f"  - Total images: {self.menu_stats['total_images']}")
        print(f"  - Menus at 90%+ completeness: {self.menu_stats['menus_90_percent_complete']} (Target: 100)")

        print(f"\n{'=' * 80}")
        if self.failed > 0:
            print(f"❌ {self.failed} tests failed")
        else:
            print(f"✅ All tests passed!")
        print(f"{'=' * 80}\n")


async def test_menu_list_api(client: httpx.AsyncClient, results: TestResults):
    """Test 1: Menu List API"""
    print("\n[Test 1] GET /api/v1/canonical-menus - Fetch menu list")

    try:
        start = time.time()
        response = await client.get(f"{BASE_URL}/api/v1/canonical-menus")
        duration_ms = (time.time() - start) * 1000
        results.add_api_time(duration_ms)

        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            menus = data.get("data", [])

            results.menu_stats["total_menus"] = total

            if total > 0:
                results.add_pass(f"Menu list retrieved ({total} menus)")
            else:
                results.add_fail("Menu list count", "No menus found")

            if len(menus) == total:
                results.add_pass("Menu data count matches total")
            else:
                results.add_fail("Menu data count", f"Expected {total}, got {len(menus)}")

            # Check image coverage
            menus_with_images = sum(1 for m in menus if m.get("image_url"))
            total_images = sum(len(m.get("image_urls", [])) if isinstance(m.get("image_urls"), list) else 1 for m in menus if m.get("image_url"))

            results.menu_stats["menus_with_images"] = menus_with_images
            results.menu_stats["total_images"] = total_images

            image_coverage_pct = (menus_with_images / max(1, total)) * 100

            if menus_with_images >= 280:
                results.add_pass(f"Image coverage: {menus_with_images} menus ({image_coverage_pct:.1f}%)")
            else:
                results.add_fail("Image coverage", f"Expected 280+, got {menus_with_images} ({image_coverage_pct:.1f}%)")

            # Check completeness
            complete_menus = sum(1 for m in menus if results.calculate_completeness(m) >= 90)
            results.menu_stats["menus_90_percent_complete"] = complete_menus

            if complete_menus >= 100:
                results.add_pass(f"Content completeness: {complete_menus} menus at 90%+")
            else:
                results.add_fail("Content completeness", f"Expected 100+, got {complete_menus}")

            return menus[:10]  # Return first 10 menus for detail testing

        else:
            results.add_fail("Menu list API", f"Status code: {response.status_code}")
            return []

    except Exception as e:
        results.add_fail("Menu list API", f"Exception: {str(e)}")
        return []


async def test_menu_detail(client: httpx.AsyncClient, menu_id: str, results: TestResults) -> Optional[Dict]:
    """Test menu detail API for a specific menu"""
    try:
        start = time.time()
        response = await client.get(f"{BASE_URL}/api/v1/canonical-menus/{menu_id}")
        duration_ms = (time.time() - start) * 1000
        results.add_api_time(duration_ms)

        if response.status_code == 200:
            return response.json()
        else:
            results.add_fail(f"Menu detail {menu_id[:8]}", f"Status code: {response.status_code}")
            return None

    except Exception as e:
        results.add_fail(f"Menu detail {menu_id[:8]}", f"Exception: {str(e)}")
        return None


async def test_multi_language_support(client: httpx.AsyncClient, menu: Dict, results: TestResults):
    """Test 3: Multi-language support"""
    languages = ["ko", "en", "ja", "zh"]
    language_fields = {
        "ko": "name_ko",
        "en": "name_en",
        "ja": "name_ja",
        "zh": "name_zh",
    }

    menu_name = menu.get("name_ko", "Unknown")
    print(f"\n[Test 3] Multi-language support for '{menu_name}'")

    for lang in languages:
        field = language_fields[lang]
        value = menu.get(field)

        if value and value.strip():
            results.add_pass(f"Language {lang.upper()}: {value}")
        else:
            results.add_fail(f"Language {lang.upper()}", f"Missing {field}")


async def test_image_loading(client: httpx.AsyncClient, image_url: str, results: TestResults):
    """Test 4: Image loading performance"""
    if not image_url:
        return

    try:
        start = time.time()
        response = await client.get(image_url, timeout=IMAGE_LOAD_TIMEOUT)
        duration_s = time.time() - start
        results.add_image_time(duration_s)

        if response.status_code == 200:
            size_kb = len(response.content) / 1024
            if duration_s < 2.0:
                results.add_pass(f"Image loaded in {duration_s:.2f}s ({size_kb:.1f}KB)")
            else:
                results.add_fail("Image load time", f"{duration_s:.2f}s (Target: < 2s)")
        else:
            results.add_fail("Image loading", f"Status code: {response.status_code}")

    except asyncio.TimeoutError:
        results.add_fail("Image loading", f"Timeout after {IMAGE_LOAD_TIMEOUT}s")
    except Exception as e:
        results.add_fail("Image loading", f"Exception: {str(e)}")


async def run_integration_tests():
    """Run all integration tests"""
    results = TestResults()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Menu List API
        menus = await test_menu_list_api(client, results)

        if not menus:
            print("\n⚠️  No menus to test. Stopping.")
            results.summary()
            return False

        # Test 2-4: Menu Detail Flow (sample 10 menus)
        print(f"\n[Test 2-4] Testing detail flow for {len(menus)} sample menus")

        for i, menu in enumerate(menus, 1):
            menu_id = menu.get("id")
            menu_name = menu.get("name_ko", "Unknown")

            print(f"\n--- Sample Menu {i}/{len(menus)}: {menu_name} ---")

            # Fetch detail
            detail = await test_menu_detail(client, menu_id, results)

            if detail:
                # Test multi-language
                await test_multi_language_support(client, detail, results)

                # Test image loading (if available)
                image_url = detail.get("image_url")
                if image_url:
                    print(f"\n[Test 4] Image loading test")
                    await test_image_loading(client, image_url, results)

    # Print summary
    results.summary()

    # Check success criteria
    success_criteria = [
        results.failed == 0,
        results.get_p95_api_time() < 500,
        results.get_avg_image_time() < 2.0 if results.image_load_times else True,
        results.menu_stats["menus_with_images"] >= 280,
        results.menu_stats["menus_90_percent_complete"] >= 100,
    ]

    return all(success_criteria)


if __name__ == "__main__":
    print("=" * 80)
    print("INTEGRATION TEST SUITE - Sprint 2 Phase 1")
    print("Menu Detail Flow: List → Detail → Images → Multi-language")
    print("=" * 80)
    print("\nStarting tests...")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("")

    success = asyncio.run(run_integration_tests())

    if success:
        print("[DONE] ✅ All integration tests passed!")
        sys.exit(0)
    else:
        print("[WARNING] ⚠️  Some tests failed or success criteria not met.")
        sys.exit(1)
