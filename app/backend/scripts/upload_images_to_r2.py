"""
메뉴 이미지 R2 업로드 파이프라인

1. Wikipedia Commons에서 이미지 다운로드
2. 로컬 AI 생성 이미지 수집
3. CloudFlare R2에 업로드
4. enriched 데이터에 이미지 URL 매핑

사용법:
  python scripts/upload_images_to_r2.py                    # 전체 실행
  python scripts/upload_images_to_r2.py --download-only    # 다운로드만 (R2 업로드 안함)
  python scripts/upload_images_to_r2.py --upload-only      # 로컬 이미지만 R2 업로드
  python scripts/upload_images_to_r2.py --limit 10         # 10개만 처리
  python scripts/upload_images_to_r2.py --source wiki      # Wikipedia만
  python scripts/upload_images_to_r2.py --source ai        # AI 생성만

Author: Claude (Senior Developer)
Date: 2026-02-19
"""
import sys
import io
import json
import argparse
import os
import re
import requests
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# 프로젝트 경로
BACKEND_DIR = Path(__file__).parent.parent
DATA_DIR = BACKEND_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
WIKI_DIR = IMAGES_DIR / "wikipedia"
AI_DIR = IMAGES_DIR / "ai_generated"

# 디렉토리 생성
WIKI_DIR.mkdir(parents=True, exist_ok=True)
AI_DIR.mkdir(parents=True, exist_ok=True)


def get_wiki_image_map() -> dict:
    """seeds/image_urls.py에서 위키 이미지 URL 매핑 로드 (메뉴명 → 영문 검색어)"""
    sys.path.insert(0, str(BACKEND_DIR))
    from seeds.image_urls import get_image_url_map
    return get_image_url_map()


# 메뉴명 → 영문 검색어 매핑 (Wikimedia Commons 검색용)
MENU_SEARCH_TERMS = {
    "갈비탕": "galbitang", "삼계탕": "samgyetang", "곰탕": "gomtang",
    "설렁탕": "seolleongtang", "감자탕": "gamjatang", "해물탕": "haemultang",
    "뼈해장국": "haejangguk", "순대국": "sundaeguk", "육개장": "yukgaejang",
    "추어탕": "chueotang", "김치찌개": "kimchi jjigae", "된장찌개": "doenjang jjigae",
    "순두부찌개": "sundubu jjigae", "부대찌개": "budae jjigae",
    "미역국": "miyeokguk", "떡국": "tteokguk", "비빔밥": "bibimbap",
    "돌솥비빔밥": "dolsot bibimbap", "김밥": "gimbap", "볶음밥": "bokkeumbap",
    "김치볶음밥": "kimchi fried rice", "제육덮밥": "jeyuk",
    "냉면": "naengmyeon", "물냉면": "mul naengmyeon", "비빔냉면": "bibim naengmyeon",
    "잔치국수": "janchi guksu", "칼국수": "kalguksu", "짜장면": "jajangmyeon",
    "짬뽕": "jjamppong", "콩국수": "kongguksu", "라면": "ramyeon korean",
    "막국수": "makguksu", "수제비": "sujebi",
    "삼겹살": "samgyeopsal", "불고기": "bulgogi", "갈비": "galbi korean",
    "닭갈비": "dakgalbi", "차돌박이": "chadolbagi", "곱창": "gopchang",
    "갈비찜": "galbijjim", "족발": "jokbal", "보쌈": "bossam",
    "해물찜": "haemul jjim", "고등어조림": "godeungeo jorim",
    "파전": "pajeon", "해물파전": "haemul pajeon", "김치전": "kimchijeon",
    "녹두전": "bindaetteok",
    "김치": "kimchi", "잡채": "japchae",
    "떡볶이": "tteokbokki", "순대": "sundae korean", "어묵": "eomuk fish cake",
    "호떡": "hotteok", "핫도그": "korean corn dog",
    "회": "hoe korean raw fish", "간장게장": "ganjang gejang",
    "오징어볶음": "ojingeo bokkeum",
    "치킨": "korean fried chicken", "양념치킨": "yangnyeom chicken",
    "돈까스": "tonkatsu korean", "돈가스": "tonkatsu korean",
    "팥빙수": "patbingsu", "호두과자": "hodugwaja",
    "우동": "udon korean", "만두": "mandu korean dumpling",
    "만두국": "manduguk", "떡만두국": "tteok mandu guk",
    "소고기국밥": "sogogi gukbap", "콩나물국밥": "kongnamul gukbap",
    "해장국": "haejangguk",
    # 추가 메뉴 (커버리지 확대)
    "소떡소떡": "sotteok sotteok", "냉모밀": "soba noodles cold",
    "통감자": "whole potato korean", "장터국밥": "gukbap korean rice soup",
    "바삭어포": "dried fish snack korean", "강원나물밥": "namul bap bibimbap",
    "해물순두부": "sundubu jjigae", "해물바": "seafood bar korean",
    "옥수수": "corn korean street food", "제육볶음": "jeyuk bokkeum",
    "회오리감자": "tornado potato korean", "열무국수": "korean noodle soup cold",
    "함박스테이크": "hamburg steak korean", "한우국밥": "beef gukbap korean",
    "케이크소세지": "korean sausage snack", "케네디소시지": "sausage korean",
    "가락자장면": "jajangmyeon",
    "사골우거지국밥": "korean beef bone soup", "사골우거지국": "korean beef bone soup",
    "델리만쥬": "delimanjoo korean", "고등어구이": "grilled mackerel korean",
    "미니츄러스": "churros korean", "고등어구이정식": "grilled mackerel korean",
    "냉메밀": "soba noodles cold",
}


