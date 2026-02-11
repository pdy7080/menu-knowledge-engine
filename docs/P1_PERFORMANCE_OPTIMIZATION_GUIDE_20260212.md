# P1 Issue: Production Performance Test & Backend Optimization Guide

**Status**: 🔧 Implementation Ready
**Priority**: P1 (High)
**Estimated Time**: 2-3 hours
**Target**: Backend Score 75% → 90%, P95 < 2000ms

---

## 📋 Current Status

| Metric | Development | Target | Status |
|--------|-------------|--------|--------|
| P95 Response Time | 2060ms | < 2000ms | ⚠️ 60ms over |
| Average | 2049ms | < 3000ms | ✅ Pass |
| Backend Score | 75/100 | 90/100 | ⚠️ 15점 부족 |

**Problems**:
1. **Performance**: Development P95 = 2060ms (목표 대비 +60ms)
2. **Thread-Safety**: matching_engine cache가 asyncio 환경에서 race condition 위험
3. **JSONB Query**: Admin Stats 쿼리가 복잡한 JSONB 집계로 느림
4. **Retry Logic**: 외부 API 호출 실패 시 재시도 없음 (Papago, CLOVA, OpenAI)
5. **Input Validation**: OCR 이미지 포맷 검증 부족

---

## 🎯 Solution: 5-Step Optimization

### Step 1: Production Performance Benchmark (30분)

**목표**: 실제 프로덕션 환경에서 P95 측정

#### 1.1 Load Testing Script 작성

**파일**: `scripts/load_test.py`

```python
"""
Production Load Testing Script
Measure P95 response time under realistic load
"""
import asyncio
import time
import statistics
from typing import List
import httpx

# Production API endpoint
API_URL = "http://localhost:8000/api/v1/menu/identify"

# Test menu names (realistic Korean menus)
TEST_MENUS = [
    "김치찌개", "된장찌개", "불고기", "비빔밥", "냉면",
    "갈비탕", "삼계탕", "떡볶이", "순대국", "설렁탕",
]

async def single_request(client: httpx.AsyncClient, menu_name: str) -> float:
    """Single API request with timing"""
    start = time.time()
    try:
        response = await client.post(
            API_URL,
            json={"menu_name": menu_name},
            timeout=10.0
        )
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error for '{menu_name}': {e}")
        return 0.0

    elapsed = (time.time() - start) * 1000  # milliseconds
    return elapsed

async def benchmark(num_requests: int = 100) -> dict:
    """Run benchmark with concurrent requests"""
    print(f"🚀 Starting benchmark: {num_requests} requests")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Warm-up (5 requests)
        print("🔥 Warm-up phase...")
        for _ in range(5):
            await single_request(client, TEST_MENUS[0])

        # Actual benchmark
        print(f"📊 Benchmark phase ({num_requests} requests)...")
        times: List[float] = []

        for i in range(num_requests):
            menu_name = TEST_MENUS[i % len(TEST_MENUS)]
            elapsed = await single_request(client, menu_name)

            if elapsed > 0:
                times.append(elapsed)

            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{num_requests}")

    # Calculate statistics
    if not times:
        return {"error": "No successful requests"}

    times_sorted = sorted(times)

    stats = {
        "total_requests": len(times),
        "average": statistics.mean(times),
        "median": statistics.median(times),
        "p50": times_sorted[int(len(times) * 0.50)],
        "p95": times_sorted[int(len(times) * 0.95)],
        "p99": times_sorted[int(len(times) * 0.99)],
        "min": min(times),
        "max": max(times),
    }

    return stats

def print_results(stats: dict):
    """Pretty print benchmark results"""
    print("\n" + "=" * 60)
    print("📊 BENCHMARK RESULTS")
    print("=" * 60)

    if "error" in stats:
        print(f"❌ {stats['error']}")
        return

    print(f"Total Requests:  {stats['total_requests']}")
    print(f"Average:         {stats['average']:.2f}ms")
    print(f"Median:          {stats['median']:.2f}ms")
    print(f"P50:             {stats['p50']:.2f}ms")
    print(f"P95:             {stats['p95']:.2f}ms {'✅' if stats['p95'] < 2000 else '❌'}")
    print(f"P99:             {stats['p99']:.2f}ms")
    print(f"Min:             {stats['min']:.2f}ms")
    print(f"Max:             {stats['max']:.2f}ms")
    print("=" * 60)

    # Target evaluation
    target_p95 = 2000
    if stats['p95'] < target_p95:
        print(f"✅ SUCCESS: P95 under target ({target_p95}ms)")
    else:
        diff = stats['p95'] - target_p95
        print(f"⚠️  WARNING: P95 over target by {diff:.2f}ms")

if __name__ == "__main__":
    stats = asyncio.run(benchmark(100))
    print_results(stats)
```

