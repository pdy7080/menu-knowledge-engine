# 원래 기획 검토 및 음식 사진 기능 고도화

**검토 일시**: 2026-02-18
**상태**: 🔴 **핵심 기능 누락 발견**
**우선순위**: **P0 (즉시 개선 필요)**

---

## 🚨 문제점 분석

### 원래 기획 (User Requirements)

사용자의 원래 아이디어:
> "외국인들이 한국 메뉴를 알 수 없으니, **인터넷에서 음식 사진을 수집해서 보여주자**"

**2가지 단계:**
1. **Phase 1 (Now)**: 우리가 인터넷에서 수집한 일반적인 음식 사진 자동 표시
2. **Phase 2 (Future)**: 가게 주인이 직접 자신의 메뉴 사진을 업로드할 수 있는 기능

---

### 현재 구현 상황

**✅ 완료된 것:**
- 텍스트 기반 메뉴 검색
- 영어 번역
- 알레르기 정보
- 난이도 정보

**❌ 누락된 것:**
- **음식 사진 표시** (가장 중요한 기능!)
- **이미지 데이터 구조**
- **사진 업로드 기능** (Phase 2)
- **이미지 관리 대시보드**

**현재 상태:**
```
검색 결과 화면:
├── ✅ 메뉴명 (한글 + 영문)
├── ✅ 설명
├── ✅ 매운맛 (🌶️🌶️🌶️)
├── ✅ 난이도
├── ✅ 알레르기
└── ❌ 음식 사진 (중요!)
```

---

## 🎯 기획 고도화 방안

### Phase 1: 인터넷 수집 사진 표시 (Sprint 2)

#### 1-1. 데이터 구조 확장

**현재 canonical_menus 테이블:**
```python
canonical_menus = {
    "id": UUID,
    "name_ko": "김치찌개",
    "name_en": "Kimchi Jjigae",
    "explanation_short": {...},
    "main_ingredients": [...],
    "allergens": [...],
    "spice_level": 3,
    "difficulty_score": 1,
    # ❌ 사진 필드 없음!
}
```

**개선 구조:**
```python
canonical_menus = {
    "id": UUID,
    "name_ko": "김치찌개",
    "name_en": "Kimchi Jjigae",

    # 새로 추가: 이미지 정보
    "image": {
        "url": "https://commons.wikimedia.org/wiki/Special:FilePath/...",
        "alt_text": "Traditional Korean kimchi stew in a stone bowl",
        "source": "wikimedia_commons",  # 출처
        "license": "CC-BY-SA-4.0",       # 라이선스
        "attribution": "Credit: [Author Name]"
    },

    # 예비 이미지 (선택사항)
    "images_backup": [
        {
            "url": "...",
            "source": "pexels",
            "license": "CC0"
        },
        {
            "url": "...",
            "source": "unsplash",
            "license": "Unsplash License"
        }
    ],

    # 설명 (기존)
    "explanation_short": {...},
    "main_ingredients": [...],
    "allergens": [...],
    "spice_level": 3,
    "difficulty_score": 1
}
```

---

#### 1-2. 이미지 수집 전략

**출처별 수집 계획:**

| 출처 | 개수 | 라이선스 | 수집 방법 | 비용 |
|------|------|---------|---------|------|
| **Wikimedia Commons** | 50-100 | CC-BY-SA | API | 무료 ✅ |
| **Unsplash** | 50-100 | CC0 | API | 무료 ✅ |
| **Pexels** | 50-100 | CC0 | API | 무료 ✅ |
| **Pixabay** | 50-100 | CC0 | API | 무료 ✅ |
| **ShutterStock** | 100-200 | Commercial | API | 유료 |

**추천 전략:**
1. **우선 (무료)**: Wikimedia + Unsplash + Pexels + Pixabay
2. **향후**: ShutterStock (고품질 필요시)

---

#### 1-3. 초기 이미지 데이터셋 (100개 메뉴)

**구성:**
```
10대 TC 메뉴: 10개 (우선 처리)
├── 김치찌개
├── 불고기
├── 갈비
├── 한우불고기
├── 돈까스
└── ... (5개 더)

인기 메뉴: 40개
├── 비빔밥
├── 삼겹살
├── 떡볶이
├── 냉면
├── ... (36개 더)

음식 카테고리별: 50개
├── 찌개류 (15개)
├── 구이류 (15개)
├── 밥/국류 (10개)
├── 면류 (10개)
└── 기타 (5개)

총 100개 (최소 500MB, 최대 2GB S3 스토리지)
```

