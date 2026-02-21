#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
translate_deep_content.py

목적: explanation_long 및 cultural_context 필드를 일본어/중국어로 번역
번역 대상:
  - explanation_long.ja / .zh (131개 메뉴, 현재 0%)
  - cultural_context.ja / .zh (260개 메뉴, 현재 0%)

API: Claude API (claude-haiku-4-5-20251001)
실행:
  cd app/backend && python scripts/translate_deep_content.py --test
  cd app/backend && python scripts/translate_deep_content.py --batch 10
  cd app/backend && python scripts/translate_deep_content.py --all
  cd app/backend && python scripts/translate_deep_content.py --stats
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

# ─────────────────────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────────────────────
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

BATCH_SIZE = 3   # 3: JSON 잘림 방지를 위해 소배치 유지
SLEEP_BETWEEN_BATCHES = 0.5

# ─────────────────────────────────────────────────────────────────────────────
# 로깅
# ─────────────────────────────────────────────────────────────────────────────
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
        logging.FileHandler("translate_deep_content.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# SSH 터널
# ─────────────────────────────────────────────────────────────────────────────
def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def start_ssh_tunnel():
    if is_port_open(DB_HOST, LOCAL_TUNNEL_PORT):
        logger.info(f"[SSH] 기존 터널 사용 (localhost:{LOCAL_TUNNEL_PORT} 이미 열려있음)")
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


# ─────────────────────────────────────────────────────────────────────────────
# DB 쿼리
# ─────────────────────────────────────────────────────────────────────────────
def get_menus_needing_deep_translation(conn, limit: Optional[int] = None) -> List[Dict]:
    """explanation_long 또는 cultural_context의 JA/ZH 번역이 없는 메뉴"""
    limit_clause = f"LIMIT {limit}" if limit else ""
    query = f"""
    SELECT
        id::text,
        name_ko,
        name_en,
        explanation_long,
        description_long_en,
        cultural_context
    FROM canonical_menus
    WHERE status = 'active'
      AND (
          (explanation_long IS NOT NULL AND (
              NOT (explanation_long ? 'ja') OR (explanation_long->>'ja') IS NULL OR (explanation_long->>'ja') = ''
              OR NOT (explanation_long ? 'zh') OR (explanation_long->>'zh') IS NULL OR (explanation_long->>'zh') = ''
          ))
          OR
          (cultural_context IS NOT NULL AND (
              NOT (cultural_context ? 'ja') OR (cultural_context->>'ja') IS NULL OR (cultural_context->>'ja') = ''
              OR NOT (cultural_context ? 'zh') OR (cultural_context->>'zh') IS NULL OR (cultural_context->>'zh') = ''
          ))
      )
    ORDER BY content_completeness DESC, created_at ASC
    {limit_clause}
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query)
    return [dict(r) for r in cur.fetchall()]


def get_translation_stats(conn) -> Dict:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN explanation_long IS NOT NULL AND explanation_long ? 'ja' AND (explanation_long->>'ja') != '' THEN 1 ELSE 0 END) as exp_long_ja,
        SUM(CASE WHEN explanation_long IS NOT NULL AND explanation_long ? 'zh' AND (explanation_long->>'zh') != '' THEN 1 ELSE 0 END) as exp_long_zh,
        SUM(CASE WHEN cultural_context IS NOT NULL AND cultural_context ? 'ja' AND (cultural_context->>'ja') != '' THEN 1 ELSE 0 END) as cultural_ja,
        SUM(CASE WHEN cultural_context IS NOT NULL AND cultural_context ? 'zh' AND (cultural_context->>'zh') != '' THEN 1 ELSE 0 END) as cultural_zh
    FROM canonical_menus WHERE status = 'active'
    """)
    return dict(cur.fetchone())


# ─────────────────────────────────────────────────────────────────────────────
# Claude API 번역
# ─────────────────────────────────────────────────────────────────────────────
def build_translation_prompt(menus: List[Dict]) -> str:
    menu_list = []
    for m in menus:
        exp_long_en = None
        if m.get("explanation_long") and isinstance(m["explanation_long"], dict):
            exp_long_en = m["explanation_long"].get("en", "")
        if not exp_long_en:
            exp_long_en = m.get("description_long_en", "")

        cultural_en = None
        if m.get("cultural_context") and isinstance(m["cultural_context"], dict):
            cultural_en = m["cultural_context"].get("en", "")

        menu_list.append({
            "id": m["id"],
            "name_ko": m["name_ko"],
            "explanation_long_en": exp_long_en or "",
            "cultural_context_en": cultural_en or "",
        })

    return f"""You are a professional food writer specializing in Korean cuisine for international travelers.
Translate the English text fields to Japanese and Chinese (Simplified) for Korean dishes.

Quality Rules:
- Use ESTABLISHED culinary terms: proper JP/ZH food vocabulary (e.g., キムチ, 豆腐, 냉면→冷麺)
- Japanese: natural, polite tone (ですます体) suitable for a food guide
- Chinese: Simplified Chinese (简体中文), fluent and natural
- Preserve cultural nuance (not just phonetic transliteration)
- IMPORTANT: Keep each translation concise — max 120 words per field
- If a field is empty string "", output "" for both languages
- Return ONLY valid JSON, no extra text

Input menus:
{json.dumps(menu_list, ensure_ascii=False, indent=2)}

Output format (EXACTLY this JSON structure):
{{
  "translations": [
    {{
      "id": "<menu_id>",
      "explanation_long": {{
        "ja": "<Japanese translation or empty string>",
        "zh": "<Chinese translation or empty string>"
      }},
      "cultural_context": {{
        "ja": "<Japanese translation or empty string>",
        "zh": "<Chinese translation or empty string>"
      }}
    }}
  ]
}}
"""