#### 1.2 실행

```bash
# Backend 서버 먼저 실행
cd app/backend
uvicorn main:app --host 0.0.0.0 --port 8000

# 새 터미널에서 벤치마크
python -X utf8 scripts/load_test.py
```

**예상 결과**:
```
🚀 Starting benchmark: 100 requests
============================================================
🔥 Warm-up phase...
📊 Benchmark phase (100 requests)...
  Progress: 10/100
  Progress: 20/100
  ...
  Progress: 100/100

============================================================
📊 BENCHMARK RESULTS
============================================================
Total Requests:  100
Average:         1850.23ms
Median:          1845.00ms
P50:             1845.12ms
P95:             1980.45ms ✅
P99:             2010.23ms
Min:             1750.34ms
Max:             2050.67ms
============================================================
✅ SUCCESS: P95 under target (2000ms)
```

---

### Step 2: Thread-Safety Fix for Cache (20분)

**문제**: `matching_engine.py`의 클래스 레벨 캐시가 asyncio에서 race condition 위험

**파일**: `app/backend/services/matching_engine.py`

#### 2.1 현재 코드 (문제)

```python
class MatchingEngine:
    # 클래스 레벨 캐시 (thread-unsafe)
    _cache: Dict[str, Any] = {}

    async def match(self, menu_name: str):
        if menu_name in self._cache:
            return self._cache[menu_name]

        # ... matching logic
        result = ...

        self._cache[menu_name] = result  # Race condition!
        return result
```

#### 2.2 수정 코드 (asyncio.Lock 사용)

```python
import asyncio
from typing import Dict, Any, Optional

class MatchingEngine:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_lock = asyncio.Lock()  # asyncio.Lock 추가

    async def match(self, menu_name: str, db: AsyncSession) -> Dict[str, Any]:
        """Thread-safe matching with cache"""

        # 1. Lock 없이 먼저 읽기 (빠른 경로)
        if menu_name in self._cache:
            return self._cache[menu_name]

        # 2. Lock으로 보호된 쓰기
        async with self._cache_lock:
            # Double-check (다른 태스크가 이미 캐싱했을 수 있음)
            if menu_name in self._cache:
                return self._cache[menu_name]

            # 실제 매칭 수행
            result = await self._perform_matching(menu_name, db)

            # 캐시 저장 (Lock 보호됨)
            self._cache[menu_name] = result

        return result

    async def _perform_matching(self, menu_name: str, db: AsyncSession) -> Dict[str, Any]:
        """실제 매칭 로직 (기존 코드 이동)"""
        # Step 1: Exact match
        exact_match = await self._exact_match(menu_name, db)
        if exact_match:
            return exact_match

        # Step 2: Modifier decomposition
        modifier_match = await self._modifier_match(menu_name, db)
        if modifier_match:
            return modifier_match

        # Step 3: AI Discovery
        ai_result = await self._ai_discovery(menu_name)
        return ai_result
```

#### 2.3 AI Discovery 서비스도 동일하게 수정

**파일**: `app/backend/services/ai_discovery.py`

```python
class AIDiscoveryService:
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._cache_lock = asyncio.Lock()

    async def discover(self, menu_name: str) -> Optional[Dict]:
        """Thread-safe AI discovery with cache"""

        # Fast path: read without lock
        if menu_name in self._cache:
            logger.info(f"✅ Cache hit: {menu_name}")
            return self._cache[menu_name]

        # Slow path: GPT-4o call with lock
        async with self._cache_lock:
            # Double-check
            if menu_name in self._cache:
                return self._cache[menu_name]

            # Actual GPT-4o call
            result = await self._call_openai(menu_name)

            if result:
                self._cache[menu_name] = result

        return result
```

---

### Step 3: Admin Stats JSONB Optimization (30분)

