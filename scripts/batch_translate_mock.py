"""
Mock Batch Translation Script (Development Mode)
Translate all canonical_menus.explanation_short using mock translations

This is for development/testing when Papago API credentials are not available.
For production, use batch_translate_papago.py with real API credentials.

Usage:
    python -X utf8 scripts/batch_translate_mock.py
"""
import sys
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'backend'))

import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal
from models import CanonicalMenu


# Mock translation function
def mock_translate(text: str, target_lang: str) -> str:
    """
    Mock translation for development
    Real production will use Papago API
    """
    if target_lang == "ja":
        return f"[JA] {text}"
    elif target_lang == "zh":
        return f"[ZH] {text}"
    else:
        return text


async def batch_translate_menus_mock():
    """Translate all menu explanations using mock translations"""

    print("🌍 Mock Batch Translation - Menu Knowledge Engine")
    print("⚠️  DEVELOPMENT MODE: Using mock translations")
    print("For production, configure PAPAGO_CLIENT_ID and use batch_translate_papago.py")
    print("=" * 60)
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

            # Mock translate to Japanese (if not exists)
            if not existing_ja:
                ja_text = mock_translate(en_text, "ja")
                updated_explanation["ja"] = ja_text
                stats["translated_ja"] += 1
                print(f"  🇯🇵 Mock JA: {ja_text[:60]}{'...' if len(ja_text) > 60 else ''}")
            else:
                print(f"  🇯🇵 Already exists: {existing_ja[:60]}{'...' if len(existing_ja) > 60 else ''}")

            # Mock translate to Chinese (if not exists)
            if not existing_zh:
                zh_text = mock_translate(en_text, "zh")
                updated_explanation["zh"] = zh_text
                stats["translated_zh"] += 1
                print(f"  🇨🇳 Mock ZH: {zh_text[:60]}{'...' if len(zh_text) > 60 else ''}")
            else:
                print(f"  🇨🇳 Already exists: {existing_zh[:60]}{'...' if len(existing_zh) > 60 else ''}")

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
        print()

        if ja_count == en_count and zh_count == en_count:
            print("✅ All translations complete!")
            print()
            print("⚠️  IMPORTANT: These are MOCK translations for development")
            print("For production, you need to:")
            print("  1. Get Papago API credentials from Naver Cloud Platform")
            print("  2. Add to .env:")
            print("     PAPAGO_CLIENT_ID=your_client_id")
            print("     PAPAGO_CLIENT_SECRET=your_client_secret")
            print("  3. Run: python scripts/batch_translate_papago.py")
            return True
        else:
            print("⚠️  Some translations missing")
            return False


if __name__ == "__main__":
    try:
        success = asyncio.run(batch_translate_menus_mock())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Translation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
