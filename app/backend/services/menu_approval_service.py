"""
Menu Approval Service - B2B 메뉴 확정 승인 검증
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from models.restaurant import Restaurant, RestaurantStatus
from models.canonical_menu import CanonicalMenu
from models.menu_upload import MenuUploadTask


class MenuApprovalValidator:
    """메뉴 승인 검증 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.validation_errors: List[str] = []

    async def validate_approval(
        self, restaurant_id: uuid.UUID, selected_menu_ids: List[uuid.UUID]
    ) -> Dict[str, Any]:
        """
        메뉴 승인 7가지 검증 로직

        Returns:
            {
                "valid": bool,
                "errors": List[str],
                "restaurant": Restaurant,
                "menus": List[CanonicalMenu]
            }
        """
        self.validation_errors = []

        # 1. Restaurant 존재 확인
        restaurant = await self._validate_restaurant_exists(restaurant_id)
        if not restaurant:
            return {
                "valid": False,
                "errors": self.validation_errors,
                "restaurant": None,
                "menus": [],
            }

        # 2. Status = pending_approval 확인
        await self._validate_restaurant_status(restaurant)

        # 3. 최소 1개 이상 메뉴 선택 확인
        await self._validate_menu_selection(selected_menu_ids)

        # 4-7. 메뉴별 검증
        menus = await self._validate_menus(selected_menu_ids)

        is_valid = len(self.validation_errors) == 0

        return {
            "valid": is_valid,
            "errors": self.validation_errors,
            "restaurant": restaurant,
            "menus": menus,
        }

    async def _validate_restaurant_exists(
        self, restaurant_id: uuid.UUID
    ) -> Optional[Restaurant]:
        """1. Restaurant 존재 확인"""
        result = await self.db.execute(
            select(Restaurant).where(Restaurant.id == restaurant_id)
        )
        restaurant = result.scalars().first()

        if not restaurant:
            self.validation_errors.append(f"Restaurant {restaurant_id} not found")
            return None

        return restaurant

    async def _validate_restaurant_status(self, restaurant: Restaurant):
        """2. Status = pending_approval 확인"""
        if restaurant.status != RestaurantStatus.pending_approval.value:
            self.validation_errors.append(
                f"Restaurant status must be 'pending_approval', current: '{restaurant.status}'"
            )

    async def _validate_menu_selection(self, selected_menu_ids: List[uuid.UUID]):
        """3. 최소 1개 이상 메뉴 선택 확인"""
        if not selected_menu_ids or len(selected_menu_ids) == 0:
            self.validation_errors.append(
                "At least one menu must be selected for approval"
            )

    async def _validate_menus(
        self, selected_menu_ids: List[uuid.UUID]
    ) -> List[CanonicalMenu]:
        """4-7. 선택된 메뉴들 검증"""
        if not selected_menu_ids:
            return []

        # 메뉴 조회
        result = await self.db.execute(
            select(CanonicalMenu).where(CanonicalMenu.id.in_(selected_menu_ids))
        )
        menus = result.scalars().all()

        # 조회된 메뉴 수 확인
        if len(menus) != len(selected_menu_ids):
            found_ids = {str(m.id) for m in menus}
            missing_ids = [
                str(mid) for mid in selected_menu_ids if str(mid) not in found_ids
            ]
            self.validation_errors.append(f"Menus not found: {', '.join(missing_ids)}")

        # 각 메뉴 검증
        for menu in menus:
            self._validate_single_menu(menu)

        # 메뉴 이름 중복 확인 (7)
        self._validate_menu_name_duplicates(menus)

        return menus

    def _validate_single_menu(self, menu: CanonicalMenu):
        """단일 메뉴 검증 (4-6)"""
        menu_id = str(menu.id)

        # 4. 모든 선택 메뉴의 번역 완료 확인 (KO, EN, JA, ZH)
        self._validate_translations(menu, menu_id)

        # 5. 필수 필드 존재 확인
        self._validate_required_fields(menu, menu_id)

        # 6. Price > 0 검증
        self._validate_price(menu, menu_id)

    def _validate_translations(self, menu: CanonicalMenu, menu_id: str):
        """4. 번역 완료 확인"""
        required_langs = ["en", "ja", "zh"]

        # name 필드 확인
        if not menu.name_ko:
            self.validation_errors.append(f"Menu {menu_id}: name_ko is missing")
        if not menu.name_en:
            self.validation_errors.append(f"Menu {menu_id}: name_en is missing")

        # explanation_short JSONB 확인
        if not menu.explanation_short or not isinstance(menu.explanation_short, dict):
            self.validation_errors.append(
                f"Menu {menu_id}: explanation_short is missing or invalid"
            )
            return

        # 각 언어별 번역 확인
        for lang in required_langs:
            if lang not in menu.explanation_short or not menu.explanation_short[lang]:
                self.validation_errors.append(
                    f"Menu {menu_id} ({menu.name_ko}): translation missing for language '{lang}'"
                )

    def _validate_required_fields(self, menu: CanonicalMenu, menu_id: str):
        """5. 필수 필드 존재 확인"""
        if not menu.name_ko:
            self.validation_errors.append(f"Menu {menu_id}: name_ko is required")
        if not menu.name_en:
            self.validation_errors.append(f"Menu {menu_id}: name_en is required")
        if not menu.explanation_short:
            self.validation_errors.append(
                f"Menu {menu_id}: explanation_short is required"
            )

    def _validate_price(self, menu: CanonicalMenu, menu_id: str):
        """6. Price > 0 검증"""
        # typical_price_min 또는 typical_price_max 중 하나라도 있어야 함
        if not menu.typical_price_min and not menu.typical_price_max:
            self.validation_errors.append(
                f"Menu {menu_id} ({menu.name_ko}): price information is missing"
            )
            return

        # 가격이 0 이하인 경우
        if menu.typical_price_min and menu.typical_price_min <= 0:
            self.validation_errors.append(
                f"Menu {menu_id} ({menu.name_ko}): typical_price_min must be > 0"
            )
        if menu.typical_price_max and menu.typical_price_max <= 0:
            self.validation_errors.append(
                f"Menu {menu_id} ({menu.name_ko}): typical_price_max must be > 0"
            )

    def _validate_menu_name_duplicates(self, menus: List[CanonicalMenu]):
        """7. 메뉴 이름 중복 확인"""
        name_ko_set = set()
        name_en_set = set()

        for menu in menus:
            # 한글 이름 중복
            if menu.name_ko in name_ko_set:
                self.validation_errors.append(
                    f"Duplicate menu name (KO): '{menu.name_ko}'"
                )
            name_ko_set.add(menu.name_ko)

            # 영문 이름 중복
            if menu.name_en in name_en_set:
                self.validation_errors.append(
                    f"Duplicate menu name (EN): '{menu.name_en}'"
                )
            name_en_set.add(menu.name_en)


