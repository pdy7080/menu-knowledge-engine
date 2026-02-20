"""
Menu API Routes
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from database import get_db
from models import Concept, Modifier, CanonicalMenu
from services.matching_engine import MenuMatchingEngine
from services.ocr_service import ocr_service
from utils.image_validation import validate_image, ImageValidationError
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["menu"])


class MenuIdentifyRequest(BaseModel):
    """메뉴 식별 요청 모델"""
    menu_name_ko: str = Field(..., min_length=1, description="Korean menu name (cannot be empty)")


async def _resolve_similar_dishes(similar_dishes: List[str], db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Convert similar_dishes from string array to full menu objects

    Args:
        similar_dishes: List of dish name strings (e.g., ["갈비구이 (Galbi Gui...)", ...])
        db: Database session

    Returns:
        List of menu objects with id, name_ko, name_en, image_url
    """
    if not similar_dishes:
        return []

    resolved = []
    for dish_string in similar_dishes:
        # Extract Korean name (before parenthesis or dash)
        # "갈비구이 (Galbi Gui - Description)" -> "갈비구이"
        name_ko = dish_string.split('(')[0].strip()

        try:
            # Look up in canonical_menus by name_ko
            result = await db.execute(
                select(CanonicalMenu).where(CanonicalMenu.name_ko == name_ko).limit(1)
            )
            menu = result.scalar_one_or_none()

            if menu:
                resolved.append({
                    "id": str(menu.id),
                    "name_ko": menu.name_ko,
                    "name_en": menu.name_en,
                    "image_url": menu.image_url or (menu.primary_image.get('url') if menu.primary_image else None),
                    "spice_level": menu.spice_level
                })
            else:
                # Fallback: return string-based object
                resolved.append({
                    "id": None,
                    "name_ko": name_ko,
                    "name_en": dish_string.split('(')[1].split(')')[0] if '(' in dish_string else name_ko,
                    "image_url": None,
                    "spice_level": 0
                })
        except Exception as e:
            logger.warning(f"Failed to resolve similar dish '{dish_string}': {e}")
            continue

    return resolved


def _serialize_canonical_menu(cm: CanonicalMenu, include_enriched: bool = False) -> Dict[str, Any]:
    """
    Serialize CanonicalMenu model to dict

    Args:
        cm: CanonicalMenu instance
        include_enriched: If True, include Sprint 2 Phase 1 enriched fields

    Returns:
        Serialized menu dict
    """
    base_fields = {
        "id": str(cm.id),
        "name_ko": cm.name_ko,
        "name_en": cm.name_en,
        "name_ja": cm.name_ja,
        "name_zh_cn": cm.name_zh_cn,
        "name_zh_tw": cm.name_zh_tw,
        "romanization": cm.romanization,
        "concept_id": str(cm.concept_id) if cm.concept_id else None,
        "explanation_short": cm.explanation_short,
        "explanation_long": cm.explanation_long,
        "cultural_context": cm.cultural_context,
        "main_ingredients": cm.main_ingredients,
        "allergens": cm.allergens,
        "dietary_tags": cm.dietary_tags,
        "spice_level": cm.spice_level,
        "serving_style": cm.serving_style,
        "typical_price_min": cm.typical_price_min,
        "typical_price_max": cm.typical_price_max,
        "image_url": cm.image_url,  # Legacy field
        "difficulty_score": cm.difficulty_score,
        "difficulty_factors": cm.difficulty_factors,
        "ai_confidence": cm.ai_confidence,
        "verified_by": cm.verified_by,
        "status": cm.status,
        # Sprint 0: 공공데이터 필드
        "standard_code": cm.standard_code,
        "category_1": cm.category_1,
        "category_2": cm.category_2,
        "serving_size": cm.serving_size,
        "has_nutrition": bool(cm.nutrition_info and cm.nutrition_info != {}),
    }

    if include_enriched:
        # Sprint 2 Phase 1 enriched fields
        enriched_fields = {
            "primary_image": cm.primary_image,
            "images": cm.images or [],
            "description_long_ko": cm.description_long_ko,
            "description_long_en": cm.description_long_en,
            "regional_variants": cm.regional_variants,
            "preparation_steps": cm.preparation_steps,
            "nutrition_detail": cm.nutrition_detail,
            "flavor_profile": cm.flavor_profile,
            "visitor_tips": cm.visitor_tips,
            "similar_dishes": cm.similar_dishes or [],
            "content_completeness": float(cm.content_completeness) if cm.content_completeness else 0.0,
        }
        base_fields.update(enriched_fields)

    return base_fields


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
async def get_canonical_menus(
    db: AsyncSession = Depends(get_db),
    include_enriched: bool = False
):
    """
    Get all canonical menus (표준 메뉴 조회)

    Query Parameters:
        include_enriched: If True, include Sprint 2 Phase 1 enriched fields
    """
    result = await db.execute(select(CanonicalMenu).order_by(CanonicalMenu.name_ko))
    menus = result.scalars().all()

    return {
        "total": len(menus),
        "data": [
            _serialize_canonical_menu(cm, include_enriched=include_enriched)
            for cm in menus
        ],
    }