---

#### 1-4. UI/UX 개선안

**검색 결과 화면 재설계:**

```html
<!-- 현재 (사진 없음) -->
<div class="result-card">
  <h2>김치찌개</h2>
  <p>Kimchi Jjigae</p>
  <div>🌶️🌶️🌶️ Spice Level 3</div>
  <div>Allergens: ...</div>
</div>

<!-- 개선 (사진 포함) -->
<div class="result-card">
  <div class="result-image-container">
    <!-- 이미지: 1:1 정사각형, 반응형 -->
    <img src="kimchi-jjigae.jpg"
         alt="Traditional Korean kimchi stew"
         loading="lazy"
         class="result-image">
    <!-- 출처 표시 (작은 텍스트) -->
    <span class="image-credit">Source: Wikimedia Commons</span>
  </div>

  <div class="result-info">
    <h2>김치찌개</h2>
    <p class="english-name">Kimchi Jjigae</p>

    <div class="result-stats">
      <span>🌶️🌶️🌶️ Spice: 3/5</span>
      <span>⏱️ Difficulty: Easy</span>
    </div>

    <div class="result-description">
      Spicy stew made with kimchi and pork
    </div>

    <div class="result-allergens">
      ⚠️ <strong>Allergens:</strong> Pork, Soy
    </div>
  </div>
</div>
```

**이미지 스타일 가이드:**
```css
.result-image-container {
  position: relative;
  width: 100%;
  max-width: 300px;
  aspect-ratio: 1 / 1;
  border-radius: 8px;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f5f5, #e9e9e9);
}

.result-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.image-credit {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 10px;
  padding: 4px 6px;
  border-radius: 4px;
}

/* 모바일 반응형 */
@media (max-width: 768px) {
  .result-image-container {
    max-width: 100%;
    margin-bottom: 16px;
  }
}
```

---

#### 1-5. API 스키마 확장

**GET /api/v1/canonical-menus (확장)**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name_ko": "김치찌개",
  "name_en": "Kimchi Jjigae",

  // 🆕 이미지 추가
  "image": {
    "url": "https://commons.wikimedia.org/wiki/Special:FilePath/Kimchi_Jjigae.jpg",
    "alt_text": "Traditional Korean kimchi stew in a stone bowl",
    "source": "wikimedia_commons",
    "license": "CC-BY-SA-4.0",
    "attribution": "Image by [Author], used under CC-BY-SA 4.0"
  },

  // 🆕 예비 이미지
  "images_backup": [
    {
      "url": "https://images.unsplash.com/photo-...",
      "source": "unsplash",
      "license": "Unsplash License"
    }
  ],

  // 기존 필드
  "explanation_short": {
    "en": "Spicy stew made with kimchi and pork"
  },
  "main_ingredients": [
    {"ko": "김치", "en": "Kimchi"},
    {"ko": "돼지고기", "en": "Pork"}
  ],
  "allergens": ["pork", "soy"],
  "spice_level": 3,
  "difficulty_score": 1
}
```

---

### Phase 2: 가게 주인 사진 업로드 (Sprint 3)

#### 2-1. 기능 요구사항

**B2B 관리자 대시보드:**
```
가게 주인 대시보드
├── 내 매장 관리
│   ├── 기본 정보
│   ├── 메뉴 목록
│   └── 📸 메뉴 사진 업로드 ← NEW
├── 사진 갤러리
│   ├── 업로드된 사진 목록
│   ├── 승인 대기 사진
│   └── 거절된 사진 (피드백)
└── 설정
    ├── 프로필
    └── 결제
