# 🚀 Sprint 3 P1-P2 상세 개발 지시서

> **작성일:** 2025-02-11
> **현황:** Sprint 3 P0 완료 (OCR + AI Matching + B2B 기본 UI)
> **목표:** P1-P2 완료 → MVP 현장 테스트 준비

---

## 📊 현재 완료 상황

### ✅ Sprint 3 P0 (완료)
- CLOVA OCR API 연동 + GPT-4o 메뉴명/가격 파싱
- AI Discovery (GPT-4o) + confidence scoring
- B2B 메뉴 업로드 + 검수 UI
- **68% 매칭률 달성** (설계 목표 70%)

### 📈 구현 현황 요약
```
├── Backend (100%)
│   ├── DB 스키마: 9개 테이블 ✅
│   ├── 시드 데이터: 112 canonical, 54 modifiers ✅
│   ├── API /identify: 4단계 매칭 ✅
│   ├── API /recognize: CLOVA OCR ✅
│   └── AI Discovery: GPT-4o ✅
│
├── Frontend B2C (100%)
│   ├── 메뉴명 검색 UI ✅
│   ├── 다중 메뉴 검색 ✅
│   ├── AI Discovery 폴백 UI ✅
│   └── 결과 카드 (영문 설명 + 알레르기) ✅
│
└── Frontend B2B (70%)
    ├── 메뉴판 업로드 UI ✅
    ├── 매칭 결과 검수 UI ✅
    ├── Admin 신규 메뉴 큐 ⏳
    ├── QR 메뉴 페이지 생성 ⏳
    └── Papago 다국어 번역 ⏳
```

---

## 🎯 Sprint 3 P1-P2 목표

> **"현장 테스트 가능 수준의 완성도 달성"**

### P1: 핵심 관리 기능 + 다국어 (2주)
- P1-1: Admin 신규 메뉴 큐 + 모니터링
- P1-2: Papago 다국어 번역 (일/중)
- P1-3: End-to-End 통합 테스트 (명동 3곳)

### P2: 부가 기능 + 성능 (1주)
- P2-1: QR 메뉴 페이지 (B2B-3)
- P2-2: 성능 최적화 (응답 시간 3초 이내)

---

## 📋 **P1-1: Admin 화면 구현** (우선순위 최고)

### 📍 위치 & 목표
- **경로:** `/app/frontend-b2b/admin.html`
- **목표:** 신규 메뉴 큐 관리 + 엔진 상태 모니터링
- **역할:** 운영자가 B2C 스캔 + B2B 미검수 메뉴를 승인/거부

### 🎨 화면 구성 (설계 문서 참조: 08_wireframe_v0.1.md)

#### Admin-1. 신규 메뉴 큐 (핵심 화면)

```html
┌────────────────────────────────────────┐
│ 🔧 Menu Knowledge Engine Admin         │
│                                        │
│ 신규 메뉴 큐: 34건                    │
│ B2C 카메라: 22건 | B2B 업로드: 12건   │
│                                        │
│ 필터: [전체] [확인필요] [자동등록]      │
│                                        │
│ ┌────────────────────────────────────┐│
│ │ #1 "왕얼큰순두부뼈해장국"           ││
│ │ 소스: B2C 스캔 (명동) 2025-02-11   ││
│ │                                    ││
│ │ 자동 분해:                         ││
│ │   왕(size) + 얼큰(taste) + ... ││
│ │   + 뼈해장국(canonical)          ││
│ │                                    ││
│ │ 매칭: canon_042 (뼈해장국)         ││
│ │ 확신도: 0.71                       ││
│ │                                    ││
│ │ [✅ 승인] [✏️ 수정] [🆕 신규 생성] ││
│ └────────────────────────────────────┘│
│                                        │
│ ─── 엔진 상태 ─── (우측 사이드바)      │
│ Canonical: 523 | Modifier: 87        │
│ DB히트율(7일): 73% | AI비용: ₩12,400 │
│ 미검토 큐: 14건                       │
└────────────────────────────────────────┘
```

### 📝 구현 체크리스트

#### 1. Backend API 추가 (3개)

