#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
번역 품질 브라우저 테스트 (Playwright)

테스트 항목:
1. API 엔드포인트 직접 호출 - 번역 데이터 존재 여부
2. 번역 품질 검증 (글자수, 문자셋, 공백 여부)
3. 프론트엔드 UI - 번역 렌더링 확인
4. 특이 메뉴 번역 품질 집중 검토

실행: python tests/test_translation_quality.py
"""

import asyncio
import json
import re
import sys
import os

# Windows cp949 콘솔 인코딩 문제 해결
if sys.stdout.encoding and sys.stdout.encoding.lower() in ("cp949", "cp932", "mbcs"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Playwright
from playwright.async_api import async_playwright, Page, BrowserContext

# DB
import psycopg2
import psycopg2.extras

# ─────────────────────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────────────────────
PROD_URL = "https://menu-knowledge.chargeapp.net"
API_BASE = f"{PROD_URL}/api/v1"
LOCAL_URL = "http://localhost:8001"
LOCAL_API = f"{LOCAL_URL}/api/v1"

DB_PASS = "eromlab" + chr(33) + "1228"
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "chargeap_menu_knowledge",
    "user": "chargeap_dcclab2022",
    "password": DB_PASS
}

REPORT_FILE = f"TRANSLATION_QUALITY_REPORT_{datetime.now().strftime('%Y%m%d_%H%M')}.md"

# 중점 테스트 메뉴 (다양한 유형)
TEST_MENUS = [
    "김치찌개",      # 대표 메뉴
    "삼계탕",        # 한식 정수
    "짜장면",        # 중화풍 한식
    "짬뽕",          # 이전 실패 메뉴
    "불고기",        # 세계적 인지도
    "비빔밥",        # 복잡한 메뉴
    "순대국밥",      # 고유 한식
    "왕갈비",        # 수식어 포함
    "된장찌개",      # 발효 음식
    "제육볶음",      # 조리법
    "오징어볶음",    # 해산물
    "돼지갈비찜",    # 이전 실패 메뉴
]

# ─────────────────────────────────────────────────────────────────────────────
# 번역 품질 검증 함수
# ─────────────────────────────────────────────────────────────────────────────
def has_japanese(text: str) -> bool:
    """일본어 문자 포함 여부 (히라가나/카타카나/한자)"""
    return bool(re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', text or ""))


def has_chinese(text: str) -> bool:
    """중국어 간체 문자 포함 여부"""
    return bool(re.search(r'[\u4e00-\u9fff]', text or ""))


def check_translation_quality(menu: Dict) -> Dict:
    """단일 메뉴 번역 품질 체크"""
    issues = []
    score = 100

    name_ko = menu.get("name_ko", "")
    name_ja = menu.get("name_ja") or ""
    name_zh = menu.get("name_zh_cn") or ""
    expl = menu.get("explanation_short") or {}
    desc_ja = expl.get("ja", "") if isinstance(expl, dict) else ""
    desc_zh = expl.get("zh", "") if isinstance(expl, dict) else ""

    # 1. 이름 번역 존재 여부
    if not name_ja:
        issues.append("❌ name_ja 없음")
        score -= 30
    elif not has_japanese(name_ja):
        issues.append(f"⚠️ name_ja 일본어 문자 없음: '{name_ja}'")
        score -= 15

    if not name_zh:
        issues.append("❌ name_zh_cn 없음")
        score -= 30
    elif not has_chinese(name_zh):
        issues.append(f"⚠️ name_zh_cn 중국어 문자 없음: '{name_zh}'")
        score -= 15

    # 2. 설명 번역 존재 여부
    if not desc_ja:
        issues.append("⚠️ explanation_short.ja 없음")
        score -= 10
    elif len(desc_ja) < 10:
        issues.append(f"⚠️ desc_ja 너무 짧음 ({len(desc_ja)}자): '{desc_ja}'")
        score -= 5
    elif not has_japanese(desc_ja):
        issues.append(f"⚠️ desc_ja 일본어 문자 없음")
        score -= 10

    if not desc_zh:
        issues.append("⚠️ explanation_short.zh 없음")
        score -= 10
    elif len(desc_zh) < 10:
        issues.append(f"⚠️ desc_zh 너무 짧음 ({len(desc_zh)}자): '{desc_zh}'")
        score -= 5
    elif not has_chinese(desc_zh):
        issues.append(f"⚠️ desc_zh 중국어 문자 없음")
        score -= 10

    # 3. 한국어가 그대로 복사된 경우
    if name_ko and name_ja == name_ko:
        issues.append(f"❌ name_ja가 한국어와 동일 (번역 안 됨)")
        score -= 25
    if name_ko and name_zh == name_ko:
        issues.append(f"❌ name_zh가 한국어와 동일 (번역 안 됨)")
        score -= 25

    # 4. 영어가 그대로 들어간 경우
    name_en = menu.get("name_en", "")
    if name_en and name_ja and name_en.lower() in name_ja.lower():
        issues.append(f"⚠️ name_ja에 영어 포함: '{name_ja}'")
        score -= 5

    return {
        "score": max(0, score),
        "issues": issues,
        "name_ja": name_ja,
        "name_zh": name_zh,
        "desc_ja": desc_ja[:60] + "..." if len(desc_ja) > 60 else desc_ja,
        "desc_zh": desc_zh[:60] + "..." if len(desc_zh) > 60 else desc_zh,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DB 직접 검증
# ─────────────────────────────────────────────────────────────────────────────
def check_db_translations() -> Dict:
    """DB에서 직접 번역 통계 및 샘플 조회"""
    print("\n[DB] 번역 데이터 직접 검증 중...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # 전체 통계
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN name_ja IS NOT NULL AND name_ja != '' THEN 1 END) as has_name_ja,
            COUNT(CASE WHEN name_zh_cn IS NOT NULL AND name_zh_cn != '' THEN 1 END) as has_name_zh,
            COUNT(CASE WHEN explanation_short IS NOT NULL
                        AND (explanation_short ? 'ja')
                        AND (explanation_short->>'ja') != '' THEN 1 END) as has_desc_ja,
            COUNT(CASE WHEN explanation_short IS NOT NULL
                        AND (explanation_short ? 'zh')
                        AND (explanation_short->>'zh') != '' THEN 1 END) as has_desc_zh
        FROM canonical_menus WHERE status = 'active'
    """)
    stats = dict(cur.fetchone())

    # 테스트 메뉴 조회
    cur.execute("""
        SELECT id::text, name_ko, name_en, name_ja, name_zh_cn, explanation_short
        FROM canonical_menus
        WHERE status = 'active'
        AND name_ko = ANY(%s)
        ORDER BY name_ko
    """, (TEST_MENUS,))
    test_results = [dict(r) for r in cur.fetchall()]

    # 전체 랜덤 샘플 (30개)
    cur.execute("""
        SELECT id::text, name_ko, name_en, name_ja, name_zh_cn, explanation_short
        FROM canonical_menus
        WHERE status = 'active'
        ORDER BY RANDOM()
        LIMIT 30
    """)
    sample_results = [dict(r) for r in cur.fetchall()]

    # 문제 있는 메뉴 찾기
    cur.execute("""
        SELECT name_ko, name_ja, name_zh_cn, translation_status, translation_error
        FROM canonical_menus
        WHERE status = 'active'
          AND (
              name_ja IS NULL OR name_ja = ''
              OR name_zh_cn IS NULL OR name_zh_cn = ''
          )
        ORDER BY name_ko
        LIMIT 20
    """)
    missing = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        "stats": stats,
        "test_menus": test_results,
        "sample": sample_results,
        "missing": missing
    }


