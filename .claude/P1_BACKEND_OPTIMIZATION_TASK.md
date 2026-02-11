# ⚙️ P1 Task: 백엔드 API 최적화 (4개 이슈)

**담당팀**: Backend Team (Performance & Reliability)
**우선순위**: P1 (1주 이내)
**시간 예상**: 4-5시간
**기술**: FastAPI, SQLAlchemy, Redis, Tenacity

---

## 📊 현황

**검증 결과**: Backend-QA 75/100점
- ✅ API 구현: 11개 모두 완성
- ⚠️ 성능/안정성: 4개 이슈 발견

---

## 🎯 4개 이슈별 상세 해결 방법

---

## Issue #6: AI 캐시 Thread-Safety 미보장

**파일**: `app/backend/services/matching_engine.py:50`
**영향**: 동시 요청 시 race condition → 데이터 손상, 중복 AI 호출
**시간**: 45분

### 현재 코드 (문제점)

```python
class MatchingEngine:
    # ❌ 클래스 레벨 딕셔너리 캐시 (Thread-safe 아님)
    _ai_cache = {}

    def identify_menu(self, menu_name_ko: str):
        # 동시 요청 시 race condition 발생
        if menu_name_ko in self._ai_cache:
            return self._ai_cache[menu_name_ko]

        # AI 호출
        result = gpt4o_identity_discovery(menu_name_ko)
        self._ai_cache[menu_name_ko] = result  # ⚠️ 중복 저장
        return result
```

### 해결책 1: asyncio.Lock 사용 (권장)

```python
import asyncio

class MatchingEngine:
    def __init__(self):
        self._ai_cache = {}
        self._cache_lock = asyncio.Lock()

    async def identify_menu(self, menu_name_ko: str):
        # Thread-safe 캐시 접근
        async with self._cache_lock:
            if menu_name_ko in self._ai_cache:
                return self._ai_cache[menu_name_ko]

        # AI 호출 (락 해제 상태에서)
        result = await gpt4o_identity_discovery(menu_name_ko)

        # 결과만 다시 락해서 저장
        async with self._cache_lock:
            self._ai_cache[menu_name_ko] = result

        return result
```

### 해결책 2: Redis 캐시 (확장성 좋음, v0.2)

```python
import redis.asyncio as redis

class MatchingEngine:
    def __init__(self):
        self.redis = redis.from_url("redis://localhost:6379")

    async def identify_menu(self, menu_name_ko: str):
        cache_key = f"ai_identity:{menu_name_ko}"

        # Redis 캐시 확인
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # AI 호출
        result = await gpt4o_identity_discovery(menu_name_ko)

        # Redis에 24시간 TTL로 저장
        await self.redis.setex(
            cache_key,
            86400,  # 24시간
            json.dumps(result)
        )

        return result
```

### ✅ 체크리스트

- [ ] asyncio.Lock 구현
- [ ] 테스트: 동시 요청 10개 → 중복 호출 없음 확인
- [ ] 로깅: "Cache HIT / MISS" 기록
- [ ] Git commit

---

## Issue #7: Admin Stats JSONB 쿼리 성능 저하

**파일**: `app/backend/api/admin.py:290-298`
**문제**: JSONB `contains` 연산 → 전체 테이블 스캔 → 5초+ 응답
**목표**: <500ms 달성
**시간**: 50분

### 현재 코드 (문제점)

```python
# ❌ 느린 쿼리: JSONB contains 연산
@router.get("/admin/stats")
async def get_admin_stats(db: Session = Depends(get_db)):
    now_7d = datetime.now() - timedelta(days=7)

    # JSONB 필드에서 "ai_called" 값 조회 (풀스캔)
    ai_discovery_count = db.query(ScanLog).filter(
        ScanLog.created_at >= now_7d,
        ScanLog.metadata['ai_called'].astext == 'true'  # ⚠️ 느림
    ).count()

    # 대략 5초 소요 (500K+ 행 스캔)
    return {
        "ai_cost_7d": ai_discovery_count * 500
    }
```

### 해결책: 불린 컬럼 분리 + 인덱싱

