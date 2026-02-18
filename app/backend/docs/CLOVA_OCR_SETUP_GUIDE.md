# CLOVA OCR 설정 가이드

**작성일**: 2026-02-18
**목표**: Menu Knowledge Engine에 CLOVA OCR을 통합하고 프로덕션 배포
**참고**: Sprint 3B - OCR Pipeline 구축

---

## 개요

CLOVA OCR은 네이버의 AI 기반 광학 문자 인식 서비스입니다. 메뉴판 사진에서 한글/영문 텍스트를 자동으로 추출합니다.

- **정확도**: 한글 95%+, 영문 90%+
- **처리 속도**: 이미지당 2-5초
- **비용**: ₩3/건 (월 10,000건 = ₩30,000)

---

## 사전 준비

### 필수 조건
- Naver Cloud Platform 계정
- 결제 수단 등록
- Root Account 또는 NCLOUD Manager 권한

### 지원 형식
- 이미지: JPG, PNG (최대 5MB)
- 언어: 한글, 영문 및 혼합

---

## Step 1: Naver Cloud Console 접속

1. https://console.ncloud.com/ 접속
2. 계정 로그인
3. 좌측 메뉴에서 **"AI·NAVER API"** 선택

```
Console Home
├─ AI·NAVER API ← 클릭
│  ├─ CLOVA OCR ← 선택
│  └─ ...
```

---

## Step 2: CLOVA OCR 서비스 생성

### 2-1. 서비스 선택

**AI·NAVER API** → **OCR** → **신청** 클릭

![CLOVA OCR Selection]

### 2-2. 요금제 선택

| 요금제 | 월 처리량 | 가격 |
|-------|---------|------|
| **Classic** | 0-100,000 건 | 건당 ₩3 |
| **Enterprise** | 100,000+ 건 | 별도 문의 |

**선택**: Classic (우리는 초기에 월 10,000건 예상)

### 2-3. 약관 동의 및 신청

- 서비스 약관 동의
- "신청" 버튼 클릭
- 신청 완료 (즉시 활성화)

---

## Step 3: API 인증 키 발급

### 3-1. 발급 페이지 이동

**AI·NAVER API** → **CLOVA OCR** → **인증 정보**

### 3-2. 키 복사

다음 두 가지 정보를 복사합니다:

```
┌─────────────────────────────────────┐
│  API Gateway URL                    │
│  https://...apigw.ntruss.com/...    │
│  (이미 설정되어 있음)               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Secret Key (API 인증 키)           │
│  aBcDeFgHiJkLmNoPqRsTuVwXyZ1234...  │ ← 복사
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  API Key (선택, 고급 사용)          │
│  (일반적으로 필요 없음)             │
└─────────────────────────────────────┘
```

⚠️ **보안 주의**: Secret Key는 절대 공개하지 마세요!

---

## Step 4: 환경 변수 설정

### 4-1. 로컬 개발 환경

**파일**: `.env` (프로젝트 루트)

```bash
# CLOVA OCR 설정
CLOVA_OCR_SECRET=aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890AbCdEfGhIjKl
CLOVA_OCR_API_URL=https://kko5u71wza.apigw.ntruss.com/custom/v1/33367/...
```

### 4-2. 프로덕션 환경 (FastComet)

**파일**: `~/.env` (홈 디렉토리, SSH)

```bash
ssh chargeap@d11475.sgp1.stableserver.net

# FastComet 서버에서
cd ~/menu-knowledge/app/backend
echo "CLOVA_OCR_SECRET=your_secret_key_here" >> .env
echo "CLOVA_OCR_API_URL=your_api_url_here" >> .env

# 확인
cat .env | grep CLOVA
```

---

## Step 5: 설정 테스트

### 5-1. 로컬 테스트

```bash
cd app/backend

# 1. 환경 변수 확인
python -c "
from config import settings
print(f'CLOVA_OCR_SECRET: {settings.CLOVA_OCR_SECRET[:20]}...')
print(f'CLOVA_OCR_API_URL: {settings.CLOVA_OCR_API_URL}')
"

# 2. OCR 서비스 초기화
python -c "
from services.ocr_service import ocr_service
print('✅ OCR Service initialized')
"

# 3. 테스트 이미지 준비
# tests/fixtures/menu_sample.jpg 에 샘플 메뉴판 이미지 배치

# 4. 실제 OCR 테스트
python -c "
from services.ocr_service import ocr_service
result = ocr_service.recognize_menu_image('tests/fixtures/menu_sample.jpg')
print(f'Success: {result.get(\"success\")}')
if result.get('menu_items'):
    for item in result['menu_items'][:3]:
        print(f'  - {item}')
"
```

### 5-2. 서버 테스트 (FastComet)