class MenuApprovalService:
    """메뉴 승인 처리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.validator = MenuApprovalValidator(db)

    async def approve_menus(
        self,
        restaurant_id: uuid.UUID,
        selected_menu_ids: List[uuid.UUID],
        admin_user_id: str,
    ) -> Dict[str, Any]:
        """
        메뉴 승인 처리

        1. 검증 실행
        2. Restaurant 상태 변경 (pending_approval → active)
        3. MenuUploadTask 상태 변경 (processing → approved)
        4. 승인 이력 기록
        """
        # 1. 검증 실행
        validation_result = await self.validator.validate_approval(
            restaurant_id, selected_menu_ids
        )

        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Menu approval validation failed",
                    "errors": validation_result["errors"],
                },
            )

        restaurant = validation_result["restaurant"]
        menus = validation_result["menus"]

        # 2. Restaurant 상태 변경
        restaurant.status = RestaurantStatus.active.value
        restaurant.approved_at = datetime.utcnow()
        restaurant.approved_by = admin_user_id

        # 3. MenuUploadTask 상태 변경 (가장 최근 업로드)
        upload_task_result = await self.db.execute(
            select(MenuUploadTask)
            .where(MenuUploadTask.restaurant_id == restaurant_id)
            .order_by(MenuUploadTask.created_at.desc())
            .limit(1)
        )
        upload_task = upload_task_result.scalars().first()

        if upload_task:
            upload_task.status = "approved"
            upload_task.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(restaurant)

        return {
            "restaurant": restaurant,
            "menus": menus,
            "approved_menu_count": len(menus),
        }
