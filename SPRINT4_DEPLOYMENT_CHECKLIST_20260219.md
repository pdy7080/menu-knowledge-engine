# Sprint 4: 배포 전 체크리스트 & 테스트 계획

**작성일**: 2026-02-19
**상태**: 배포 준비 단계

---

## 📋 배포 전 준비 (Pre-deployment)

### 1. 환경 변수 확인

**FastComet 서버에서**:

```bash
# SSH 접속
ssh chargeap@d11475.sgp1.stableserver.net

# .env 파일 확인
cd ~/menu-knowledge/app/backend
cat .env | grep -E "OPENAI|CLOVA|REDIS"
```

**필수 항목**:
- [ ] `OPENAI_API_KEY` - ChatGPT API 키
- [ ] `CLOVA_OCR_SECRET` - CLOVA 인증 키
- [ ] `CLOVA_OCR_API_URL` - CLOVA API 엔드포인트
- [ ] `REDIS_HOST` - localhost 또는 Redis 서버 주소
- [ ] `REDIS_PORT` - 6379 (기본값)
- [ ] `REDIS_DB` - 0 (기본값)

**설정 명령**:
```bash
# OpenAI API 키 추가
echo "OPENAI_API_KEY=sk-xxxxxxxxxxxx" >> ~/.env

# .env 파일에 추가된 항목 확인
source ~/.env && echo "✅ Environment loaded"
```

---

### 2. 의존성 확인

```bash
# venv 활성화
source venv/bin/activate

# requirements.txt 업데이트 확인
pip list | grep -E "openai|redis|fastapi|sqlalchemy"
```

**필수 패키지**:
- [ ] `openai>=1.3.0` (GPT-4o mini Vision)
- [ ] `redis>=4.5.0` (캐싱)
- [ ] `fastapi>=0.104.0`
- [ ] `sqlalchemy[asyncio]>=2.0.0`
- [ ] `opencv-python>=4.8.0` (이미지 전처리)

**설치**:
```bash
pip install -r requirements.txt --upgrade
```

---

### 3. 데이터베이스 마이그레이션 확인

```bash
# 기존 마이그레이션 확인
alembic current

# 새 마이그레이션 필요 여부 확인
alembic revision --autogenerate -m "sprint4_ocr_abstraction"
```

**Sprint 4에서 DB 변경 없음** (OcrResult는 메모리 객체, ScanLog는 기존 테이블 사용)

---

### 4. Redis 연결 테스트

```bash
# Redis 서버 상태 확인
redis-cli ping

# 출력: PONG
```

---

## 🧪 배포 후 테스트

### Phase 1: 단위 테스트 (Unit Tests)

#### 1-1. OcrProviderGpt 테스트

```bash
cd ~/menu-knowledge/app/backend

# 테스트 실행
python -m pytest tests/services/test_ocr_provider_gpt.py -v

# 예상 결과:
# test_extract_with_valid_image PASSED
# test_extract_with_invalid_image PASSED
# test_handwriting_detection PASSED
# test_confidence_calculation PASSED
# test_health_check PASSED
```

**테스트 케이스**:
```python
def test_extract_with_valid_image():
    """GPT Vision으로 유효한 이미지 분석"""
    # 샘플 메뉴판 이미지로 테스트
    result = ocr_provider_gpt.extract("tests/fixtures/menu_sample.jpg")
    assert result.success == True
    assert len(result.menu_items) > 0
    assert result.confidence > 0.75

def test_handwriting_detection():
    """손글씨 감지 테스트"""
    result = ocr_provider_gpt.extract("tests/fixtures/handwritten_menu.jpg")
    assert result.has_handwriting == True

def test_confidence_calculation():
    """신뢰도 계산 로직"""
    # confidence = 0.75 + item_bonus - error_penalty
    result = ocr_provider_gpt.extract("tests/fixtures/menu.jpg")
    assert 0.0 <= result.confidence <= 1.0
```

#### 1-2. OcrProviderClova 테스트

```bash
python -m pytest tests/services/test_ocr_provider_clova.py -v

# 예상 결과:
# test_extract_wraps_existing_service PASSED
# test_menu_item_conversion PASSED
# test_backward_compatibility PASSED
```

#### 1-3. OcrTierRouter 테스트

```bash
python -m pytest tests/services/test_ocr_tier_router.py -v

# 예상 결과:
# test_tier1_success_no_fallback PASSED
# test_tier1_low_confidence_triggers_tier2 PASSED
# test_tier1_handwriting_triggers_tier2 PASSED
# test_fallback_reason_generated PASSED
```

#### 1-4. OrchestratorService 테스트

```bash
python -m pytest tests/services/test_ocr_orchestrator.py -v

# 예상 결과:
# test_extract_menu_caching PASSED
# test_metrics_collection PASSED
# test_cache_hit_on_same_image PASSED
# test_metrics_calculation PASSED
```

---

### Phase 2: 통합 테스트 (Integration Tests)

#### 2-1. B2B 벌크 업로드 API 테스트