def _resolve_search_term(menu_name: str) -> str | None:
    """메뉴명에서 Wikimedia Commons 검색어 결정 (접미사 매칭 fallback)"""
    # 1. 직접 매칭
    if menu_name in MENU_SEARCH_TERMS:
        return MENU_SEARCH_TERMS[menu_name]

    # 2. 접미사 기반 매칭 (긴 것부터 시도)
    candidates = sorted(MENU_SEARCH_TERMS.keys(), key=len, reverse=True)
    for base in candidates:
        if menu_name.endswith(base) and len(menu_name) > len(base):
            return MENU_SEARCH_TERMS[base]

    # 3. 부분 포함 매칭 (핵심 음식명이 포함된 경우)
    for base in candidates:
        if base in menu_name and len(base) >= 2:
            return MENU_SEARCH_TERMS[base]

    return None


def download_wiki_images(limit: int = 0) -> dict:
    """Wikimedia Commons API로 이미지 검색 + requests로 다운로드 (동기)

    주의: upload.wikimedia.org는 브라우저 User-Agent만 허용 (bot UA → 403)
    따라서 API 검색은 bot UA, 이미지 다운로드는 브라우저 UA 사용
    """
    import time

    # canonical 메뉴 목록 로드
    enriched_file = DATA_DIR / "canonical_seed_enriched.json"
    if enriched_file.exists():
        with open(enriched_file, 'r', encoding='utf-8') as f:
            menus = [m["name_ko"] for m in json.load(f)]
    else:
        menus = list(MENU_SEARCH_TERMS.keys())

    if limit > 0:
        menus = menus[:limit]

    print(f"\n[Wikimedia Commons] {len(menus)}개 메뉴 이미지 검색")
    print("-" * 40)

    downloaded = {}
    failed = 0
    skipped_no_term = 0
    api_url = "https://commons.wikimedia.org/w/api.php"

    # 기존 manifest에서 thumb_url 복구 (캐시된 이미지용)
    manifest_file = DATA_DIR / "image_manifest.json"
    prev_manifest = {}
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8') as f:
            prev = json.load(f)
            prev_manifest = prev.get("images", {})

    # API 검색용 세션 (bot UA OK)
    api_session = requests.Session()
    api_session.headers.update({
        "User-Agent": "MenuKnowledgeEngine/1.0 (https://github.com/menu-engine; dev@example.com)"
    })

    # 이미지 다운로드용 세션 (브라우저 UA 필수)
    dl_session = requests.Session()
    dl_session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    # 이미 처리한 검색어 캐시 (동일 base 메뉴는 같은 이미지)
    seen_terms = {}

    for i, menu_name in enumerate(menus, 1):
        clean_name = re.sub(r'[^\w가-힣\-_]', '', menu_name)
        local_path = WIKI_DIR / f"{clean_name}.jpg"

        # 이미 다운로드된 경우 스킵 (manifest에서 thumb_url 복구)
        if local_path.exists() and local_path.stat().st_size > 1000:
            prev_info = prev_manifest.get(menu_name, {})
            downloaded[menu_name] = {
                "local_path": str(local_path),
                "source": "wiki",
                "status": "cached",
                "wiki_thumb_url": prev_info.get("wiki_thumb_url"),
            }
            continue

        # 검색어 결정 (접미사 fallback 포함)
        search_term = _resolve_search_term(menu_name)
        if not search_term:
            skipped_no_term += 1
            print(f"  [{i:3d}] {menu_name}: 검색어 없음")
            continue

        # 같은 검색어로 이미 다운로드한 이미지가 있으면 복사
        if search_term in seen_terms:
            src_info = seen_terms[search_term]
            if src_info:
                src_path, src_thumb_url = src_info if isinstance(src_info, tuple) else (src_info, None)
                if src_path and Path(src_path).exists():
                    import shutil
                    shutil.copy2(src_path, local_path)
                    downloaded[menu_name] = {
                        "local_path": str(local_path),
                        "source": "wiki",
                        "size_kb": local_path.stat().st_size // 1024,
                        "status": "copied",
                        "wiki_thumb_url": src_thumb_url,
                    }
                    continue

        # Wikimedia Commons API 검색
        try:
            time.sleep(1.0)  # Rate limiting
            params = {
                "action": "query",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {search_term}",
                "gsrnamespace": 6,
                "gsrlimit": 3,
                "prop": "imageinfo",
                "iiprop": "url|size|mime",
                "iiurlwidth": 500,
                "format": "json",
            }
            resp = api_session.get(api_url, params=params, timeout=15)
            if resp.status_code == 429:
                failed += 1
                print(f"  [{i:3d}] {menu_name}: API rate limited (429), waiting 10s...")
                time.sleep(10.0)
                continue
            if resp.status_code != 200:
                failed += 1
                print(f"  [{i:3d}] {menu_name}: API HTTP {resp.status_code}")
                continue

            data = resp.json()
            pages = data.get("query", {}).get("pages", {})

            if not pages:
                failed += 1
                seen_terms[search_term] = None
                print(f"  [{i:3d}] {menu_name}: 검색 결과 없음 (term={search_term})")
                continue

            # 첫 번째 JPEG/PNG 이미지의 썸네일 URL 선택
            thumb_url = None
            for pid, page in sorted(pages.items(), key=lambda x: x[0]):
                ii = page.get("imageinfo", [{}])[0]
                mime = ii.get("mime", "")
                if "jpeg" in mime or "png" in mime:
                    thumb_url = ii.get("thumburl")
                    if thumb_url:
                        break

            if not thumb_url:
                failed += 1
                seen_terms[search_term] = None
                print(f"  [{i:3d}] {menu_name}: 썸네일 URL 없음")
                continue

            # 썸네일 다운로드 (브라우저 UA 세션, 429 재시도 포함)
            time.sleep(1.5)
            for retry in range(3):
                dl_resp = dl_session.get(thumb_url, timeout=15)
                if dl_resp.status_code == 429:
                    wait = 15 * (retry + 1)
                    print(f"  [{i:3d}] {menu_name}: Rate limited, waiting {wait}s... (retry {retry+1}/3)")
                    time.sleep(wait)
                    continue
                break

            if dl_resp.status_code == 200 and len(dl_resp.content) > 1000:
                ct = dl_resp.headers.get("content-type", "")
                if "image" in ct:
                    with open(local_path, "wb") as f:
                        f.write(dl_resp.content)
                    downloaded[menu_name] = {
                        "local_path": str(local_path),
                        "source": "wiki",
                        "size_kb": len(dl_resp.content) // 1024,
                        "status": "downloaded",
                        "wiki_thumb_url": thumb_url,
                    }
                    seen_terms[search_term] = (str(local_path), thumb_url)
                    print(f"  [{i:3d}] {menu_name} -> {len(dl_resp.content)//1024}KB (term={search_term})")
                else:
                    failed += 1
                    print(f"  [{i:3d}] {menu_name}: content-type={ct}")
            elif dl_resp.status_code == 429:
                failed += 1
                print(f"  [{i:3d}] {menu_name}: Rate limit 3회 재시도 실패")
            else:
                failed += 1
                print(f"  [{i:3d}] {menu_name}: Download HTTP {dl_resp.status_code}")

        except Exception as e:
            failed += 1
            print(f"  [{i:3d}] {menu_name}: ERROR {e}")

        if i % 20 == 0 or i == len(menus):
            cached = sum(1 for d in downloaded.values() if d["status"] == "cached")
            new = sum(1 for d in downloaded.values() if d["status"] == "downloaded")
            copied = sum(1 for d in downloaded.values() if d["status"] == "copied")
            print(f"  --- [{i}/{len(menus)}] 신규 {new}개 + 복사 {copied}개 + 캐시 {cached}개, 실패 {failed}개 ---")

    cached = sum(1 for d in downloaded.values() if d["status"] == "cached")
    new = sum(1 for d in downloaded.values() if d["status"] == "downloaded")
    copied = sum(1 for d in downloaded.values() if d["status"] == "copied")
    print(f"\n  결과: 신규 {new}개, 복사 {copied}개, 캐시 {cached}개, 실패 {failed}개, 검색어없음 {skipped_no_term}개")
    return downloaded


