#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_legacy_cultural_context.py

목적: 구형 포맷(origin/history/significance in KO)의 cultural_context를
     신형 다국어 포맷(ko/en/ja/zh 단락)으로 변환

대상: 111개 메뉴 (cultural_context에 'en' 키가 없는 것)
사용: Claude API (claude-haiku-4-5-20251001)

실행:
  cd app/backend && python scripts/fix_legacy_cultural_context.py --stats
  cd app/backend && python scripts/fix_legacy_cultural_context.py --test
  cd app/backend && python scripts/fix_legacy_cultural_context.py --all
"""
import os
import sys
import json
import time
import logging
import argparse
import subprocess
import socket
from typing import Optional, List, Dict
from pathlib import Path

import psycopg2
import psycopg2.extras
import anthropic

# ─── 설정 ───────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent.parent
env_file = BACKEND_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

SSH_KEY = str(Path.home() / ".ssh" / "menu_deploy")
SSH_USER = "chargeap"
SSH_HOST = "d11475.sgp1.stableserver.net"
LOCAL_TUNNEL_PORT = 5433

DB_HOST = "localhost"
DB_PORT = LOCAL_TUNNEL_PORT
DB_NAME = "chargeap_menu_knowledge"
DB_USER = "chargeap_dcclab2022"
DB_PASS = "eromlab!1228"

BATCH_SIZE = 3   # 소배치 (각 메뉴가 4언어로 생성되므로)

# ─── 로깅 ───────────────────────────────────────────────────────────────────
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("fix_legacy_cultural.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


# ─── SSH 터널 ────────────────────────────────────────────────────────────────
def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def start_ssh_tunnel():
    if is_port_open(DB_HOST, LOCAL_TUNNEL_PORT):
        logger.info(f"[SSH] 기존 터널 사용")
        return None
    cmd = [
        "ssh", "-i", SSH_KEY,
        "-L", f"{LOCAL_TUNNEL_PORT}:localhost:5432",
        "-N", "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=60",
        "-o", "ExitOnForwardFailure=yes",
        f"{SSH_USER}@{SSH_HOST}"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    if proc.poll() is not None:
        raise RuntimeError(f"SSH tunnel failed (exit code: {proc.returncode})")
    logger.info(f"[SSH] 터널 시작 (PID: {proc.pid})")
    return proc


def connect_db():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASS,
        connect_timeout=10
    )
    conn.autocommit = False
    return conn


# ─── DB 쿼리 ──────────────────────────────────────────────────────────────────
def get_legacy_menus(conn, limit: Optional[int] = None) -> List[Dict]:
    """구형 포맷 (en 키 없는) cultural_context를 가진 메뉴"""
    limit_clause = f"LIMIT {limit}" if limit else ""
    query = f"""
    SELECT
        id::text,
        name_ko,
        name_en,
        cultural_context
    FROM canonical_menus
    WHERE status = 'active'
      AND cultural_context IS NOT NULL
      AND NOT (cultural_context ? 'en')
    ORDER BY content_completeness DESC, name_ko ASC
    {limit_clause}
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query)
    return [dict(r) for r in cur.fetchall()]


def get_stats(conn) -> Dict:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN cultural_context ? 'en' AND cultural_context->>'en' != '' THEN 1 ELSE 0 END) as has_en,
        SUM(CASE WHEN cultural_context ? 'ja' AND cultural_context->>'ja' != '' THEN 1 ELSE 0 END) as has_ja,
        SUM(CASE WHEN cultural_context ? 'zh' AND cultural_context->>'zh' != '' THEN 1 ELSE 0 END) as has_zh,
        SUM(CASE WHEN NOT (cultural_context ? 'en') THEN 1 ELSE 0 END) as legacy_format
    FROM canonical_menus WHERE status = 'active'
    """)
    return dict(cur.fetchone())


# ─── Claude API ───────────────────────────────────────────────────────────────
def build_conversion_prompt(menus: List[Dict]) -> str:
    """구형 포맷 → 신형 다국어 단락으로 변환 요청"""
    menu_list = []
    for m in menus:
        ctx = m.get("cultural_context") or {}
        origin = ctx.get("origin", "")
        history = ctx.get("history", "")
        significance = ctx.get("significance", "")

        menu_list.append({
            "id": m["id"],
            "name_ko": m["name_ko"],
            "name_en": m.get("name_en", ""),
            "origin_ko": origin,
            "history_ko": history,
            "significance_ko": significance,
        })

    return f"""You are a professional food writer specializing in Korean cuisine for international travelers.

Convert Korean food cultural context (provided as origin + history + significance fragments) into:
1. A cohesive Korean paragraph (ko) — combine and polish the fragments naturally
2. A natural English translation (en) — max 120 words, suitable for a travel food guide
3. A natural Japanese translation (ja) — use ですます体, max 120 words
4. A Simplified Chinese translation (zh) — max 120 words