**① 신규 메뉴 큐 조회**
```python
@router.get("/api/v1/admin/queue")
async def get_menu_queue(
    status: str = "all",  # all, pending, confirmed, rejected
    source: str = "all",  # all, b2c, b2b
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    신규 메뉴 큐 조회
    Returns:
      - id, menu_name_ko, source, created_at
      - decomposition_result, confidence
      - matched_canonical, status
    """
```

**② 메뉴 승인/거부**
```python
@router.post("/api/v1/admin/queue/{queue_id}/approve")
async def approve_menu(
    queue_id: str,
    action: str,  # approve, reject, edit
    canonical_menu_id: str = None,  # edit 시 지정
    db: AsyncSession = Depends(get_db)
):
    """
    신규 메뉴 큐 승인
    - approve: canonical_menus에 등록
    - reject: scan_logs.status = 'rejected'
    - edit: 수정 후 재심사
    """
```

**③ 엔진 상태 대시보드**
```python
@router.get("/api/v1/admin/stats")
async def get_engine_stats(db: AsyncSession = Depends(get_db)):
    """
    엔진 모니터링 통계
    Returns:
      - canonical_count: 등록된 메뉴 수
      - modifier_count: 수식어 사전 크기
      - db_hit_rate_7d: 7일 DB 히트율 (%)
      - ai_cost_7d: 7일 AI 비용 (₩)
      - pending_queue_count: 미검토 큐
    """
```

#### 2. Frontend UI 구현

**파일 구조:**
```
frontend-b2b/
├── admin.html           # Admin 대시보드 (메인)
├── admin-queue.html     # 신규 메뉴 큐 탭
├── admin-stats.html     # 통계 탭
└── js/admin.js          # Admin 로직
```

**admin.html 요구사항:**
- [ ] 탭 네비게이션: [신규 메뉴 큐] [통계] [설정]
- [ ] 신규 메뉴 큐 리스트:
  - 각 항목: 메뉴명, 소스, 분해 결과, 확신도
  - 필터: [전체] [확인필요(0.65~0.85)] [자동등록(>=0.85)] [보류(<0.65)]
  - 정렬: [최신순] [확신도순]
- [ ] 메뉴 카드 액션:
  - [✅ 승인]: canonical 등록 + evidence 저장
  - [✏️ 수정]: 모달 열기 (메뉴명/분해 수정)
  - [🆕 신규]: 새 canonical 생성 (AI 결과 활용)
- [ ] 우측 사이드바: 실시간 통계 (5초마다 갱신)

**admin.js 로직:**
```javascript
// 큐 로드
async function loadQueue(filter = 'all') {
  const res = await fetch(`/api/v1/admin/queue?status=${filter}`);
  const data = await res.json();
  renderQueueItems(data.data);
}

// 메뉴 승인
async function approveMenu(queueId) {
  const res = await fetch(`/api/v1/admin/queue/${queueId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ action: 'approve' })
  });
  // 큐에서 제거 + 통계 갱신
  loadQueue();
  updateStats();
}

// 통계 갱신
async function updateStats() {
  const res = await fetch('/api/v1/admin/stats');
  const stats = await res.json();
  // UI 업데이트
}
```

### ✅ 완료 기준

- [ ] 3개 Backend API 모두 구현 + 테스트
- [ ] Admin 큐 UI 렌더링 (20개 항목 이상)
- [ ] 필터/정렬 기능 작동
- [ ] 승인/거부 액션 DB 저장 확인
- [ ] 통계 UI 실시간 갱신 (5초)

---

## 🌍 **P1-2: Papago 다국어 번역 API 연동**

### 📍 목표
- 영어 자동 생성 (이미 구현됨, GPT-4o)
- **일본어/중국어 보조 번역** (Papago API)
- 캐싱으로 비용 절감

### 🏗️ 구현 아키텍처

```
입력: canonical_menu_id
  ↓
[캐시 확인]
  ├─ hit → 즉시 반환 ✅
  ├─ miss ↓

[Papago API 호출]
  ├─ 영어 설명 → 일본어 번역
  ├─ 영어 설명 → 중국어(간체) 번역
  ↓
[DB 저장]
  explanation_short:
    {
      "en": "Spicy stew...",
      "ja": "スパイシーシチュー...",
      "zh": "辛い煮込み..."
    }
```

### 📝 구현 체크리스트

#### 1. Papago API Service 작성

**파일:** `/app/backend/services/papago_service.py`

```python
from services.papago_service import papago_service

