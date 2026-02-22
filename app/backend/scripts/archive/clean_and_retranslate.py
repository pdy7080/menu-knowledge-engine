#!/usr/bin/env python3
"""
Mock 번역 데이터 제거 및 실제 GPT-4o 번역으로 교체
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from config import settings
from models.canonical_menu import CanonicalMenu


async def main():
    """Mock 데이터 제거 및 실제 번역으로 재실행"""

    engine = create_engine(settings.DATABASE_URL)

    print("\n" + "=" * 80)
    print("[CLEANUP] Mock 번역 데이터 제거 및 실제 GPT-4o 번역 교체")
    print("=" * 80)

    # Step 1: Mock 데이터 확인
    with Session(engine) as session:
        menus = session.query(CanonicalMenu).all()

        mock_count = 0
        for menu in menus:
            if menu.explanation_short:
                ja = menu.explanation_short.get("ja", "")
                zh = menu.explanation_short.get("zh", "")

                if ja.startswith("[JA]") or zh.startswith("[ZH]"):
                    mock_count += 1

                    # Mock 데이터 제거
                    menu.explanation_short["ja"] = ""
                    menu.explanation_short["zh"] = ""

        print("\n[STEP 1] Mock 데이터 감지 및 제거")
        print(f"  - 제거된 Mock 번역: {mock_count}개 메뉴")

        if mock_count > 0:
            session.commit()
            print("  - DB 업데이트 완료")

    # Step 2: 실제 GPT-4o 번역 실행
    print("\n[STEP 2] 실제 GPT-4o 번역 실행")
    print("  - 명령어:")
    print(
        "    python scripts/translate_canonical_menus_gpt4o.py --language ja,zh --batch-size 10"
    )

    print("\n" + "=" * 80)
    print(
        "[COMPLETE] Cleanup 완료! 이제 translate_canonical_menus_gpt4o.py를 실행하세요."
    )
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
