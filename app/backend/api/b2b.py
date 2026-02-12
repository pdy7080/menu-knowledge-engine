"""
B2B API Routes - 식당 등록 및 관리
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
import uuid

from database import get_db
from models.restaurant import Restaurant, RestaurantStatus

router = APIRouter(prefix="/api/v1/b2b", tags=["b2b"])


class RestaurantCreateRequest(BaseModel):
    """식당 등록 요청"""
    name: str
    name_en: Optional[str] = None
    owner_name: str
    owner_phone: str
    owner_email: Optional[EmailStr] = None
    address: str
    address_detail: Optional[str] = None
    postal_code: Optional[str] = None
    business_license: str
    business_type: Optional[str] = "Korean"


class RestaurantApprovalRequest(BaseModel):
    """식당 승인/거부 요청"""
    action: str  # "approve" or "reject"
    admin_user_id: str
    rejection_reason: Optional[str] = None


@router.post("/restaurants")
async def register_restaurant(
    request: RestaurantCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    B2B 식당 등록 API

    사장님이 직접 식당을 등록하면 승인 대기 상태로 생성됨
    Admin이 승인 후 활성화
    """
    # 1. 사업자 번호 중복 확인
    existing = await db.execute(
        select(Restaurant).where(
            Restaurant.business_license == request.business_license
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=400,
            detail=f"Business license {request.business_license} already registered"
        )

    # 2. 식당 생성
    restaurant = Restaurant(
        name=request.name,
        name_en=request.name_en,
        owner_name=request.owner_name,
        owner_phone=request.owner_phone,
        owner_email=request.owner_email,
        address=request.address,
        address_detail=request.address_detail,
        postal_code=request.postal_code,
        business_license=request.business_license,
        business_type=request.business_type,
        status=RestaurantStatus.pending_approval
    )

    db.add(restaurant)
    await db.commit()
    await db.refresh(restaurant)

    return {
        "success": True,
        "restaurant_id": str(restaurant.id),
        "status": restaurant.status,
        "message": "Restaurant registered. Waiting for admin approval.",
        "approval_url": f"http://localhost:8000/admin/restaurants/{restaurant.id}"
    }


@router.get("/restaurants/{restaurant_id}")
async def get_restaurant(
    restaurant_id: str,
    db: AsyncSession = Depends(get_db)
):
    """식당 정보 조회"""
    result = await db.execute(
        select(Restaurant).where(Restaurant.id == uuid.UUID(restaurant_id))
    )
    restaurant = result.scalars().first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return {
        "id": str(restaurant.id),
        "name": restaurant.name,
        "name_en": restaurant.name_en,
        "owner_name": restaurant.owner_name,
        "owner_phone": restaurant.owner_phone,
        "owner_email": restaurant.owner_email,
        "address": restaurant.address,
        "address_detail": restaurant.address_detail,
        "postal_code": restaurant.postal_code,
        "business_license": restaurant.business_license,
        "business_type": restaurant.business_type,
        "status": restaurant.status,
        "created_at": restaurant.created_at.isoformat() if restaurant.created_at else None,
        "approved_at": restaurant.approved_at.isoformat() if restaurant.approved_at else None,
    }


@router.post("/restaurants/{restaurant_id}/approve")
async def approve_restaurant(
    restaurant_id: str,
    request: RestaurantApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    식당 승인/거부 API (Admin Only)
    """
    # 1. 식당 조회
    result = await db.execute(
        select(Restaurant).where(Restaurant.id == uuid.UUID(restaurant_id))
    )
    restaurant = result.scalars().first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # 2. 승인/거부 처리
    if request.action == "approve":
        restaurant.status = RestaurantStatus.active
        restaurant.approved_at = datetime.utcnow()
        restaurant.approved_by = request.admin_user_id
        message = f"Restaurant '{restaurant.name}' approved and activated"

    elif request.action == "reject":
        restaurant.status = RestaurantStatus.rejected
        restaurant.rejection_reason = request.rejection_reason
        message = f"Restaurant '{restaurant.name}' rejected"

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {request.action}. Use 'approve' or 'reject'"
        )

    await db.commit()

    return {
        "success": True,
        "restaurant_id": str(restaurant.id),
        "status": restaurant.status,
        "message": message
    }


@router.get("/restaurants")
async def list_restaurants(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """식당 목록 조회 (Admin)"""
    query = select(Restaurant).order_by(Restaurant.created_at.desc())

    # 상태 필터
    if status:
        query = query.where(Restaurant.status == status)

    # 전체 카운트
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 페이징
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    restaurants = result.scalars().all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [
            {
                "id": str(r.id),
                "name": r.name,
                "name_en": r.name_en,
                "owner_name": r.owner_name,
                "owner_phone": r.owner_phone,
                "business_license": r.business_license,
                "business_type": r.business_type,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in restaurants
        ]
    }
