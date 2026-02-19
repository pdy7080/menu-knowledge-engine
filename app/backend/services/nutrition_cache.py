"""
영양정보 캐싱 서비스
Redis TTL 90일 + DB fallback
공공데이터 API 호출을 최소화하고 <100ms 응답 보장
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from models.canonical_menu import CanonicalMenu
from services.cache_service import cache_service
from services.public_data_client import public_data_client
from services.normalize import normalize_menu_name, generate_search_variants

logger = logging.getLogger(__name__)

# TTL: 90일 (영양정보는 거의 변하지 않음)
TTL_NUTRITION = 90 * 24 * 60 * 60  # 7,776,000초


class NutritionCacheService:
    """영양정보 캐싱 서비스 (Redis + DB + 공공데이터 API)"""

    def _cache_key(self, canonical_id: str) -> str:
        return f"nutrition:{canonical_id}"

    async def get_nutrition(
        self, canonical_id: UUID, db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        영양정보 조회 (3단계 fallback)
        1. Redis 캐시 → 2. DB nutrition_info → 3. 공공데이터 API

        Args:
            canonical_id: canonical_menus.id
            db: AsyncSession

        Returns:
            {"nutrition": {...}, "serving_size": str, "source": str, "cached": bool}
        """
        str_id = str(canonical_id)
        cache_key = self._cache_key(str_id)

        # Step 1: Redis 캐시 확인
        cached = await cache_service.get(cache_key)
        if cached is not None:
            logger.debug(f"[Nutrition] Cache hit: {str_id}")
            cached["cached"] = True
            return cached

        # Step 2: DB에서 조회
        result = await db.execute(
            select(CanonicalMenu).where(CanonicalMenu.id == canonical_id)
        )
        menu = result.scalar_one_or_none()

        if not menu:
            return None

        # DB에 영양정보가 있으면 캐시에 저장 후 반환
        if menu.nutrition_info and menu.nutrition_info != {}:
            nutrition_data = {
                "nutrition": menu.nutrition_info,
                "serving_size": menu.serving_size,
                "source": "db",
                "last_updated": menu.last_nutrition_updated.isoformat() if menu.last_nutrition_updated else None,
            }
            await cache_service.set(cache_key, nutrition_data, TTL_NUTRITION)
            nutrition_data["cached"] = False
            return nutrition_data

        # Step 3: 공공데이터 API에서 조회
        return await self._fetch_and_cache(menu, db)

    async def _fetch_and_cache(
        self, menu: CanonicalMenu, db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """공공데이터 API 호출 → DB 저장 → 캐시 저장"""
        # 메뉴명 변형 생성하여 검색
        variants = generate_search_variants(menu.name_ko)

        enriched = None
        for variant in variants:
            enriched = await public_data_client.enrich_menu(variant)
            if enriched and enriched.get("nutrition_info"):
                break

        if not enriched or not enriched.get("nutrition_info"):
            logger.info(f"[Nutrition] No data found for: {menu.name_ko}")
            return None

        now = datetime.now(timezone.utc)

        # DB 업데이트
        await db.execute(
            update(CanonicalMenu)
            .where(CanonicalMenu.id == menu.id)
            .values(
                standard_code=enriched.get("standard_code") or menu.standard_code,
                category_1=enriched.get("category_1") or menu.category_1,
                category_2=enriched.get("category_2") or menu.category_2,
                serving_size=enriched.get("serving_size") or menu.serving_size,
                nutrition_info=enriched["nutrition_info"],
                last_nutrition_updated=now,
            )
        )
        await db.commit()

        # Redis 캐시에 저장
        nutrition_data = {
            "nutrition": enriched["nutrition_info"],
            "serving_size": enriched.get("serving_size"),
            "source": "public_data",
            "last_updated": now.isoformat(),
        }
        str_id = str(menu.id)
        await cache_service.set(self._cache_key(str_id), nutrition_data, TTL_NUTRITION)

        nutrition_data["cached"] = False
        logger.info(f"[Nutrition] Fetched and cached: {menu.name_ko}")
        return nutrition_data

    async def invalidate(self, canonical_id: UUID) -> bool:
        """캐시 무효화 (데이터 갱신 시)"""
        cache_key = self._cache_key(str(canonical_id))
        return await cache_service.delete(cache_key)

    async def bulk_fetch(
        self, menu_ids: list, db: AsyncSession
    ) -> Dict[str, Optional[Dict]]:
        """
        벌크 영양정보 조회 (데이터 임포트 시 사용)

        Args:
            menu_ids: canonical_menu ID 목록
            db: AsyncSession

        Returns:
            {str(id): nutrition_data or None}
        """
        results = {}
        for menu_id in menu_ids:
            results[str(menu_id)] = await self.get_nutrition(menu_id, db)
        return results


# Global instance
nutrition_cache = NutritionCacheService()
