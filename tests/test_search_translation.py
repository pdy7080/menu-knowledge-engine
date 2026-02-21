#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메뉴 검색 → 번역 결과 렌더링 집중 테스트
"""
import asyncio, sys, os, re, json
from playwright.async_api import async_playwright

if sys.stdout.encoding and sys.stdout.encoding.lower() in ("cp949", "cp932", "mbcs"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROD_URL = "https://menu-knowledge.chargeapp.net"
SS = "tests/screenshots"
os.makedirs(SS, exist_ok=True)

TEST_MENUS = ["김치찌개", "삼겹살", "비빔밥", "불고기", "순대국밥"]

async def search_and_capture(page, menu_name, lang_btn_text, lang_code):
    """메뉴 검색 후 언어 전환하여 스크린샷"""
    # 페이지 초기화
    await page.goto(PROD_URL, wait_until="networkidle", timeout=15000)
    await page.wait_for_timeout(500)

    # 언어 버튼 먼저 선택
    if lang_btn_text != "EN":
        btn = page.locator(f"text={lang_btn_text}")
        await btn.click()
        await page.wait_for_timeout(300)

    # 검색창 입력
    inp = page.locator("input[type=text], input[placeholder*='menu'], input[placeholder*='Menu']").first
    await inp.click()
    await inp.fill(menu_name)
    await page.wait_for_timeout(200)

    # 검색 실행
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(4000)  # API 응답 대기

    # 스크린샷
    fname = f"{SS}/search_{menu_name}_{lang_code}.png"
    await page.screenshot(path=fname, full_page=False)
    return fname


async def main():
    print("=" * 60)
    print("메뉴 검색 + 번역 렌더링 테스트")
    print("=" * 60)

    results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()

        # API 응답 인터셉트로 번역 데이터 확인
        api_responses = []
        async def handle_response(response):
            if "/api/v1/" in response.url and response.status == 200:
                try:
                    body = await response.json()
                    api_responses.append({"url": response.url, "data": body})
                except:
                    pass
        page.on("response", handle_response)

        # ── 김치찌개 × 3개 언어 ─────────────────────────────────
        print(f"\n[1] 김치찌개 EN 검색...")
        fname = await search_and_capture(page, "김치찌개", "EN", "en")
        print(f"  스크린샷: {fname}")

        print(f"\n[2] 김치찌개 日本語 검색...")
        fname = await search_and_capture(page, "김치찌개", "日本語", "ja")
        print(f"  스크린샷: {fname}")

        print(f"\n[3] 김치찌개 中文 검색...")
        fname = await search_and_capture(page, "김치찌개", "中文", "zh")
        print(f"  스크린샷: {fname}")

        # ── 삼겹살 검색 후 언어 전환 ────────────────────────────
        print(f"\n[4] 삼겹살 EN 검색...")
        await page.goto(PROD_URL, wait_until="networkidle")
        inp = page.locator("input[type=text]").first
        await inp.fill("삼겹살")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(4000)
        await page.screenshot(path=f"{SS}/search_samgyup_en.png")

        # 결과 페이지에서 언어 전환
        print(f"\n[5] 삼겹살 결과 → 日本語 전환...")
        ja_btn = page.locator("text=日本語")
        await ja_btn.click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{SS}/search_samgyup_ja.png")
        body_ja = await page.text_content("body")

        print(f"\n[6] 삼겹살 결과 → 中文 전환...")
        zh_btn = page.locator("text=中文")
        await zh_btn.click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{SS}/search_samgyup_zh.png")
        body_zh = await page.text_content("body")

        # 분석
        ja_chars = len(re.findall(r'[\u3040-\u30ff]', body_ja or ""))
        zh_chars = len(re.findall(r'[\u4e00-\u9fff]', body_zh or ""))
        print(f"\n  삼겹살 일본어 페이지 - 히라가나/카타카나: {ja_chars}자")
        print(f"  삼겹살 중국어 페이지 - 한자: {zh_chars}자")

        # ── 비빔밥 × 중문 검색 ───────────────────────────────────
        print(f"\n[7] 비빔밥 中文 직접 검색...")
        fname = await search_and_capture(page, "비빔밥", "中文", "zh")
        print(f"  스크린샷: {fname}")

        # API 인터셉트 결과 출력
        print(f"\n[API 인터셉트] 총 {len(api_responses)}개 API 호출 감지")
        for r in api_responses[:5]:
            url_short = r["url"].split("?")[0].split("/")[-2:]
            data = r["data"]
            if isinstance(data, dict):
                items = data.get("items", data.get("data", []))
                if items and isinstance(items, list) and items:
                    item = items[0]
                    print(f"  /{'/'.join(url_short)}: {item.get('name_ko','?')} -> JA:{item.get('name_ja','?')[:15]} ZH:{item.get('name_zh_cn','?')[:15]}")

        await browser.close()

    print("\n" + "=" * 60)
    print("스크린샷 목록:")
    for f in sorted(os.listdir(SS)):
        if "search_" in f:
            print(f"  {SS}/{f}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