@router.get("/canonical-menus/{menu_id}")
async def get_canonical_menu_by_id(
    menu_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get single canonical menu by ID with full enriched content

    Sprint 2 Phase 2: Returns all fields including:
    - primary_image, images
    - description_long_ko, description_long_en
    - regional_variants, preparation_steps, nutrition_detail
    - flavor_profile, visitor_tips, similar_dishes (with full objects)
    - content_completeness
    """
    result = await db.execute(
        select(CanonicalMenu).where(CanonicalMenu.id == menu_id)
    )
    menu = result.scalar_one_or_none()

    if not menu:
        raise HTTPException(status_code=404, detail=f"Menu not found: {menu_id}")

    # Serialize menu data
    menu_data = _serialize_canonical_menu(menu, include_enriched=True)

    # Resolve similar_dishes to full objects (Sprint 2 Phase 2)
    if menu.similar_dishes:
        menu_data['similar_dishes'] = await _resolve_similar_dishes(menu.similar_dishes, db)

    return menu_data


@router.get("/canonical-menus/{menu_id}/images")
async def get_canonical_menu_images(
    menu_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get images only for a canonical menu (Sprint 2 Phase 1)

    Useful for gallery views, image carousels, etc.

    Returns:
        {
            "menu_id": "uuid",
            "menu_name_ko": "김치찌개",
            "primary_image": {...},
            "images": [{...}, {...}],
            "total_images": 3,
            "legacy_image_url": "..." (for backward compatibility)
        }
    """
    result = await db.execute(
        select(CanonicalMenu).where(CanonicalMenu.id == menu_id)
    )
    menu = result.scalar_one_or_none()

    if not menu:
        raise HTTPException(status_code=404, detail=f"Menu not found: {menu_id}")

    # Count total images
    total_images = 0
    if menu.primary_image:
        total_images += 1
    if menu.images:
        total_images += len(menu.images)

    return {
        "menu_id": str(menu.id),
        "menu_name_ko": menu.name_ko,
        "menu_name_en": menu.name_en,
        "primary_image": menu.primary_image,
        "images": menu.images or [],
        "total_images": total_images,
        "legacy_image_url": menu.image_url,  # Backward compatibility
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


@router.post("/menu/recognize")
async def recognize_menu_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    OCR 메뉴 인식 API (Sprint 3 - P0-1)

    Flow:
    1. Upload menu image
    2. CLOVA OCR → Extract text
    3. GPT-4o → Parse menu items (name_ko, price_ko)
    4. Return structured menu list

    Returns:
        {
            "success": bool,
            "menu_items": [{"name_ko": str, "price_ko": str}, ...],
            "raw_text": str,
            "ocr_confidence": float
        }
    """
    # Read file bytes
    content = await file.read()

    # Validate image format, size, dimensions
    try:
        img_format, width, height = validate_image(content)
        logger.info(f"✅ Image validated: {img_format} {width}x{height}")
    except ImageValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image: {str(e)}"
        )

    # Save uploaded file temporarily
    temp_path = None
    try:
        # Create temp file with validated format
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{img_format.lower()}") as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        # Process with OCR service
        result = ocr_service.recognize_menu_image(temp_path)

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "OCR processing failed")
            )

        return {
            "success": True,
            "menu_items": result["menu_items"],
            "raw_text": result.get("raw_text", ""),
            "ocr_confidence": result.get("ocr_confidence", 0.0),
            "count": len(result["menu_items"])
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )
    finally:
        # Clean up temp file (Bug #3 Fix: Log errors instead of silent failure)
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.debug(f"Cleaned up temp file: {temp_path}")
            except PermissionError as e:
                logger.error(f"Permission denied when deleting temp file {temp_path}: {e}")
                # On Windows, file might be locked. Try delayed cleanup
                try:
                    import atexit
                    atexit.register(lambda: os.remove(temp_path) if os.path.exists(temp_path) else None)
                    logger.info(f"Scheduled delayed cleanup for {temp_path}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to schedule delayed cleanup: {cleanup_error}")
            except Exception as e:
                logger.error(f"Error deleting temp file {temp_path}: {e}")
                # File remains on disk - log for manual cleanup
                logger.warning(f"DISK LEAK WARNING: Temp file not deleted: {temp_path}")