Quality requirements:
- Each paragraph should flow naturally, not just list facts
- Use established culinary terms in JA/ZH
- Make it engaging and informative for tourists
- Return ONLY valid JSON, no extra text

Menus to convert:
{json.dumps(menu_list, ensure_ascii=False, indent=2)}

Output format (EXACTLY this structure):
{{
  "results": [
    {{
      "id": "<menu_id>",
      "cultural_context": {{
        "ko": "<Korean paragraph>",
        "en": "<English paragraph>",
        "ja": "<Japanese paragraph>",
        "zh": "<Chinese paragraph>"
      }}
    }}
  ]
}}
"""


def call_claude(client: anthropic.Anthropic, prompt: str) -> Optional[str]:
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except anthropic.RateLimitError:
        logger.warning("Rate limit hit, waiting 60s...")
        time.sleep(60)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None


def parse_response(text: str) -> Optional[Dict]:
    try:
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()
        else:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                return None
            text = text[start:end]
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nRaw: {text[:400]}")
        return None


def update_cultural_context(conn, menu_id: str, cultural_context: Dict):
    """cultural_context 전체를 새 포맷으로 교체"""
    if not any(cultural_context.get(k) for k in ["ko", "en", "ja", "zh"]):
        return False
    cur = conn.cursor()
    cur.execute("""
    UPDATE canonical_menus
    SET cultural_context = %s::jsonb,
        updated_at = NOW()
    WHERE id = %s::uuid
    """, (json.dumps(cultural_context, ensure_ascii=False), menu_id))
    conn.commit()
    return True


# ─── 배치 처리 ────────────────────────────────────────────────────────────────
def process_batch(conn, client: anthropic.Anthropic, menus: List[Dict]) -> int:
    if not menus:
        return 0

    prompt = build_conversion_prompt(menus)
    logger.info(f"Converting batch of {len(menus)} menus...")

    text = call_claude(client, prompt)
    if text is None:
        logger.error("Claude returned None")
        return 0

    result = parse_response(text)
    if not result or "results" not in result:
        logger.error(f"Invalid response: {text[:300]}")
        return 0

    success = 0
    for item in result["results"]:
        menu_id = item.get("id")
        if not menu_id:
            continue
        cultural = item.get("cultural_context", {})
        if not cultural.get("en"):
            logger.warning(f"  ⚠️ {menu_id}: missing EN in result")
            continue
        try:
            if update_cultural_context(conn, menu_id, cultural):
                success += 1
                langs = [k for k in ["ko", "en", "ja", "zh"] if cultural.get(k)]
                logger.info(f"  ✅ {menu_id}: {langs}")
        except Exception as e:
            logger.error(f"  ❌ DB update failed for {menu_id}: {e}")
            conn.rollback()

    return success


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="구형 cultural_context → 신형 다국어 포맷 변환")
    parser.add_argument("--test", action="store_true", help="3개 테스트")
    parser.add_argument("--batch", type=int, help="처리할 메뉴 수")
    parser.add_argument("--all", action="store_true", help="전체 처리 (111개)")
    parser.add_argument("--stats", action="store_true", help="통계만 출력")
    args = parser.parse_args()

    if not CLAUDE_API_KEY:
        logger.error("ANTHROPIC_API_KEY not found in .env")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    tunnel = start_ssh_tunnel()

    try:
        conn = connect_db()
        logger.info("✅ DB connected")

        stats = get_stats(conn)
        logger.info(f"Stats: {stats}")

        if args.stats:
            return

        limit = 3 if args.test else (args.batch if args.batch else None)
        menus = get_legacy_menus(conn, limit=limit)
        total = len(menus)
        logger.info(f"Found {total} menus with legacy cultural_context")

        if total == 0:
            logger.info("No menus to convert!")
            return

        total_success = 0
        for i in range(0, total, BATCH_SIZE):
            batch = menus[i:i + BATCH_SIZE]
            names = [m["name_ko"] for m in batch]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
            logger.info(f"Batch [{batch_num}/{total_batches}]: {names}")

            success = process_batch(conn, client, batch)
            total_success += success
            logger.info(f"  Result: {success}/{len(batch)}")

            if i + BATCH_SIZE < total:
                time.sleep(0.5)

        logger.info(f"\n{'='*50}")
        logger.info(f"Conversion complete: {total_success}/{total} menus updated")
        logger.info(f"{'='*50}")

        final_stats = get_stats(conn)
        logger.info(f"Final stats: {final_stats}")

    finally:
        if tunnel:
            tunnel.terminate()
            logger.info("[SSH] 터널 종료")
        else:
            logger.info("[SSH] 기존 터널 유지")


if __name__ == "__main__":
    main()
