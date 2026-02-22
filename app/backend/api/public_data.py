"""
Sprint 0: 공공데이터 API 라우터
- GET  /api/v1/menu/nutrition/{canonical_id}
- GET  /api/v1/menu/category-search
- GET  /api/v1/menu/by-standard-code/{code}
- POST /api/v1/public-data/sync
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from database import get_db
from models.canonical_menu import CanonicalMenu
from services.nutrition_cache import nutrition_cache

router = APIRouter(prefix="/api/v1", tags=["public-data"])


# ========== 1. 영양정보 조회 ==========


@router.get("/menu/nutrition/{canonical_id}")
async def get_nutrition(
    canonical_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    메뉴 영양정보 조회
    3단계 fallback: Redis 캐시 → DB → 공공데이터 API
    """
    result = await nutrition_cache.get_nutrition(canonical_id, db)

    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "nutrition_not_found",
                "message": f"No nutrition data for menu: {canonical_id}",
            },
        )

    return {
        "canonical_id": str(canonical_id),
        "nutrition": result.get("nutrition", {}),
        "serving_size": result.get("serving_size"),
        "cache_info": {
            "source": result.get("source", "unknown"),
            "cached": result.get("cached", False),
            "last_updated": result.get("last_updated"),
        },
    }


# ========== 2. 카테고리 검색 ==========


@router.get("/menu/category-search")
async def category_search(
    category_1: Optional[str] = Query(None, description="대분류 (예: 한식, 중식)"),
    category_2: Optional[str] = Query(None, description="중분류 (예: 찌개류, 구이류)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    카테고리 기반 메뉴 검색
    정부 표준 분류 체계 사용
    """
    if not category_1 and not category_2:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_category",
                "message": "At least one of category_1 or category_2 is required",
            },
        )

    query = select(CanonicalMenu)

    if category_1:
        query = query.where(CanonicalMenu.category_1 == category_1)
    if category_2:
        query = query.where(CanonicalMenu.category_2 == category_2)

    # Count
    count_query = select(CanonicalMenu.id)
    if category_1:
        count_query = count_query.where(CanonicalMenu.category_1 == category_1)
    if category_2:
        count_query = count_query.where(CanonicalMenu.category_2 == category_2)
    count_result = await db.execute(count_query)
    total = len(count_result.all())

    # Paginate
    offset = (page - 1) * per_page
    query = query.order_by(CanonicalMenu.name_ko).offset(offset).limit(per_page)

    result = await db.execute(query)
    menus = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "data": [
            {
                "id": str(m.id),
                "name_ko": m.name_ko,
                "name_en": m.name_en,
                "category_1": m.category_1,
                "category_2": m.category_2,
                "standard_code": m.standard_code,
                "serving_size": m.serving_size,
                "has_nutrition": bool(m.nutrition_info and m.nutrition_info != {}),
            }
            for m in menus
        ],
    }


# ========== 3. 표준코드 조회 ==========


@router.get("/menu/by-standard-code/{code}")
async def get_by_standard_code(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    정부 표준 음식코드로 메뉴 조회
    메뉴젠 API의 FOOD_CD로 매핑
    """
    result = await db.execute(
        select(CanonicalMenu).where(CanonicalMenu.standard_code == code)
    )
    menu = result.scalar_one_or_none()

    if not menu:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "invalid_standard_code",
                "message": f"No menu found for code: {code}",
            },
        )

    return {
        "id": str(menu.id),
        "standard_code": menu.standard_code,
        "name_ko": menu.name_ko,
        "name_en": menu.name_en,
        "category_1": menu.category_1,
        "category_2": menu.category_2,
        "serving_size": menu.serving_size,
        "has_nutrition": bool(menu.nutrition_info and menu.nutrition_info != {}),
    }


# ========== 4. 공공데이터 동기화 (Admin) ==========


class SyncRequest(BaseModel):
    admin_key: str
    limit: int = 50


@router.post("/public-data/sync")
async def sync_public_data(
    request: SyncRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    공공데이터 동기화 (Admin 전용)
    영양정보가 없는 메뉴에 대해 공공데이터 API 호출
    """
    from config import settings

    if request.admin_key != settings.SECRET_KEY:
        raise HTTPException(
            status_code=403,
            detail={"error": "invalid_admin_key", "message": "Invalid admin key"},
        )

    # 영양정보가 없는 메뉴 조회
    query = (
        select(CanonicalMenu)
        .where(
            (CanonicalMenu.nutrition_info.is_(None))
            | (CanonicalMenu.nutrition_info == {})
        )
        .order_by(CanonicalMenu.name_ko)
        .limit(request.limit)
    )
    result = await db.execute(query)
    menus = result.scalars().all()

    if not menus:
        return {
            "status": "complete",
            "message": "All menus have nutrition data",
            "processed": 0,
        }

    success = 0
    failed = 0

    for menu in menus:
        try:
            nutrition_data = await nutrition_cache.get_nutrition(menu.id, db)
            if nutrition_data:
                success += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    return {
        "status": "completed",
        "processed": len(menus),
        "success": success,
        "failed": failed,
        "remaining": await _count_without_nutrition(db),
    }


async def _count_without_nutrition(db: AsyncSession) -> int:
    """영양정보 없는 메뉴 수 카운트"""
    result = await db.execute(
        select(CanonicalMenu.id).where(
            (CanonicalMenu.nutrition_info.is_(None))
            | (CanonicalMenu.nutrition_info == {})
        )
    )
    return len(result.all())