class PapagoTranslator:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/papago/n2mt"

    async def translate(self, text: str, target_lang: str) -> str:
        """
        Naver Papago 번역 호출
        target_lang: 'ja' | 'zh-CN'
        Returns: 번역된 텍스트
        """
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        data = {
            "source": "ko",
            "target": target_lang,
            "text": text
        }
        # aiohttp 또는 httpx로 비동기 호출
        ...

papago_service = PapagoTranslator(
    client_id=settings.PAPAGO_CLIENT_ID,
    client_secret=settings.PAPAGO_CLIENT_SECRET,
)
```

#### 2. 번역 파이프라인 통합

**기존 AI Discovery 플로우에 추가:**

```python
# services/matching_engine.py에 추가

async def enrich_canonical_menu(canonical_menu: CanonicalMenu):
    """
    새로 생성된 canonical에 다국어 설명 추가
    """
    # 1. 영어 설명 (이미 있음)
    explanation_en = canonical_menu.explanation_short["en"]

    # 2. 일본어 번역
    explanation_ja = await papago_service.translate(
        explanation_en,
        target_lang="ja"
    )

    # 3. 중국어 번역
    explanation_zh = await papago_service.translate(
        explanation_en,
        target_lang="zh-CN"
    )

    # 4. DB 저장
    canonical_menu.explanation_short = {
        "en": explanation_en,
        "ja": explanation_ja,
        "zh": explanation_zh
    }
    await db.commit()
```

#### 3. B2C 결과 화면 - 언어 선택 탭 추가

**frontend/index.html:**

```html
<!-- 기존: 메뉴 카드 위에 추가 -->
<div class="language-selector">
  <button class="lang-btn active" data-lang="en">English</button>
  <button class="lang-btn" data-lang="ja">日本語</button>
  <button class="lang-btn" data-lang="zh">中文</button>
</div>

<!-- 메뉴 카드: 각 언어별 설명 표시 -->
<div class="menu-card">
  <h3 id="menu-name">{{ menu.composed_name_en }}</h3>
  <p id="explanation" class="explanation-en">
    {{ menu.explanation_short.en }}
  </p>
  <!-- ja, zh 버전은 hidden -->
</div>
```

**frontend/js/app.js:**

```javascript
// 언어 선택 토글
document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const lang = e.target.dataset.lang;
    switchLanguage(lang);
  });
});

function switchLanguage(lang) {
  const explanation = document.getElementById('explanation');
  const menuItem = currentMenu;  // 현재 메뉴

  // explanation_short[lang]로 텍스트 변경
  explanation.textContent = menuItem.explanation_short[lang];

  // 버튼 활성화 상태 변경
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });
}
```

### ✅ 완료 기준

- [ ] Papago API 서비스 구현 + 테스트
- [ ] AI Discovery 후 자동 번역 (일/중)
- [ ] B2C 언어 선택 탭 구현
- [ ] 캐싱 확인 (Papago 호출 수 추적)
- [ ] 번역 품질 샘플 검증 (3개 메뉴)

---

## 🧪 **P1-3: End-to-End 통합 테스트**

### 📍 목표
**"실제 식당 메뉴판으로 전체 파이프라인 검증"**

### 🏪 테스트 식당 선정 (명동)

| # | 식당명 | 메뉴 특징 | 테스트 포인트 |
|---|--------|---------|------------|
| 1 | 명동 교자 | 간단한 메뉴 (5~10개) | OCR 정확도 (깔끔함) |
| 2 | 신계순 순대국 | 복잡한 메뉴 (20~30개) | 매칭률 (변형 많음) |
| 3 | 명동 할머니순대 | 손글씨 섞임 | OCR 한계 (접사진) |

### 📋 테스트 체크리스트

#### Phase 1: 데이터 수집 (2시간)

- [ ] 3개 식당 메뉴판 사진 촬영
  - 각 30~50장 (다각도, 조명 변화)
  - 해상도: 1920x1080 이상
  - 파일 저장: `/app/data/test_menus/{restaurant}/`

#### Phase 2: B2C 흐름 테스트 (30분)

```
1. 사진 1장 업로드 (B2C)
   ↓
2. /api/v1/menu/recognize 호출 (OCR)
   ↓