```

#### 2-2. 데이터 구조 확장

**새로운 테이블: menu_images**

```sql
CREATE TABLE menu_images (
  id UUID PRIMARY KEY,
  menu_id UUID NOT NULL REFERENCES canonical_menus(id),
  shop_id UUID NOT NULL REFERENCES shops(id),

  -- 이미지 정보
  image_url VARCHAR(500),           -- S3 경로
  image_s3_key VARCHAR(500),        -- S3 key
  image_width INTEGER,
  image_height INTEGER,
  image_size_bytes INTEGER,

  -- 업로드 정보
  uploaded_at TIMESTAMP,
  uploaded_by UUID,                 -- shop_owner_id

  -- 승인 프로세스
  status VARCHAR(20),               -- pending, approved, rejected
  approved_at TIMESTAMP,
  approved_by UUID,                 -- admin_id
  rejection_reason TEXT,            -- 거절 사유

  -- 우선순위
  priority INTEGER DEFAULT 0,       -- 낮을수록 상단 표시
  is_featured BOOLEAN DEFAULT false,

  -- 메타데이터
  metadata JSONB,                   -- 추가 정보
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_menu_images_menu ON menu_images(menu_id);
CREATE INDEX idx_menu_images_shop ON menu_images(shop_id);
CREATE INDEX idx_menu_images_status ON menu_images(status);
```

#### 2-3. 승인 워크플로우

**프로세스:**
```
가게 주인이 사진 업로드
    ↓
이미지 자동 검증 (크기, 형식, NSFW 필터)
    ↓
어드민 승인 (또는 자동 승인)
    ↓
승인된 사진 → 검색 결과에 표시
```

**자동 검증:**
- ✅ 파일 형식: JPG, PNG, WebP
- ✅ 파일 크기: 5MB 이하
- ✅ 이미지 해상도: 최소 300x300px
- ✅ NSFW 필터: Google Vision API
- ❌ 워터마크 또는 로고 많음
- ❌ 모호한 이미지 (음식이 아님)

---

### Phase 3: 고급 기능 (Sprint 4+)

#### 3-1. 이미지 AI 분석

**자동 메뉴 인식:**
```python
# 사진 업로드 시 자동 분석
image_features = {
    "detected_dish": "Bulgogi",      # 메뉴 자동 인식
    "confidence": 0.95,              # 신뢰도
    "ingredients": ["beef", "soy"],  # 재료 자동 감지
    "spice_level_estimated": 2,      # 매운맛 추정
    "color_dominant": "#D4541E"      # 색상 분석
}

# 사용자에게 확인 요청
"We detected: Bulgogi (95% confidence)"
"Does this look correct?"
```

#### 3-2. 이미지 기반 검색

**사진으로 메뉴 검색:**
```
사용자가 가게 메뉴판 사진 찍음
    ↓
OCR로 메뉴명 추출
    ↓
메뉴 검색 및 결과 반환
    ↓
해당 가게의 실제 사진 표시
```

---

## 📊 구현 로드맵

### Sprint 2 (이번 주): Phase 1 구현

| 작업 | 예상 시간 | 담당 |
|------|---------|------|
| DB 스키마 확장 (image 필드) | 2시간 | Backend |
| 이미지 수집 스크립트 작성 | 4시간 | Backend |
| Wikimedia/Unsplash API 통합 | 3시간 | Backend |
| 초기 100개 이미지 데이터 구성 | 5시간 | Data |
| API 엔드포인트 확장 | 2시간 | Backend |
| UI 개선 (이미지 표시) | 6시간 | Frontend |
| S3 이미지 호스팅 설정 | 2시간 | DevOps |
| 테스트 및 배포 | 4시간 | QA/DevOps |

**총 예상**: 28시간 (1주)

---

### Sprint 3 (다음 달): Phase 2 구현

| 작업 | 예상 시간 | 담당 |
|------|---------|------|
| B2B 관리자 대시보드 | 16시간 | Frontend |
| 이미지 업로드 API | 8시간 | Backend |
| 이미지 검증 (자동) | 6시간 | Backend |
| 승인 워크플로우 | 4시간 | Backend |
| 어드민 승인 패널 | 8시간 | Frontend |
| 이미지 최적화 (WebP, 압축) | 4시간 | Backend |
| 테스트 및 배포 | 6시간 | QA/DevOps |

**총 예상**: 52시간 (2주)

---

## 🎨 UI 목업 설계

### 검색 결과 화면 (개선안)

```
┌─────────────────────────────────────┐
│  ← Back    Search Results            │
├─────────────────────────────────────┤
│                                       │
│  ┌─────────────────────────────────┐ │
│  │                                   │ │
│  │    [음식 사진 - 300x300px]        │ │
│  │    (로딩 중... 또는 플레이스홀더) │ │
│  │                                   │ │
│  │  Wikimedia ↗                      │ │
│  └─────────────────────────────────┘ │
│                                       │
│  ▪ 김치찌개                          │
│    Kimchi Jjigae                     │
│                                       │
│  🌶️🌶️🌶️ Spice: 3/5 ⏱️ Easy        │
│                                       │
│  Spicy stew made with kimchi and     │
│  pork. A classic Korean comfort food │
│  enjoyed across the country.          │
│                                       │
│  ⚠️ Allergens: Pork, Soy, Sesame    │
│                                       │
│  ⓘ Allergen info is based on        │
│    general recipes and may vary.     │
│                                       │
│  ✓ 100% Match (exact)                │
│                                       │
└─────────────────────────────────────┘
```

---

## 📱 모바일 반응형 설계

### 모바일 화면

```
┌──────────────────────┐
│ ← Back  Search       │
├──────────────────────┤
│                      │
│  ┌────────────────┐  │
│  │  [사진 전체]   │  │
│  │ 300x300px      │  │
│  │                │  │
│  │ Wikimedia ↗    │  │
│  └────────────────┘  │
│                      │
│  김치찌개            │
│  Kimchi Jjigae       │
│                      │
│  🌶️🌶️🌶️ Spice: 3   │
│  ⏱️ Difficulty: Easy │
│                      │
│  Spicy stew made     │
│  with kimchi and pork│
│                      │
│  ⚠️ Allergens:      │
│  • Pork             │
│  • Soy              │
│  • Sesame           │
│                      │
│  ✓ 100% Match       │
│                      │
└──────────────────────┘
```

---

## 📋 실행 체크리스트

### Sprint 2 준비 사항

- [ ] **DB 마이그레이션 스크립트 작성**
  ```sql
  ALTER TABLE canonical_menus ADD COLUMN image JSONB;
  ALTER TABLE canonical_menus ADD COLUMN images_backup JSONB[];
  CREATE INDEX idx_canonical_menus_has_image ON canonical_menus USING HASH(image);
  ```

- [ ] **이미지 수집 스크립트 개발**
  ```python
  # scripts/collect_food_images.py
  - Wikimedia Commons API 연결
  - Unsplash API 연결
  - Pexels API 연결
  - 이미지 다운로드 & S3 업로드
  - 메타데이터 저장
  ```

- [ ] **S3 버킷 설정**
  ```
  Bucket: menu-knowledge-images
  ├── canonical/ (공식 이미지)
  │   ├── kimchi-jjigae-1.jpg
  │   ├── kimchi-jjigae-2.jpg
  │   └── ...
  ├── user-uploads/ (가게 주인 업로드)
  │   ├── pending/
  │   ├── approved/
  │   └── rejected/
  └── thumbnails/ (캐시)
  ```

- [ ] **API 응답 스키마 확장**
  ```
  GET /api/v1/canonical-menus/{id}
  응답: { ... image: {...}, images_backup: [...] }
  ```

- [ ] **프론트엔드 이미지 표시 컴포넌트**
  ```typescript
  <MenuImage
    url={menu.image?.url}
    alt={menu.image?.alt_text}
    fallback={menu.images_backup}
    lazy={true}
  />
  ```

---

## 🎯 최종 목표

### Phase 1 (완료 후):
✅ 모든 메뉴에 고품질 음식 사진 표시
✅ 외국인들이 메뉴를 시각적으로 이해
✅ 신뢰도 향상 (텍스트만 < 텍스트+사진)

### Phase 2 (완료 후):
✅ 가게 주인이 자신의 실제 메뉴 사진 업로드 가능
✅ 사용자에게 가장 최신, 정확한 정보 제공
✅ B2B 참여도 증가 (가게 주인의 자발적 참여)

### Phase 3 (완료 후):
✅ AI 기반 자동 메뉴 인식
✅ 사진으로 메뉴 검색 (OCR + 메뉴 매칭)
✅ 완전한 시각적 메뉴 가이드

---

## 💡 핵심 통찰

**사진의 중요성:**
- 텍스트만: 외국인이 메뉴를 상상할 수 없음 → 불안감 → 주문 회피
- 텍스트 + 사진: 명확한 시각적 정보 → 신뢰 → 자신감 있는 주문

**경쟁력:**
- 현재 서비스 (Papago, Google Translate): 번역만 제공
- 우리의 차별점: 번역 + 상세 정보 + **실제 사진** ← 이것이 핵심!

**데이터 전략:**
- Phase 1: 공개 라이선스 이미지로 신속한 시장 진입
- Phase 2: 실제 가게 사진으로 정확성과 신뢰도 극대화
- Phase 3: AI로 자동화 및 UX 개선

---

**결론**: 음식 사진은 단순 UI 개선이 아니라, **서비스의 핵심 가치**입니다.

Sprint 2에서 반드시 구현해야 합니다! 🎯

---

작성: Claude Code
날짜: 2026-02-18
우선순위: **P0 (Critical)**