def call_claude(client: anthropic.Anthropic, prompt: str) -> Optional[str]:
    """Claude API 호출"""
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


def parse_translation_response(text: str) -> Optional[Dict]:
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
        logger.error(f"JSON parse error: {e}\nRaw: {text[:300]}")
        return None


def update_menu_translations(conn, menu_id: str, exp_long_update: Dict, cultural_update: Dict):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if exp_long_update.get("ja") or exp_long_update.get("zh"):
        cur.execute("""
        UPDATE canonical_menus
        SET explanation_long = COALESCE(explanation_long, '{}') || %s::jsonb,
            updated_at = NOW()
        WHERE id = %s::uuid
        """, (json.dumps(exp_long_update, ensure_ascii=False), menu_id))

    if cultural_update.get("ja") or cultural_update.get("zh"):
        cur.execute("""
        UPDATE canonical_menus
        SET cultural_context = COALESCE(cultural_context, '{}') || %s::jsonb,
            updated_at = NOW()
        WHERE id = %s::uuid
        """, (json.dumps(cultural_update, ensure_ascii=False), menu_id))

    conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# 배치 처리
# ─────────────────────────────────────────────────────────────────────────────
def process_batch(conn, client: anthropic.Anthropic, menus: List[Dict]) -> int:
    if not menus:
        return 0

    prompt = build_translation_prompt(menus)
    logger.info(f"Translating batch of {len(menus)} menus...")

    text = call_claude(client, prompt)
    if text is None:
        logger.error("Claude returned None")
        return 0

    result = parse_translation_response(text)
    if not result or "translations" not in result:
        logger.error(f"Invalid response structure: {text[:200]}")
        return 0

    success = 0
    for trans in result["translations"]:
        menu_id = trans.get("id")
        if not menu_id:
            continue

        exp_long = trans.get("explanation_long", {})
        cultural = trans.get("cultural_context", {})
        exp_long_clean = {k: v for k, v in exp_long.items() if v}
        cultural_clean = {k: v for k, v in cultural.items() if v}

        if exp_long_clean or cultural_clean:
            try:
                update_menu_translations(conn, menu_id, exp_long_clean, cultural_clean)
                success += 1
                logger.info(f"  ✅ {menu_id}: exp_long={list(exp_long_clean.keys())}, cultural={list(cultural_clean.keys())}")
            except Exception as e:
                logger.error(f"  ❌ DB update failed for {menu_id}: {e}")
                conn.rollback()

    return success


def main():
    parser = argparse.ArgumentParser(description="Claude API로 explanation_long/cultural_context JA/ZH 번역")
    parser.add_argument("--test", action="store_true", help="5개 메뉴 테스트")
    parser.add_argument("--batch", type=int, help="처리할 메뉴 수")
    parser.add_argument("--all", action="store_true", help="전체 처리")
    parser.add_argument("--stats", action="store_true", help="통계만 출력")
    args = parser.parse_args()

    if not CLAUDE_API_KEY:
        logger.error("ANTHROPIC_API_KEY not found in .env")
        sys.exit(1)

    logger.info(f"Claude model: {CLAUDE_MODEL}")
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    tunnel = start_ssh_tunnel()

    try:
        conn = connect_db()
        logger.info("✅ DB connected")

        stats = get_translation_stats(conn)
        logger.info(f"Translation stats: {stats}")

        if args.stats:
            return

        limit = 5 if args.test else (args.batch if args.batch else None)
        menus = get_menus_needing_deep_translation(conn, limit=limit)
        total = len(menus)
        logger.info(f"Found {total} menus needing deep translation")

        if total == 0:
            logger.info("No menus to translate!")
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
            logger.info(f"  Batch result: {success}/{len(batch)} succeeded")

            if i + BATCH_SIZE < total:
                time.sleep(SLEEP_BETWEEN_BATCHES)

        logger.info(f"\n{'='*50}")
        logger.info(f"Translation complete: {total_success}/{total} menus updated")
        logger.info(f"{'='*50}")

        final_stats = get_translation_stats(conn)
        logger.info(f"Final stats: {final_stats}")

    finally:
        if tunnel:
            tunnel.terminate()
            logger.info("[SSH] 터널 종료")
        else:
            logger.info("[SSH] 기존 터널 유지")


if __name__ == "__main__":
    main()
