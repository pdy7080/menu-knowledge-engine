#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
"""
Claude API 배치 번역 스크립트 (v2 - Direct API)

목적: 모든 미번역 메뉴를 Claude API로 일본어/중국어 번역
실행: python scripts/claude_api_translation.py
     python scripts/claude_api_translation.py --limit 50  (테스트용)
     python scripts/claude_api_translation.py --test  (10개 테스트)

번역 대상:
  - name_ja        : 일본어 메뉴명
  - name_zh_cn     : 중국어(간체) 메뉴명
  - explanation_short.ja : 일본어 설명
  - explanation_short.zh : 중국어 설명
"""

import os
import sys
import json
import subprocess
import time
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, List

import psycopg2
import psycopg2.extras
import anthropic

# ─────────────────────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────────────────────
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SSH_KEY = str(Path.home() / ".ssh" / "menu_deploy")
SSH_USER = "chargeap"
SSH_HOST = "d11475.sgp1.stableserver.net"
LOCAL_TUNNEL_PORT = 5433

DB_HOST = "localhost"
DB_PORT = LOCAL_TUNNEL_PORT
DB_NAME = "chargeap_menu_knowledge"
DB_USER = "chargeap_dcclab2022"
DB_PASS = os.environ.get("DB_PASSWORD", "")

# Claude 모델 - claude-haiku-4-5 (빠르고 저렴)
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
BATCH_SIZE = 8  # 한 번에 번역할 메뉴 수 (Claude API 1 call)
SLEEP_BETWEEN_BATCHES = 0.5  # Rate limit 방지


# ─────────────────────────────────────────────────────────────────────────────
# 로깅
# ─────────────────────────────────────────────────────────────────────────────
def setup_logging(log_file="translation_claude_api.log"):
    # Windows cp949 콘솔 인코딩 문제 해결
    if sys.stdout.encoding and sys.stdout.encoding.lower() in (
        "cp949",
        "cp932",
        "mbcs",
    ):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ─────────────────────────────────────────────────────────────────────────────
# SSH 터널
# ─────────────────────────────────────────────────────────────────────────────
def is_port_open(host: str, port: int) -> bool:
    """포트가 열려있는지 확인"""
    import socket

    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def start_ssh_tunnel():
    """SSH 터널 열기 (localhost:5433 -> server:5432)
    이미 터널이 열려있으면 재사용."""
    # 이미 포트가 열려있는지 확인
    if is_port_open(DB_HOST, LOCAL_TUNNEL_PORT):
        logger.info(
            f"[SSH] 기존 터널 사용 (localhost:{LOCAL_TUNNEL_PORT} 이미 열려있음)"
        )
        return None  # 기존 터널 사용, 종료 시 닫지 않음

    cmd = [
        "ssh",
        "-i",
        SSH_KEY,
        "-L",
        f"{LOCAL_TUNNEL_PORT}:localhost:5432",
        "-N",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "ServerAliveInterval=60",
        "-o",
        "ExitOnForwardFailure=yes",
        f"{SSH_USER}@{SSH_HOST}",
    ]
    logger.info(f"[SSH] 터널 시작: localhost:{LOCAL_TUNNEL_PORT} -> {SSH_HOST}:5432")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)  # 터널 연결 대기

    if proc.poll() is not None:
        raise RuntimeError(f"[SSH] 터널 시작 실패 (exit code: {proc.returncode})")

    logger.info(f"[SSH] 터널 연결 완료 (PID: {proc.pid})")
    return proc