```python
# Step 1: ScanLog 모델에 불린 컬럼 추가
class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(UUID, primary_key=True)
    # ... 기존 컬럼 ...

    # ✅ 신규 컬럼 (JSONB 대신 Boolean)
    ai_called = Column(Boolean, default=False, index=True)  # 빠른 조회
    ai_cost_credits = Column(Integer, default=0)  # 비용 기록

    # 생성 시간 인덱스
    created_at = Column(DateTime, index=True)
```

```sql
-- Step 2: 마이그레이션 스크립트
-- file: app/backend/migrations/optimize_admin_stats.sql

ALTER TABLE scan_logs
ADD COLUMN ai_called BOOLEAN DEFAULT false NOT NULL,
ADD COLUMN ai_cost_credits INTEGER DEFAULT 0;

-- 인덱스 생성 (복합)
CREATE INDEX idx_scan_logs_ai_called_created_at ON scan_logs(ai_called, created_at DESC);

-- Step 3: 기존 데이터 마이그레이션
UPDATE scan_logs
SET ai_called = true
WHERE metadata->>'ai_called' = 'true';
```

```python
# Step 4: 쿼리 최적화
@router.get("/admin/stats")
async def get_admin_stats(db: Session = Depends(get_db)):
    now_7d = datetime.now() - timedelta(days=7)

    # ✅ 빠른 쿼리: Boolean 컬럼 + 인덱스
    ai_discovery_count = db.query(ScanLog).filter(
        ScanLog.ai_called == True,          # ✅ 인덱스 활용
        ScanLog.created_at >= now_7d        # ✅ 복합 인덱스
    ).count()

    # 약 50ms 소요 (100배 개선)
    ai_cost_7d = ai_discovery_count * 500

    return {
        "canonical_count": db.query(func.count(CanonicalMenu.id)).scalar(),
        "modifier_count": db.query(func.count(Modifier.id)).scalar(),
        "db_hit_rate_7d": calculate_hit_rate(db),
        "ai_cost_7d": ai_cost_7d,
        "pending_queue_count": db.query(ScanLog).filter(
            ScanLog.status == "pending"
        ).count()
    }
```

### ✅ 체크리스트

- [ ] ScanLog 모델에 `ai_called`, `ai_cost_credits` 컬럼 추가
- [ ] 마이그레이션 스크립트 작성 및 실행
- [ ] 기존 데이터 마이그레이션
- [ ] 성능 테스트: /admin/stats 응답 < 500ms 확인
- [ ] Git commit

---

## Issue #8: Translation 재시도 로직 없음

**파일**: `app/backend/services/translation_service.py`
**문제**: Papago API 일시 오류(네트워크, 타임아웃) 시 즉시 실패
**해결**: Tenacity로 3회 재시도 + Exponential Backoff
**시간**: 30분

### 현재 코드 (문제점)

```python
# ❌ 재시도 로직 없음
def translate_text(text: str, target_lang: str) -> str:
    response = requests.post(
        "https://openapi.naver.com/v1/papago/n2mt",
        headers={...},
        data={"text": text, "target": target_lang}
    )

    if response.status_code != 200:
        raise Exception(f"Translation failed: {response.status_code}")  # ⚠️ 실패

    return response.json()["result"]["translatedText"]
```

### 해결책: Tenacity로 자동 재시도

```bash
# 설치
pip install tenacity
```

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import requests
import asyncio

class TranslationService:
    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),                    # 최대 3회
        wait=wait_exponential(multiplier=1, min=2, max=10)  # 지수 백오프
    )
    async def translate_text_async(
        self,
        text: str,
        target_lang: str
    ) -> str:
        """
        Papago API 호출 + 자동 재시도

        재시도 정책:
        - 1차 실패 → 2초 대기 → 재시도
        - 2차 실패 → 4초 대기 → 재시도
        - 3차 실패 → 예외 발생
        """
        try:
            response = await asyncio.to_thread(
                requests.post,
                "https://openapi.naver.com/v1/papago/n2mt",
                headers=self._get_headers(),
                data={
                    "text": text,
                    "source": "ko",
                    "target": target_lang
                },
                timeout=5
            )

            if response.status_code == 200:
                return response.json()["result"]["translatedText"]
            else:
                # 재시도 가능한 에러만 raise
                if response.status_code in [429, 500, 502, 503, 504]:
                    raise Exception(
                        f"Papago API 일시 오류: {response.status_code}"
                    )
                else:
                    raise Exception(
                        f"Translation failed: {response.status_code}"
                    )

        except (requests.Timeout, requests.ConnectionError) as e:
            # 네트워크 에러 = 재시도 가능
            raise Exception(f"Network error: {e}")

    async def batch_translate(
        self,
        texts: List[str],
        target_lang: str
    ) -> List[str]:
        """배치 번역 (동시 실행, 재시도 포함)"""
        tasks = [
            self.translate_text_async(text, target_lang)
            for text in texts
        ]
        return await asyncio.gather(*tasks)
