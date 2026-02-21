#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enrich_missing_menus.py

목적: content_completeness = 0인 메뉴들(149개)에 enriched content 생성
대상 필드:
  - description_long_ko, description_long_en
  - preparation_steps (JSONB)
  - visitor_tips (JSONB)
  - cultural_context (JA/ZH 포함)
  - nutrition_detail (JSONB)
  - regional_variants (JSONB)
  - flavor_profile (JSONB)
  - similar_dishes (JSONB[])
  - content_completeness → 100

API: Claude API (claude-haiku-4-5-20251001)

실행:
  cd app/backend && python scripts/enrich_missing_menus.py --test
  cd app/backend && python scripts/enrich_missing_menus.py --batch 10
  cd app/backend && python scripts/enrich_missing_menus.py --all
  cd app/backend && python scripts/enrich_missing_menus.py --stats
  cd app/backend && python scripts/enrich_missing_menus.py --clear-checkpoint
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

CHECKPOINT_FILE = Path("enrich_missing_checkpoint.json")
SLEEP_BETWEEN_MENUS = 0.3  # Claude는 rate limit 여유로움

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
        logging.FileHandler("enrich_missing_menus.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# SSH 터널 & DB
# ─────────────────────────────────────────────────────────────────────────────
def is_port_open(host, port):
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
        raise RuntimeError("SSH tunnel failed")
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
def get_missing_menus(conn, limit: Optional[int] = None) -> List[Dict]:
    processed_ids = load_checkpoint()
    exclude_clause = ""
    if processed_ids:
        ids_str = ", ".join(f"'{id_}'" for id_ in processed_ids)
        exclude_clause = f"AND id::text NOT IN ({ids_str})"

    limit_clause = f"LIMIT {limit}" if limit else ""
    query = f"""
    SELECT
        id::text,
        name_ko,
        name_en,
        spice_level,
        main_ingredients,
        allergens
    FROM canonical_menus
    WHERE status = 'active'
      AND (content_completeness IS NULL OR content_completeness = 0)
      {exclude_clause}
    ORDER BY created_at ASC
    {limit_clause}
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query)
    return [dict(r) for r in cur.fetchall()]


def get_enrichment_stats(conn) -> Dict:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN content_completeness >= 100 THEN 1 ELSE 0 END) as fully_enriched,
        SUM(CASE WHEN content_completeness = 0 OR content_completeness IS NULL THEN 1 ELSE 0 END) as missing
    FROM canonical_menus WHERE status = 'active'
    """)
    return dict(cur.fetchone())