def connect_db():
    """DB 연결 (터널 통해)"""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        connect_timeout=10,
    )
    conn.autocommit = False
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# DB 쿼리
# ─────────────────────────────────────────────────────────────────────────────
def get_menus_needing_translation(conn, limit: Optional[int] = None) -> List[Dict]:
    """번역이 필요한 메뉴 목록 조회"""
    limit_clause = f"LIMIT {limit}" if limit else ""
    query = f"""
    SELECT
        id::text,
        name_ko,
        name_en,
        name_ja,
        name_zh_cn,
        explanation_short,
        explanation_long,
        description_long_en
    FROM canonical_menus
    WHERE status = 'active'
      AND (
          name_ja IS NULL OR name_ja = ''
          OR name_zh_cn IS NULL OR name_zh_cn = ''
          OR explanation_short IS NULL
          OR NOT (explanation_short ? 'ja')
          OR (explanation_short->>'ja') = ''
          OR NOT (explanation_short ? 'zh')
          OR (explanation_short->>'zh') = ''
      )
    ORDER BY content_completeness DESC, created_at ASC
    {limit_clause}
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query)
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_translation_stats(conn) -> Dict:
    """현재 번역 통계"""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT COUNT(*) as total FROM canonical_menus WHERE status='active'")
    total = cur.fetchone()["total"]

    cur.execute(
        """
        SELECT COUNT(*) as cnt FROM canonical_menus
        WHERE status='active'
          AND name_ja IS NOT NULL AND name_ja != ''
          AND name_zh_cn IS NOT NULL AND name_zh_cn != ''
          AND explanation_short IS NOT NULL
          AND (explanation_short ? 'ja') AND (explanation_short->>'ja') != ''
          AND (explanation_short ? 'zh') AND (explanation_short->>'zh') != ''
    """
    )
    translated = cur.fetchone()["cnt"]

    return {
        "total": total,
        "translated": translated,
        "pending": total - translated,
        "rate": f"{translated/total*100:.1f}%" if total > 0 else "0%",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Claude API 번역
# ─────────────────────────────────────────────────────────────────────────────
def build_translation_prompt(menus: List[Dict]) -> str:
    """번역 프롬프트 생성"""
    menu_list = []
    for m in menus:
        expl_en = ""
        if m.get("explanation_short"):
            expl_en = m["explanation_short"].get("en", "")
        if not expl_en and m.get("description_long_en"):
            # 긴 설명에서 첫 문장만 사용
            expl_en = m["description_long_en"][:200].split(".")[0] + "."

        menu_list.append(
            {
                "id": m["id"],
                "name_ko": m["name_ko"],
                "name_en": m.get("name_en") or "",
                "description_en": expl_en
                or f"Korean dish: {m.get('name_en', m['name_ko'])}",
            }
        )

    return f"""You are a Korean food and culture expert specializing in food translation.

Translate the following Korean menu items into Japanese and Chinese (Simplified).

Rules:
- For names: Use natural Japanese/Chinese names. For uniquely Korean dishes, use transliteration + brief explanation in parentheses if needed.
- For descriptions: Write 1-2 natural, appetizing sentences in each language based on the English description.
- Be culturally accurate and appealing to Japanese/Chinese diners.
- Keep Japanese descriptions in natural Japanese style (polite but not overly formal).
- Keep Chinese descriptions in natural Mandarin (Simplified Chinese).

Menu items:
{json.dumps(menu_list, ensure_ascii=False, indent=2)}