```bash
# HTTP 요청으로 테스트
curl -X POST http://localhost:8001/api/v1/menu/recognize \
  -F "file=@sample_menu.jpg" | jq '.ocr_text'

# 응답 예시:
# [
#   {"name_ko": "뼈해장국", "price_ko": "12000원"},
#   {"name_ko": "갈비", "price_ko": "15000원"}
# ]
```

---

## Step 6: 프로덕션 배포

### 6-1. FastComet 배포

```bash
# 1. SSH 접속
ssh chargeap@d11475.sgp1.stableserver.net

# 2. 코드 동기화
cd ~/menu-knowledge/app/backend
git pull origin master

# 3. 환경 변수 설정 (위의 Step 4-2 참조)
# .env 파일에 CLOVA_OCR_SECRET 추가

# 4. 서비스 재시작
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart menu-api

# 5. 헬스 체크
curl https://menu.chargeapp.net/api/v1/health | jq .

# 6. 로그 확인
tail -20 ~/menu-api.log
```

### 6-2. 모니터링 설정

```bash
# CloudWatch에 CLOVA 요청 시간 기록
# (자동으로 logs에 기록됨)

# 에러 모니터링
grep -i "clova\|ocr" ~/menu-api.log | tail -20
```

---

## Step 7: 비용 모니터링

### 월별 비용 추정

| 월 건수 | 금액 |
|--------|------|
| 1,000 | ₩3,000 |
| 5,000 | ₩15,000 |
| 10,000 | ₩30,000 |
| 50,000 | ₩150,000 |
| 100,000+ | 별도 문의 |

### 신용 잔액 확인

1. Naver Cloud Console 접속
2. 우측 상단 **"요금 및 이용"** 클릭
3. **"이용 내역"** → **"CLOVA OCR"** 확인

### 경고 설정

```
예산 한도 초과 알림:
- 월 ₩50,000 초과 시 이메일 알림 설정 권장
- Console → 알림 → 비용 알림
```

---

## 문제 해결

### Q1: "401 Unauthorized" 오류

**원인**: Secret Key가 잘못되었거나 만료됨

**해결**:
```bash
# 1. Secret Key 재확인
# Naver Cloud Console → CLOVA OCR → 인증 정보

# 2. 환경 변수 다시 설정
echo "CLOVA_OCR_SECRET=새로운_키" >> ~/.env

# 3. 서비스 재시작
source venv/bin/activate
sudo systemctl restart menu-api
```

### Q2: "429 Too Many Requests" 오류

**원인**: API 호출 한도 초과 (분당 100건)

**해결**:
```python
# 요청 대기 시간 추가
import time
time.sleep(1)  # 1초 대기 후 재시도
```

### Q3: OCR 정확도가 낮음

**원인**: 이미지 품질 문제

**개선 방법**:
```python
# 1. 이미지 전처리 활성화 (기본값: True)
from services.ocr_service import ocr_service
result = ocr_service.recognize_menu_image(
    'menu.jpg',
    enable_preprocessing=True  # ← 활성화
)

# 2. 이미지 요구사항:
#    - 해상도: 1920x1080 이상 권장
#    - 밝기: 충분한 조명
#    - 각도: 수평 또는 수직
#    - 대비: 명확한 텍스트
```

### Q4: "Connection timeout" 오류

**원인**: 네트워크 또는 Naver Cloud 서버 응답 지연

**해결**:
```bash
# 1. 네트워크 확인
ping kko5u71wza.apigw.ntruss.com

# 2. 재시도 로직 (이미 구현됨)
# services/ocr_service.py에서 자동 재시도 3회

# 3. 최악의 경우 graceful fallback
# 전처리된 이미지만 저장 후 수동 처리 필요
```

---

## FAQ

### Q: CLOVA 대신 로컬 OCR 사용 가능한가?

**A**: 가능합니다 (Sprint 5 예정):
- Tesseract: 한글 지원, 무료
- EasyOCR: 정확도 높음, GPU 필요
- 단점: 정확도 Naver 70% 대 vs 95%+

### Q: 비용 절감 방법?

**A**:
1. 이미지 전처리로 정확도 향상 → 재시도 감소 (10-15% 비용 절감)
2. Redis 캐싱으로 중복 요청 방지
3. 백그라운드 처리로 오류율 감소

### Q: API 한도가 부족하면?

**A**: Enterprise 플랜 신청
- Naver Cloud → CLOVA OCR → 요금제 변경
- 별도 SLA 제공
- 회사 규모 확인 후 가격 협의

---

## 지원

### 연락처
- **기술 문의**: Naver Cloud Support (console.ncloud.com)
- **결제 문의**: support@ncloud.com
- **긴급 대응**: 24/7 지원

### 참고 문서
- [CLOVA OCR 공식 가이드](https://guide.ncloud-docs.com/docs/ocr-overview)
- [API 스펙](https://guide.ncloud-docs.com/docs/ocr-api)
- [가격 정보](https://www.ncloud.com/product/aiService/ocr)

---

**마지막 업데이트**: 2026-02-18
**상태**: Sprint 3B - 완료
