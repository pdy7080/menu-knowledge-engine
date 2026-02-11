"""
Menu API Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from database import get_db
from models import Concept, Modifier, CanonicalMenu
from services.matching_engine import MenuMatchingEngine

router = APIRouter(prefix="/api/v1", tags=["menu"])


class MenuIdentifyRequest(BaseModel):
    """메뉴 식별 요청 모델"""
    menu_name_ko: str


@router.get("/concepts")
async def get_concepts(db: AsyncSession = Depends(get_db)):
    """Get all concepts (개념 트리 조회)"""
    result = await db.execute(select(Concept).order_by(Concept.sort_order))
    concepts = result.scalars().all()

    return {
        "total": len(concepts),
        "data": [
            {
                "id": str(c.id),
                "name_ko": c.name_ko,
                "name_en": c.name_en,
                "parent_id": str(c.parent_id) if c.parent_id else None,
                "definition_ko": c.definition_ko,
                "definition_en": c.definition_en,
            }
            for c in concepts
        ],
    }


@router.get("/modifiers")
async def get_modifiers(db: AsyncSession = Depends(get_db)):
    """Get all modifiers (수식어 사전 조회)"""
    result = await db.execute(select(Modifier).order_by(Modifier.priority.desc(), Modifier.text_ko))
    modifiers = result.scalars().all()

    return {
        "total": len(modifiers),
        "data": [
            {
                "id": str(m.id),
                "text_ko": m.text_ko,
                "type": m.type,
                "semantic_key": m.semantic_key,
                "translation_en": m.translation_en,
                "affects_spice": m.affects_spice,
                "affects_size": m.affects_size,
                "priority": m.priority,
            }
            for m in modifiers
        ],
    }


@router.get("/canonical-menus")
async def get_canonical_menus(db: AsyncSession = Depends(get_db)):
    """Get all canonical menus (표준 메뉴 조회)"""
    result = await db.execute(select(CanonicalMenu).order_by(CanonicalMenu.name_ko))
    menus = result.scalars().all()

    return {
        "total": len(menus),
        "data": [
            {
                "id": str(cm.id),
                "name_ko": cm.name_ko,
                "name_en": cm.name_en,
                "concept_id": str(cm.concept_id),
                "explanation_short": cm.explanation_short,
                "main_ingredients": cm.main_ingredients,
                "allergens": cm.allergens,
                "spice_level": cm.spice_level,
                "difficulty_score": cm.difficulty_score,
                "image_url": cm.image_url,
            }
            for cm in menus
        ],
    }


@router.post("/menu/identify")
async def identify_menu(
    request: MenuIdentifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    메뉴 식별 API
    3단계 매칭 파이프라인: Exact Match → Modifier Decomposition → AI Discovery
    """
    engine = MenuMatchingEngine(db)
    result = await engine.match_menu(request.menu_name_ko)
    return result.to_dict()