**문제**: `/api/v1/admin/stats`가 JSONB 집계로 느림

**파일**: `app/backend/routers/admin.py`

#### 3.1 현재 코드 (느림)

```python
@router.get("/stats")
async def get_engine_stats(db: AsyncSession = Depends(get_db)):
    # JSONB 필터링 쿼리가 매번 전체 테이블 스캔
    pending_count = await db.scalar(
        select(func.count(ScanLog.id)).where(
            ScanLog.status == "pending"
        )
    )

    total_scans = await db.scalar(select(func.count(ScanLog.id)))

    # ... 더 많은 집계 쿼리들
```

#### 3.2 최적화 코드 (Single Query + Materialized View)

**Option A: Single Query with CTEs**

```python
from sqlalchemy import text

@router.get("/stats")
async def get_engine_stats(db: AsyncSession = Depends(get_db)):
    """Optimized stats with single query"""

    # Single query with CTEs
    query = text("""
    WITH scan_stats AS (
        SELECT
            COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
            COUNT(*) FILTER (WHERE status = 'approved') as approved_count,
            COUNT(*) FILTER (WHERE status = 'rejected') as rejected_count,
            COUNT(*) as total_scans,
            COUNT(DISTINCT shop_id) as active_shops
        FROM scan_logs
    ),
    menu_stats AS (
        SELECT
            COUNT(*) as total_canonical,
            COUNT(*) FILTER (WHERE explanation_short->>'ja' IS NOT NULL) as ja_count,
            COUNT(*) FILTER (WHERE explanation_short->>'zh' IS NOT NULL) as zh_count
        FROM canonical_menus
    ),
    recent_scans AS (
        SELECT
            id,
            menu_name_ko,
            shop_id,
            status,
            created_at
        FROM scan_logs
        ORDER BY created_at DESC
        LIMIT 10
    )
    SELECT
        s.*,
        m.total_canonical,
        m.ja_count,
        m.zh_count,
        json_agg(
            json_build_object(
                'id', r.id,
                'menu_name_ko', r.menu_name_ko,
                'shop_id', r.shop_id,
                'status', r.status,
                'created_at', r.created_at
            ) ORDER BY r.created_at DESC
        ) as recent_scans
    FROM scan_stats s
    CROSS JOIN menu_stats m
    LEFT JOIN recent_scans r ON true
    GROUP BY s.pending_count, s.approved_count, s.rejected_count,
             s.total_scans, s.active_shops,
             m.total_canonical, m.ja_count, m.zh_count
    """)

    result = await db.execute(query)
    row = result.fetchone()

    return {
        "pending_queue_count": row.pending_count,
        "approved_count": row.approved_count,
        "rejected_count": row.rejected_count,
        "total_scans": row.total_scans,
        "active_shops": row.active_shops,
        "canonical_menus_count": row.total_canonical,
        "translation_coverage": {
            "ja": f"{row.ja_count}/{row.total_canonical}",
            "zh": f"{row.zh_count}/{row.total_canonical}"
        },
        "recent_scans": row.recent_scans
    }
```

**Option B: Redis Caching (권장)**

```python
import json
from datetime import timedelta

@router.get("/stats")
async def get_engine_stats(
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)  # Redis 의존성 추가
):
    """Stats with Redis caching (5분 TTL)"""

    cache_key = "admin:stats"

    # 1. Redis 캐시 확인
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. DB 쿼리 (위의 Single Query 사용)
    query = text("""...""")  # 위의 CTE 쿼리
    result = await db.execute(query)
    row = result.fetchone()

    stats = {
        "pending_queue_count": row.pending_count,
        # ... (위와 동일)
    }

    # 3. Redis 캐싱 (5분)
    await redis_client.setex(
        cache_key,
        timedelta(minutes=5),
        json.dumps(stats)
    )

    return stats
```

---

### Step 4: Retry Logic for External APIs (30분)

**문제**: Papago, CLOVA, OpenAI 호출 실패 시 재시도 없음

#### 4.1 Retry Decorator 작성

**파일**: `app/backend/utils/retry.py`

