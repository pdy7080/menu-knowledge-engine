# CLOVA OCR 설정 가이드

**작성일**: 2026-02-18
**목적**: CLOVA OCR API 키 발급 및 설정 방법 안내

---

## 개요

Menu Knowledge Engine은 메뉴판 이미지 인식을 위해 **Naver Cloud의 CLOVA OCR** 서비스를 사용합니다.
이 가이드는 CLOVA OCR API 키를 발급받아 프로젝트에 설정하는 방법을 설명합니다.

---

## 1단계: Naver Cloud 가입

### 1-1. Naver Cloud Console 접속

- URL: https://console.ncloud.com/
- 네이버 계정으로 로그인
- 신규 사용자: 무료 크레딧 제공 (₩100,000)

### 1-2. 결제 정보 등록

- Console → 결제 관리 → 결제 수단 등록
- 신용카드 또는 계좌 등록 (무료 크레딧 소진 후 과금)

---

## 2단계: CLOVA OCR 서비스 생성

### 2-1. AI·NAVER API 메뉴 진입

1. Naver Cloud Console 메인 페이지
2. 좌측 메뉴 → **AI·NAVER API**
3. **CLOVA OCR** 선택

### 2-2. Custom OCR 도메인 생성

1. "도메인 생성" 버튼 클릭
2. 도메인 타입: **Custom OCR**
3. 도메인 이름: `menu-ocr` (예시)
4. 템플릿: **General** (일반 문서 인식)
5. 생성 확인

### 2-3. API 엔드포인트 확인

- 생성된 도메인 클릭
- API Gateway Invoke URL 확인 (예: `https://kko5u71wza.apigw.ntruss.com/...`)
- 이 URL은 `app/backend/services/ocr_service.py`의 `self.clova_api_url`에 이미 설정됨

---

## 3단계: API 인증 키 발급

### 3-1. Secret Key 발급

1. CLOVA OCR 도메인 상세 페이지
2. **API Gateway** 탭 선택
3. **Secret Key** 확인 (숨김 처리됨)
4. "복사" 버튼으로 복사

이 값이 `.env` 파일의 `CLOVA_OCR_SECRET`입니다.

### 3-2. API Key 확인 (선택 사항)

- CLOVA OCR v2는 Secret Key만으로 인증 가능
- API Key가 별도로 필요한 경우, 콘솔에서 확인

---

## 4단계: 환경 변수 설정

### 4-1. .env 파일 생성

프로젝트 루트의 `app/backend/` 폴더에서:

```bash
# .env.example 복사
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 VS Code로 열기
```

### 4-2. CLOVA OCR 설정 추가

`.env` 파일에서 아래 값 입력:

```bash
# CLOVA OCR API (for menu image recognition)
CLOVA_OCR_SECRET=your_secret_key_here_from_step_3_1
CLOVA_OCR_API_KEY=  # 선택 사항, 비워둬도 됨
```

**예시**:
```bash
CLOVA_OCR_SECRET=abc123def456ghi789jkl012mno345pqr678stu901vwx234
```

---

## 5단계: 설정 테스트

### 5-1. Python 환경 확인

```bash
cd app/backend
source venv/bin/activate  # 가상환경 활성화

# 환경 변수 로드 확인
python -c "from config import get_settings; print(get_settings().CLOVA_OCR_SECRET)"
```

**기대 출력**: API Secret Key 값이 출력되어야 함

### 5-2. OCR 서비스 테스트

샘플 메뉴 이미지로 테스트:

```bash
# 샘플 이미지 다운로드 (예시)
wget https://example.com/sample_menu.jpg -O test_menu.jpg

# Python 스크립트로 테스트
python << EOF
import asyncio
from services.ocr_service import ocr_service

async def test():
    result = await ocr_service.recognize_menu_image('test_menu.jpg')
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Menu Items: {result['menu_items']}")
        print(f"Confidence: {result['ocr_confidence']}")
    else:
        print(f"Error: {result.get('error')}")

asyncio.run(test())
EOF
```