3. 각 메뉴명 /api/v1/menu/identify 호출 (매칭)
   ↓
4. 결과 카드 렌더링 확인
   └─ 영문 설명 정확도
   └─ 알레르기 정보 정확도
   └─ 응답 시간 <= 3초
```

**로그 기록:**
```json
{
  "restaurant": "명동 교자",
  "image_file": "menu_001.jpg",
  "ocr_result": {
    "count": 8,
    "menu_items": ["교자", "탄탄면", ...],
    "ocr_confidence": 0.92,
    "processing_time_ms": 1200
  },
  "matching_results": {
    "exact_match": 7,
    "ai_discovery": 1,
    "db_hit_rate": 0.875
  },
  "api_response_time_ms": 2500,
  "user_feedback": "✅ All correct"
}
```

#### Phase 3: B2B 흐름 테스트 (30분)

```
1. 메뉴판 사진 업로드 (B2B 관리자)
   ↓
2. OCR + 매칭 자동 처리
   ↓
3. 검수 화면 (B2B-2)
   - 자동 매칭 결과 확인
   - 신뢰도 배지 (✅ ⚠️ ❓) 검증
   - 사장님 수정 비율 측정
   ↓
4. 전체 승인 → QR 메뉴 페이지 생성 (B2B-3)
   ↓
5. QR 코드 스캔 → 메뉴 페이지 확인
   - 다국어 표시 (영/일/중)
   - 알레르기 정보 정확도
```

#### Phase 4: 성능 측정 (15분)

```
KPI 측정:

1. OCR 인식률
   = 정확하게 인식된 메뉴명 / 전체 메뉴 수
   목표: >= 80%

2. DB 매칭률
   = AI 호출 없이 DB만으로 처리 / 전체 메뉴
   목표: >= 70%

3. 응답 시간 (p95)
   = 95% 요청이 이 시간 이내 완료
   목표: <= 3초

4. 사장님 수정률
   = 자동 결과 수정한 메뉴 / 전체 메뉴
   목표: <= 20% (수정률이 낮을수록 좋음)
```

### 📊 검증 리포트 작성

**파일:** `/app/data/E2E_TEST_REPORT_20250218.md`

```markdown
# End-to-End 통합 테스트 리포트

## 테스트 환경
- 날짜: 2025-02-18
- 위치: 명동
- 테스트 식당: 3곳
- 테스트 메뉴판: 총 67개 사진

## 결과 요약

### 1. 명동 교자 (간단한 메뉴)
- 메뉴 수: 8개
- OCR 인식률: 100% (8/8)
- DB 매칭률: 87.5% (7/8)
- AI Discovery: 1개 (교자 → Gyoza)
- 평균 응답 시간: 2.3초
- 사장님 수정률: 0% (수정 없음)

### 2. 신계순 순대국 (복잡한 메뉴)
- 메뉴 수: 24개
- OCR 인식률: 91.7% (22/24)
- DB 매칭률: 70.8% (17/24)
- AI Discovery: 7개 (변형 메뉴)
- 평균 응답 시간: 2.8초
- 사장님 수정률: 12.5% (3개 수정)

### 3. 명동 할머니순대 (손글씨)
- 메뉴 수: 35개
- OCR 인식률: 74.3% (26/35)  ⚠️ 낮음
- DB 매칭률: 68.6% (24/35)
- AI Discovery: 11개
- 평균 응답 시간: 3.2초
- 사장님 수정률: 14.3% (5개 수정)

## 종합 지표

| 지표 | 목표 | 실제 | 평가 |
|------|------|------|------|
| OCR 인식률 | 80%+ | 85.1% | ✅ 통과 |
| DB 매칭률 | 70%+ | 75.6% | ✅ 통과 |
| 응답 시간(p95) | 3초 이내 | 3.2초 | ⚠️ 한계 |
| 사장님 수정률 | 20% 이하 | 8.9% | ✅ 통과 |

## 주요 발견사항

1. **OCR 문제**: 손글씨/필기체는 CLOVA가 취약
   → 사용자 UX: "깨끗한 사진 안내" + 수동 입력 fallback

2. **응답 시간**: 다중 메뉴 검색 시 3초 근처
   → P2-2에서 캐싱 + DB 인덱싱으로 개선

