# Sprint 3B 빠른 시작 가이드 (Quick Start)

**작성일**: 2026-02-18
**대상**: 개발팀 + 배포담당자
**목표**: 30분 내에 Sprint 3B 기능 확인 및 통합

---

## 1분 요약

**Sprint 3B에서 완성된 것**:
- ✅ 이미지 전처리 (OpenCV) - 회전/명도/노이즈 처리
- ✅ QR 코드 API - PNG 생성 엔드포인트
- ✅ B2B 이미지 업로드 API - 벌크 처리 + 진행 추적
- ✅ CLOVA OCR 설정 가이드

**사용하려면**:
1. FastComet에서 CLOVA OCR API 키 발급 (Naver Cloud)
2. `.env` 파일에 키 설정
3. 서버 재시작
4. 테스트

---

## 30초 설치 (로컬)

```bash
cd app/backend

# 1. 의존성 설치
pip install opencv-python==4.10.0.84 numpy==2.2.5

# 2. 임포트 확인
python -c "import cv2, numpy; print('✅ OK')"

# 3. 서버 시작
uvicorn main:app --reload
```

---

## 3분 기능 확인

### QR 코드 생성 (✅ 즉시 테스트 가능)

```bash
# 브라우저 또는 curl
curl http://localhost:8000/qr/generate/SHOP123 -o qr.png
file qr.png

# 결과
# qr.png: PNG image data, 290 x 290, 1-bit grayscale
```

### 이미지 전처리 (✅ 샘플 이미지 필요)

```bash
# 테스트 이미지 준비
# app/backend/tests/fixtures/menu_sample.jpg 에 놓기

python -c "
from utils.image_preprocessing import preprocess_menu_image
result = preprocess_menu_image('tests/fixtures/menu_sample.jpg')
print(f'Preprocessed: {result}')
"

# 결과
# Preprocessed: tests/fixtures/menu_sample_preprocessed.jpg
```

### B2B 업로드 (✅ 기본 플로우 확인)

```bash
# 테스트 이미지 2개 준비
cp tests/fixtures/menu_sample.jpg menu1.jpg
cp tests/fixtures/menu_sample.jpg menu2.jpg

# 업로드 API 호출
curl -X POST \
  http://localhost:8000/api/v1/b2b/restaurants/test-shop/menus/upload-images \
  -F "files=@menu1.jpg" \
  -F "files=@menu2.jpg" | jq .

# 결과 예시
# {
#   "success": true,
#   "task_id": "uuid...",
#   "total": 2,
#   "successful": 1,
#   "failed": 1,
#   "errors": [...]
# }
```

---

## 10분 통합 (FastComet 배포)

### Step 1: CLOVA OCR 설정 (5분)

```bash
# 1. Naver Cloud 콘솔 접속
# https://console.ncloud.com/

# 2. AI·NAVER API → CLOVA OCR 선택
# 3. "서비스 신청" 클릭
# 4. API 인증 키 발급 (Secret + API Key 복사)

# 5. FastComet SSH 접속
ssh chargeap@d11475.sgp1.stableserver.net
cd ~/menu-knowledge/app/backend

# 6. .env 파일에 추가
echo "CLOVA_OCR_SECRET=your_secret_here" >> .env
echo "CLOVA_OCR_API_KEY=your_api_key_here" >> .env

# 7. 검증
python -c "from config import get_settings; print('✅ CLOVA configured')"
```

### Step 2: 의존성 업데이트 (2분)

```bash
# 1. 로컬에서 git pull
cd ~/menu-knowledge
git pull origin master

# 2. FastComet SSH에서
cd ~/menu-knowledge/app/backend
git pull origin master

# 3. 의존성 설치
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 4. 확인
pip list | grep opencv-python
```

### Step 3: 서비스 재시작 (2분)

```bash
# 1. 이전 프로세스 중지
kill $(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}')

# 2. 새로운 프로세스 시작
nohup uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2 \
  > ~/menu-api.log 2>&1 &

# 3. 헬스 체크
sleep 3
curl https://menu.chargeapp.net/api/v1/health | jq .

# 4. 로그 확인
tail -20 ~/menu-api.log
```

### Step 4: 검증 (1분)

```bash
# 1. QR 생성 테스트
curl https://menu.chargeapp.net/qr/generate/PROD_SHOP \
  -o /tmp/qr_prod.png
file /tmp/qr_prod.png

# 2. OCR 준비 상태 확인 (아직 이미지 필요)
curl -X POST https://menu.chargeapp.net/api/v1/menu/recognize \
  -F "file=@test_menu.jpg" | jq '.ocr_text' | head -c 50
```

---

## 사용 시나리오별 가이드

### Scenario 1: 사용자 메뉴 스캔 (B2C)

