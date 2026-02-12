"""
Papago Batch Translation Script
Translate all canonical_menus.explanation_short from EN to JA/ZH

Usage:
    python -X utf8 scripts/batch_translate_papago.py

Requirements:
    - PAPAGO_CLIENT_ID in .env
    - PAPAGO_CLIENT_SECRET in .env
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'backend'))

import asyncio
from sqlalchemy import select
from database import engine, AsyncSessionLocal
from models import CanonicalMenu
from services.translation_service import translation_service
import json


async def batch_translate_menus():
    """Translate all menu explanations from EN to JA/ZH"""

    print("🌍 Papago Batch Translation - Menu Knowledge Engine")
    print("=" * 60)

    # Check API credentials
    if not translation_service.papago_client_id:
        print("❌ PAPAGO_CLIENT_ID not found in environment")
        print("Please add to .env file:")
        print("  PAPAGO_CLIENT_ID=your_client_id")
        print("  PAPAGO_CLIENT_SECRET=your_client_secret")
        return False

    print("✅ Papago API credentials found")
    print()

    # Connect to database
    async with AsyncSessionLocal() as db:
        # Get all canonical menus
        result = await db.execute(select(CanonicalMenu))
        menus = result.scalars().all()

        total = len(menus)
        print(f"📊 Found {total} canonical menus to translate")
        print()

        # Statistics
        stats = {
            "total": total,
            "translated_ja": 0,
            "translated_zh": 0,
            "failed": 0,
            "skipped": 0
        }

        # Translate each menu
        for i, menu in enumerate(menus, 1):
            print(f"[{i}/{total}] {menu.name_ko} ({menu.name_en})")

            # Check if explanation_short exists
            if not menu.explanation_short:
                print(f"  ⏭️  No explanation - skipping")
                stats["skipped"] += 1
                continue

            # Get English explanation
            if isinstance(menu.explanation_short, dict):
                en_text = menu.explanation_short.get("en")
            else:
                en_text = menu.explanation_short

            if not en_text:
                print(f"  ⏭️  No EN explanation - skipping")
                stats["skipped"] += 1
                continue

            # Check if already translated
            if isinstance(menu.explanation_short, dict):
                existing_ja = menu.explanation_short.get("ja")
                existing_zh = menu.explanation_short.get("zh")
            else:
                existing_ja = None
                existing_zh = None

            # Prepare updated explanation
            updated_explanation = {
                "en": en_text
            }

            if isinstance(menu.explanation_short, dict):
                updated_explanation.update(menu.explanation_short)

            # Translate to Japanese (if not exists)
            if not existing_ja:
                print(f"  🇯🇵 Translating to Japanese...", end=" ")
                ja_text = translation_service.translate(en_text, "en", "ja")

                if ja_text:
                    updated_explanation["ja"] = ja_text
                    stats["translated_ja"] += 1
                    print(f"✅ {ja_text[:50]}{'...' if len(ja_text) > 50 else ''}")
                else:
                    print("❌ Failed")
                    stats["failed"] += 1
            else:
                print(f"  🇯🇵 Already translated: {existing_ja[:50]}{'...' if len(existing_ja) > 50 else ''}")

            # Translate to Chinese (if not exists)
            if not existing_zh:
                print(f"  🇨🇳 Translating to Chinese...", end=" ")
                zh_text = translation_service.translate(en_text, "en", "zh-CN")

                if zh_text:
                    updated_explanation["zh"] = zh_text
                    stats["translated_zh"] += 1
                    print(f"✅ {zh_text[:50]}{'...' if len(zh_text) > 50 else ''}")
                else:
                    print("❌ Failed")
                    stats["failed"] += 1
            else:
                print(f"  🇨🇳 Already translated: {existing_zh[:50]}{'...' if len(existing_zh) > 50 else ''}")

            # Update database
            menu.explanation_short = updated_explanation

            print()

        # Commit all changes
        print("💾 Committing changes to database...")
        await db.commit()
        print("✅ Database updated successfully")
        print()

        # Print statistics
        print("=" * 60)
        print("📊 Translation Statistics")
        print("=" * 60)
        print(f"Total menus:          {stats['total']}")
        print(f"Translated to JA:     {stats['translated_ja']}")
        print(f"Translated to ZH:     {stats['translated_zh']}")
        print(f"Skipped (no EN):      {stats['skipped']}")
        print(f"Failed:               {stats['failed']}")
        print("=" * 60)

        # Calculate completion
        expected_keys = (total - stats['skipped']) * 2  # JA + ZH
        completed_keys = stats['translated_ja'] + stats['translated_zh']
        completion_rate = (completed_keys / expected_keys * 100) if expected_keys > 0 else 0

        print(f"✅ Completion: {completed_keys}/{expected_keys} ({completion_rate:.1f}%)")
        print()

        # Verification
        print("🔍 Verifying translations...")
        result = await db.execute(select(CanonicalMenu))
        menus = result.scalars().all()

        ja_count = 0
        zh_count = 0
        en_count = 0

        for menu in menus:
            if isinstance(menu.explanation_short, dict):
                if menu.explanation_short.get("en"):
                    en_count += 1
                if menu.explanation_short.get("ja"):
                    ja_count += 1
                if menu.explanation_short.get("zh"):
                    zh_count += 1

        print(f"  EN: {en_count}/{total}")
        print(f"  JA: {ja_count}/{total}")
        print(f"  ZH: {zh_count}/{total}")

        if ja_count == en_count and zh_count == en_count:
            print("✅ All translations complete!")
            return True
        else:
            print("⚠️  Some translations missing")
            return False


if __name__ == "__main__":
    try:
        success = asyncio.run(batch_translate_menus())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Translation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