# ─────────────────────────────────────────────────────────────────────────────
# Playwright 브라우저 테스트
# ─────────────────────────────────────────────────────────────────────────────
async def test_api_endpoint(page: Page, base_url: str, menu_name: str) -> Optional[Dict]:
    """API 엔드포인트로 메뉴 조회"""
    try:
        # 메뉴 검색 API 호출
        response = await page.goto(
            f"{base_url}/canonical-menus?search={menu_name}&limit=1",
            wait_until="networkidle",
            timeout=15000
        )
        if response and response.ok:
            content = await page.text_content("body")
            data = json.loads(content)
            if data.get("items") and len(data["items"]) > 0:
                return data["items"][0]
    except Exception as e:
        print(f"  API 오류 ({menu_name}): {e}")
    return None


async def test_frontend_ui(page: Page, base_url: str) -> Dict:
    """프론트엔드 UI 번역 렌더링 테스트"""
    results = {
        "accessible": False,
        "title": "",
        "screenshots": [],
        "errors": []
    }

    try:
        print(f"\n[UI] 프론트엔드 접속 중: {base_url}")
        response = await page.goto(base_url, wait_until="networkidle", timeout=20000)

        if response and response.ok:
            results["accessible"] = True
            results["title"] = await page.title()
            print(f"  ✓ 접속 성공: '{results['title']}'")

            # 스크린샷 저장
            ss_path = f"tests/screenshots/frontend_{datetime.now().strftime('%H%M%S')}.png"
            os.makedirs("tests/screenshots", exist_ok=True)
            await page.screenshot(path=ss_path, full_page=False)
            results["screenshots"].append(ss_path)
            print(f"  ✓ 스크린샷: {ss_path}")

            # 콘솔 에러 확인
            errors = []
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

    except Exception as e:
        results["errors"].append(str(e))
        print(f"  ✗ UI 접근 실패: {e}")

    return results