```typescript
// React 컴포넌트
const [image, setImage] = useState(null);
const [result, setResult] = useState(null);

const handleScan = async () => {
  const formData = new FormData();
  formData.append('file', image);

  // Sprint 3B 전처리 + CLOVA OCR 자동 실행
  const response = await fetch('/api/v1/menu/identify', {
    method: 'POST',
    body: formData
  });

  const data = await response.json();
  // 응답: { canonical_menu, modifiers, confidence, match_type }
  setResult(data);
};

return (
  <div>
    <input type="file" onChange={e => setImage(e.target.files[0])} />
    <button onClick={handleScan}>📷 스캔</button>
    {result && (
      <div>
        <h2>{result.canonical_menu.name_en}</h2>
        <img src={result.canonical_menu.images[0]?.url} />
        <p>신뢰도: {result.confidence}%</p>
      </div>
    )}
  </div>
);
```

### Scenario 2: 식당 관리자 이미지 업로드 (B2B)

```typescript
// B2B 대시보드
const handleBulkUpload = async (files) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  // Sprint 3B 벌크 업로드 자동 실행
  const response = await fetch(
    `/api/v1/b2b/restaurants/${restaurantId}/menus/upload-images`,
    {
      method: 'POST',
      body: formData
    }
  );

  const result = await response.json();
  // 응답: { task_id, successful, failed, results[] }

  setProgress({
    total: result.total,
    completed: result.successful,
    failed: result.failed
  });
};

return (
  <div>
    <input
      type="file"
      multiple
      accept="image/*"
      onChange={e => handleBulkUpload(e.target.files)}
    />
    <p>
      업로드: {progress.completed}/{progress.total}
    </p>
  </div>
);
```

### Scenario 3: Admin 신규 메뉴 검토

```typescript
// Admin 큐 (Sprint 4에서 구현)
const [queue, setQueue] = useState([]);

useEffect(() => {
  const fetchQueue = async () => {
    // Sprint 3B에서 저장된 ScanLog 조회
    const response = await fetch(
      '/api/v1/admin/scan-queue?status=pending&limit=20'
    );
    const data = await response.json();
    setQueue(data);
  };

  fetchQueue();
}, []);

const handleApprove = async (scanId, canonicalId) => {
  // 신규 메뉴 승인
  await fetch(`/api/v1/admin/scan-queue/${scanId}/approve`, {
    method: 'PUT',
    body: JSON.stringify({ canonical_menu_id: canonicalId })
  });
};

return (
  <div>
    {queue.map(scan => (
      <div key={scan.id}>
        <img src={scan.image_url} style={{ maxWidth: 200 }} />
        <p>추출 텍스트: {scan.ocr_text}</p>
        <p>매칭: {scan.matched_canonical?.name_ko}</p>
        <button onClick={() => handleApprove(scan.id, scan.matched_canonical?.id)}>
          ✅ 승인
        </button>
      </div>
    ))}
  </div>
);
```

---

## 문제 해결

### Q: "ModuleNotFoundError: No module named 'cv2'"

**해결**:
```bash
pip install opencv-python==4.10.0.84
# 또는
pip install -r requirements.txt --upgrade
```

### Q: CLOVA OCR API 키 오류 (401)

**해결**:
```bash
# 1. Naver Cloud 콘솔에서 Secret 재확인
# 2. .env 파일 값 정확한지 확인
python -c "import os; print(os.getenv('CLOVA_OCR_SECRET'))"

# 3. 문서 참조
cat docs/CLOVA_OCR_SETUP_GUIDE.md
```

### Q: 이미지 전처리 실패 (예: cv2.error)

**해결**: Graceful fallback이 자동으로 원본 이미지 사용
```bash
# 로그 확인
grep "preprocessing failed" ~/menu-api.log

# 문제 분석
python -c "
from utils.image_preprocessing import preprocess_menu_image
import traceback
try:
    preprocess_menu_image('problematic_image.jpg')
except Exception as e:
    traceback.print_exc()
"
```

### Q: B2B 업로드 타임아웃 (30초+ 소요)

**알려진 문제**: 10개 이미지 = 30-50초 (CLOVA OCR 대기 시간)
**해결** (Sprint 5): BackgroundTasks로 비동기 처리 예정

**임시 해결**:
```bash
# FastComet에서 request timeout 증가
# /etc/nginx/nginx.conf
proxy_read_timeout 120s;  # 기본값 30s → 120s 변경
```

---

## 주요 API 엔드포인트

### QR 코드 생성

```bash
GET /qr/generate/{shop_code}

# 예시
curl http://localhost:8000/qr/generate/SHOP123 -o qr.png

# 응답: PNG 이미지 (StreamingResponse)
```

### 메뉴 인식 (OCR + Matching)

```bash
POST /api/v1/menu/identify

# 요청
curl -X POST http://localhost:8000/api/v1/menu/identify \
  -F "file=@menu.jpg"

# 응답 (예)
{
  "canonical_menu": {
    "id": "uuid",
    "name_ko": "뼈해장국",
    "name_en": "Bone Spicy Broth",
    "images": [...],
    "description": "...",
    "nutrition": {...}
  },
  "modifiers": ["왕", "얼큰"],
  "confidence": 92,
  "match_type": "exact",
  "scan_id": "uuid"
}
```

