"""
Admin API Routes - Sprint 3 P1-1
신규 메뉴 큐 관리 + 엔진 모니터링
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from database import get_db
from models import ScanLog, CanonicalMenu, Modifier, MenuVariant
import uuid

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
    db: AsyncSession = Depends(get_db)
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
                select(CanonicalMenu).where(CanonicalMenu.id == log.matched_canonical_id)
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

    return {
        "total": total,
        "data": data,
        "limit": limit,
        "offset": offset
    }


@router.post("/queue/{queue_id}/approve")
async def approve_menu_queue(
    queue_id: str,
    request: QueueApproveRequest,
    db: AsyncSession = Depends(get_db)
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
    result = await db.execute(
        select(ScanLog).where(ScanLog.id == uuid.UUID(queue_id))
    )
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
            "message": f"Menu '{scan_log.menu_name_ko}' approved and added to knowledge base"
        }

    elif request.action == "reject":
        # Reject: Mark as rejected
        scan_log.status = "rejected"
        scan_log.reviewed_at = datetime.utcnow()
        scan_log.review_notes = request.notes

        await db.commit()

        return {
            "success": True,
            "message": f"Menu '{scan_log.menu_name_ko}' rejected"
        }

    elif request.action == "edit":
        # Edit: Create new canonical menu
        if not request.canonical_menu_id:
            raise HTTPException(
                status_code=400,
                detail="canonical_menu_id required for edit action"
            )

        # Link to canonical
        scan_log.matched_canonical_id = uuid.UUID(request.canonical_menu_id)
        scan_log.status = "confirmed"
        scan_log.reviewed_at = datetime.utcnow()
        scan_log.review_notes = request.notes

        await db.commit()

        return {
            "success": True,
            "message": f"Menu '{scan_log.menu_name_ko}' linked to canonical menu"
        }

    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")


@router.get("/stats")
async def get_engine_stats(db: AsyncSession = Depends(get_db)):
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
    # 1. Canonical count
    canonical_result = await db.execute(select(func.count(CanonicalMenu.id)))
    canonical_count = canonical_result.scalar()

    # 2. Modifier count
    modifier_result = await db.execute(select(func.count(Modifier.id)))
    modifier_count = modifier_result.scalar()

    # 3. Pending queue count
    pending_result = await db.execute(
        select(func.count(ScanLog.id)).where(
            or_(
                ScanLog.status == "pending",
                ScanLog.status.is_(None)
            )
        )
    )
    pending_count = pending_result.scalar()

    # 4. 7일 통계
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    # Scans in last 7 days
    scans_7d_result = await db.execute(
        select(func.count(ScanLog.id)).where(
            ScanLog.created_at >= seven_days_ago
        )
    )
    scans_7d = scans_7d_result.scalar()

    # DB hit rate (scans with matched_canonical_id)
    hits_7d_result = await db.execute(
        select(func.count(ScanLog.id)).where(
            and_(
                ScanLog.created_at >= seven_days_ago,
                ScanLog.matched_canonical_id.isnot(None)
            )
        )
    )
    hits_7d = hits_7d_result.scalar()
    db_hit_rate_7d = hits_7d / scans_7d if scans_7d > 0 else 0.0

    # Average confidence (last 7 days)
    avg_conf_result = await db.execute(
        select(func.avg(ScanLog.confidence)).where(
            ScanLog.created_at >= seven_days_ago
        )
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
                ScanLog.evidences.contains({"ai_called": True})  # JSONB query
            )
        )
    )
    ai_calls_7d = ai_calls_7d_result.scalar() or 0
    ai_cost_7d = ai_calls_7d * 0.00009 * 1300  # KRW

    return {
        "canonical_count": canonical_count,
        "modifier_count": modifier_count,
        "pending_queue_count": pending_count,
        "scans_7d": scans_7d,
        "db_hit_rate_7d": round(db_hit_rate_7d, 3),
        "avg_confidence_7d": round(float(avg_confidence_7d), 3),
        "ai_cost_7d": round(ai_cost_7d, 0),  # ₩
    }