3. **매칭 성공**: 68% → 75% 개선 (수식어 분해 효과 입증)
   → 추가 modifiers 확대 시 80% 달성 가능

## 권장사항

1. Admin 큐에서 손글씨 실패 케이스 우선 관리
2. 자주 실패하는 메뉴 → canonical 신규 추가
3. DB 인덱싱 + 캐싱으로 응답 시간 2초대 달성
```

### ✅ 완료 기준

- [ ] 3개 식당 메뉴판 수집 + 촬영 완료
- [ ] B2C 흐름 완료 (67개 메뉴 all-in-one 테스트)
- [ ] B2B 흐름 완료 (검수 UI + 승인 + QR)
- [ ] 4대 KPI 측정 및 리포트 작성
- [ ] 모든 지표 목표치 달성 확인

---

## 🎯 **P2-1: QR 메뉴 페이지 (B2B-3)**

### 📍 목표
**"사장님이 메뉴 승인 후 QR 코드 생성 → 외국인이 QR 스캔 → 다국어 메뉴 보기"**

### 🏗️ 아키텍처

```
B2B 승인 완료
  ↓
POST /api/v1/shop/{shop_id}/generate-qr
  ├─ QR 코드 생성 (shop_code 인코딩)
  ├─ 메뉴 페이지 HTML 렌더링
  └─ URL: https://menu.example.com/s/{shop_code}
  ↓
QR 스캔 (외국인)
  ↓
GET /s/{shop_code}?lang=en
  ├─ shop_id 역조회
  ├─ canonical_menus 조회
  ├─ 카테고리별 정렬
  ├─ 다국어 설명 로드
  └─ HTML 렌더링