**기대 출력**:
```
Success: True
Menu Items: [{'name_ko': '김치찌개', 'price_ko': '8,000'}, ...]
Confidence: 0.95
```

### 5-3. API 엔드포인트 테스트

FastAPI 서버 실행:

```bash
uvicorn main:app --reload --port 8001
```

다른 터미널에서:

```bash
curl -X POST "http://localhost:8001/api/v1/menu/recognize" \
  -F "file=@test_menu.jpg"
```

**기대 응답**:
```json
{
  "success": true,
  "menu_items": [
    {"name_ko": "김치찌개", "price_ko": "8,000"},
    {"name_ko": "된장찌개", "price_ko": "7,000"}
  ],
  "raw_text": "김치찌개 8,000원\n된장찌개 7,000원",
  "ocr_confidence": 0.95,
  "count": 2
}
```

---

## 6단계: 프로덕션 배포

### 6-1. FastComet 서버에 설정

```bash
# SSH 접속
ssh chargeap@d11475.sgp1.stableserver.net

# 프로젝트 디렉토리로 이동
cd ~/menu-knowledge/app/backend

# .env 파일 편집
nano .env

# CLOVA_OCR_SECRET 추가 (로컬과 동일한 값)
```

### 6-2. 서비스 재시작

```bash
# uvicorn 프로세스 재시작
kill $(ps aux | grep 'uvicorn main:app' | awk '{print $2}')
nohup uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2 > ~/menu-knowledge-server.log 2>&1 &

# 로그 확인
tail -f ~/menu-knowledge-server.log
```

---

## 문제 해결

### 에러: "CLOVA_OCR_SECRET not configured"

**원인**: .env 파일에 Secret Key가 설정되지 않음

**해결**:
1. `.env` 파일 존재 확인
2. `CLOVA_OCR_SECRET=` 값 확인
3. 서버 재시작

### 에러: "CLOVA OCR API error: 401 Unauthorized"

**원인**: Secret Key가 잘못됨

**해결**:
1. Naver Cloud Console에서 Secret Key 재확인
2. 복사 시 공백 문자 포함 여부 확인
3. `.env` 파일에 올바른 값 입력 후 재시작

### 에러: "CLOVA OCR API error: 403 Forbidden"

**원인**: API Gateway Invoke URL이 잘못됨

**해결**:
1. `app/backend/services/ocr_service.py` Line 27 확인
2. Naver Cloud Console에서 정확한 URL 복사
3. `self.clova_api_url` 값 업데이트

### 에러: "OCR processing timeout"

**원인**: 이미지 크기가 너무 크거나 네트워크 지연

**해결**:
1. 이미지 크기 확인 (10MB 이하 권장)
2. 네트워크 연결 확인
3. `services/ocr_service.py` Line 119 timeout 값 증가 (현재 30초)

---

## 비용 구조

### CLOVA OCR 요금

| 항목 | 단가 |
|------|------|
| Custom OCR | ₩3 / 건 |
| 무료 크레딧 | ₩100,000 (신규 가입) |

**예상 비용**:
- 월 10,000건 스캔 시: ₩30,000/월
- 월 50,000건 스캔 시: ₩150,000/월

**비용 절감 전략**:
1. DB 히트율 70%+ 유지 → AI 호출 최소화
2. 이미지 전처리로 OCR 정확도 향상 → 재시도 감소
3. Redis 캐싱으로 중복 스캔 방지

---

## 참고 자료

- **Naver Cloud Console**: https://console.ncloud.com/
- **CLOVA OCR 문서**: https://api.ncloud-docs.com/docs/ai-application-service-ocr
- **API Reference**: https://api.ncloud-docs.com/docs/ai-application-service-ocr-ocr
- **요금표**: https://www.ncloud.com/product/aiService/ocr

---

**최종 수정**: 2026-02-18
**작성자**: Menu Knowledge Engine Team