# ─────────────────────────────────────────────────────────────────────────────
# 체크포인트
# ─────────────────────────────────────────────────────────────────────────────
def load_checkpoint() -> List[str]:
    if CHECKPOINT_FILE.exists():
        try:
            return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_checkpoint(processed_ids: List[str]):
    CHECKPOINT_FILE.write_text(
        json.dumps(processed_ids, ensure_ascii=False),
        encoding="utf-8"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 카테고리 감지
# ─────────────────────────────────────────────────────────────────────────────
def detect_category(name_ko: str) -> str:
    if any(k in name_ko for k in ["찌개"]):
        return "stew"
    if any(k in name_ko for k in ["탕", "국", "해장국"]):
        return "soup"
    if any(k in name_ko for k in ["구이", "불고기", "갈비", "삼겹"]):
        return "grilled"
    if any(k in name_ko for k in ["볶음", "떡볶이"]):
        return "stirfried"
    if any(k in name_ko for k in ["밥", "비빔밥", "김밥", "덮밥"]):
        return "rice"
    if any(k in name_ko for k in ["면", "냉면", "국수", "칼국수"]):
        return "noodles"
    return "general"


CATEGORY_HINTS = {
    "stew":      {"nutrition": "300-450", "method": "broth-based stew (찌개)"},
    "soup":      {"nutrition": "250-400", "method": "clear soup (탕/국)"},
    "grilled":   {"nutrition": "450-600", "method": "grilled/barbecue"},
    "stirfried": {"nutrition": "350-500", "method": "stir-fried"},
    "rice":      {"nutrition": "500-700", "method": "rice dish"},
    "noodles":   {"nutrition": "400-600", "method": "noodle dish"},
    "general":   {"nutrition": "350-500", "method": "Korean dish"},
}


# ─────────────────────────────────────────────────────────────────────────────
# Claude API 프롬프트 & 호출
# ─────────────────────────────────────────────────────────────────────────────
def build_enrichment_prompt(menu: Dict) -> str:
    cat = detect_category(menu["name_ko"])
    hints = CATEGORY_HINTS.get(cat, CATEGORY_HINTS["general"])
    spice = menu.get("spice_level") or 0
    ingredients = []
    if menu.get("main_ingredients"):
        for ing in menu["main_ingredients"]:
            if isinstance(ing, dict):
                ingredients.append(ing.get("ko") or ing.get("en") or "")
            elif isinstance(ing, str):
                ingredients.append(ing)

    cal_min = hints["nutrition"].split("-")[0]

    return f"""Generate comprehensive Korean menu content for a food guide app.

Menu details:
- Korean Name: {menu["name_ko"]}
- English Name: {menu.get("name_en", "")}
- Cooking Method: {hints["method"]}
- Spice Level: {spice}/5
- Main Ingredients: {", ".join(i for i in ingredients if i) or "not specified"}

Output ONLY valid JSON with these exact fields (no extra text):
{{
  "description_long_ko": "한국어 상세 설명 (150-200자)",
  "description_long_en": "English detailed description (150-200 chars)",
  "preparation_steps": [
    {{"step": 1, "instruction_ko": "한국어 조리 단계", "instruction_en": "English cooking step"}}
  ],
  "visitor_tips": {{
    "ordering": "How to order tip in English",
    "eating": "How to eat properly in English",
    "pairing": ["side dish 1", "side dish 2"]
  }},
  "cultural_context": {{
    "ko": "한국어 문화적 배경",
    "en": "English cultural background",
    "ja": "日本語の文化的背景",
    "zh": "中文文化背景"
  }},
  "nutrition_detail": {{
    "calories": {cal_min},
    "protein_g": 15,
    "fat_g": 10,
    "carbs_g": 40,
    "sodium_mg": 800
  }},
  "regional_variants": [
    {{"region": "지역명", "local_name": "현지 이름", "differences": "차이점 설명"}}
  ],
  "flavor_profile": {{
    "spiciness": {spice},
    "sweetness": 2,
    "saltiness": 3,
    "umami": 4
  }},
  "similar_dishes": ["비슷한 메뉴1", "비슷한 메뉴2", "비슷한 메뉴3"]
}}
Requirements:
- preparation_steps: 4-6 steps
- regional_variants: 2-3 variants
- nutrition_detail calories range: {hints["nutrition"]} kcal
"""


def call_claude(client: anthropic.Anthropic, prompt: str) -> Optional[str]:
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except anthropic.RateLimitError:
        logger.warning("Rate limit hit, waiting 60s...")
        time.sleep(60)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None


def parse_enrichment_response(text: str) -> Optional[Dict]:
    try:
        if "```json" in text:
            s = text.find("```json") + 7
            e = text.find("```", s)
            text = text[s:e].strip()
        elif "```" in text:
            s = text.find("```") + 3
            e = text.find("```", s)
            text = text[s:e].strip()
        else:
            s = text.find("{")
            e = text.rfind("}") + 1
            if s == -1 or e == 0:
                return None
            text = text[s:e]
        return json.loads(text)
    except json.JSONDecodeError as ex:
        logger.error(f"JSON parse error: {ex}")
        return None


def update_menu_enrichment(conn, menu_id: str, enriched: Dict):
    cur = conn.cursor()

    desc_ko = enriched.get("description_long_ko", "")
    desc_en = enriched.get("description_long_en", "")

    prep_steps = enriched.get("preparation_steps", [])
    if isinstance(prep_steps, list) and prep_steps:
        normalized_steps = []
        for step in prep_steps:
            normalized_steps.append({
                "step": step.get("step", len(normalized_steps) + 1),
                "instruction_ko": step.get("instruction_ko", ""),
                "instruction_en": step.get("instruction_en", step.get("instruction", "")),
            })
        prep_steps_json = json.dumps(
            {"steps": normalized_steps, "serving_suggestions": [], "etiquette": []},
            ensure_ascii=False
        )
    else:
        prep_steps_json = None

    tips = enriched.get("visitor_tips")
    tips_json = json.dumps(tips, ensure_ascii=False) if tips else None

    cultural = enriched.get("cultural_context")
    cultural_json = json.dumps(cultural, ensure_ascii=False) if cultural else None

    nutrition = enriched.get("nutrition_detail")
    nutrition_json = json.dumps(nutrition, ensure_ascii=False) if nutrition else None

    regional = enriched.get("regional_variants", [])
    regional_json = json.dumps(regional, ensure_ascii=False) if regional else None

    flavor = enriched.get("flavor_profile")
    flavor_json = json.dumps(flavor, ensure_ascii=False) if flavor else None

    similar = enriched.get("similar_dishes", [])
    similar_json = json.dumps(similar, ensure_ascii=False) if similar else None

    # similar_dishes는 jsonb[] 타입이므로 별도 처리
    cur.execute("""
    UPDATE canonical_menus SET
        description_long_ko = COALESCE(%s, description_long_ko),
        description_long_en = COALESCE(%s, description_long_en),
        preparation_steps = COALESCE(%s::jsonb, preparation_steps),
        visitor_tips = COALESCE(%s::jsonb, visitor_tips),
        cultural_context = COALESCE(%s::jsonb, cultural_context),
        nutrition_detail = COALESCE(%s::jsonb, nutrition_detail),
        regional_variants = COALESCE(%s::jsonb, regional_variants),
        flavor_profile = COALESCE(%s::jsonb, flavor_profile),
        similar_dishes = COALESCE(
            ARRAY(SELECT jsonb_array_elements(%s::jsonb)),
            similar_dishes
        ),
        content_completeness = 100,
        updated_at = NOW()
    WHERE id = %s::uuid
    """, (
        desc_ko or None, desc_en or None,
        prep_steps_json, tips_json, cultural_json,
        nutrition_json, regional_json, flavor_json,
        similar_json,
        menu_id
    ))
    conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Claude API로 미완성 149개 메뉴 enriched content 생성")
    parser.add_argument("--test", action="store_true", help="3개 메뉴 테스트")
    parser.add_argument("--batch", type=int, help="처리할 메뉴 수")
    parser.add_argument("--all", action="store_true", help="전체 처리")
    parser.add_argument("--stats", action="store_true", help="DB 통계만 출력")
    parser.add_argument("--clear-checkpoint", action="store_true", help="체크포인트 초기화")
    args = parser.parse_args()

    if args.clear_checkpoint and CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        logger.info("Checkpoint cleared")

    if not CLAUDE_API_KEY:
        logger.error("ANTHROPIC_API_KEY not found in .env")
        sys.exit(1)

    logger.info(f"Claude model: {CLAUDE_MODEL}")
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    tunnel = start_ssh_tunnel()

    try:
        conn = connect_db()
        logger.info("✅ DB connected")

        stats = get_enrichment_stats(conn)
        logger.info(f"Current stats: {stats}")

        if args.stats:
            return

        limit = 3 if args.test else (args.batch if args.batch else None)
        menus = get_missing_menus(conn, limit=limit)
        logger.info(f"Found {len(menus)} menus to enrich")

        if not menus:
            logger.info("Nothing to enrich! All menus are complete.")
            return

        processed_ids = load_checkpoint()
        success_count = 0
        fail_count = 0

        for i, menu in enumerate(menus):
            name = menu["name_ko"]
            menu_id = menu["id"]
            logger.info(f"[{i+1}/{len(menus)}] Enriching: {name}")

            prompt = build_enrichment_prompt(menu)
            text = call_claude(client, prompt)

            if text is None:
                logger.warning(f"  No response for {name}")
                fail_count += 1
                continue

            enriched = parse_enrichment_response(text)
            if not enriched:
                logger.error(f"  Parse failed for {name}")
                fail_count += 1
                continue

            try:
                update_menu_enrichment(conn, menu_id, enriched)
                processed_ids.append(menu_id)
                save_checkpoint(processed_ids)
                success_count += 1
                logger.info(f"  ✅ {name} enriched successfully")
            except Exception as e:
                logger.error(f"  ❌ DB update failed: {e}")
                conn.rollback()
                fail_count += 1

            if i + 1 < len(menus):
                time.sleep(SLEEP_BETWEEN_MENUS)

        logger.info(f"\n{'='*50}")
        logger.info(f"Enrichment complete: {success_count} success, {fail_count} fail")
        logger.info(f"{'='*50}")

        final_stats = get_enrichment_stats(conn)
        logger.info(f"Final stats: {final_stats}")

    finally:
        if tunnel:
            tunnel.terminate()
            logger.info("[SSH] 터널 종료")
        else:
            logger.info("[SSH] 기존 터널 유지")


if __name__ == "__main__":
    main()
