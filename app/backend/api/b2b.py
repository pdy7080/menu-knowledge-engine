"""
B2B API Routes - 식당 등록 및 관리
"""

import json
import logging
import tempfile
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
import uuid

from database import get_db
from models.restaurant import Restaurant, RestaurantStatus
from services.cache_service import cache_service, TTL_RESTAURANT_INFO
from services.menu_approval_service import MenuApprovalService
from services.menu_upload_service import MenuUploadService
from services.ocr_orchestrator import ocr_orchestrator
from services.qr_code_service import QRCodeService
from utils.image_validation import validate_image

logger = logging.getLogger(__name__)

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


class MenuApprovalRequest(BaseModel):
    """메뉴 확정 승인 요청"""

    admin_user_id: str
    selected_menu_ids: List[str]  # UUID strings


@router.post("/restaurants")
async def register_restaurant(
    request: RestaurantCreateRequest, db: AsyncSession = Depends(get_db)
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
            detail=f"Business license {request.business_license} already registered",
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
        status=RestaurantStatus.pending_approval,
    )

    db.add(restaurant)
    await db.commit()
    await db.refresh(restaurant)

    return {
        "success": True,
        "restaurant_id": str(restaurant.id),
        "status": restaurant.status,
        "message": "Restaurant registered. Waiting for admin approval.",
        "approval_url": f"http://localhost:8000/admin/restaurants/{restaurant.id}",
    }


@router.get("/restaurants/{restaurant_id}")
async def get_restaurant(restaurant_id: str, db: AsyncSession = Depends(get_db)):
    """식당 정보 조회 (Redis 캐싱, TTL: 1시간)"""
    # Check cache first
    cache_key = f"restaurant:{restaurant_id}"
    cached_data = await cache_service.get(cache_key)
    if cached_data is not None:
        return cached_data

    # Query database
    result = await db.execute(
        select(Restaurant).where(Restaurant.id == uuid.UUID(restaurant_id))
    )
    restaurant = result.scalars().first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant_data = {
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
        "created_at": (
            restaurant.created_at.isoformat() if restaurant.created_at else None
        ),
        "approved_at": (
            restaurant.approved_at.isoformat() if restaurant.approved_at else None
        ),
    }

    # Save to cache (1 hour TTL)
    await cache_service.set(cache_key, restaurant_data, TTL_RESTAURANT_INFO)

    return restaurant_data


@router.post("/restaurants/{restaurant_id}/approve")
async def approve_restaurant(
    restaurant_id: str,
    request: RestaurantApprovalRequest,
    db: AsyncSession = Depends(get_db),
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
            detail=f"Invalid action: {request.action}. Use 'approve' or 'reject'",
        )

    await db.commit()

    # Invalidate restaurant cache
    cache_key = f"restaurant:{restaurant_id}"
    await cache_service.delete(cache_key)

    return {
        "success": True,
        "restaurant_id": str(restaurant.id),
        "status": restaurant.status,
        "message": message,
    }


@router.get("/restaurants")
async def list_restaurants(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
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
        ],
    }