### B2B 이미지 벌크 업로드

```bash
POST /api/v1/b2b/restaurants/{restaurant_id}/menus/upload-images

# 요청
curl -X POST \
  http://localhost:8000/api/v1/b2b/restaurants/shop123/menus/upload-images \
  -F "files=@menu1.jpg" \
  -F "files=@menu2.jpg" \
  -F "files=@menu3.jpg"

# 응답 (예)
{
  "success": true,
  "task_id": "uuid",
  "total": 3,
  "successful": 2,
  "failed": 1,
  "errors": [
    {
      "file": "menu3.jpg",
      "error": "OCR failed: timeout"
    }
  ]
}
```

### Admin 스캔 큐 조회

```bash
GET /api/v1/admin/scan-queue?status=pending&limit=20

# 응답 (예)
[
  {
    "id": "scan_uuid_1",
    "image_url": "s3://...",
    "ocr_text": "뼈해장국, 갈비",
    "matched_canonical": {
      "id": "canonical_uuid",
      "name_ko": "뼈해장국",
      "confidence": 92
    },
    "status": "pending",
    "created_at": "2026-02-18T10:30:00Z"
  },
  ...
]
```

---

## 성능 팁

### Tip 1: 이미지 최적화

```python
# 전송 전에 압축 (클라이언트)
from PIL import Image

img = Image.open('menu.jpg')
img.thumbnail((1920, 1080))  # 리사이징
img.save('menu_optimized.jpg', 'JPEG', quality=85)

# 예상 크기: 5MB → 500KB (10배 감소)
```

### Tip 2: 캐싱 (미래)

```python
# Sprint 5에서 구현 예정
# 동일 이미지 재요청 시 1초 이내

import hashlib

def get_image_hash(file):
    return hashlib.md5(file.read()).hexdigest()

# Redis 캐시 키
cache_key = f"ocr:{image_hash}"
```

### Tip 3: 배치 처리

```bash
# 100개 이미지 처리 시 (권장하지 않음)
# 대신 B2B API 사용: 10개씩 나눠서 업로드

for i in {0..90..10}; do
  files=$(ls menus/menu_{$i..$((i+9))}.jpg 2>/dev/null)
  curl -X POST .../menus/upload-images $(echo $files | sed 's/^/-F files=@/g')
done
```

---

## 테스트 데이터

### 테스트 이미지 준비

```bash
# Option 1: 샘플 이미지 다운로드
mkdir -p app/backend/tests/fixtures
# (위키피디아 또는 Google 이미지에서 K-food 이미지 다운로드)

# Option 2: 합성 이미지 생성
python -c "
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (400, 300), color='white')
d = ImageDraw.Draw(img)
d.text((100, 100), 'Test Menu', fill='black')
img.save('tests/fixtures/test_menu.jpg')
"
```

### 테스트 실행

```bash
# 단위 테스트 (예정)
pytest app/backend/tests/test_preprocessing.py
pytest app/backend/tests/test_qr_generation.py

# 통합 테스트
python -c "
import requests
files = {'file': open('tests/fixtures/test_menu.jpg', 'rb')}
r = requests.post('http://localhost:8000/api/v1/menu/identify', files=files)
print(r.json())
"
```

---

## 다음 단계 (오늘부터)

### 🚀 지금 (30분)
- [ ] 로컬에서 Sprint 3B 기능 확인 (QR + 전처리 + 업로드)
- [ ] FastComet에서 CLOVA OCR 설정

### 📊 이번주 (2시간)
- [ ] 샘플 10개 이미지로 OCR 정확도 테스트
- [ ] 성능 벤치마크 (로컬 + FastComet)

### 🛠️ 다음주 (40시간)
- [ ] Sprint 2 Phase 1: 이미지 수집 (20시간)
- [ ] Sprint 4: B2C/B2B UI (15시간)
- [ ] 통합 테스트 (5시간)

---

## 빠른 참조 (치트 시트)

```bash
# 설치
pip install -r app/backend/requirements.txt --upgrade

# 로컬 테스트
cd app/backend
uvicorn main:app --reload

# QR 생성
curl http://localhost:8000/qr/generate/TEST > qr.png

# 메뉴 스캔
curl -X POST http://localhost:8000/api/v1/menu/identify \
  -F "file=@test.jpg" | jq .

# B2B 업로드
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/test/menus/upload-images \
  -F "files=@menu1.jpg" -F "files=@menu2.jpg" | jq .

# FastComet 배포
ssh chargeap@d11475.sgp1.stableserver.net
cd ~/menu-knowledge/app/backend
git pull && source venv/bin/activate && pip install -r requirements.txt
echo "CLOVA_OCR_SECRET=xxx" >> .env
sudo systemctl restart menu-api

# 로그 확인
tail -f ~/menu-api.log
```

---

**문서 작성**: Claude Code
**최종 업데이트**: 2026-02-18
**문의**: Sprint 3B 관련 기술 문제는 SPRINT3B_TECHNICAL_REVIEW_20260218.md 참조