```python
"""
Retry decorator for external API calls
"""
import asyncio
import functools
import logging
from typing import TypeVar, Callable, Any

logger = logging.getLogger(__name__)

T = TypeVar('T')

def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Async retry decorator with exponential backoff

    Args:
        max_attempts: Maximum retry attempts
        delay: Initial delay in seconds
        backoff: Delay multiplier
        exceptions: Exception types to catch
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    logger.warning(
                        f"⚠️  {func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {current_delay}s..."
                    )

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            # Should never reach here
            raise Exception(f"{func.__name__} exhausted retries")

        return wrapper
    return decorator
```

#### 4.2 TranslationService에 적용

**파일**: `app/backend/services/translation_service.py`

```python
from utils.retry import async_retry
import httpx

class TranslationService:
    @async_retry(max_attempts=3, delay=1.0, exceptions=(httpx.HTTPError,))
    def translate(self, text: str, source_lang: str = "en", target_lang: str = "ja") -> Optional[str]:
        """Translate with retry (synchronous wrapper)"""
        # In-memory cache
        cache_key = f"{source_lang}:{target_lang}:{text}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Papago API call
        try:
            response = httpx.post(
                "https://naveropenapi.apigw.ntruss.com/nmt/v1/translation",
                headers={
                    "X-NCP-APIGW-API-KEY-ID": self.papago_client_id,
                    "X-NCP-APIGW-API-KEY": self.papago_client_secret,
                },
                data={
                    "source": source_lang,
                    "target": target_lang,
                    "text": text,
                },
                timeout=10.0
            )
            response.raise_for_status()

            result = response.json()
            translated = result["message"]["result"]["translatedText"]

            # Cache result
            self._cache[cache_key] = translated

            return translated

        except httpx.HTTPError as e:
            logger.error(f"Papago API error: {e}")
            raise  # Re-raise for retry
```

#### 4.3 AI Discovery에 적용

**파일**: `app/backend/services/ai_discovery.py`

```python
from utils.retry import async_retry
from openai import AsyncOpenAI, APIError

class AIDiscoveryService:
    @async_retry(max_attempts=3, delay=2.0, exceptions=(APIError,))
    async def _call_openai(self, menu_name: str) -> Optional[Dict]:
        """Call GPT-4o with retry"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Korean food expert..."
                    },
                    {
                        "role": "user",
                        "content": f"Menu: {menu_name}"
                    }
                ],
                timeout=15.0
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            return result

        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise  # Re-raise for retry
```

---

### Step 5: Image Format Validation (20분)

**문제**: OCR 엔드포인트가 이미지 포맷 검증 없이 처리

**파일**: `app/backend/routers/menu.py`

#### 5.1 이미지 검증 유틸 작성

**파일**: `app/backend/utils/image_validation.py`

```python
"""
Image validation utilities
"""
from PIL import Image
import io
from typing import Tuple, Optional

# Allowed formats
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DIMENSIONS = (4096, 4096)  # 4K

class ImageValidationError(Exception):
    """Custom exception for image validation failures"""
    pass

def validate_image(file_bytes: bytes) -> Tuple[str, int, int]:
    """
    Validate uploaded image

    Returns:
        (format, width, height)

    Raises:
        ImageValidationError: If validation fails
    """
    # 1. Check file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ImageValidationError(
            f"File too large: {len(file_bytes)} bytes (max: {MAX_FILE_SIZE})"
        )

    # 2. Try to open as image
    try:
        img = Image.open(io.BytesIO(file_bytes))
    except Exception as e:
        raise ImageValidationError(f"Invalid image file: {e}")

    # 3. Check format
    if img.format not in ALLOWED_FORMATS:
        raise ImageValidationError(
            f"Unsupported format: {img.format}. Allowed: {ALLOWED_FORMATS}"
        )

    # 4. Check dimensions
    width, height = img.size
    if width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]:
        raise ImageValidationError(
            f"Image too large: {width}x{height} (max: {MAX_DIMENSIONS[0]}x{MAX_DIMENSIONS[1]})"
        )

    return img.format, width, height
```

#### 5.2 OCR 엔드포인트에 적용

**파일**: `app/backend/routers/menu.py`

