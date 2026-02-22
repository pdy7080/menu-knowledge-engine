"""enriched 데이터에서 이미지 URL SQL UPDATE문 생성"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
enriched_file = DATA_DIR / "canonical_seed_enriched.json"

with open(enriched_file, "r", encoding="utf-8") as f:
    data = json.load(f)

sql_lines = [
    "-- Sprint 2 Phase 2: 이미지 URL 업데이트",
    "-- Generated from canonical_seed_enriched.json",
    f"-- Total: {sum(1 for m in data if m.get('image_url'))} menus with images",
    "",
    "BEGIN;",
    "",
]

updated = 0
for menu in data:
    name = menu["name_ko"]
    image_url = menu.get("image_url")
    image_source = menu.get("image_source", "wiki")

    if not image_url:
        continue

    # Escape single quotes in URL
    safe_url = image_url.replace("'", "''")
    safe_name = name.replace("'", "''")

    # primary_image JSONB
    primary_image = json.dumps(
        {
            "url": image_url,
            "source": image_source,
            "license": "CC BY-SA 4.0" if image_source == "wiki" else "AI Generated",
            "attribution": "Wikimedia Commons" if image_source == "wiki" else "DALL-E",
        },
        ensure_ascii=False,
    ).replace("'", "''")

    sql_lines.append(
        f"UPDATE canonical_menus SET "
        f"image_url = '{safe_url}', "
        f"primary_image = '{primary_image}'::jsonb "
        f"WHERE name_ko = '{safe_name}';"
    )
    updated += 1

sql_lines.append("")
sql_lines.append("COMMIT;")
sql_lines.append(f"\n-- Updated {updated} menus")

output_file = Path(__file__).parent.parent / "migrations" / "sprint2_update_images.sql"
output_file.parent.mkdir(exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(sql_lines))

print(f"Generated: {output_file.name} ({updated} UPDATE statements)")