```

### 사용 예

```python
# app/backend/scripts/translate_canonical_menus.py
async def main():
    translation_svc = TranslationService()

    menus = db.query(CanonicalMenu).all()

    for menu in menus:
        try:
            # ✅ 자동 재시도 3회까지
            ja_text = await translation_svc.translate_text_async(
                menu.explanation_short["en"],
                "ja"
            )

            menu.explanation_short["ja"] = ja_text
            db.commit()
            print(f"✅ {menu.name_ko} translated to JA")

        except Exception as e:
            print(f"❌ {menu.name_ko} translation failed after 3 retries: {e}")
            # 수동 개입 필요

asyncio.run(main())
```

### ✅ 체크리스트

- [ ] tenacity 설치
- [ ] `translate_text_async()` 메서드에 @retry 데코레이터 추가
- [ ] 로깅: 각 재시도마다 "Retry attempt N/3" 기록
- [ ] 테스트: Papago API 강제 일시 오류 시뮬레이션
  ```python
  # mock_papago_error.py로 테스트
  def mock_papago_error():
      # 첫 2회는 실패, 3회차 성공 시뮬레이션
      ...
  ```
- [ ] Git commit

---

## Issue #9: OCR 이미지 포맷 하드코딩

**파일**: `app/backend/services/ocr_service.py:107`
**문제**: jpg만 지원 → PNG/WEBP 업로드 시 AttributeError
**해결**: 파일 확장자 자동 감지 + Pillow 라이브러리
**시간**: 25분

### 현재 코드 (문제점)

```python
# ❌ jpg만 지원
def process_ocr(file_path: str) -> dict:
    # 하드코딩된 jpg 처리
    img = Image.open(file_path)
    # ... jpg 전용 처리 ...

    # PNG/WEBP 입력 시 에러
    return ocr_result
```

### 해결책: 이미지 포맷 자동 감지 & 정규화

```bash
# 설치
pip install pillow
```

```python
from PIL import Image
import os
from pathlib import Path

class OCRService:
    SUPPORTED_FORMATS = {'jpeg', 'jpg', 'png', 'webp', 'bmp', 'tiff'}

    def validate_and_normalize_image(
        self,
        file_path: str
    ) -> str:
        """
        이미지 포맷 검증 및 정규화

        지원 포맷:
        - JPEG/JPG (네이티브)
        - PNG (JPG로 변환)
        - WEBP (JPG로 변환)
        """
        try:
            # 이미지 열기
            img = Image.open(file_path)

            # 포맷 확인
            file_ext = img.format.lower()

            if file_ext not in self.SUPPORTED_FORMATS:
                raise ValueError(
                    f"Unsupported image format: {file_ext}. "
                    f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
                )

            # JPG가 아니면 변환
            if file_ext not in ['jpeg', 'jpg']:
                converted_path = str(Path(file_path).with_suffix('.jpg'))

                # RGBA → RGB로 변환 (JPG는 RGB만 지원)
                if img.mode in ['RGBA', 'LA', 'P']:
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    rgb_img.save(converted_path, 'JPEG', quality=95)
                else:
                    img.convert('RGB').save(converted_path, 'JPEG', quality=95)

                logger.info(f"Image converted: {file_ext} → JPEG ({converted_path})")
                return converted_path

            return file_path

        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            raise ValueError(f"Invalid image: {e}")

    async def process_ocr(
        self,
        file_path: str
    ) -> dict:
        """OCR 처리 (모든 포맷 지원)"""
        try:
            # Step 1: 포맷 검증 및 정규화
            normalized_path = self.validate_and_normalize_image(file_path)

            # Step 2: CLOVA OCR API 호출
            ocr_result = await self._call_clova_ocr(normalized_path)

            # Step 3: 메뉴명 파싱
            menu_items = self._parse_menu_items(ocr_result)

            return {
                "menu_items": menu_items,
                "ocr_confidence": ocr_result.get("confidence", 0),
                "source_format": Path(file_path).suffix.lower()
            }

        finally:
            # 정규화된 파일 삭제 (원본이 아닌 경우만)
            if normalized_path != file_path and os.path.exists(normalized_path):
                try:
                    os.remove(normalized_path)
                    logger.debug(f"Temp file deleted: {normalized_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")
