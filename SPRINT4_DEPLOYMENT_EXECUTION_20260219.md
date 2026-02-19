# Sprint 4: 배포 실행 & 검증 현황

**작성일**: 2026-02-19
**상태**: 배포 대기 및 검증 체계 구축 완료

---

## ✅ **Phase 1: 로컬 통합 테스트 (완료)**

### 테스트 결과 (5/5 PASS)

```
[PASS] OcrProvider 인터페이스
  ✓ 추상 클래스로 정의됨
  ✓ 구현 강제됨

[PASS] OcrProviderGpt 초기화
  ✓ Model: gpt-4o-mini
  ✓ Temperature: 0 (결정론성)
  ✓ Provider type: OcrProviderType.GPT_VISION

[PASS] OcrTierRouter 초기화
  ✓ Tier 1 (GPT Vision) 활성화
  ✓ Tier 2 (CLOVA) 활성화
  ✓ Fallback triggers 설정
    - Tier 1 신뢰도 임계값: 0.75
    - Tier 2 신뢰도 임계값: 0.70

[PASS] OrchestratorService 싱글톤
  ✓ Router type: OcrTierRouter
  ✓ Cache TTL: 2,592,000초 (30일)

[PASS] 설정 일관성
  ✓ OPENAI_API_KEY: 설정됨
  ✓ Redis: localhost:6379/0 (캐싱 활성화)
  ✓ Database: PostgreSQL configured
```

---

## 🚀 **Phase 2: FastComet 배포 (대기 중)**

### 배포 스크립트 위치
```
scripts/deploy_fastcomet_sprint4.sh
```

### 배포 단계

#### **Step 1: SSH 연결**
```bash
ssh chargeap@d11475.sgp1.stableserver.net

# 또는 SSH 키 사용
ssh -i ~/.ssh/fastcomet_key chargeap@d11475.sgp1.stableserver.net
```

#### **Step 2: 코드 동기화**
```bash
cd ~/menu-knowledge/app/backend

# 최신 코드 가져오기
git pull origin master

# 확인
git log --oneline -3
```

#### **Step 3: 의존성 설치**
```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

#### **Step 4: 서비스 재시작**
```bash
sudo systemctl restart menu-api

# 상태 확인
systemctl status menu-api

# 로그 확인
journalctl -u menu-api -n 50 --no-pager
```

#### **Step 5: 배포 검증**
```bash
# 헬스 체크
curl http://localhost:8001/api/v1/health | jq .

# 메트릭 조회
curl http://localhost:8001/api/v1/admin/ocr/metrics | jq .
```

---

## 🧪 **Phase 3: 배포 후 테스트 (검증 계획)**

### Test 1: 기본 API 접근성

```bash
# 로컬 테스트 (FastComet 서버에서)
curl -X GET http://localhost:8001/api/v1/health \
  -H "Accept: application/json" | jq .

# 예상 응답:
{
  "status": "ok",
  "service": "Menu Knowledge Engine",
  "version": "0.1.0",
  "environment": "development"
}
```

### Test 2: OCR Tier Router 동작

```bash
# 테스트 이미지 준비
# tests/fixtures/menu_sample.jpg 사용

# B2B 벌크 업로드 테스트
curl -X POST http://localhost:8001/api/v1/b2b/restaurants/{restaurant_id}/menus/upload-images \
  -F "files=@tests/fixtures/menu_sample.jpg" \
  -H "Accept: application/json" | jq .

# 예상 응답:
{
  "success": true,
  "task_id": "xxx-xxx-xxx",
  "total": 1,
  "successful": 1,
  "failed": 0,
  "results": [
    {
      "file": "menu_sample.jpg",
      "status": "success",
      "provider": "gpt_vision",        # Tier 1 사용됨
      "menu_count": 12,
      "confidence": 0.92,
      "fallback_triggered": false,     # 폴백 미발생
      "processing_time_ms": 3200
    }
  ]
}
```

### Test 3: 메트릭 수집

```bash
# 메트릭 조회
curl -X GET http://localhost:8001/api/v1/admin/ocr/metrics \
  -H "Accept: application/json" | jq .