Respond ONLY with a JSON array (no markdown, no explanation):
[
  {{
    "id": "uuid-here",
    "name_ja": "日本語名",
    "name_zh_cn": "中文名",
    "desc_ja": "日本語の説明（1〜2文）",
    "desc_zh": "中文描述（1-2句）"
  }}
]"""


def translate_batch(client: anthropic.Anthropic, menus: List[Dict]) -> Dict[str, Dict]:
    """Claude API로 배치 번역 수행"""
    prompt = build_translation_prompt(menus)

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    result_text = response.content[0].text.strip()

    # JSON 파싱 (마크다운 코드블록 제거)
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif result_text.startswith("```"):
        result_text = result_text.split("```")[1].split("```")[0].strip()

    results = json.loads(result_text)

    # id를 키로 하는 dict 반환
    return {r["id"]: r for r in results}


# ─────────────────────────────────────────────────────────────────────────────
# DB 업데이트
# ─────────────────────────────────────────────────────────────────────────────
def update_translation(conn, menu_id: str, translation: Dict) -> bool:
    """번역 결과를 DB에 저장"""
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 현재 explanation_short 가져오기
        cur.execute(
            "SELECT explanation_short FROM canonical_menus WHERE id = %s", (menu_id,)
        )
        row = cur.fetchone()
        current_expl = (
            dict(row["explanation_short"]) if row and row["explanation_short"] else {}
        )

        # 번역 추가
        if translation.get("desc_ja"):
            current_expl["ja"] = translation["desc_ja"]
        if translation.get("desc_zh"):
            current_expl["zh"] = translation["desc_zh"]

        # 업데이트 실행
        cur.execute(
            """
            UPDATE canonical_menus
            SET
                name_ja = CASE WHEN (name_ja IS NULL OR name_ja = '') THEN %s ELSE name_ja END,
                name_zh_cn = CASE WHEN (name_zh_cn IS NULL OR name_zh_cn = '') THEN %s ELSE name_zh_cn END,
                explanation_short = %s,
                translation_status = 'completed',
                translation_attempted_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
        """,
            (
                translation.get("name_ja") or None,
                translation.get("name_zh_cn") or None,
                json.dumps(current_expl, ensure_ascii=False),
                menu_id,
            ),
        )

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"  [DB ERROR] {menu_id}: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Claude API 배치 번역")
    parser.add_argument("--test", action="store_true", help="10개만 테스트")
    parser.add_argument("--limit", type=int, help="처리할 최대 메뉴 수")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"배치 크기 (기본: {BATCH_SIZE})",
    )
    args = parser.parse_args()

    limit = 10 if args.test else args.limit
    batch_size = args.batch_size

    logger.info("=" * 60)
    logger.info("Claude API 배치 번역 시작")
    logger.info(f"  모델: {CLAUDE_MODEL}")
    logger.info(f"  배치 크기: {batch_size}")
    logger.info(f"  제한: {limit if limit else '없음 (전체)'}")
    logger.info("=" * 60)

    # 1. SSH 터널 시작
    tunnel_proc = None
    try:
        tunnel_proc = start_ssh_tunnel()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    try:
        # 2. DB 연결
        logger.info("[DB] 연결 중...")
        try:
            conn = connect_db()
            logger.info("[DB] 연결 성공")
        except Exception as e:
            logger.error(f"[DB] 연결 실패: {e}")
            sys.exit(1)

        # 3. 통계 출력
        stats = get_translation_stats(conn)
        logger.info("\n[현재 번역 상태]")
        logger.info(f"  전체: {stats['total']}개")
        logger.info(f"  번역 완료: {stats['translated']}개")
        logger.info(f"  번역 필요: {stats['pending']}개")
        logger.info(f"  완료율: {stats['rate']}\n")

        # 4. 번역 필요 메뉴 조회
        logger.info("[SCAN] 번역 필요 메뉴 조회 중...")
        menus = get_menus_needing_translation(conn, limit=limit)
        total = len(menus)
        logger.info(f"[SCAN] 번역 대상: {total}개")

        if total == 0:
            logger.info("[DONE] 번역할 메뉴가 없습니다.")
            return

        # 5. Claude API 초기화
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        logger.info("[API] Claude API 초기화 완료\n")

        # 6. 배치 번역 실행
        success = 0
        failed = 0
        total_batches = (total + batch_size - 1) // batch_size

        for batch_idx in range(0, total, batch_size):
            batch = menus[batch_idx : batch_idx + batch_size]
            batch_num = batch_idx // batch_size + 1
            batch_names = [m["name_ko"] for m in batch]

            logger.info(f"[BATCH {batch_num}/{total_batches}] {', '.join(batch_names)}")

            # Claude API 호출
            try:
                translations = translate_batch(client, batch)

                for menu in batch:
                    menu_id = menu["id"]
                    if menu_id in translations:
                        t = translations[menu_id]
                        ok = update_translation(conn, menu_id, t)
                        if ok:
                            logger.info(
                                f"  [OK] {menu['name_ko']:15s} "
                                f"-> {t.get('name_ja', '?'):15s} / {t.get('name_zh_cn', '?')}"
                            )
                            success += 1
                        else:
                            logger.warning(f"  [DB FAIL] {menu['name_ko']}")
                            failed += 1
                    else:
                        logger.warning(f"  [MISS] {menu['name_ko']} - 번역 결과 없음")
                        failed += 1

            except json.JSONDecodeError as e:
                logger.error(f"  [JSON ERROR] 배치 {batch_num}: {e}")
                logger.debug("  응답 텍스트 파싱 실패")
                failed += len(batch)
            except anthropic.RateLimitError:
                logger.warning("  [RATE LIMIT] 60초 대기 후 재시도...")
                time.sleep(60)
                # 재시도
                try:
                    translations = translate_batch(client, batch)
                    for menu in batch:
                        menu_id = menu["id"]
                        if menu_id in translations:
                            ok = update_translation(
                                conn, menu_id, translations[menu_id]
                            )
                            if ok:
                                success += 1
                            else:
                                failed += 1
                        else:
                            failed += 1
                except Exception as e2:
                    logger.error(f"  [ERROR] 재시도 실패: {e2}")
                    failed += len(batch)
            except Exception as e:
                logger.error(f"  [ERROR] 배치 {batch_num}: {e}")
                failed += len(batch)
                time.sleep(2)
                continue

            # Rate limit 방지 대기
            if batch_idx + batch_size < total:
                time.sleep(SLEEP_BETWEEN_BATCHES)

        # 7. 최종 통계
        stats_after = get_translation_stats(conn)
        logger.info("\n" + "=" * 60)
        logger.info("[RESULT] 번역 완료")
        logger.info(f"  성공: {success}개")
        logger.info(f"  실패: {failed}개")
        logger.info(f"  처리: {total}개")
        logger.info(
            f"  전체 번역 완료율: {stats_after['rate']} ({stats_after['translated']}/{stats_after['total']})"
        )
        logger.info("=" * 60)

        conn.close()

    finally:
        if tunnel_proc is not None:
            tunnel_proc.terminate()
            logger.info("[SSH] 터널 종료")
        else:
            logger.info("[SSH] 기존 터널 유지 (종료 안 함)")


if __name__ == "__main__":
    main()