def collect_ai_images() -> dict:
    """로컬 AI 생성 이미지 수집"""
    collected = {}

    if not AI_DIR.exists():
        return collected

    for img_path in AI_DIR.glob("*.png"):
        # 파일명에서 메뉴명 추출 (예: "김치찌개_ai.png" → "김치찌개")
        name = img_path.stem.replace("_ai", "").replace("_dall-e", "")
        collected[name] = {
            "local_path": str(img_path),
            "source": "ai",
            "size_kb": img_path.stat().st_size // 1024,
            "status": "local",
        }

    # JPEG도 수집
    for img_path in AI_DIR.glob("*.jpg"):
        name = img_path.stem.replace("_ai", "")
        if name not in collected:
            collected[name] = {
                "local_path": str(img_path),
                "source": "ai",
                "size_kb": img_path.stat().st_size // 1024,
                "status": "local",
            }

    print(f"\n[AI Images] {len(collected)}개 수집")
    for name, info in collected.items():
        print(f"  {name}: {info['size_kb']}KB")

    return collected


def upload_to_r2(all_images: dict) -> dict:
    """CloudFlare R2에 업로드"""
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key = os.getenv("R2_ACCESS_KEY_ID")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket = os.getenv("R2_BUCKET_NAME")
    public_url = os.getenv("R2_PUBLIC_URL", "")

    if not all([account_id, access_key, secret_key, bucket]):
        print("\n[R2] 환경변수 미설정 - Wikimedia Commons URL로 대체")
        print("  → R2 설정 시: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY 필요")

        # R2 미설정 시 다운로드 시 저장한 wiki_thumb_url 사용
        url_count = 0
        for name, info in all_images.items():
            thumb_url = info.get("wiki_thumb_url")
            if thumb_url:
                info["public_url"] = thumb_url
                info["r2_key"] = None
                url_count += 1
            elif info["source"] == "ai":
                info["public_url"] = None
                info["r2_key"] = None
            else:
                info["public_url"] = None
                info["r2_key"] = None
        print(f"  → {url_count}/{len(all_images)}개 Wikimedia URL 매핑 완료")
        return all_images

    print(f"\n[R2] {len(all_images)}개 업로드 시작")
    print(f"  Bucket: {bucket}")
    print(f"  Public URL: {public_url}")
    print("-" * 40)

    try:
        from utils.s3_uploader import S3Uploader
        uploader = S3Uploader(
            provider="r2",
            bucket_name=bucket,
            account_id=account_id,
            access_key=access_key,
            secret_key=secret_key,
            public_url=public_url,
        )
    except Exception as e:
        print(f"  [ERROR] R2 클라이언트 초기화 실패: {e}")
        return all_images

    uploaded = 0
    skipped = 0
    errors = 0

    for name, info in all_images.items():
        local_path = info["local_path"]
        if not os.path.exists(local_path):
            errors += 1
            continue

        source = info["source"]
        ext = Path(local_path).suffix or ".jpg"
        r2_key = f"menu-images/{source}/{re.sub(r'[^\\w가-힣\\-_]', '', name)}{ext}"

        # 이미 업로드된 경우 스킵
        if uploader.file_exists(r2_key):
            info["public_url"] = uploader.get_public_url(r2_key)
            info["r2_key"] = r2_key
            skipped += 1
            continue

        try:
            url = uploader.upload_image(
                local_path,
                r2_key,
                metadata={"menu_name": name, "source": source},
            )
            info["public_url"] = url
            info["r2_key"] = r2_key
            uploaded += 1

            if uploaded % 10 == 0:
                print(f"  진행: {uploaded}개 업로드, {skipped}개 스킵")

        except Exception as e:
            errors += 1
            info["public_url"] = None
            info["r2_key"] = None
            print(f"  [ERROR] {name}: {e}")

    print(f"\n  결과: {uploaded}개 업로드, {skipped}개 스킵, {errors}개 에러")
    return all_images