async def test_menu_detail_page(page: Page, base_url: str, menu_id: str, menu_name: str) -> Dict:
    """메뉴 상세 페이지 번역 렌더링 테스트"""
    result = {"menu": menu_name, "ja_visible": False, "zh_visible": False, "screenshot": ""}

    try:
        # 메뉴 상세 URL (다양한 URL 패턴 시도)
        test_urls = [
            f"{base_url}/?menu={menu_id}",
            f"{base_url}/menu/{menu_id}",
            f"{base_url}#menu={menu_id}",
        ]

        for url in test_urls:
            resp = await page.goto(url, wait_until="networkidle", timeout=10000)
            if resp and resp.ok:
                content = await page.text_content("body")
                # 일본어/중국어 텍스트 확인
                if re.search(r'[\u3040-\u30ff]', content or ""):  # 히라가나
                    result["ja_visible"] = True
                if re.search(r'[\u4e00-\u9fff]', content or ""):  # 한자
                    result["zh_visible"] = True
                break

        ss_path = f"tests/screenshots/detail_{menu_name}_{datetime.now().strftime('%H%M%S')}.png"
        await page.screenshot(path=ss_path)
        result["screenshot"] = ss_path

    except Exception as e:
        result["error"] = str(e)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# 보고서 생성
# ─────────────────────────────────────────────────────────────────────────────
def generate_report(db_data: Dict, api_results: List[Dict], ui_results: Dict, quality_results: List[Dict]) -> str:
    """마크다운 품질 보고서 생성"""
    stats = db_data["stats"]
    total = stats["total"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# 번역 품질 테스트 리포트",
        f"**날짜**: {now}",
        f"**도구**: Playwright + PostgreSQL 직접 검증",
        "",
        "---",
        "",
        "## 1. 전체 번역 통계 (DB 직접 조회)",
        "",
        f"| 항목 | 수치 | 비율 |",
        f"|------|------|------|",
        f"| 전체 활성 메뉴 | {total}개 | 100% |",
        f"| name_ja 완료 | {stats['has_name_ja']}개 | {stats['has_name_ja']/total*100:.1f}% |",
        f"| name_zh_cn 완료 | {stats['has_name_zh']}개 | {stats['has_name_zh']/total*100:.1f}% |",
        f"| desc_ja 완료 | {stats['has_desc_ja']}개 | {stats['has_desc_ja']/total*100:.1f}% |",
        f"| desc_zh 완료 | {stats['has_desc_zh']}개 | {stats['has_desc_zh']/total*100:.1f}% |",
        "",
    ]

    # 번역 누락 메뉴
    if db_data["missing"]:
        lines += [
            f"## 2. 번역 누락 메뉴 ({len(db_data['missing'])}개)",
            "",
            "| 메뉴명 | name_ja | name_zh | 상태 |",
            "|--------|---------|---------|------|",
        ]
        for m in db_data["missing"]:
            lines.append(
                f"| {m['name_ko']} | {m['name_ja'] or '❌'} | {m['name_zh_cn'] or '❌'} | {m['translation_status']} |"
            )
        lines.append("")
    else:
        lines += ["## 2. 번역 누락 메뉴", "", "✅ 모든 메뉴 번역 완료", ""]

    # 품질 분석 결과
    lines += [
        "## 3. 품질 분석 (30개 랜덤 샘플)",
        "",
    ]

    perfect = [r for r in quality_results if r["score"] == 100]
    issues = [r for r in quality_results if r["score"] < 100]

    lines += [
        f"- **완벽한 번역**: {len(perfect)}/{len(quality_results)}개",
        f"- **문제 있는 번역**: {len(issues)}/{len(quality_results)}개",
        "",
    ]

    if issues:
        lines += [
            "### 품질 이슈 목록",
            "",
            "| 메뉴 | 점수 | 이슈 |",
            "|------|------|------|",
        ]
        for r in sorted(issues, key=lambda x: x["score"]):
            issue_str = " / ".join(r["issues"][:2])
            lines.append(f"| {r['name_ko']} | {r['score']} | {issue_str} |")
        lines.append("")

    # 테스트 메뉴 상세 결과
    lines += [
        "## 4. 핵심 메뉴 번역 샘플",
        "",
        "| 한국어 | 일본어명 | 중국어명 | 일본어 설명 |",
        "|--------|---------|---------|------------|",
    ]
    for m in db_data["test_menus"]:
        expl = m.get("explanation_short") or {}
        desc_ja = expl.get("ja", "")[:40] + "..." if len(expl.get("ja", "")) > 40 else expl.get("ja", "")
        lines.append(
            f"| {m['name_ko']} | {m.get('name_ja') or '❌'} | {m.get('name_zh_cn') or '❌'} | {desc_ja} |"
        )
    lines.append("")

    # API 테스트 결과
    if api_results:
        lines += [
            "## 5. API 엔드포인트 테스트",
            "",
            "| 메뉴 | API 응답 | name_ja | name_zh |",
            "|------|----------|---------|---------|",
        ]
        for r in api_results:
            status = "✅" if r.get("found") else "❌"
            lines.append(
                f"| {r['menu']} | {status} | {r.get('name_ja','N/A')[:20]} | {r.get('name_zh','N/A')[:20]} |"
            )
        lines.append("")

    # UI 테스트 결과
    lines += [
        "## 6. 프론트엔드 UI 테스트",
        "",
        f"- **프로덕션 URL**: {'✅ 접속 가능' if ui_results.get('prod_accessible') else '❌ 접속 불가'}",
        f"- **페이지 제목**: {ui_results.get('prod_title', 'N/A')}",
        f"- **스크린샷**: {', '.join(ui_results.get('screenshots', []))}",
        "",
    ]

    # 종합 판정
    name_ja_rate = stats['has_name_ja'] / total * 100
    name_zh_rate = stats['has_name_zh'] / total * 100
    desc_ja_rate = stats['has_desc_ja'] / total * 100
    desc_zh_rate = stats['has_desc_zh'] / total * 100
    avg_rate = (name_ja_rate + name_zh_rate + desc_ja_rate + desc_zh_rate) / 4
    quality_score = len(perfect) / len(quality_results) * 100 if quality_results else 0

    verdict = "✅ PASS" if avg_rate >= 95 and quality_score >= 70 else "⚠️ 부분 통과" if avg_rate >= 80 else "❌ FAIL"

    lines += [
        "## 7. 종합 판정",
        "",
        f"| 지표 | 값 | 기준 |",
        f"|------|----|----|",
        f"| 이름 번역 완료율 | {(name_ja_rate+name_zh_rate)/2:.1f}% | ≥95% |",
        f"| 설명 번역 완료율 | {(desc_ja_rate+desc_zh_rate)/2:.1f}% | ≥90% |",
        f"| 샘플 품질 점수 | {quality_score:.0f}% | ≥70% |",
        f"| **최종 판정** | **{verdict}** | |",
        "",
        "---",
        f"*리포트 생성: {now} by Claude + Playwright*",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────────────────
async def main():
    print("=" * 60)
    print("번역 품질 테스트 시작")
    print("=" * 60)

    os.makedirs("tests/screenshots", exist_ok=True)

    # 1. DB 직접 검증
    db_data = check_db_translations()
    stats = db_data["stats"]
    print(f"\n[통계] 전체: {stats['total']}, name_ja: {stats['has_name_ja']}, name_zh: {stats['has_name_zh']}")
    print(f"       desc_ja: {stats['has_desc_ja']}, desc_zh: {stats['has_desc_zh']}")

    # 2. 30개 샘플 품질 분석
    print("\n[품질] 30개 랜덤 샘플 품질 분석 중...")
    quality_results = []
    for menu in db_data["sample"]:
        q = check_translation_quality(menu)
        q["name_ko"] = menu["name_ko"]
        quality_results.append(q)
        if q["issues"]:
            print(f"  ⚠️ {menu['name_ko']}: {', '.join(q['issues'][:2])}")
    print(f"  완벽 번역: {sum(1 for r in quality_results if r['score']==100)}/30개")

    # 3. 핵심 테스트 메뉴 품질
    print("\n[핵심 메뉴 번역 결과]")
    for m in db_data["test_menus"]:
        expl = m.get("explanation_short") or {}
        print(f"  {m['name_ko']:12s} -> JA:{m.get('name_ja','❌'):15s} ZH:{m.get('name_zh_cn','❌')}")

    # 4. Playwright 브라우저 테스트
    api_results = []
    ui_results = {}

    print("\n[브라우저] Playwright 테스트 시작...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        page = await context.new_page()

        # 프로덕션 UI 접속 테스트
        try:
            resp = await page.goto(PROD_URL, wait_until="networkidle", timeout=15000)
            if resp and resp.ok:
                ui_results["prod_accessible"] = True
                ui_results["prod_title"] = await page.title()
                ss_path = "tests/screenshots/prod_main.png"
                await page.screenshot(path=ss_path)
                ui_results["screenshots"] = [ss_path]
                print(f"  ✓ 프로덕션 UI 접속 성공: '{ui_results['prod_title']}'")
            else:
                ui_results["prod_accessible"] = False
                print(f"  ✗ 프로덕션 UI 응답 없음 (status: {resp.status if resp else 'N/A'})")
        except Exception as e:
            ui_results["prod_accessible"] = False
            print(f"  ✗ 프로덕션 접속 실패: {e}")

        # API 엔드포인트 테스트
        print("\n[API] 핵심 메뉴 API 응답 테스트...")
        api_page = await context.new_page()
        for menu_name in TEST_MENUS[:8]:
            try:
                resp = await api_page.goto(
                    f"{API_BASE}/canonical-menus?search={menu_name}&limit=1",
                    wait_until="networkidle", timeout=10000
                )
                if resp and resp.ok:
                    content = await api_page.text_content("body")
                    data = json.loads(content)
                    items = data.get("items", data.get("data", []))
                    if items:
                        item = items[0]
                        api_results.append({
                            "menu": menu_name,
                            "found": True,
                            "name_ja": item.get("name_ja", ""),
                            "name_zh": item.get("name_zh_cn", ""),
                        })
                        print(f"  ✓ {menu_name}: JA={item.get('name_ja','?')[:15]} ZH={item.get('name_zh_cn','?')[:15]}")
                    else:
                        api_results.append({"menu": menu_name, "found": False})
                        print(f"  ✗ {menu_name}: 결과 없음")
                else:
                    api_results.append({"menu": menu_name, "found": False})
            except Exception as e:
                api_results.append({"menu": menu_name, "found": False, "error": str(e)})
                print(f"  ✗ {menu_name}: {e}")

        await browser.close()

    # 5. 보고서 생성
    print("\n[보고서] 생성 중...")
    report = generate_report(db_data, api_results, ui_results, quality_results)

    report_path = f"tests/{REPORT_FILE}"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ 리포트 저장: {report_path}")

    # 콘솔 요약 출력
    total = stats["total"]
    print("\n" + "=" * 60)
    print("번역 품질 테스트 완료")
    print("=" * 60)
    print(f"  name_ja:  {stats['has_name_ja']}/{total} ({stats['has_name_ja']/total*100:.1f}%)")
    print(f"  name_zh:  {stats['has_name_zh']}/{total} ({stats['has_name_zh']/total*100:.1f}%)")
    print(f"  desc_ja:  {stats['has_desc_ja']}/{total} ({stats['has_desc_ja']/total*100:.1f}%)")
    print(f"  desc_zh:  {stats['has_desc_zh']}/{total} ({stats['has_desc_zh']/total*100:.1f}%)")
    perfect = sum(1 for r in quality_results if r["score"] == 100)
    print(f"  품질:     {perfect}/30 완벽 ({perfect/30*100:.0f}%)")
    print(f"  리포트:   {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
