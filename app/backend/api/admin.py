"""
Admin API Routes - Sprint 3 P1-1 + Sprint 4 OCR Metrics + Multi-Language Auto-Translation
신규 메뉴 큐 관리 + 엔진 모니터링 + OCR Tier 메트릭 + 자동 번역
"""

import os
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from database import get_db
from models import ScanLog, CanonicalMenu, Modifier
from services.cache_service import cache_service, TTL_ADMIN_STATS
from services.ocr_orchestrator import ocr_orchestrator
from services.auto_translate_service import get_auto_translate_service
from schemas.canonical_menu import (
    CanonicalMenuCreate,
    CanonicalMenuResponse,
    TranslateRequest,
)

logger = logging.getLogger(__name__)

# ===========================
# Admin Authentication
# ===========================
_security = HTTPBearer()


def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> None:
    """Bearer token verification for all admin endpoints"""
    expected = os.environ.get("ADMIN_SECRET_KEY", "")
    if not expected or credentials.credentials != expected:
        raise HTTPException(status_code=403, detail="Forbidden")


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ===========================
# Request/Response Models
# ===========================
class QueueApproveRequest(BaseModel):
    """메뉴 승인 요청"""

    action: str  # approve, reject, edit
    canonical_menu_id: Optional[str] = None
    notes: Optional[str] = None