```bash
python -m pytest tests/api/test_b2b_bulk_upload.py -v

# 예상 결과:
# test_single_image_upload PASSED (3~5초)
# test_multiple_images_upload PASSED
# test_image_validation_failure PASSED
# test_ocr_failure_handling PASSED
# test_cache_consistency PASSED
```

**수동 테스트**:

```bash
# 1. 테스트 서버 시작
cd ~/menu-knowledge/app/backend
uvicorn main:app --host 127.0.0.1 --port 8001 --reload

# 2. 이미지 업로드 테스트 (다른 터미널)
curl -X POST http://localhost:8001/api/v1/b2b/restaurants/{restaurant_id}/menus/upload-images \
  -F "files=@menu1.jpg" \
  -F "files=@menu2.jpg" \
  -H "Accept: application/json" | jq .

# 3. 응답 확인
{
  "success": true,
  "task_id": "xxx-xxx",
  "total": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "file": "menu1.jpg",
      "status": "success",
      "provider": "gpt_vision",
      "menu_count": 12,
      "confidence": 0.92,
      "fallback_triggered": false,
      "processing_time_ms": 3200
    }
  ]
}
```

#### 2-2. 메트릭 수집 테스트

```bash
# 메트릭 조회
curl http://localhost:8001/api/v1/admin/ocr/metrics | jq .

# 예상 응답:
{
  "tier_1_count": 2,
  "tier_2_count": 0,
  "tier_1_success_rate": "100.0%",
  "tier_2_fallback_rate": "0.0%",
  "avg_processing_time_ms": 3200,
  "price_error_count": 0,
  "price_error_rate": "0.0%",
  "handwriting_detection_rate": "0.0%"
}
```

#### 2-3. 캐싱 일관성 테스트

```bash
# 동일 이미지 두 번 업로드
curl -X POST http://localhost:8001/api/v1/b2b/restaurants/{id}/menus/upload-images \
  -F "files=@menu.jpg" | jq '.results[0] | {confidence, result_hash}'

# 첫 번째 응답
{
  "confidence": 0.92,
  "result_hash": "abc123..."
}

# 두 번째 응답 (캐시 히트 시)
{
  "confidence": 0.92,
  "result_hash": "abc123..."  # ← 동일한 해시
}

# ✅ 결과 일관성 확인!
```

---

### Phase 3: 성능 벤치마크

#### 3-1. 처리 시간 측정

```bash
# 10개 이미지 처리 시간 측정
python scripts/benchmark_ocr.py \
  --images tests/fixtures/menus/*.jpg \
  --count 10

# 예상 결과:
# Tier 1 (GPT): 3200ms avg (3000-3500ms 범위)
# Tier 2 (CLOVA): 2800ms avg (2500-3200ms 범위)
# Cache hit: 50ms avg
```

#### 3-2. 메모리 사용량 측정

```bash
# 메모리 프로파일링
python -m memory_profiler scripts/profile_ocr.py

# 예상 결과:
# Peak memory: ~250MB
# Cache memory: ~50MB (30-day TTL)
```

#### 3-3. 동시 요청 처리

```bash
# 5개 동시 요청 테스트
for i in {1..5}; do
  curl -X POST http://localhost:8001/api/v1/b2b/restaurants/{id}/menus/upload-images \
    -F "files=@menu.jpg" \
    -H "Accept: application/json" &
done
wait

# 예상: 모든 요청 정상 처리, 응답 시간 < 5초
```

---

### Phase 4: 엣지 케이스 테스트

#### 4-1. 손글씨 메뉴판

```bash
# 손글씨 메뉴판 이미지로 테스트
curl -X POST http://localhost:8001/api/v1/b2b/restaurants/{id}/menus/upload-images \
  -F "files=@handwritten_menu.jpg" | jq .

# 예상 결과:
# "fallback_triggered": true,
# "fallback_reason": "손글씨 감지"
# "provider": "clova"  (Tier 2로 자동 전환)
```

#### 4-2. 저품질 이미지

```bash
# 흐릿한 이미지로 테스트
curl -X POST http://localhost:8001/api/v1/b2b/restaurants/{id}/menus/upload-images \
  -F "files=@blurry_menu.jpg" | jq .

# 예상 결과:
# "fallback_triggered": true,
# "fallback_reason": "신뢰도 0.65"
# "provider": "clova"
```

#### 4-3. 매우 많은 메뉴 항목

```bash
# 100개 이상 메뉴 항목이 있는 이미지
curl -X POST http://localhost:8001/api/v1/b2b/restaurants/{id}/menus/upload-images \
  -F "files=@huge_menu.jpg" | jq .

# 예상 결과:
# "fallback_triggered": true,
# "fallback_reason": "메뉴 개수 이상 (156개)"
# "provider": "clova"
```

#### 4-4. 유효하지 않은 이미지

```bash
# 텍스트 파일을 이미지로 업로드
curl -X POST http://localhost:8001/api/v1/b2b/restaurants/{id}/menus/upload-images \
  -F "files=@text_file.txt" | jq .

# 예상 결과:
# "status": "failed",
# "error": "Invalid image: format not supported"
```

