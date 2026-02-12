"""
Menu API Routes
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
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