# ===========================
# Admin Endpoints
# ===========================
@router.get("/queue")
async def get_menu_queue(
    status: str = "all",  # all, pending, confirmed, rejected
    source: str = "all",  # all, b2c, b2b
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """
    신규 메뉴 큐 조회 (P1-1)

    B2C 스캔 + B2B 업로드된 메뉴 중 미검토 항목 조회

    Args:
        status: 필터 (all, pending, confirmed, rejected)
        source: 소스 (all, b2c, b2b)
        limit: 페이지 크기
        offset: 페이지 오프셋

    Returns:
        {
            "total": int,
            "data": [
                {
                    "id": str,
                    "menu_name_ko": str,
                    "source": str,  # "b2c" or "b2b"
                    "created_at": str,
                    "decomposition_result": {...},
                    "confidence": float,
                    "matched_canonical": {...} or null,
                    "status": str  # "pending", "confirmed", "rejected"
                }
            ]
        }
    """
    # Build query
    query = select(ScanLog).order_by(ScanLog.created_at.desc())

    # Status filter
    if status != "all":
        query = query.where(ScanLog.status == status)

    # Source filter (we'll need to add a source field to ScanLog)
    # For now, we'll use shop_id: null = b2c, not null = b2b
    if source == "b2c":
        query = query.where(ScanLog.shop_id.is_(None))
    elif source == "b2b":
        query = query.where(ScanLog.shop_id.isnot(None))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute
    result = await db.execute(query)
    scan_logs = result.scalars().all()

    # Format response
    data = []
    for log in scan_logs:
        item = {
            "id": str(log.id),
            "menu_name_ko": log.menu_name_ko,
            "source": "b2b" if log.shop_id else "b2c",
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "confidence": log.confidence or 0.0,
            "status": log.status or "pending",
        }

        # Get matched canonical if exists
        if log.matched_canonical_id:
            canonical_result = await db.execute(
                select(CanonicalMenu).where(
                    CanonicalMenu.id == log.matched_canonical_id
                )
            )
            canonical = canonical_result.scalars().first()
            if canonical:
                item["matched_canonical"] = {
                    "id": str(canonical.id),
                    "name_ko": canonical.name_ko,
                    "name_en": canonical.name_en,
                }
            else:
                item["matched_canonical"] = None
        else:
            item["matched_canonical"] = None

        # Get decomposition result from evidences
        # (For now, we'll leave this as placeholder)
        item["decomposition_result"] = log.evidences or {}

        data.append(item)

    return {"total": total, "data": data, "limit": limit, "offset": offset}


@router.post("/queue/{queue_id}/approve")
async def approve_menu_queue(
    queue_id: str,
    request: QueueApproveRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """
    신규 메뉴 큐 승인/거부 (P1-1)

    Args:
        queue_id: ScanLog ID
        request:
            - action: "approve" | "reject" | "edit"
            - canonical_menu_id: canonical ID (approve/edit 시)
            - notes: 관리자 메모

    Returns:
        {"success": bool, "message": str}
    """
    # Get scan log
    result = await db.execute(select(ScanLog).where(ScanLog.id == uuid.UUID(queue_id)))
    scan_log = result.scalars().first()

    if not scan_log:
        raise HTTPException(status_code=404, detail="Queue item not found")

    # Perform action
    if request.action == "approve":
        # Approve: Mark as confirmed
        scan_log.status = "confirmed"
        scan_log.reviewed_at = datetime.utcnow()
        scan_log.review_notes = request.notes

        # If canonical_menu_id provided, update link
        if request.canonical_menu_id:
            scan_log.matched_canonical_id = uuid.UUID(request.canonical_menu_id)

        await db.commit()

        return {
            "success": True,
            "message": f"Menu '{scan_log.menu_name_ko}' approved and added to knowledge base",
        }

    elif request.action == "reject":
        # Reject: Mark as rejected
        scan_log.status = "rejected"
        scan_log.reviewed_at = datetime.utcnow()
        scan_log.review_notes = request.notes

        await db.commit()

        return {"success": True, "message": f"Menu '{scan_log.menu_name_ko}' rejected"}

    elif request.action == "edit":
        # Edit: Create new canonical menu
        if not request.canonical_menu_id:
            raise HTTPException(
                status_code=400, detail="canonical_menu_id required for edit action"
            )

        # Link to canonical
        scan_log.matched_canonical_id = uuid.UUID(request.canonical_menu_id)
        scan_log.status = "confirmed"
        scan_log.reviewed_at = datetime.utcnow()
        scan_log.review_notes = request.notes

        await db.commit()

        return {
            "success": True,
            "message": f"Menu '{scan_log.menu_name_ko}' linked to canonical menu",
        }

    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")


@router.get("/stats")
async def get_engine_stats(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """
    엔진 모니터링 통계 (P1-1)

    Returns:
        {
            "canonical_count": int,      # 등록된 canonical 메뉴 수
            "modifier_count": int,        # 수식어 사전 크기
            "db_hit_rate_7d": float,      # 7일 DB 히트율 (0.0-1.0)
            "ai_cost_7d": float,          # 7일 AI 비용 (₩)
            "pending_queue_count": int,   # 미검토 큐 수
            "scans_7d": int,              # 7일 스캔 수
            "avg_confidence_7d": float,   # 7일 평균 신뢰도
        }
    """
    # Check cache first
    cache_key = "admin:stats"
    cached_stats = await cache_service.get(cache_key)
    if cached_stats is not None:
        return cached_stats

    # 1. Canonical count
    canonical_result = await db.execute(select(func.count(CanonicalMenu.id)))
    canonical_count = canonical_result.scalar()

    # 2. Modifier count
    modifier_result = await db.execute(select(func.count(Modifier.id)))
    modifier_count = modifier_result.scalar()

    # 3. Pending queue count
    pending_result = await db.execute(
        select(func.count(ScanLog.id)).where(
            or_(ScanLog.status == "pending", ScanLog.status.is_(None))
        )
    )
    pending_count = pending_result.scalar()

    # 4. 7일 통계
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    # Scans in last 7 days
    scans_7d_result = await db.execute(
        select(func.count(ScanLog.id)).where(ScanLog.created_at >= seven_days_ago)
    )
    scans_7d = scans_7d_result.scalar()

    # DB hit rate (scans with matched_canonical_id)
    hits_7d_result = await db.execute(
        select(func.count(ScanLog.id)).where(
            and_(
                ScanLog.created_at >= seven_days_ago,
                ScanLog.matched_canonical_id.isnot(None),
            )
        )
    )
    hits_7d = hits_7d_result.scalar()
    db_hit_rate_7d = hits_7d / scans_7d if scans_7d > 0 else 0.0

    # Average confidence (last 7 days)
    avg_conf_result = await db.execute(
        select(func.avg(ScanLog.confidence)).where(ScanLog.created_at >= seven_days_ago)
    )
    avg_confidence_7d = avg_conf_result.scalar() or 0.0

    # AI cost calculation (placeholder)
    # Assume: GPT-4o-mini = $0.00015 per 1K input tokens + $0.0006 per 1K output
    # Average: 200 input + 100 output = $0.00009 per call
    # Convert to KRW (1 USD = 1300 KRW)
    ai_calls_7d_result = await db.execute(
        select(func.count(ScanLog.id)).where(
            and_(
                ScanLog.created_at >= seven_days_ago,
                ScanLog.evidences.contains({"ai_called": True}),  # JSONB query
            )
        )
    )
    ai_calls_7d = ai_calls_7d_result.scalar() or 0
    ai_cost_7d = ai_calls_7d * 0.00009 * 1300  # KRW

    stats = {
        "canonical_count": canonical_count,
        "modifier_count": modifier_count,
        "pending_queue_count": pending_count,
        "scans_7d": scans_7d,
        "db_hit_rate_7d": round(db_hit_rate_7d, 3),
        "avg_confidence_7d": round(float(avg_confidence_7d), 3),
        "ai_cost_7d": round(ai_cost_7d, 0),  # ₩
    }

    # Save to cache (5 minutes TTL)
    await cache_service.set(cache_key, stats, TTL_ADMIN_STATS)

    return stats


@router.get("/ocr/metrics")
async def get_ocr_metrics(
    _: None = Depends(verify_admin_token),
):
    """
    OCR Tier Router 메트릭 조회 (Sprint 4)

    Tier 1 (GPT Vision) vs Tier 2 (CLOVA) 성능 비교

    Returns:
        {
            "tier_1_count": int,              # Tier 1로 처리한 이미지 수
            "tier_2_count": int,              # Tier 2로 폴백한 이미지 수
            "total_count": int,               # 전체 처리 이미지 수
            "tier_1_success_rate": str,       # Tier 1 성공률 (%)
            "tier_2_fallback_rate": str,      # Tier 2 폴백률 (%)
            "avg_processing_time_ms": float,  # 평균 처리 시간 (ms)
            "price_error_count": int,         # 가격 파싱 에러 수
            "price_error_rate": str,          # 가격 에러율 (%)
            "handwriting_detection_rate": str,# 손글씨 감지율 (%)
            "last_updated": str               # 마지막 업데이트 시간 (ISO 8601)
        }
    """
    metrics = await ocr_orchestrator.get_metrics()

    # Default values if no metrics yet
    if not metrics:
        metrics = {
            "tier_1_count": 0,
            "tier_2_count": 0,
            "total_count": 0,
            "avg_processing_time_ms": 0,
            "price_error_count": 0,
            "handwriting_count": 0,
        }

    return {
        "tier_1_count": metrics.get("tier_1_count", 0),
        "tier_2_count": metrics.get("tier_2_count", 0),
        "total_count": metrics.get("total_count", 0),
        "tier_1_success_rate": metrics.get("tier_1_success_rate", "0.0%"),
        "tier_2_fallback_rate": metrics.get("tier_2_fallback_rate", "0.0%"),
        "avg_processing_time_ms": metrics.get("avg_processing_time_ms", 0),
        "price_error_count": metrics.get("price_error_count", 0),
        "price_error_rate": metrics.get("price_error_rate", "0.0%"),
        "handwriting_detection_rate": metrics.get("handwriting_detection_rate", "0.0%"),
        "last_updated": metrics.get(
            "last_updated", datetime.utcnow().isoformat() + "Z"
        ),
    }


# ===========================
# Multi-Language Auto-Translation (Sprint 2 Phase 3)
# ===========================


async def _background_translate_menu(
    menu_id: uuid.UUID, menu_name_ko: str, description_en: str, db_url: str
):
    """
    Background task for auto-translation

    Note: BackgroundTasks runs after response is sent, so we need to create
    a new DB session here (can't reuse the request session which will be closed)
    """
    from database import AsyncSessionLocal
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        try:
            # Translate
            logger.info(f"🔄 Background translation started: {menu_name_ko}")
            translations = await get_auto_translate_service().auto_translate_new_menu(
                menu_id=menu_id,
                menu_name_ko=menu_name_ko,
                description_en=description_en,
                db=db,
            )

            # Update status
            result = await db.execute(
                select(CanonicalMenu).where(CanonicalMenu.id == menu_id)
            )
            menu = result.scalar_one_or_none()

            if menu:
                if translations and any(translations.values()):
                    menu.translation_status = "completed"
                    logger.info(f"✅ Translation completed: {menu_name_ko}")
                else:
                    menu.translation_status = "failed"
                    menu.translation_error = "No translations returned"
                    logger.warning(f"⚠️ Translation returned empty: {menu_name_ko}")

                menu.translation_attempted_at = datetime.utcnow()
                await db.commit()

        except Exception as e:
            logger.error(f"❌ Background translation failed: {menu_name_ko} - {e}")
            # Update error status
            try:
                result = await db.execute(
                    select(CanonicalMenu).where(CanonicalMenu.id == menu_id)
                )
                menu = result.scalar_one_or_none()
                if menu:
                    menu.translation_status = "failed"
                    menu.translation_error = str(e)[:500]  # Truncate long errors
                    menu.translation_attempted_at = datetime.utcnow()
                    await db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update error status: {update_error}")


@router.post("/canonical-menus", response_model=CanonicalMenuResponse)
async def create_canonical_menu(
    menu_data: CanonicalMenuCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """
    Create new canonical menu with auto-translation (Sprint 2 Phase 3)

    Flow:
    1. Create menu with English data
    2. Return immediate response with translation_status="pending"
    3. Background task translates to Japanese/Chinese
    4. Check menu later to see translation_status="completed"

    Note: Translation happens asynchronously. The response returns immediately
    with translation_status="pending". Check the menu again after ~3 seconds
    to see the translated content.
    """
    # Create canonical menu
    menu = CanonicalMenu(
        concept_id=menu_data.concept_id,
        name_ko=menu_data.name_ko,
        name_en=menu_data.name_en,
        name_ja=menu_data.name_ja,
        name_zh_cn=menu_data.name_zh_cn,
        name_zh_tw=menu_data.name_zh_tw,
        romanization=menu_data.romanization,
        explanation_short={"en": menu_data.explanation_short_en},
        main_ingredients=menu_data.main_ingredients or [],
        allergens=menu_data.allergens or [],
        dietary_tags=menu_data.dietary_tags or [],
        spice_level=menu_data.spice_level or 0,
        serving_style=menu_data.serving_style,
        typical_price_min=menu_data.typical_price_min,
        typical_price_max=menu_data.typical_price_max,
        translation_status="pending",
        verified_by="admin",
    )

    db.add(menu)
    await db.commit()
    await db.refresh(menu)

    logger.info(f"✅ Menu created: {menu.name_ko} (ID: {menu.id})")

    # Trigger background translation
    from config import settings

    background_tasks.add_task(
        _background_translate_menu,
        menu_id=menu.id,
        menu_name_ko=menu.name_ko,
        description_en=menu_data.explanation_short_en,
        db_url=settings.DATABASE_URL,
    )

    logger.info(f"🚀 Background translation queued: {menu.name_ko}")

    return CanonicalMenuResponse(
        id=menu.id,
        name_ko=menu.name_ko,
        name_en=menu.name_en,
        name_ja=menu.name_ja,
        name_zh_cn=menu.name_zh_cn,
        name_zh_tw=menu.name_zh_tw,
        romanization=menu.romanization,
        concept_id=menu.concept_id,
        explanation_short=menu.explanation_short,
        translation_status=menu.translation_status,
        translation_attempted_at=menu.translation_attempted_at,
        spice_level=menu.spice_level,
        created_at=menu.created_at,
    )


@router.post("/canonical-menus/{menu_id}/translate")
async def retranslate_menu(
    menu_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """
    Manually re-translate a single menu (Sprint 2 Phase 3)

    Use this to retry failed translations or update translations for existing menus.
    """
    # Get menu
    result = await db.execute(select(CanonicalMenu).where(CanonicalMenu.id == menu_id))
    menu = result.scalar_one_or_none()

    if not menu:
        raise HTTPException(status_code=404, detail=f"Menu not found: {menu_id}")

    # Check if menu has English description
    if not menu.explanation_short or not menu.explanation_short.get("en"):
        raise HTTPException(
            status_code=400,
            detail="Menu must have English description (explanation_short.en) to translate",
        )

    # Reset status to pending
    menu.translation_status = "pending"
    menu.translation_error = None
    await db.commit()

    # Trigger background translation
    from config import settings

    background_tasks.add_task(
        _background_translate_menu,
        menu_id=menu.id,
        menu_name_ko=menu.name_ko,
        description_en=menu.explanation_short["en"],
        db_url=settings.DATABASE_URL,
    )

    logger.info(f"🔄 Re-translation queued: {menu.name_ko}")

    return {
        "success": True,
        "message": f"Re-translation queued for menu: {menu.name_ko}",
        "menu_id": str(menu.id),
        "translation_status": "pending",
    }


@router.post("/canonical-menus/translate-all")
async def translate_all_menus(
    request: TranslateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """
    Bulk re-translate menus by status filter (Sprint 2 Phase 3)

    Query Parameters:
        status_filter: "failed" (default), "pending", or "all"

    Use cases:
        - Fix all failed translations: status_filter=failed
        - Translate all pending menus: status_filter=pending
        - Re-translate everything: status_filter=all (use with caution!)
    """
    # Build query
    query = select(CanonicalMenu)

    if request.status_filter == "failed":
        query = query.where(CanonicalMenu.translation_status == "failed")
    elif request.status_filter == "pending":
        query = query.where(CanonicalMenu.translation_status == "pending")
    elif request.status_filter == "all":
        # Re-translate everything
        pass
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status_filter: {request.status_filter}. Use 'failed', 'pending', or 'all'",
        )

    # Only translate menus with English description
    query = query.where(CanonicalMenu.explanation_short.op("?")("en"))

    result = await db.execute(query)
    menus = result.scalars().all()

    if not menus:
        return {
            "success": True,
            "message": f"No menus found with status_filter={request.status_filter}",
            "count": 0,
        }

    # Queue background translations
    from config import settings

    queued_count = 0
    for menu in menus:
        # Reset status
        menu.translation_status = "pending"
        menu.translation_error = None

        # Queue translation
        background_tasks.add_task(
            _background_translate_menu,
            menu_id=menu.id,
            menu_name_ko=menu.name_ko,
            description_en=menu.explanation_short.get("en", ""),
            db_url=settings.DATABASE_URL,
        )
        queued_count += 1

    await db.commit()

    logger.info(
        f"🚀 Bulk translation queued: {queued_count} menus (filter={request.status_filter})"
    )

    return {
        "success": True,
        "message": f"Queued {queued_count} menus for translation",
        "count": queued_count,
        "status_filter": request.status_filter,
    }