def update_enriched_data(all_images: dict) -> int:
    """enriched 데이터에 이미지 URL 매핑"""
    enriched_file = DATA_DIR / "canonical_seed_enriched.json"
    if not enriched_file.exists():
        print("\n[Enriched] canonical_seed_enriched.json 없음")
        return 0

    with open(enriched_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated = 0
    for menu in data:
        name = menu["name_ko"]
        # 직접 매칭 → public_url 있는 버전 우선 → 공백 제거 매칭
        img_info = all_images.get(name)
        if not img_info or not img_info.get("public_url"):
            img_info = all_images.get(name.replace(" ", ""))
        if img_info and img_info.get("public_url"):
            menu["image_url"] = img_info["public_url"]
            menu["image_source"] = img_info["source"]
            menu["image_r2_key"] = img_info.get("r2_key")
            updated += 1

    with open(enriched_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[Enriched] {updated}/{len(data)}개 메뉴에 이미지 URL 매핑")
    return updated


def save_image_manifest(all_images: dict):
    """이미지 매니페스트 저장"""
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "total_images": len(all_images),
        "by_source": {},
        "images": {},
    }

    for name, info in all_images.items():
        source = info["source"]
        manifest["by_source"][source] = manifest["by_source"].get(source, 0) + 1
        manifest["images"][name] = {
            "source": source,
            "public_url": info.get("public_url"),
            "wiki_thumb_url": info.get("wiki_thumb_url"),
            "r2_key": info.get("r2_key"),
            "size_kb": info.get("size_kb"),
        }

    manifest_file = DATA_DIR / "image_manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n[Manifest] {manifest_file.name} 저장 ({len(all_images)}개)")