@router.post("/restaurants/{restaurant_id}/menus/upload")
async def upload_menus(
    restaurant_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """
    B2B 메뉴 일괄 업로드 API

    CSV 또는 JSON 파일로 메뉴를 일괄 등록
    - 자동 번역 (GPT-4o-mini)
    - 중복 체크
    - 에러 처리 및 재시도
    """
    try:
        # MenuUploadService 인스턴스 생성
        service = MenuUploadService(db)

        # 파일 처리
        upload_task = await service.process_upload(
            restaurant_id=uuid.UUID(restaurant_id), file=file
        )

        return {
            "success": True,
            "upload_task_id": str(upload_task.id),
            "file_name": upload_task.file_name,
            "file_type": upload_task.file_type,
            "status": upload_task.status,
            "total_menus": upload_task.total_menus,
            "successful": upload_task.successful,
            "failed": upload_task.failed,
            "skipped": upload_task.skipped,
            "created_at": (
                upload_task.created_at.isoformat() if upload_task.created_at else None
            ),
            "started_at": (
                upload_task.started_at.isoformat() if upload_task.started_at else None
            ),
            "completed_at": (
                upload_task.completed_at.isoformat()
                if upload_task.completed_at
                else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Menu upload failed: {str(e)}")


@router.get("/restaurants/{restaurant_id}/menus/upload/{upload_task_id}")
async def get_upload_task(
    restaurant_id: str, upload_task_id: str, db: AsyncSession = Depends(get_db)
):
    """
    업로드 작업 조회 API

    업로드 진행 상황 및 결과 확인
    """
    from models.menu_upload import MenuUploadTask, MenuUploadDetail

    # Upload Task 조회
    result = await db.execute(
        select(MenuUploadTask).where(
            MenuUploadTask.id == uuid.UUID(upload_task_id),
            MenuUploadTask.restaurant_id == uuid.UUID(restaurant_id),
        )
    )
    upload_task = result.scalars().first()

    if not upload_task:
        raise HTTPException(status_code=404, detail="Upload task not found")

    # Details 조회
    details_result = await db.execute(
        select(MenuUploadDetail)
        .where(MenuUploadDetail.upload_task_id == uuid.UUID(upload_task_id))
        .order_by(MenuUploadDetail.row_number)
    )
    details = details_result.scalars().all()

    return {
        "upload_task": {
            "id": str(upload_task.id),
            "restaurant_id": str(upload_task.restaurant_id),
            "file_name": upload_task.file_name,
            "file_type": upload_task.file_type,
            "status": upload_task.status,
            "total_menus": upload_task.total_menus,
            "successful": upload_task.successful,
            "failed": upload_task.failed,
            "skipped": upload_task.skipped,
            "error_log": upload_task.error_log,
            "created_at": (
                upload_task.created_at.isoformat() if upload_task.created_at else None
            ),
            "started_at": (
                upload_task.started_at.isoformat() if upload_task.started_at else None
            ),
            "completed_at": (
                upload_task.completed_at.isoformat()
                if upload_task.completed_at
                else None
            ),
        },
        "details": [
            {
                "id": str(d.id),
                "name_ko": d.name_ko,
                "name_en": d.name_en,
                "price": d.price,
                "status": d.status,
                "error_message": d.error_message,
                "created_menu_id": (
                    str(d.created_menu_id) if d.created_menu_id else None
                ),
                "row_number": d.row_number,
            }
            for d in details
        ],
    }


@router.post("/restaurants/{restaurant_id}/menus/approve")
async def approve_restaurant_menus(
    restaurant_id: str, request: MenuApprovalRequest, db: AsyncSession = Depends(get_db)
):
    """
    B2B 메뉴 확정 승인 API

    식당에서 업로드한 메뉴를 최종 검증 후 승인하고 QR 코드 생성

    검증 항목:
    1. Restaurant 존재 확인
    2. Status = pending_approval 확인
    3. 최소 1개 이상 메뉴 선택 확인
    4. 모든 선택 메뉴의 번역 완료 확인 (KO, EN, JA, ZH)
    5. 필수 필드 존재 확인
    6. Price > 0 검증
    7. 메뉴 이름 중복 확인
    """
    try:
        # UUID 변환
        restaurant_uuid = uuid.UUID(restaurant_id)
        menu_uuids = [uuid.UUID(mid) for mid in request.selected_menu_ids]

        # 1. 메뉴 승인 처리
        approval_service = MenuApprovalService(db)
        approval_result = await approval_service.approve_menus(
            restaurant_uuid, menu_uuids, request.admin_user_id
        )

        restaurant = approval_result["restaurant"]
        menus = approval_result["menus"]
        approved_count = approval_result["approved_menu_count"]

        # 2. QR 코드 생성
        qr_service = QRCodeService()

        # shop_code 생성 (restaurant_id 기반)
        shop_code = f"SHOP{str(restaurant.id)[:8].upper()}"

        qr_result = qr_service.generate_qr(
            restaurant_id=restaurant.id,
            shop_code=shop_code,
            menu_count=approved_count,
            languages=["ko", "en", "ja", "zh"],
        )

        # 3. 응답 반환
        return {
            "success": True,
            "message": f"Restaurant '{restaurant.name}' approved with {approved_count} menus",
            "restaurant": {
                "id": str(restaurant.id),
                "name": restaurant.name,
                "status": restaurant.status,
                "approved_at": (
                    restaurant.approved_at.isoformat()
                    if restaurant.approved_at
                    else None
                ),
                "approved_by": restaurant.approved_by,
            },
            "approved_menus": {
                "count": approved_count,
                "menu_ids": [str(m.id) for m in menus],
            },
            "qr_code": {
                "shop_code": shop_code,
                "qr_code_url": qr_result["qr_code_url"],
                "qr_code_file_path": qr_result["qr_code_file_path"],
                "activation_date": qr_result["activation_date"],
                "languages": qr_result["languages"],
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Menu approval failed: {str(e)}")


@router.post("/restaurants/{restaurant_id}/menus/upload-images")
async def bulk_upload_menu_images(
    restaurant_id: str,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    B2B 메뉴 이미지 벌크 업로드 API (Sprint 4 - OCR Tier Router)

    식당에서 다중 메뉴 이미지를 한 번에 업로드

    Flow (Tier-based OCR):
    1. 각 이미지 검증 (format, size, dimensions)
    2. OCR 분석 (Tier Router: GPT Vision → CLOVA fallback)
       - Tier 1: GPT-4o mini Vision (빠른 처리, JSON 구조화)
       - Tier 2: CLOVA OCR (Tier 1 실패 시, 한글 특화)
    3. 결과 캐싱 (해시 기반, 30일 TTL)
    4. ScanLog에 저장
    5. MenuUploadTask로 진행 상황 추적

    Args:
        restaurant_id: 식당 UUID
        files: 업로드할 이미지 파일 리스트

    Returns:
        {
            "success": bool,
            "task_id": str,
            "total": int,
            "successful": int,
            "failed": int,
            "results": [
                {
                    "file": str,
                    "status": "success" | "failed",
                    "provider": "gpt_vision" | "clova" | null,
                    "menu_count": int,
                    "confidence": float,
                    "fallback_triggered": bool,
                    "processing_time_ms": int,
                    "error": str (if failed)
                }
            ]
        }
    """
    from datetime import timezone
    from models.menu_upload import MenuUploadTask
    from models.scan_log import ScanLog
    from utils.image_validation import ImageValidationError

    # 1. 업로드 작업 생성
    task = MenuUploadTask(
        id=uuid.uuid4(),
        restaurant_id=uuid.UUID(restaurant_id),
        file_name=f"bulk_upload_{len(files)}_images.zip",
        file_type="images",
        total_menus=len(files),
        status="processing",
        started_at=datetime.now(timezone.utc),
    )
    db.add(task)
    await db.commit()

    successful = 0
    failed = 0
    results = []

    # 2. 각 이미지 처리
    for idx, file in enumerate(files):
        temp_path = None

        try:
            # 2-1. 파일 읽기
            content = await file.read()

            # 2-2. 이미지 검증
            try:
                img_format, width, height = validate_image(content)
            except ImageValidationError as e:
                failed += 1
                results.append(
                    {
                        "file": file.filename,
                        "status": "failed",
                        "error": f"Invalid image: {str(e)}",
                    }
                )
                continue

            # 2-3. 임시 파일 저장
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{img_format.lower()}"
            ) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name

            # 2-4. OCR 분석 (Tier Router 사용)
            ocr_result = await ocr_orchestrator.extract_menu(
                image_path=temp_path,
                enable_preprocessing=True,
                use_cache=True,  # 캐싱 활성화
            )

            # 2-5. 결과 처리
            if ocr_result.success and ocr_result.menu_items:
                # 각 메뉴 아이템을 ScanLog에 저장
                for item in ocr_result.menu_items:
                    scan_log = ScanLog(
                        id=uuid.uuid4(),
                        session_id=f"b2b_upload_{task.id}",
                        language="ko",
                        menu_name_ko=item.name_ko,
                        ocr_raw_text=ocr_result.raw_text,
                        confidence=ocr_result.confidence,
                        shop_id=uuid.UUID(restaurant_id),
                        status="pending",
                        evidences={
                            "source": "b2b_bulk_upload",
                            "file_name": file.filename,
                            "price": item.price,
                            "ocr_provider": (
                                ocr_result.provider.value
                                if ocr_result.provider
                                else None
                            ),
                            "fallback_triggered": ocr_result.triggered_fallback,
                            "fallback_reason": ocr_result.fallback_reason,
                        },
                    )
                    db.add(scan_log)

                successful += 1
                results.append(
                    {
                        "file": file.filename,
                        "status": "success",
                        "provider": (
                            ocr_result.provider.value if ocr_result.provider else None
                        ),
                        "menu_count": len(ocr_result.menu_items),
                        "confidence": float(ocr_result.confidence),
                        "fallback_triggered": ocr_result.triggered_fallback,
                        "processing_time_ms": ocr_result.processing_time_ms,
                    }
                )

            else:
                failed += 1
                results.append(
                    {
                        "file": file.filename,
                        "status": "failed",
                        "error": f"OCR failed: {ocr_result.raw_text or 'Unknown error'}",
                    }
                )

        except Exception as e:
            failed += 1
            logger.error(f"Error processing {file.filename}: {e}", exc_info=True)
            results.append({"file": file.filename, "status": "failed", "error": str(e)})

        finally:
            # Cleanup
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    # 전처리된 이미지도 정리
                    base, _ = os.path.splitext(temp_path)
                    preprocessed = f"{base}_preprocessed.jpg"
                    if os.path.exists(preprocessed):
                        os.remove(preprocessed)
                except Exception as e:
                    logger.warning(f"Failed to cleanup {temp_path}: {e}")

    # 3. 작업 완료 업데이트
    task.successful = successful
    task.failed = failed
    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)
    task.error_log = (
        json.dumps([r for r in results if r["status"] == "failed"])
        if failed > 0
        else None
    )

    await db.commit()

    return {
        "success": True,
        "task_id": str(task.id),
        "total": len(files),
        "successful": successful,
        "failed": failed,
        "results": results,
    }
