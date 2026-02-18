"""
시드 데이터 실행 스크립트
Concept 47개 + Modifier 50개 입력
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import AsyncSessionLocal, init_db
from models import Concept, Modifier, CanonicalMenu
from seeds.seed_concepts import get_concept_seeds
from seeds.seed_modifiers import get_modifier_seeds
from seeds.seed_canonical_menus import get_canonical_menu_seeds
from seeds.seed_canonical_menus_ext import get_canonical_menu_extension
from seeds.image_urls import get_image_url_map, DEFAULT_FOOD_IMAGE


async def seed_concepts():
    """Concept 시드 데이터 입력 (대분류 + 중분류)"""
    async with AsyncSessionLocal() as session:
        # 기존 데이터 삭제
        print(f"[*] Deleting existing Concepts...")
        await session.execute(Concept.__table__.delete())
        await session.commit()
        print(f"[OK] Existing Concepts deleted\n")

        concept_data = get_concept_seeds()

        print(f"[*] Seeding Concepts...")
        parent_map = {}
        total_count = 0

        for parent_concept in concept_data:
            # 대분류 생성
            parent = Concept(
                name_ko=parent_concept["name_ko"],
                name_en=parent_concept["name_en"],
                definition_ko=parent_concept.get("definition_ko"),
                definition_en=parent_concept.get("definition_en"),
                parent_id=None,
                sort_order=total_count,
            )
            session.add(parent)
            await session.flush()  # ID 생성
            parent_map[parent_concept["name_ko"]] = parent.id
            total_count += 1
            print(f"  [OK] {parent.name_ko} ({parent.name_en})")

            # 중분류 생성
            for idx, child_data in enumerate(parent_concept.get("children", [])):
                child = Concept(
                    name_ko=child_data["name_ko"],
                    name_en=child_data["name_en"],
                    definition_ko=child_data.get("definition_ko"),
                    definition_en=child_data.get("definition_en"),
                    parent_id=parent.id,
                    sort_order=idx,
                )
                session.add(child)
                total_count += 1
                print(f"    |- {child.name_ko} ({child.name_en})")

        await session.commit()
        print(f"[OK] Concepts seeded: {total_count} records\n")


async def seed_modifiers():
    """Modifier 시드 데이터 입력 (50개)"""
    async with AsyncSessionLocal() as session:
        # 기존 데이터 삭제
        print(f"[*] Deleting existing Modifiers...")
        await session.execute(Modifier.__table__.delete())
        await session.commit()
        print(f"[OK] Existing Modifiers deleted\n")

        modifier_data = get_modifier_seeds()

        print(f"[*] Seeding Modifiers...")

        for mod_dict in modifier_data:
            modifier = Modifier(
                text_ko=mod_dict["text_ko"],
                type=mod_dict["type"],
                semantic_key=mod_dict["semantic_key"],
                translation_en=mod_dict["translation_en"],
                affects_spice=mod_dict.get("affects_spice"),
                affects_size=mod_dict.get("affects_size"),
                priority=mod_dict["priority"],
            )
            session.add(modifier)
            print(f"  [OK] {modifier.text_ko} ({modifier.type}) - {modifier.translation_en}")

        await session.commit()
        print(f"[OK] Modifiers seeded: {len(modifier_data)} records\n")


async def seed_canonical_menus():
    """Canonical Menu 시드 데이터 입력 (123 + 177 = 300개)"""
    async with AsyncSessionLocal() as session:
        # Concept ID 매핑을 위해 모든 concept 조회
        from sqlalchemy import select
        result = await session.execute(select(Concept))
        concepts = result.scalars().all()
        concept_map = {c.name_ko: c.id for c in concepts}

        # 기본 메뉴 + 확장 메뉴 병합
        canonical_data = get_canonical_menu_seeds() + get_canonical_menu_extension()
        image_map = get_image_url_map()

        print(f"[*] Seeding Canonical Menus (base + extension)...")
        image_count = 0

        for menu_dict in canonical_data:
            # concept_id 찾기
            concept_name = menu_dict["concept"]
            if concept_name not in concept_map:
                print(f"  [WARN] Concept '{concept_name}' not found, skipping {menu_dict['name_ko']}")
                continue

            # main_ingredients를 JSONB 구조로 변환
            main_ingredients_jsonb = [
                {"en": ing} for ing in menu_dict["primary_ingredients"]
            ]

            # 이미지 URL 매핑
            image_url = image_map.get(menu_dict["name_ko"], None)
            if image_url:
                image_count += 1

            canonical = CanonicalMenu(
                name_ko=menu_dict["name_ko"],
                name_en=menu_dict["name_en"],
                concept_id=concept_map[concept_name],
                explanation_short={
                    "ko": menu_dict["description_ko"],
                    "en": menu_dict["description_en"],
                },
                main_ingredients=main_ingredients_jsonb,
                allergens=menu_dict["allergens"],
                spice_level=menu_dict["spice_level"],
                difficulty_score=menu_dict["difficulty_score"],
                image_url=image_url,
            )
            session.add(canonical)

        await session.commit()
        print(f"[OK] Canonical Menus seeded: {len(canonical_data)} records")
        print(f"[OK] Image URLs mapped: {image_count}/{len(canonical_data)} menus\n")


async def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("Menu Knowledge Engine - Seed Data")
    print("=" * 60)
    print()

    # 1. DB 테이블 생성
    print("[*] Creating database tables...")
    await init_db()
    print("[OK] Database tables created\n")

    # 2. Canonical Menu 먼저 삭제 (foreign key 때문에)
    async with AsyncSessionLocal() as session:
        print(f"[*] Deleting existing Canonical Menus...")
        await session.execute(CanonicalMenu.__table__.delete())
        await session.commit()
        print(f"[OK] Existing Canonical Menus deleted\n")

    # 3. Concept 시드
    await seed_concepts()

    # 4. Modifier 시드
    await seed_modifiers()

    # 5. Canonical Menu 시드
    await seed_canonical_menus()

    print("=" * 60)
    print("[SUCCESS] Seeding completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