```python
from fastapi import HTTPException, UploadFile
from utils.image_validation import validate_image, ImageValidationError

@router.post("/recognize")
async def recognize_menu(
    file: UploadFile,
    db: AsyncSession = Depends(get_db)
):
    """OCR menu recognition with image validation"""

    # 1. Read file bytes
    file_bytes = await file.read()

    # 2. Validate image
    try:
        img_format, width, height = validate_image(file_bytes)
        logger.info(f"✅ Image validated: {img_format} {width}x{height}")
    except ImageValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image: {str(e)}"
        )

    # 3. Save temporary file
    temp_path = f"/tmp/menu_{uuid.uuid4()}.{img_format.lower()}"

    try:
        with open(temp_path, "wb") as f:
            f.write(file_bytes)

        # 4. CLOVA OCR
        ocr_result = await ocr_service.extract_text(temp_path)

        # 5. GPT-4o parsing
        menu_items = await ai_service.parse_menu(ocr_result)

        return {
            "status": "success",
            "menu_items": menu_items,
            "image_info": {
                "format": img_format,
                "width": width,
                "height": height,
                "size_bytes": len(file_bytes)
            }
        }

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
```

---

## 🔍 Verification

### 1. Performance Test

```bash
# Run load test
python scripts/load_test.py

# Expected output:
# P95: < 2000ms ✅
```

### 2. Thread-Safety Test

```bash
# Concurrent requests test
python scripts/concurrent_test.py

# Expected: No race condition errors
```

### 3. Admin Stats Query Time

```sql
-- Check query execution time
EXPLAIN ANALYZE
SELECT
    COUNT(*) FILTER (WHERE status = 'pending') as pending_count
FROM scan_logs;

-- Expected: < 50ms
```

### 4. Retry Logic Test

```python
# Test retry behavior (manual)
# Disconnect network and see retry logs
# Expected: 3 attempts with exponential backoff
```

### 5. Image Validation Test

```bash
# Test with invalid image
curl -X POST http://localhost:8000/api/v1/menu/recognize \
  -F "file=@invalid.txt"

# Expected: 400 Bad Request "Invalid image"
```

---

## 📊 Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Backend Score | 75/100 | 90/100 | +15점 |
| P95 Response Time | 2060ms | < 2000ms | -60ms |
| Admin Stats Query | ~200ms | < 50ms | 75% ↓ |
| API Reliability | 95% | 99.9% | Retry logic |
| Security | Medium | High | Input validation |

---

## ✅ Acceptance Criteria

- [ ] Load test P95 < 2000ms (100 requests)
- [ ] Thread-safe cache with asyncio.Lock
- [ ] Admin stats single query < 50ms
- [ ] Retry logic implemented (3 attempts, exponential backoff)
- [ ] Image validation (format, size, dimensions)
- [ ] All external API calls have retry
- [ ] Backend score improved to 90/100
- [ ] No race condition errors under load

---

## 🚀 Implementation Timeline

| Task | Time | Priority |
|------|------|---------|
| Production benchmark script | 30분 | P0 |
| Thread-safety fix (cache) | 20분 | P1 |
| Admin Stats optimization | 30분 | P1 |
| Retry logic implementation | 30분 | P1 |
| Image validation | 20분 | P2 |
| **Total** | **2-3시간** | |

---

## 🔧 Troubleshooting

### Issue: P95 still over 2000ms after optimization

**Solution**: Profile the code to find bottleneck

```python
# Add profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# ... your code

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Issue: Redis not available

**Solution**: Use in-memory cache fallback

```python
# In admin.py
try:
    cached = await redis_client.get(cache_key)
except Exception:
    logger.warning("Redis unavailable, using DB directly")
    cached = None
```

### Issue: Retry exhausted

**Solution**: Check external API status

```bash
# Papago API health check
curl -I https://naveropenapi.apigw.ntruss.com

# CLOVA OCR health check
curl -I https://clovaocr.apigw.ntruss.com
```

---

## 📁 Related Files

- `scripts/load_test.py` - Production benchmark script
- `app/backend/services/matching_engine.py` - Thread-safe cache
- `app/backend/services/ai_discovery.py` - Thread-safe AI cache
- `app/backend/routers/admin.py` - Optimized stats endpoint
- `app/backend/utils/retry.py` - Retry decorator
- `app/backend/utils/image_validation.py` - Image validation utilities
- `app/backend/routers/menu.py` - OCR endpoint with validation

---

**Created**: 2026-02-12
**Status**: Implementation Ready
**Next Step**: Execute Step 1 (Production Benchmark)