```

### 📝 구현 체크리스트

#### 1. Backend API

**① QR 생성 엔드포인트**
```python
@router.post("/api/v1/shop/{shop_id}/generate-qr")
async def generate_qr(
    shop_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    QR 코드 + 메뉴 페이지 생성

    1. shop_code 생성 (UUID의 처음 8자)
    2. QR 코드 생성 (pyqrcode 또는 qrcode library)
    3. shop.qr_url 저장

    Returns:
      {
        "shop_code": "a1b2c3d4",
        "qr_url": "https://menu.example.com/s/a1b2c3d4",
        "qr_image_base64": "iVBORw0KGgo..."
      }
    """
```

**② 메뉴 페이지 조회**
```python
@router.get("/s/{shop_code}")
async def get_shop_menu_page(
    shop_code: str,
    lang: str = "en",  # en, ja, zh
    db: AsyncSession = Depends(get_db)
):
    """
    QR 스캔 후 메뉴 페이지

    Returns: HTML 페이지 (직접 렌더링, 아니면 JSON)
    """
    # shop_code → shop_id
    # shop_id → menu_variants 조회
    # canonical_menus 조회
    # 카테고리별 정렬
    # 다국어 설명 삽입
```

#### 2. Frontend - QR 메뉴 페이지

**파일:** `/app/backend/templates/shop_menu.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <title>{{ shop.name_ko }} - Menu Lens Korea</title>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="/css/menu-page.css">
</head>
<body>
  <div class="container">

    <!-- Header -->
    <header class="shop-header">
      <h1>{{ shop.name_ko }}</h1>
      <p>{{ shop.name_en }}</p>
      <div class="language-tabs">
        <button class="tab active" data-lang="en">English</button>
        <button class="tab" data-lang="ja">日本語</button>
        <button class="tab" data-lang="zh">中文</button>
      </div>
    </header>

    <!-- Menu Section -->
    <div class="menu-content">
      {% for category in categories %}
      <section class="category">
        <h2>{{ category.name_en }}</h2>

        {% for menu in category.menus %}
        <div class="menu-card">
          {% if menu.image_url %}
          <img src="{{ menu.image_url }}" alt="{{ menu.composed_name_en }}">
          {% endif %}

          <div class="menu-details">
            <h3>{{ menu.composed_name_en }}</h3>
            <p class="korean-name">{{ menu.name_ko }}</p>

            <p class="description" id="desc-{{ menu.id }}">
              {{ menu.explanation_short[lang] }}
            </p>

            <div class="menu-info">
              <span class="spice">🌶️ {{ menu.spice_level }}/5</span>
              <span class="allergens">🐷 Pork</span>
              <span class="difficulty">⭐⭐⭐</span>
            </div>

            {% if menu.price_ko %}
            <p class="price">{{ menu.price_ko }}</p>
            {% endif %}
          </div>
        </div>
        {% endfor %}
      </section>
      {% endfor %}
    </div>

    <!-- Cultural Tips -->
    <section class="cultural-tips">
      <h2>💡 Tips for This Restaurant</h2>
      <ul>
        {% for tip in tips %}
        <li>{{ tip.description_en }}</li>
        {% endfor %}
      </ul>
    </section>

    <!-- Footer -->
    <footer>
      <p>Powered by Menu Lens Korea</p>
      <p><small>이 서비스는 AI 기술을 사용하여 번역합니다.</small></p>
    </footer>
  </div>

  <script>
    // 언어 탭 토글
    document.querySelectorAll('.language-tabs .tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const lang = e.target.dataset.lang;
        switchMenuLanguage(lang);
      });
    });

    function switchMenuLanguage(lang) {
      // 모든 description 업데이트
      document.querySelectorAll('[id^="desc-"]').forEach(el => {
        const menuId = el.id.replace('desc-', '');
        // 서버에서 새 언어 데이터 로드 또는 이미 로드된 데이터 사용
        el.textContent = menuData[menuId][lang];
      });
    }
  </script>
</body>
</html>
```

#### 3. QR 코드 디자인

**요구사항:**
- 크기: 100x100mm (인쇄용)
- 내용: `https://menu.example.com/s/{shop_code}`
- 오류 정정: Level H (30% 손상까지 인식 가능)
- 출력 형식: PNG (고해상도)

**Python 구현:**
```python
import qrcode

def generate_qr_code(shop_code: str) -> bytes:
    qr_url = f"https://menu.example.com/s/{shop_code}"
    qr = qrcode.QRCode(
        version=1,  # 최소 크기
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # PNG로 저장
    import io
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()
```

### ✅ 완료 기준

- [ ] QR 생성 API 구현 + 테스트
- [ ] 메뉴 페이지 HTML 렌더링
- [ ] 언어 탭 (영/일/중) 토글
- [ ] 카테고리별 메뉴 정렬
- [ ] QR 코드 인쇄 테스트 (스캔 확인)
- [ ] B2B-3 UI와 일치 검증

---

## ⚡ **P2-2: 성능 최적화**

### 📍 목표
**"응답 시간 3초 → 2초 달성"**

### 📊 현재 병목 분석

```
/api/v1/menu/identify 호출 시간:
  ├─ DB 쿼리: 800ms (canonical 조회)
  ├─ 수식어 분해: 200ms
  ├─ AI Discovery (필요 시): 1500ms ~
  └─ 응답 직렬화: 50ms

  합계: 2050ms (DB 히트) ~ 3550ms (AI 필요)
```

### 🔧 최적화 항목

#### 1. DB 인덱싱 (가장 빠른 개선)

**파일:** `/app/backend/models/canonical_menu.py`

```python
from sqlalchemy import Index

class CanonicalMenu(Base):
    __tablename__ = "canonical_menus"

    # 기존 컬럼들...

    # 인덱스 추가
    __table_args__ = (
        Index('ix_name_ko', 'name_ko', postgresql_using='hash'),  # 정확 매칭
        Index('ix_concept_id', 'concept_id'),  # 카테고리별 조회
        Index('ix_created_at', 'created_at'),  # 최신순 정렬
    )
```

**마이그레이션:**
```bash
# Alembic으로 인덱스 추가
alembic revision --autogenerate -m "Add canonical_menu indexes"
alembic upgrade head
```

#### 2. 캐싱 (Redis)

**목표:** 자주 조회되는 canonical 메뉴 메모리 캐싱

```python
# services/cache_service.py

import redis.asyncio as redis
from config import settings

redis_client = redis.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
)

async def get_canonical_menu_cached(menu_id: str) -> CanonicalMenu:
    # 캐시 확인
    cached = await redis_client.get(f"canonical:{menu_id}")
    if cached:
        return json.loads(cached)

    # DB 조회
    menu = await db.get(CanonicalMenu, menu_id)

    # 캐시 저장 (TTL: 24시간)
    await redis_client.setex(
        f"canonical:{menu_id}",
        86400,
        json.dumps(menu.dict())
    )

    return menu
```

#### 3. API 응답 최적화

**문제:** 불필요한 필드 전송

**개선:**
```python
class MenuIdentifyResponse(BaseModel):
    """응답 필드 최소화"""
    match_type: str
    canonical: dict  # 필요한 필드만
    confidence: float

    # 제거: cultural_context, similar_dishes 등
    #       (B2C 결과에는 불필요)
```

#### 4. 데이터베이스 쿼리 최적화

**현재 문제:**
```python
# ❌ N+1 쿼리
for menu_variant in menu_variants:
    canonical = await db.get(CanonicalMenu, menu_variant.canonical_id)
    # N번 쿼리 실행!
```

**개선:**
```python
# ✅ 조인 쿼리 1회
from sqlalchemy import joinedload

query = (
    select(MenuVariant)
    .options(joinedload(MenuVariant.canonical_menu))
    .filter(MenuVariant.shop_id == shop_id)
)
```

### 📈 성능 측정 방법

**Endpoint 응답 시간 로깅:**

```python
# middleware

import time
from starlette.middleware.base import BaseHTTPMiddleware

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        # 로그
        logger.info(
            f"{request.method} {request.url.path} "
            f"duration={duration*1000:.2f}ms"
        )

        return response

app.add_middleware(TimingMiddleware)
```

**성능 리포트 생성:**

```bash
# 7일 로그 분석
cat logs/app.log | grep "POST /api/v1/menu/identify" \
  | awk '{print $(NF-1)}' \
  | sort -n \
  | awk '{sum+=$1; count++}
          END {
            print "P95:", $(NR*0.95);
            print "P99:", $(NR*0.99);
            print "Average:", sum/count;
          }'
```

### ✅ 완료 기준

- [ ] DB 인덱싱 추가 + 성능 테스트
- [ ] Redis 캐싱 구현 (canonical, modifiers)
- [ ] API 응답 필드 최소화
- [ ] N+1 쿼리 제거
- [ ] 응답 시간 p95 < 2초 달성 (측정 증명)

---

## 🎬 **개발 순서 및 일정**

### 📅 권장 개발 순서

```
Week 1 (4일):
  ✅ P1-1: Admin 신규 메뉴 큐 (백엔드 API 3개 + 프론트엔드)

Week 2 (3일):
  ✅ P1-2: Papago 다국어 번역 (서비스 + B2C 언어 탭)

Week 2 (2일):
  ✅ P1-3: E2E 테스트 (현장 3곳 + 리포트)

Week 3 (2일):
  ✅ P2-1: QR 메뉴 페이지 (API + HTML)

Week 3 (2일):
  ✅ P2-2: 성능 최적화 (인덱싱 + 캐싱)
```

### 🔄 각 항목별 의존성

```
P1-1 (Admin) ─────┐
                   ├─→ P1-3 (E2E 테스트)
P1-2 (번역) ──────┤
                   └─→ P2-1 (QR 페이지)
                         │
                         └─→ P2-2 (최적화)
```

---

## ✅ **최종 체크리스트**

### Before Commit
- [ ] 타입 힌트 완성 (mypy --strict)
- [ ] 린트 통과 (ruff check)
- [ ] 테스트 커버리지 > 70%
- [ ] 디버깅 코드 제거 (print, console.log)
- [ ] `.env.example` 업데이트

### Before Deployment
- [ ] README 업데이트 (new features)
- [ ] DB 마이그레이션 스크립트 테스트
- [ ] 성능 리포트 작성
- [ ] KPI 측정값 기록
- [ ] GitHub 태그 생성 (v0.1-p2)

---

## 📞 **개발 중 참고 문서**

| 문서 | 경로 |
|------|------|
| API 명세 | `기획/3차_설계문서_20250211/06_api_specification_v0.1.md` |
| Wireframe | `기획/3차_설계문서_20250211/08_wireframe_v0.1.md` |
| 시드 가이드 | `기획/3차_설계문서_20250211/07_seed_data_guide.md` |
| 데이터 흐름 | `기획/3차_설계문서_20250211/04_data_flow_scenarios.md` |

---

**🚀 Sprint 3 P1-P2 개발 지시서 완료!**

질문이나 기술 지원이 필요하면 언제든 알려주세요. 화이팅! 💪
