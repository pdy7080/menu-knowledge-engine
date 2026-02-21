#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프로덕션 UI 번역 렌더링 라이브 브라우저 테스트

테스트 시나리오:
  1. 메인 페이지 로딩 확인
  2. 日本語 버튼 클릭 → 일본어 UI 전환 확인
  3. 中文 버튼 클릭 → 중국어 UI 전환 확인
  4. 메뉴 검색 → 번역 결과 렌더링 확인
  5. Popular Dishes 클릭 → 상세 번역 확인
"""
import asyncio, sys, os, json, re
from playwright.async_api import async_playwright

if sys.stdout.encoding and sys.stdout.encoding.lower() in ("cp949", "cp932", "mbcs"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROD_URL = "https://menu-knowledge.chargeapp.net"
SS_DIR = "tests/screenshots"
os.makedirs(SS_DIR, exist_ok=True)

def ss(name): return f"{SS_DIR}/{name}.png"

async def main():
    print("=" * 60)
    print("라이브 브라우저 번역 렌더링 테스트")
    print(f"대상: {PROD_URL}")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--lang=ko-KR"])
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR"
        )
        page = await ctx.new_page()

        # ── 1. 메인 페이지 ──────────────────────────────────────────
        print("\n[1] 메인 페이지 접속...")
        await page.goto(PROD_URL, wait_until="networkidle", timeout=20000)
        await page.screenshot(path=ss("01_main_ko"))
        title = await page.title()
        print(f"  ✓ 제목: {title}")

        # Popular Dishes 태그 확인
        tags = await page.query_selector_all(".menu-tag, .popular-tag, .tag-btn, button")
        tag_texts = []
        for t in tags[:20]:
            txt = (await t.text_content() or "").strip()
            if txt and len(txt) > 0:
                tag_texts.append(txt)
        print(f"  ✓ 버튼/태그: {tag_texts[:10]}")

        # ── 2. 日本語 버튼 클릭 ──────────────────────────────────────
        print("\n[2] 日本語 버튼 클릭...")
        ja_btn = await page.query_selector("text=日本語")
        if ja_btn:
            await ja_btn.click()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=ss("02_main_ja"))
            content = await page.text_content("body")
            # 일본어 문자 확인
            ja_chars = re.findall(r'[\u3040-\u30ff]', content or "")
            print(f"  ✓ 일본어 클릭 성공, 히라가나/카타카나 문자 수: {len(ja_chars)}")
            # UI 요소 텍스트 변화 확인
            headings = await page.query_selector_all("h1, h2, h3, p")
            for h in headings[:5]:
                txt = (await h.text_content() or "").strip()[:60]
                if txt:
                    print(f"    [{h.evaluate('el => el.tagName')}]: {txt}")
        else:
            print("  ✗ 日本語 버튼 없음")

        # ── 3. 中文 버튼 클릭 ──────────────────────────────────────
        print("\n[3] 中文 버튼 클릭...")
        zh_btn = await page.query_selector("text=中文")
        if zh_btn:
            await zh_btn.click()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=ss("03_main_zh"))
            content = await page.text_content("body")
            zh_chars = re.findall(r'[\u4e00-\u9fff]', content or "")
            print(f"  ✓ 중국어 클릭 성공, 한자 문자 수: {len(zh_chars)}")
        else:
            print("  ✗ 中文 버튼 없음")

        # EN으로 복귀
        en_btn = await page.query_selector("text=EN")
        if en_btn:
            await en_btn.click()
            await page.wait_for_timeout(800)

        # ── 4. 메뉴 검색 (김치찌개) ──────────────────────────────────
        print("\n[4] 메뉴 검색 테스트: 김치찌개...")
        search_input = await page.query_selector("input[type=text], input[placeholder*='menu'], input[placeholder*='Menu'], textarea")
        if search_input:
            await search_input.click()
            await search_input.fill("김치찌개")
            await page.wait_for_timeout(500)
            await page.screenshot(path=ss("04_search_input"))

            # 검색 버튼 클릭 또는 Enter
            search_btn = await page.query_selector("button[type=submit], .search-btn, button.btn-search")
            if search_btn:
                await search_btn.click()
            else:
                await page.keyboard.press("Enter")

            await page.wait_for_timeout(3000)
            await page.screenshot(path=ss("05_search_result_kimchi"))

            # 결과 텍스트 확인
            body_text = await page.text_content("body")
            ja_in_result = bool(re.search(r'キムチ|チゲ|[\u3040-\u30ff]', body_text or ""))
            zh_in_result = bool(re.search(r'泡菜|[\u4e00-\u9fff]', body_text or ""))
            print(f"  ✓ 검색 완료")
            print(f"  일본어 텍스트 노출: {'✅' if ja_in_result else '❌'}")
            print(f"  중국어 텍스트 노출: {'✅' if zh_in_result else '❌'}")
        else:
            print("  ✗ 검색 입력창 없음")

        # ── 5. 검색 결과에서 일본어 탭 전환 ────────────────────────────
        print("\n[5] 검색 결과 + 日本語 전환...")
        ja_btn2 = await page.query_selector("text=日本語")
        if ja_btn2:
            await ja_btn2.click()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=ss("06_result_ja"))
            body = await page.text_content("body")
            ja_count = len(re.findall(r'[\u3040-\u30ff\u4e00-\u9fff]', body or ""))
            print(f"  ✓ 결과 페이지 일본어/한자 문자: {ja_count}개")

        # ── 6. Popular Dish 클릭 (삼겹살) ───────────────────────────
        print("\n[6] Popular Dish 클릭: 삼겹살...")
        # EN으로 복귀
        en_btn2 = await page.query_selector("text=EN")
        if en_btn2:
            await en_btn2.click()
            await page.wait_for_timeout(500)

        samgyup = await page.query_selector("text=삼겹살")
        if samgyup:
            await samgyup.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path=ss("07_samgyup_detail"))
            body = await page.text_content("body")
            has_en = bool(re.search(r'pork|belly|grill', body.lower() or ""))
            print(f"  ✓ 삼겹살 상세 페이지")
            print(f"  영문 설명 노출: {'✅' if has_en else '❌'}")
        else:
            print("  ✗ 삼겹살 버튼 없음")

        # ── 7. 삼겹살 상세 + 中文 전환 ──────────────────────────────
        print("\n[7] 삼겹살 상세 + 中文 전환...")
        zh_btn2 = await page.query_selector("text=中文")
        if zh_btn2:
            await zh_btn2.click()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=ss("08_samgyup_zh"))
            body = await page.text_content("body")
            zh_count = len(re.findall(r'[\u4e00-\u9fff]', body or ""))
            print(f"  ✓ 중국어 전환, 한자 수: {zh_count}개")
            # 삼겹살 관련 중국어 확인
            zh_name = bool(re.search(r'五花肉|삼겹살', body or ""))
            print(f"  삼겹살 중국어명 노출: {'✅' if zh_name else '⚠️ 확인 필요'}")

        # ── 8. API 직접 호출로 데이터 검증 ─────────────────────────
        print("\n[8] API 직접 검증 (canonical-menus 엔드포인트)...")
        api_page = await ctx.new_page()

        # 올바른 API 엔드포인트 탐색
        endpoints_to_try = [
            f"{PROD_URL}/api/v1/canonical-menus/search?q=김치찌개",
            f"{PROD_URL}/api/v1/canonical-menus?name=김치찌개",
            f"{PROD_URL}/api/v1/canonical-menus?q=김치찌개",
            f"{PROD_URL}/api/v1/canonical-menus?limit=5",
        ]
        for ep in endpoints_to_try:
            try:
                resp = await api_page.goto(ep, wait_until="networkidle", timeout=8000)
                if resp and resp.ok:
                    body = await api_page.text_content("body")
                    data = json.loads(body)
                    print(f"  ✓ {ep.split('?')[1] if '?' in ep else ep[-30:]}")
                    print(f"    응답 타입: {type(data).__name__}, 키: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                    if isinstance(data, dict) and data.get("items"):
                        item = data["items"][0]
                        print(f"    첫 항목: {item.get('name_ko')} | JA:{item.get('name_ja','❌')} | ZH:{item.get('name_zh_cn','❌')}")
                    elif isinstance(data, list) and data:
                        item = data[0]
                        print(f"    첫 항목: {item.get('name_ko')} | JA:{item.get('name_ja','❌')} | ZH:{item.get('name_zh_cn','❌')}")
                    break
            except Exception as e:
                print(f"  ✗ 오류: {e}")

        await browser.close()

    # ── 결과 요약 ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("테스트 완료 - 스크린샷 저장 위치:")
    for f in sorted(os.listdir(SS_DIR)):
        if f.endswith(".png"):
            print(f"  📸 {SS_DIR}/{f}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