def main():
    parser = argparse.ArgumentParser(description="메뉴 이미지 R2 업로드 파이프라인")
    parser.add_argument("--download-only", action="store_true", help="다운로드만 (R2 업로드 안함)")
    parser.add_argument("--upload-only", action="store_true", help="로컬 이미지만 R2 업로드")
    parser.add_argument("--limit", type=int, default=0, help="처리할 메뉴 수 제한")
    parser.add_argument("--source", choices=["wiki", "ai", "all"], default="all", help="이미지 소스")
    args = parser.parse_args()

    print("=" * 60)
    print("메뉴 이미지 R2 업로드 파이프라인")
    print(f"시간: {datetime.now().isoformat()}")
    print(f"소스: {args.source}")
    print(f"모드: {'다운로드만' if args.download_only else '업로드만' if args.upload_only else '전체'}")
    print("=" * 60)

    all_images = {}

    # Step 1: 이미지 수집
    if not args.upload_only:
        if args.source in ("wiki", "all"):
            wiki_images = download_wiki_images(limit=args.limit)
            all_images.update(wiki_images)

        if args.source in ("ai", "all"):
            ai_images = collect_ai_images()
            # AI 이미지가 Wiki와 겹치면 AI 우선
            for name, info in ai_images.items():
                if name not in all_images or all_images[name]["source"] == "wiki":
                    all_images[name] = info
    else:
        # upload-only: 기존 다운로드된 이미지 수집
        for img_path in WIKI_DIR.glob("*.jpg"):
            name = img_path.stem
            all_images[name] = {
                "local_path": str(img_path),
                "source": "wiki",
                "size_kb": img_path.stat().st_size // 1024,
                "status": "local",
            }
        ai_images = collect_ai_images()
        all_images.update(ai_images)

    print(f"\n총 이미지: {len(all_images)}개")

    if args.download_only:
        save_image_manifest(all_images)
        print("\n[DONE] 다운로드 완료 (R2 업로드 생략)")
        print("=" * 60)
        return

    # Step 2: R2 업로드
    all_images = upload_to_r2(all_images)

    # Step 3: enriched 데이터 업데이트
    updated = update_enriched_data(all_images)

    # Step 4: 매니페스트 저장
    save_image_manifest(all_images)

    # 결과 요약
    with_url = sum(1 for info in all_images.values() if info.get("public_url"))
    print(f"\n{'=' * 60}")
    print(f"[DONE] 파이프라인 완료")
    print(f"  총 이미지: {len(all_images)}개")
    print(f"  URL 확보: {with_url}개")
    print(f"  enriched 업데이트: {updated}개")
    print(f"  시간: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