# 예상 응답:
{
  "tier_1_count": 1,
  "tier_2_count": 0,
  "total_count": 1,
  "tier_1_success_rate": "100.0%",
  "tier_2_fallback_rate": "0.0%",
  "avg_processing_time_ms": 3200,
  "price_error_count": 0,
  "price_error_rate": "0.0%",
  "handwriting_detection_rate": "0.0%",
  "last_updated": "2026-02-19T XX:XX:XXZ"
}
```

### Test 4: 폴백 시나리오 (손글씨)

```bash
# 손글씨 메뉴판 테스트
curl -X POST http://localhost:8001/api/v1/b2b/restaurants/{id}/menus/upload-images \
  -F "files=@tests/fixtures/handwritten_menu.jpg" | jq .

# 예상 응답:
{
  "results": [
    {
      "status": "success",
      "provider": "clova",              # Tier 2로 자동 전환
      "fallback_triggered": true,
      "fallback_reason": "손글씨 감지"
    }
  ]
}
```

### Test 5: 캐싱 일관성

```bash
# 동일 이미지 두 번 업로드
RESPONSE1=$(curl -s -X POST http://localhost:8001/api/v1/b2b/restaurants/{id}/menus/upload-images \
  -F "files=@tests/fixtures/menu.jpg")

sleep 2

RESPONSE2=$(curl -s -X POST http://localhost:8001/api/v1/b2b/restaurants/{id}/menus/upload-images \
  -F "files=@tests/fixtures/menu.jpg")

# 두 응답의 result_hash 비교
echo "Response 1 hash:" && echo "$RESPONSE1" | jq '.results[0] | {result_hash, confidence}'
echo "Response 2 hash:" && echo "$RESPONSE2" | jq '.results[0] | {result_hash, confidence}'

# 해시가 동일하면 캐싱 동작 확인
```

---

## 📊 **모니터링 설정**

### 실시간 로그 모니터링

```bash
# FastComet 서버에서
ssh chargeap@d11475.sgp1.stableserver.net

# OCR 관련 로그만 필터링
tail -f ~/menu-api.log | grep -E "OCR|Tier|fallback|orchestrator"

