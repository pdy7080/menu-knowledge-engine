"""
Browser E2E Test - Ralph Loop Iteration
Playwright로 프로덕션 사이트 브라우저 테스트
"""
from playwright.sync_api import sync_playwright
import json
import time

PROD_URL = "https://menu-knowledge.chargeapp.net"


def test_landing_page(page, base_url):
    """랜딩 페이지 로드 및 검색 테스트"""
    issues = []

    # 1. 페이지 로드
    response = page.goto(base_url, wait_until="networkidle", timeout=15000)
    if response.status != 200:
        issues.append(f"Landing page returned {response.status}")

    # 2. 콘솔 에러 캡처
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.wait_for_timeout(2000)

    # 3. 검색 기능 테스트
    search_input = page.locator('#menuInput')
    if search_input.count() > 0:
        search_input.fill("김치찌개")
        search_btn = page.locator('#searchBtn')
        if search_btn.count() > 0:
            search_btn.click()
            page.wait_for_timeout(3000)
    else:
        issues.append("Search input #menuInput not found on landing page")

    # 4. CSS 로드 확인
    stylesheets = page.evaluate("() => Array.from(document.styleSheets).length")
    if stylesheets < 1:
        issues.append(f"Only {stylesheets} stylesheets loaded")

    # 5. Popular dishes 버튼 확인
    dish_tags = page.locator('.dish-tag')
    if dish_tags.count() == 0:
        issues.append("No dish-tag buttons found on landing page")

    # 6. JS 에러 확인 (API 연결 실패는 제외)
    real_errors = [e for e in console_errors
                   if not any(skip in e for skip in ['API Status', 'fetch', 'network', 'CORS'])]
    if real_errors:
        issues.extend([f"Console error: {e}" for e in real_errors[:3]])

    return issues


def test_menu_detail_page(page, base_url):
    """메뉴 상세 페이지 테스트"""
    issues = []

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    response = page.goto(f"{base_url}/menu-detail.html?name=김치찌개", wait_until="networkidle", timeout=15000)
    if response.status != 200:
        issues.append(f"Menu detail page returned {response.status}")

    page.wait_for_timeout(4000)

    # 페이지 로드 확인
    body_text = page.text_content("body")
    if "김치" not in (body_text or ""):
        issues.append("Menu name '김치' not displayed on detail page")

    # 탭 버튼 확인
    tabs = page.locator('.tab-btn')
    if tabs.count() == 0:
        issues.append("No tab buttons found on detail page")

    # 이미지 영역 확인
    image_carousel = page.locator('#imageCarouselContainer')
    if image_carousel.count() == 0:
        issues.append("Image carousel container not found")

    # JS 에러 확인 (DB 연결 에러는 허용)
    real_errors = [e for e in console_errors
                   if not any(skip in e for skip in ['API Error', 'fetch', 'network', '500', 'HTTP 500'])]
    if real_errors:
        issues.extend([f"Console error: {e}" for e in real_errors[:3]])

    return issues


def test_api_health_from_browser(page, base_url):
    """브라우저에서 API health check 테스트"""
    issues = []

    response = page.goto(f"{base_url}/health", timeout=10000)
    if response.status != 200:
        issues.append(f"Health endpoint returned {response.status}")
    else:
        body = page.text_content("body")
        if "ok" not in (body or "").lower():
            issues.append("Health check did not return ok status")

    return issues


def test_css_cache_busting(page, base_url):
    """CSS 캐시 버스팅 파라미터 확인"""
    issues = []

    response = page.goto(base_url, wait_until="domcontentloaded", timeout=15000)
    if response.status != 200:
        issues.append(f"Page returned {response.status}")
        return issues

    # CSS 링크에 ?v= 파라미터 확인
    css_links = page.evaluate("""
        () => Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
                   .map(l => l.href)
    """)
    local_css = [link for link in css_links if 'chargeapp.net' in link or 'localhost' in link]
    for link in local_css:
        if '?v=' not in link and '?v=' not in link:
            issues.append(f"CSS without cache busting: {link}")

    return issues


def run_all_tests(base_url=PROD_URL):
    """모든 테스트 실행"""
    all_issues = []
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("=== Test 1: API Health Check ===")
        issues = test_api_health_from_browser(page, base_url)
        results['api_health'] = issues
        all_issues.extend(issues)
        if not issues:
            print("  PASS")
        else:
            for i in issues:
                print(f"  FAIL: {i}")

        print("\n=== Test 2: Landing Page ===")
        issues = test_landing_page(page, base_url)
        results['landing_page'] = issues
        all_issues.extend(issues)
        if not issues:
            print("  PASS")
        else:
            for i in issues:
                print(f"  FAIL: {i}")

        print("\n=== Test 3: CSS Cache Busting ===")
        issues = test_css_cache_busting(page, base_url)
        results['css_cache_busting'] = issues
        all_issues.extend(issues)
        if not issues:
            print("  PASS")
        else:
            for i in issues:
                print(f"  FAIL: {i}")

        print("\n=== Test 4: Menu Detail Page ===")
        issues = test_menu_detail_page(page, base_url)
        results['menu_detail'] = issues
        all_issues.extend(issues)
        if not issues:
            print("  PASS")
        else:
            for i in issues:
                print(f"  FAIL: {i}")

        browser.close()

    return all_issues, results


if __name__ == "__main__":
    print(f"Testing: {PROD_URL}")
    print("=" * 50)
    issues, results = run_all_tests()
    print(f"\n{'='*50}")
    print(f"Total issues: {len(issues)}")
    if issues:
        print("RESULT: FAIL")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("RESULT: ALL PASS")