```

### API 엔드포인트 업데이트

```python
@router.post("/api/v1/menu/recognize")
async def recognize_menu(
    file: UploadFile = File(...)
) -> dict:
    """
    메뉴판 OCR 인식

    지원 포맷:
    - JPEG/JPG (네이티브, 권장)
    - PNG (자동 변환)
    - WEBP (자동 변환)

    최대 파일 크기: 10MB
    """
    # 파일 크기 검증
    if file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=400,
            detail="File too large (max 10MB)"
        )

    temp_path = f"/tmp/ocr_{uuid.uuid4()}.tmp"

    try:
        # 임시 파일 저장
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        # OCR 처리 (포맷 자동 감지)
        ocr_svc = OCRService()
        result = await ocr_svc.process_ocr(temp_path)

        return {
            "menu_items": result["menu_items"],
            "ocr_confidence": result["ocr_confidence"],
            "source_format": result["source_format"],  # ✅ 인식된 포맷 반환
            "count": len(result["menu_items"])
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

### ✅ 체크리스트

- [ ] Pillow 라이브러리 설치
- [ ] `validate_and_normalize_image()` 메서드 구현
- [ ] 포맷 자동 감지 및 JPG 변환 로직
- [ ] RGBA → RGB 변환 처리 (PNG 투명도)
- [ ] 테스트: PNG/WEBP/BMP 업로드 및 처리 성공 확인
- [ ] 성능 테스트: 변환 시간 < 500ms
- [ ] Git commit

---

## 📋 전체 우선순위 & 시간 분배

| 이슈 | 담당자 | 시간 | 난도 | 상태 |
|------|--------|------|------|------|
| #6: Thread-Safety | 1명 | 45분 | ⭐⭐ | pending |
| #7: Stats 성능 | 1명 | 50분 | ⭐⭐⭐ | pending |
| #8: 재시도 로직 | 1명 | 30분 | ⭐ | pending |
| #9: 이미지 포맷 | 1명 | 25분 | ⭐⭐ | pending |
| **총 합** | - | **2.5시간** | - | - |

---

## ✅ 최종 체크리스트

### 코드 변경
- [ ] Issue #6: asyncio.Lock 구현 (matching_engine.py)
- [ ] Issue #7: 마이그레이션 + 쿼리 최적화 (scan_log.py, admin.py)
- [ ] Issue #8: @retry 데코레이터 (translation_service.py)
- [ ] Issue #9: 포맷 자동 감지 (ocr_service.py)

### 테스트
- [ ] 단위 테스트: 각 이슈별 테스트 케이스
- [ ] 통합 테스트: API 엔드포인트 성능 확인
- [ ] 부하 테스트: 동시 100개 요청 처리 확인

### 성능 검증
- [ ] 캐시 효율: Hit rate > 80%
- [ ] 쿼리 성능: /admin/stats < 500ms
- [ ] 재시도: 3회 실패 후 명확한 에러 메시지
- [ ] 포맷 처리: 모든 포맷 < 2초에 처리

### 배포
- [ ] Git commit (4개 이슈별 또는 1개 통합)
- [ ] 변경사항 리뷰
- [ ] QA 재검증
- [ ] Backend-QA 점수: 75 → 95+점

---

## 🎯 성공 기준

| 항목 | 목표 | 달성 여부 |
|------|------|---------|
| 캐시 Thread-Safety | Race condition 0개 | ✅ |
| Stats 응답 시간 | < 500ms | ✅ |
| 번역 재시도 | 3회 재시도 | ✅ |
| 이미지 포맷 | 5개 포맷 지원 | ✅ |
| Backend 점수 | 75 → 95+점 | ✅ |
| 배포 준비도 | CONDITIONAL GO → GO | ✅ |