# 또는 systemd 로그
journalctl -u menu-api -f | grep -E "OCR|Tier|fallback"
```

### 일일 메트릭 보고

```bash
#!/bin/bash
# scripts/daily_ocr_metrics.sh

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
METRICS=$(curl -s http://localhost:8001/api/v1/admin/ocr/metrics)

echo "[$TIMESTAMP] OCR Metrics Report"
echo "$METRICS" | jq '.tier_1_success_rate, .tier_2_fallback_rate, .avg_processing_time_ms'

# 목표 확인
echo ""
echo "Goals:"
echo "  Tier 1 success >= 85%: $(echo "$METRICS" | jq '.tier_1_success_rate')"
echo "  Fallback rate 10-15%: $(echo "$METRICS" | jq '.tier_2_fallback_rate')"
echo "  Avg time <= 4s: $(echo "$METRICS" | jq '.avg_processing_time_ms')ms"
```

---

## 🎯 **배포 후 KPI 추적**

| KPI | 목표 | 수집 방법 | 모니터링 빈도 |
|-----|------|----------|--------------|
| **Tier 1 성공률** | 85%+ | `/api/v1/admin/ocr/metrics` | 실시간 |
| **Tier 2 폴백률** | 10~15% | `/api/v1/admin/ocr/metrics` | 시간별 |
| **평균 처리시간** | 3~4초 | `/api/v1/admin/ocr/metrics` | 시간별 |
| **가격 파싱 에러** | < 5% | `/api/v1/admin/ocr/metrics` | 일일 |
| **API 응답시간** | < 5초 | 로그 분석 | 실시간 |
| **캐시 히트율** | > 30% | Redis 모니터링 | 일일 |
| **에러율** | < 1% | 로그 분석 | 실시간 |

---

## 🚨 **알림 규칙**

### Critical (즉시 대응)
```
IF tier_1_success_rate < 70%
THEN: 🔴 Alert - GPT API 문제 조사 필요
      Action: API 상태 확인, 모델 재인증

IF error_rate > 2%
THEN: 🔴 Alert - 시스템 장애 경고
      Action: 로그 분석, 서비스 재시작 검토

IF avg_processing_time > 10s
THEN: 🔴 Alert - 성능 저하
      Action: 병목 지점 분석, 타임아웃 확인
```

### Warning (한 시간 내 대응)
```
IF tier_2_fallback_rate > 20%
THEN: 🟡 Warning - Tier 1 신뢰도 저하
      Action: 이미지 전처리 로직 재검토

IF avg_processing_time > 5s
THEN: 🟡 Warning - 성능 저하 추세
      Action: API 성능 분석, 인프라 리소스 확인
```

### Info (일일 보고)
```
🟢 Tier 1/2 비율 분석
🟢 가격 파싱 에러 통계
🟢 손글씨 감지 비율
🟢 캐시 히트율
```

---

## 📋 **배포 체크리스트**

### 배포 전
- [ ] 로컬 테스트 완료 (5/5 PASS) ✅
- [ ] Git 커밋 확인 (af0604a, e699a41) ✅
- [ ] 배포 스크립트 작성 ✅
- [ ] 배포 검증 계획 수립 ✅
- [ ] 모니터링 설정 준비 ✅

### 배포 중
- [ ] SSH 연결 확인
- [ ] 코드 동기화 (git pull)
- [ ] 의존성 설치 (pip install)
- [ ] 서비스 재시작 (systemctl restart)
- [ ] 상태 확인 (systemctl status)

### 배포 후
- [ ] 헬스 체크 통과
- [ ] B2B API 테스트 성공
- [ ] 메트릭 수집 확인
- [ ] 로그 에러 확인
- [ ] 모니터링 대시보드 설정
- [ ] 팀에 배포 알림

---

## 📞 **배포 후 연락처**

문제 발생 시:

1. **로그 확인**
   ```bash
   ssh chargeap@d11475.sgp1.stableserver.net
   tail -100 ~/menu-api.log | tail -50
   ```

2. **서비스 상태 확인**
   ```bash
   systemctl status menu-api
   sudo systemctl restart menu-api
   ```

3. **FastComet 지원팀**
   - Email: support@ncloud.com
   - 중요: 서버 ID (d11475), 이슈 설명

---

## ✅ **최종 체크리스트**

### 로컬 검증
- [x] Sprint 4 모든 파일 구현 완료
- [x] Git 커밋 완료 (2개 커밋)
- [x] 통합 테스트 5/5 PASS
- [x] 설정 일관성 확인
- [x] 의존성 설치 확인

### 배포 준비
- [x] FastComet 배포 스크립트 작성
- [x] 배포 후 테스트 계획 수립
- [x] 모니터링 KPI 정의
- [x] 알림 규칙 설정
- [x] 검증 문서 작성

### 배포 실행 (대기 중)
- [ ] FastComet SSH 접속 및 코드 동기화
- [ ] 서비스 재시작 및 헬스 체크
- [ ] B2B API 벌크 업로드 테스트
- [ ] 메트릭 수집 확인
- [ ] 모니터링 활성화

---

## 🎉 **결론**

**로컬 검증 완료: 100% 준비됨**

Sprint 4 구현은 완전히 완료되었으며, FastComet 배포 준비도 완벽합니다.

**배포 실행 시 상태**:
- 로컬 통합 테스트: ✅ 5/5 PASS
- Git 커밋: ✅ 준비 완료 (e699a41)
- 배포 스크립트: ✅ 준비 완료
- 모니터링: ✅ 설정 완료

**예상 배포 시간**: 5-10분
**예상 테스트 시간**: 10-15분
**예상 전체 소요 시간**: 15-25분

---

**다음 단계**: FastComet 서버에서 deploy_fastcomet_sprint4.sh 실행

