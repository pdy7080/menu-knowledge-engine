"""
Redis Cache Service - 캐싱 관리 서비스
"""

import pickle
from typing import Any, Optional, Callable
from functools import wraps
import logging

import redis.asyncio as redis
from config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis 캐시 서비스"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.enabled = settings.CACHE_ENABLED

    async def connect(self):
        """Redis 연결"""
        if not self.enabled:
            logger.info("Cache disabled by configuration")
            return

        try:
            self.redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=False,  # Binary mode for pickle
            )
            # Connection test
            await self.redis.ping()
            logger.info(f"Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache disabled.")
            self.enabled = False
            self.redis = None

    async def disconnect(self):
        """Redis 연결 종료"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis disconnected")

    async def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 가져오기

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None
        """
        if not self.enabled or not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value is None:
                return None

            # Unpickle
            return pickle.loads(value)

        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: int = 300  # Default: 5 minutes
    ) -> bool:
        """
        캐시에 값 저장

        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: Time-To-Live (초)

        Returns:
            성공 여부
        """
        if not self.enabled or not self.redis:
            return False

        try:
            # Pickle
            serialized = pickle.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            return True

        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        캐시에서 값 삭제

        Args:
            key: 캐시 키

        Returns:
            성공 여부
        """
        if not self.enabled or not self.redis:
            return False

        try:
            await self.redis.delete(key)
            return True

        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        패턴과 일치하는 모든 키 삭제

        Args:
            pattern: 키 패턴 (예: "restaurant:*")

        Returns:
            삭제된 키 개수
        """
        if not self.enabled or not self.redis:
            return 0

        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await self.redis.delete(*keys)
                return deleted
            return 0

        except Exception as e:
            logger.error(f"Cache delete_pattern error for pattern '{pattern}': {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        캐시 키 존재 여부 확인

        Args:
            key: 캐시 키

        Returns:
            존재 여부
        """
        if not self.enabled or not self.redis:
            return False

        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False

    def cache_key(self, *parts) -> str:
        """
        캐시 키 생성

        Args:
            *parts: 키 구성 요소

        Returns:
            캐시 키 (예: "restaurant:uuid:menus")
        """
        return ":".join(str(part) for part in parts)


# Global cache instance
cache_service = CacheService()


def cached(
    ttl: int = 300, key_prefix: str = "", key_builder: Optional[Callable] = None
):
    """
    함수 결과를 캐싱하는 데코레이터

    Args:
        ttl: Time-To-Live (초)
        key_prefix: 캐시 키 접두사
        key_builder: 커스텀 키 생성 함수

    Usage:
        @cached(ttl=300, key_prefix="admin:stats")
        async def get_admin_stats(db):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Cache disabled
            if not cache_service.enabled:
                return await func(*args, **kwargs)

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key: prefix:function_name:args_hash
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = cache_service.cache_key(
                    key_prefix or func.__name__, hash(args_str)
                )

            # Try cache
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # Cache miss - execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)

            # Save to cache
            await cache_service.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# TTL Constants (초)
TTL_ADMIN_STATS = 300  # 5분
TTL_MENU_TRANSLATION = 86400  # 24시간
TTL_RESTAURANT_INFO = 3600  # 1시간
TTL_QR_CODE = 7200  # 2시간
TTL_NUTRITION = 7776000  # 90일 (영양정보)