---

## 🚨 모니터링 대시보드 설정

### 1. Tier 1 성공률 추적

```sql
-- 매일 집계
SELECT
  DATE(created_at) as date,
  COUNT(*) as total,
  SUM(CASE WHEN triggered_fallback = false THEN 1 ELSE 0 END) as tier1_success,
  ROUND(100.0 * SUM(CASE WHEN triggered_fallback = false THEN 1 ELSE 0 END) / COUNT(*), 1) as success_rate
FROM ocr_metrics
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### 2. 폴백 이유 분석

```sql
SELECT
  fallback_reason,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM ocr_metrics WHERE triggered_fallback = true), 1) as percentage
FROM ocr_metrics
WHERE triggered_fallback = true
GROUP BY fallback_reason
ORDER BY count DESC;
```

### 3. 평균 처리 시간 추적

```sql
SELECT
  provider,
  ROUND(AVG(processing_time_ms), 0) as avg_time_ms,
  MIN(processing_time_ms) as min_time_ms,
  MAX(processing_time_ms) as max_time_ms,
  COUNT(*) as count
FROM ocr_metrics
GROUP BY provider
ORDER BY avg_time_ms DESC;
```

---

## 📊 배포 후 모니터링 규칙

| 메트릭 | 목표 | 경고 | 조치 |
|--------|------|------|------|
| **Tier 1 성공률** | 85%+ | < 70% | 🔴 GPT API 문제 조사 |
| **Tier 2 폴백률** | 10~15% | > 20% | 🟡 이미지 전처리 재검토 |
| **평균 처리 시간** | 3~4초 | > 5초 | 🟡 API 성능 모니터링 |
| **가격 파싱 에러** | < 5% | > 10% | 🟢 파싱 로직 최적화 |
| **캐시 히트율** | > 30% | < 10% | 🟢 정상 범위 |
| **API 에러율** | < 1% | > 2% | 🔴 즉시 조사 |

---

## 🔄 배포 단계별 실행 계획

### **Step 1: 로컬 테스트** (현재 위치)
```bash
cd ~/menu-knowledge/app/backend

# 1. 단위 테스트
pytest tests/services/test_ocr_*.py -v

# 2. 통합 테스트
pytest tests/api/test_b2b_bulk_upload.py -v

# 3. 서버 실행 및 수동 테스트
uvicorn main:app --host 127.0.0.1 --port 8001
```

### **Step 2: FastComet 배포**
```bash
ssh chargeap@d11475.sgp1.stableserver.net
cd ~/menu-knowledge/app/backend

# 1. 코드 업데이트
git pull origin master

# 2. 의존성 설치
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 3. 서비스 재시작
sudo systemctl restart menu-api

# 4. 헬스 체크
curl https://menu.chargeapp.net/api/v1/health | jq .
```

### **Step 3: 배포 후 테스트**
```bash
# 1. API 접근성 확인
curl https://menu.chargeapp.net/api/v1/health

# 2. B2B 엔드포인트 테스트
curl -X POST https://menu.chargeapp.net/api/v1/b2b/restaurants/{id}/menus/upload-images \
  -F "files=@menu.jpg"

# 3. 메트릭 조회
curl https://menu.chargeapp.net/api/v1/admin/ocr/metrics | jq .

# 4. 로그 확인
tail -50 ~/menu-api.log | grep -i "ocr\|tier\|fallback"
```

### **Step 4: 모니터링 & 최적화**
- Tier 1 성공률 추적 (목표: 85%+)
- 폴백 이유 분석
- 성능 병목 지점 파악
- 필요시 프롬프트/파라미터 조정

---

## ✅ 최종 체크리스트

- [ ] **사전 준비**
  - [ ] 환경 변수 확인 (OpenAI, CLOVA, Redis)
  - [ ] 의존성 설치 (openai, redis 패키지)
  - [ ] 데이터베이스 상태 확인
  - [ ] Redis 연결 테스트

- [ ] **로컬 테스트**
  - [ ] 단위 테스트 통과 (test_ocr_*.py)
  - [ ] 통합 테스트 통과 (test_b2b_bulk_upload.py)
  - [ ] 메트릭 수집 확인
  - [ ] 캐싱 일관성 확인

- [ ] **배포**
  - [ ] FastComet에 코드 푸시
  - [ ] 의존성 설치
  - [ ] 서비스 재시작
  - [ ] 헬스 체크 통과

- [ ] **배포 후 테스트**
  - [ ] API 접근성 확인
  - [ ] B2B 벌크 업로드 테스트
  - [ ] 메트릭 조회 테스트
  - [ ] 로그 확인 (에러 없음)

- [ ] **모니터링**
  - [ ] 대시보드 설정
  - [ ] 알림 규칙 정의
  - [ ] 첫 주간 집중 모니터링

---

**다음 단계**: FastComet 배포 (Step 2 실행)

