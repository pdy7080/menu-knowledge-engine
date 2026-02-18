# Phase 1 상세 설계: 한국 중심 이미지 수집 및 콘텐츠 강화

**작성일**: 2026-02-18
**우선순위**: **P0 (Critical)**
**목표**: 한국 공식 출처 중심 고품질 이미지 + 전문적 콘텐츠 제공

---

## 🎯 핵심 전략 변경

### ❌ 이전 계획 (외국 사이트 중심)
```
Wikimedia Commons (CC-BY-SA)
Unsplash (CC0)
Pexels (CC0)
Pixabay (CC0)
```

### ✅ 개선된 계획 (한국 중심)
```
1순위: 한국관광공사, 문화부, 공공 DB
2순위: 한국 위키피디아, 지식백과
3순위: 네이버 등 한국 사이트 (저작권 확인)
```

---

## 📸 이미지 수집 루트 재설계

### Tier 1: 공식 한국 정부 출처 (최우선)

#### 1-1. 한국관광공사 (Korea Tourism Organization)
**사이트**: https://www.visitkorea.or.kr/
**API**: https://api.visitkorea.or.kr/

**특징**:
- ✅ 한국 음식문화 공식 이미지 풍부
- ✅ 저작권 명확 (공공데이터 대부분 CC 라이선스)
- ✅ 메뉴명 + 한영 설명 함께 제공
- ✅ 관광지별 음식 정보 풍부

**수집 가능 항목**:
- 각 지역 특산 음식 사진
- 조리 과정 사진
- 레스토랑 사진
- 음식 문화 설명

**예시 API**:
```python
# 한국관광공사 관광정보 API
# API URL: https://api.visitkorea.or.kr/openapi/service/rest/KorService
# API Key: 필요 (무료 등록)

# 음식/맛집 정보 조회
# /searchFestival: 축제 정보 (음식 관련)
# /searchStays: 숙박정보 (음식문화 포함)
# /searchKeyword: 키워드 검색
```

**가입 방법**:
1. visitkorea.or.kr 가입
2. API 키 신청
3. 이용약관 동의 (공개 사용 가능)

---

#### 1-2. 한국문화정보원 (Korean Culture Information Service)
**사이트**: https://www.culture.go.kr/
**포털**: https://www.culturecontent.com/

**특징**:
- ✅ 한국 전통음식 공식 정보
- ✅ 문화재청 연계 (전통음식 문화유산)
- ✅ 레시피 + 역사 + 이미지

**수집 가능 항목**:
- 한국 전통음식 (비빔밥, 김치찌개 등)
- 음식 역사 및 문화 설명
- 고품질 음식 사진
- 조리법 설명

**예시**:
```
한국음식문화백과
├── 비빔밥
│   ├── 역사: "조선시대 궁중 음식에서 비롯..."
│   ├── 조리법: 상세 설명
│   ├── 지역별 특징: 전주비빔밥, 남원비빔밥
│   └── 고품질 이미지: 3-5장
├── 김치찌개
├── 불고기
└── ...
```

---

#### 1-3. 공공데이터포탈 (Public Data Portal)
**사이트**: https://www.data.go.kr/

**특징**:
- ✅ 한국 정부 공개 데이터
- ✅ 음식문화 관련 데이터셋
- ✅ 자유로운 저작권 (공개 데이터)

**활용 가능 데이터**:
```
- 한국 음식 표준 분류
- 음식 영양정보 (식약청)
- 알레르기 정보 표준
- 지역별 특산 음식 목록
- 음식 문화유산 정보
```

**예시 검색어**:
- "한국 음식 분류"
- "음식 영양정보"
- "전통 음식 목록"
- "지역 특산 음식"

---

### Tier 2: 한국 학술/백과 출처

#### 2-1. 위키피디아 한국어 (Korean Wikipedia)
**사이트**: https://ko.wikipedia.org/

**특징**:
- ✅ CC-BY-SA 라이선스 (명확한 저작권)
- ✅ 한국 음식 항목 풍부
- ✅ 영어 버전과 교차 검증 가능
- ✅ 참고 문헌 풍부 (신뢰도 높음)

**한국 음식 항목**:
```
한국 음식
├── 비빔밥 (Bibimbap)
├── 불고기 (Bulgogi)
├── 갈비 (Galbi/Short ribs)
├── 김치찌개 (Kimchi Jjigae)
├── 떡볶이 (Tteokbokki)
├── 냉면 (Naengmyeon)
└── ... (100+ 항목)

각 항목:
- 한글 설명
- 영어 설명
- 역사/유래
- 조리법
- 변종/지역별 특징
- 이미지 (CC 라이선스)
```

**API**:
```python
# MediaWiki API (위키피디아)
# URL: https://ko.wikipedia.org/w/api.php

# 예: "비빔밥" 정보 조회
import requests

url = "https://ko.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "titles": "비빔밥",
    "format": "json",
    "prop": "extracts|images|pageimages"
}
response = requests.get(url, params=params)
```

---

#### 2-2. 한국학중앙연구원 (Academy of Korean Studies)
**사이트**: https://www.aks.ac.kr/
**자료실**: https://www.koreandb.net/

**특징**:
- ✅ 한국 음식 학술 자료
- ✅ 전통음식 문화 연구
- ✅ 신뢰도 높은 출처

**활용 가능 항목**:
- 전통음식 역사
- 음식 문화 분석
- 지역별 음식 특징
- 학술 논문

---

### Tier 3: 한국 전문 웹사이트

#### 3-1. 한국관광공사 음식 서브사이트
**사이트**: https://www.visitkorea.or.kr/ksf/
**특징**: 한국음식문화 전문 정보

**포함 내용**:
- 한국 대표 음식 소개
- 지역별 음식 정보
- 음식 축제 정보
- 맛집 추천

---

#### 3-2. 한국외식진흥원 (Korea Food Service Industry Association)
**사이트**: http://www.kfsa.or.kr/

**특징**:
- ✅ 외식산업 정보
- ✅ 음식 표준화 정보
- ✅ 영양정보 제공

---

#### 3-3. 농촌진흥청 (Rural Development Administration)
**사이트**: https://www.rda.go.kr/

**특징**:
- ✅ 한국 식재료 정보
- ✅ 음식 영양정보
- ✅ 조리 가이드
- ✅ 공개 이미지

**활용 항목**:
- 한국 채소/고기/해산물 정보
- 음식 조리법
- 영양정보

---

#### 3-4. 네이버 지식백과 (Naver Knowledge Encyclopedia)
**사이트**: https://terms.naver.com/

**특징**:
- ✅ 한국 음식 정보 상세
- ✅ 이미지 풍부
- ✅ 일반인도 접근 쉬움

**예시**:
```
검색: "비빔밥"

결과:
- 설명: "밥 위에 소채와 고기를 얹고 고추장으로 무친 음식..."
- 이미지: 5-10장
- 역사: "조선 궁중 음식에서 비롯..."
- 영양정보: 칼로리, 단백질 등
- 조리법: 단계별 설명
- 지역별 특징: 전주, 남원, 순천 비빔밥
```

**주의**: 저작권 확인 필요 (일부 사용자 제작)

---

## 📊 이미지 수집 우선순위 표

| 순위 | 출처 | 품질 | 저작권 | 이용성 | 추천도 |
|------|------|------|--------|--------|--------|
| **1** | 한국관광공사 API | ⭐⭐⭐⭐⭐ | ✅ 명확 | 쉬움 | ⭐⭐⭐⭐⭐ |
| **2** | 문화정보원 포털 | ⭐⭐⭐⭐⭐ | ✅ 명확 | 중간 | ⭐⭐⭐⭐⭐ |
| **3** | 공공데이터포탈 | ⭐⭐⭐⭐ | ✅ 명확 | 중간 | ⭐⭐⭐⭐ |
| **4** | 위키피디아 한국어 | ⭐⭐⭐⭐ | ✅ CC-BY-SA | 쉬움 | ⭐⭐⭐⭐ |
| **5** | 농촌진흥청 | ⭐⭐⭐ | ✅ 공개 | 중간 | ⭐⭐⭐ |
| **6** | 네이버 지식백과 | ⭐⭐⭐⭐ | ⚠️ 확인필요 | 쉬움 | ⭐⭐⭐ |

---

## 💡 콘텐츠 강화 전략

### 현재 수준 (단순 번역)
```json
{
  "name_ko": "비빔밥",
  "name_en": "Bibimbap",
  "description": "Rice with vegetables and gochujang"  // ❌ 너무 간단
}
```

### 개선된 수준 (전문적 설명)
```json
{
  "name_ko": "비빔밥",
  "name_en": "Bibimbap (Mixed Rice Bowl)",

  // 🆕 상세 설명
  "description": {
    "short_en": "Mixed rice bowl with vegetables and gochujang sauce",
    "long_en": "A traditional Korean comfort food consisting of steamed rice topped with assorted sautéed vegetables, a fried egg, and minced meat, all beautifully arranged in a heated stone or regular bowl. The dish is mixed together with gochujang (red chili pepper paste), creating a harmonious blend of flavors and textures that represents the essence of Korean home cooking.",

    "origin": "The bibimbap has its roots in the Korean royal court during the Joseon Dynasty, where it was a way to use up leftover vegetables and grains.",
    "cultural_significance": "Known as the national representative dish of Korea, bibimbap symbolizes harmony and balance in Korean culinary philosophy."
  },

  // 🆕 지역별 특징
  "regional_variants": [
    {
      "region": "Jeonju, Jeollabuk-do",
      "name_en": "Jeonju Bibimbap",
      "characteristics": "Premium quality with high-grade ingredients, gochujang made from aged soybeans, traditionally served in a stone bowl",
      "specialty": "Uses local vegetables and premium beef"
    },
    {
      "region": "Namwon, Jeollabuk-do",
      "name_en": "Namwon Bibimbap",
      "characteristics": "Lighter version with more vegetables, less oil",
      "specialty": "Famous for its fresh local vegetables"
    }
  ],

  // 🆕 조리법 상세
  "preparation": {
    "main_components": [
      {"item": "Steamed rice", "amount": "1 bowl"},
      {"item": "Gochujang (Korean red chili paste)", "amount": "1-2 tbsp"},
      {"item": "Sesame oil", "amount": "1 tsp"},
      {"item": "Fried egg", "amount": "1"},
      {"item": "Ground beef (or mushroom for vegetarian)", "amount": "50g"},
      {"item": "Bean sprouts", "amount": "30g"},
      {"item": "Zucchini", "amount": "30g"},
      {"item": "Spinach", "amount": "30g"},
      {"item": "Carrots", "amount": "20g"},
      {"item": "Kimchi", "amount": "30g"},
      {"item": "Sesame seeds", "amount": "to garnish"}
    ],
    "steps": [
      "1. Prepare and blanch vegetables separately",
      "2. Stir-fry each vegetable with salt and sesame oil",
      "3. Brown ground beef with soy sauce and garlic",
      "4. Fry egg sunny-side up",
      "5. Arrange all components artfully on hot rice in a stone bowl",
      "6. Top with egg and sesame seeds",
      "7. Mix thoroughly before eating with gochujang and sesame oil"
    ]
  },

  // 🆕 영양정보
  "nutrition": {
    "per_serving": {
      "calories": 650,
      "protein_g": 25,
      "carbs_g": 85,
      "fat_g": 18,
      "fiber_g": 8,
      "sodium_mg": 800
    },
    "health_benefits": [
      "High in vegetables providing various vitamins and minerals",
      "Good source of protein from egg and meat",
      "Capsaicin from gochujang has potential anti-inflammatory properties",
      "Complex carbs from rice provide sustained energy"
    ]
  },

  // 🆕 맛/매운맛 프로필
  "flavor_profile": {
    "spice_level": 2,  // 1-5 scale
    "spice_description": "Mildly spicy due to gochujang, but heat can be adjusted",
    "taste_notes": ["savory", "slightly sweet", "umami from sesame"],
    "texture": "Mix of soft rice, tender vegetables, and slightly crispy sesame",
    "overall": "Comfort food - warming, satisfying, complex flavor balance"
  },

  // 🆕 문화/역사 정보
  "cultural_info": {
    "korean_philosophy": "Represents 'harmony' (조화) in Korean cuisine - balance of colors, textures, and flavors",
    "occasions": "Everyday meal, celebrations, healing food for stomach issues",
    "etiquette": "Mix all ingredients with gochujang before eating; the stone bowl should sizzle",
    "sayings": "'When tired, eat bibimbap' - Korean proverb emphasizing its restorative properties"
  },

  // 🆕 방문자 팁
  "visitor_tips": {
    "ordering": "Order 'bibimbap' (비빔밥) - vegetarian option is 'yachaesaem bibimbap' (야채샘비빔밥)",
    "eating": "Mix quickly while bowl is hot to enhance flavors; the sizzling creates crispy rice bits",
    "temperature": "Served piping hot - be careful when mixing",
    "pairing": "Great with kimchi on the side and a glass of rice wine (makgeolli) or beer"
  },

  // 🆕 유사 메뉴
  "similar_dishes": [
    "Dolsot Bibimbap (Stone Pot Bibimbap) - with crispy rice crust",
    "Hoe Bibimbap (Raw Fish Bibimbap) - premium version with sashimi",
    "Nakji Bibimbap (Octopus Bibimbap) - seafood version"
  ],

  // 🆕 이미지 메타데이터
  "images": [
    {
      "url": "https://commons.wikimedia.org/...",
      "alt_text": "Traditional Jeonju bibimbap in a heated stone bowl with vegetables, egg, and meat arranged artfully on rice",
      "source": "Korea Tourism Organization",
      "license": "CC-BY-4.0",
      "caption": "Authentic Jeonju Bibimbap - the iconic presentation in a stone bowl"
    },
    {
      "url": "https://...",
      "alt_text": "Close-up of bibimbap being mixed with gochujang and sesame oil",
      "source": "Korean Culture Information Service",
      "license": "CC-BY-4.0",
      "caption": "Mixing the bibimbap creates the perfect flavor combination"
    },
    {
      "url": "https://...",
      "alt_text": "Step-by-step preparation of bibimbap vegetables",
      "source": "Rural Development Administration",
      "license": "CC0",
      "caption": "Preparing the fresh vegetables for bibimbap"
    }
  ]
}
```

---

## 🏗️ 콘텐츠 수집 구조

### 각 메뉴별 정보 템플릿

```
메뉴명 (한글/영문)
├── 📝 설명
│   ├── 짧은 설명 (1줄)
│   ├── 상세 설명 (3-4문장)
│   ├── 역사/유래 (2-3문장)
│   └── 문화적 의미 (1-2문장)
│
├── 🗺️ 지역별 특징
│   ├── 지역명
│   ├── 지역 특화 방식
│   └── 특징 설명
│
├── 👨‍🍳 조리법
│   ├── 주요 재료 (리스트 + 양)
│   ├── 단계별 조리 (7-10 단계)
│   └── 팁과 주의사항
│
├── 🥗 영양정보
│   ├── 칼로리, 단백질, 탄수화물, 지방
│   ├── 건강상 이점
│   └── 다이어트 고려사항
│
├── 👅 맛 프로필
│   ├── 매운맛 레벨 (1-5)
│   ├── 맛 특성 (짜맛, 신맛 등)
│   ├── 식감 설명
│   └── 전체 인상
│
├── 🎭 문화정보
│   ├── 철학적 의미
│   ├── 먹는 장소/시기
│   ├── 식사 에티켓
│   └── 관련 속담/표현
│
├── 🧳 방문자 팁
│   ├── 주문법
│   ├── 먹는 법
│   ├── 온도/신선도
│   └── 추천 곁반찬/음료
│
├── 🔗 관련 메뉴
│   └── 유사 또는 변종 메뉴 (3-5개)
│
└── 📷 이미지 (최소 3장)
    ├── 완성된 요리 사진
    ├── 조리 과정 사진
    └── 지역 특화 버전
```

---

## 🔄 구현 프로세스 (Phase 1 - Sprint 2)

### 주차 1: 이미지 수집 (10시간)

**Day 1-2: 공식 API 통합 (4시간)**
```python
# 1. 한국관광공사 API 연결
from korea_tourism_api import VisitKoreaTourismAPI

api = VisitKoreaTourismAPI(api_key="YOUR_KEY")

# 메뉴 정보 + 이미지 수집
food_items = [
    "비빔밥", "불고기", "갈비", "한우불고기",
    "김치찌개", "떡볶이", "냉면", "돈까스",
    "팔보채", "순두부찌개", "옛날통닭", "숯불갈비"
]

for menu in food_items:
    info = api.search_food(menu, lang="ko")
    images = api.get_images(info.id)
    save_to_database(menu, info, images)
```

**Day 2-3: 위키피디아 크롤링 (3시간)**
```python
# 2. 위키피디아 한국어 API 통합
from mediawiki import MediaWiki

wiki = MediaWiki(lang='ko')

for menu in food_items:
    # 한글 항목 조회
    page = wiki.page(menu)
    content = page.content
    images = page.images

    # 영문 항목도 교차 검증
    wiki_en = MediaWiki(lang='en')
    page_en = wiki_en.page(translate_to_english(menu))

    extract_and_save(menu, content, page_en.content, images)
```

**Day 3-4: 공공데이터포탈 (3시간)**
```python
# 3. 공공데이터포탈 API 연결
from korea_public_data import PublicDataPortal

portal = PublicDataPortal(auth_key="YOUR_KEY")

# 영양정보, 알레르기, 지역정보
nutrition_data = portal.search("한국음식영양정보", query_type="식약청")
allergen_data = portal.search("음식알레르기정보")
regional_food = portal.search("지역특산음식목록")

merge_with_existing_data(nutrition_data, allergen_data, regional_food)
```

### 주차 2: 콘텐츠 강화 (12시간)

**Day 5-6: 설명 작성 (6시간)**
- 각 메뉴 10-15가지 콘텐츠 포인트 작성
- 한영 이중 작성
- 전문가 검수 (음식 전문가 1인)

**Day 7-8: 지역별 특징 (4시간)**
- 각 메뉴의 유명한 지역 변종 조사
- 지역별 특징 정보 추가

**Day 9-10: 테스트 및 배포 (6시간)**
- 이미지 로딩 테스트
- 콘텐츠 정확성 검증
- API 응답 성능 테스트

---

## 📋 DB 스키마 확장 (상세)

### canonical_menus 테이블

```sql
ALTER TABLE canonical_menus ADD COLUMN (
    -- 기본 이미지
    primary_image JSONB,  -- url, alt_text, source, license

    -- 추가 이미지 (3-5개)
    images JSONB[],

    -- 상세 설명
    description_long_en TEXT,
    description_long_ko TEXT,

    -- 문화정보
    origin_story TEXT,           -- 유래/역사
    cultural_significance TEXT,  -- 문화적 의미
    korean_philosophy TEXT,      -- 한국 철학적 의미

    -- 지역별 정보
    regional_variants JSONB,  -- [{region, name, characteristics}]

    -- 조리정보
    preparation_steps JSONB,  -- [{step_number, description}]
    main_ingredients JSONB,   -- [{ingredient, amount, english_name}]
    cooking_tips TEXT,

    -- 맛 프로필
    flavor_profile JSONB,  -- {spice_level, taste_notes[], texture}

    -- 영양정보 (상세)
    nutrition_detail JSONB,  -- {calories, protein, carbs, fat, sodium, fiber}
    health_benefits TEXT[],

    -- 방문자 정보
    visitor_tips JSONB,  -- {ordering, eating, temperature, pairing}
    etiquette TEXT,

    -- 유사 메뉴
    similar_dishes JSONB[],  -- [{dish_name, description}]

    -- 메타데이터
    source_references JSONB,  -- [{source, url, date}]
    last_updated_from JSONB,  -- {api: 'korea_tourism', date: '2026-02-18'}

    -- 콘텐츠 품질
    content_completeness DECIMAL,  -- 0-100%
    verified_by TEXT,  -- 검증자 정보
    verified_date TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_canonical_primary_image ON canonical_menus USING GIN(primary_image);
CREATE INDEX idx_canonical_variants ON canonical_menus USING GIN(regional_variants);
CREATE INDEX idx_canonical_verified ON canonical_menus(verified_date DESC);
```

---

## 🎨 API 응답 예시 (확장)

### GET /api/v1/canonical-menus/{id}

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name_ko": "비빔밥",
  "name_en": "Bibimbap",

  // 🆕 이미지 (3개)
  "primary_image": {
    "url": "https://images.korea-tourism.go.kr/bibimbap-1.jpg",
    "alt_text": "Traditional Jeonju bibimbap in heated stone bowl",
    "source": "Korea Tourism Organization",
    "license": "CC-BY-4.0",
    "caption": "Authentic Jeonju Bibimbap with sizzling stone bowl",
    "width": 1200,
    "height": 800
  },

  "images": [
    {
      "url": "https://images.korea-tourism.go.kr/bibimbap-prep.jpg",
      "alt_text": "Step-by-step preparation of bibimbap",
      "source": "Korean Culture Information Service",
      "caption": "Preparing fresh vegetables for bibimbap"
    },
    {
      "url": "https://commons.wikimedia.org/wiki/Special:FilePath/Bibimbap.jpg",
      "alt_text": "Namwon bibimbap regional variant",
      "source": "Korean Wikipedia",
      "license": "CC-BY-SA-4.0",
      "caption": "Namwon-style bibimbap with local vegetables"
    }
  ],

  // 🆕 상세 설명
  "description": {
    "short": "Mixed rice bowl with vegetables and gochujang",
    "long": "A traditional Korean comfort food consisting of steamed rice topped with assorted sautéed vegetables, a fried egg, and minced meat, all beautifully arranged in a heated stone or regular bowl. The dish is mixed together with gochujang..."
  },

  // 🆕 역사/문화
  "cultural_info": {
    "origin": "Originated in the Joseon Dynasty royal court as a way to use leftover vegetables and grains",
    "significance": "Korea's representative national dish, symbolizing harmony and balance",
    "philosophy": "Represents the yin-yang principle in Korean cuisine with balanced colors and flavors",
    "occasions": "Everyday meal, celebrations, healing food",
    "etiquette": "Mix all ingredients with gochujang before eating; sizzling sound in stone bowl enhances experience"
  },

  // 🆕 지역별 변종
  "regional_variants": [
    {
      "region": "Jeonju, Jeollabuk-do",
      "name": "Jeonju Bibimbap",
      "characteristics": "Premium quality with aged gochujang, high-grade ingredients, stone bowl",
      "specialty": "Local vegetables and premium beef"
    },
    {
      "region": "Namwon, Jeollabuk-do",
      "name": "Namwon Bibimbap",
      "characteristics": "Lighter version with fresh local vegetables",
      "specialty": "Emphasis on vegetable quality"
    }
  ],

  // 🆕 조리정보
  "preparation": {
    "ingredients": [
      {"name": "Steamed rice", "amount": "1 bowl", "korean": "밥"},
      {"name": "Gochujang", "amount": "1-2 tbsp", "korean": "고추장"},
      {"name": "Ground beef", "amount": "50g", "korean": "소고기"}
    ],
    "steps": [
      {
        "number": 1,
        "description": "Prepare and blanch vegetables separately"
      },
      {
        "number": 2,
        "description": "Stir-fry each vegetable with salt and sesame oil"
      }
    ],
    "time_minutes": 25,
    "difficulty": "Easy",
    "tips": "Mix quickly while hot to enhance flavors"
  },

  // 🆕 영양정보 (상세)
  "nutrition": {
    "per_serving": {
      "calories": 650,
      "protein_g": 25,
      "carbs_g": 85,
      "fat_g": 18,
      "fiber_g": 8,
      "sodium_mg": 800
    },
    "health_benefits": [
      "High in vegetables providing vitamins and minerals",
      "Good protein source from egg and meat",
      "Capsaicin has anti-inflammatory properties",
      "Complex carbs provide sustained energy"
    ]
  },

  // 🆕 맛 프로필
  "flavor_profile": {
    "spice_level": 2,
    "spice_description": "Mildly spicy, adjustable by amount of gochujang",
    "taste_notes": ["savory", "slightly sweet", "umami"],
    "texture": "Mix of soft rice, tender vegetables, crispy sesame",
    "overall": "Warming, satisfying, complex balance"
  },

  // 🆕 방문자 팁
  "visitor_tips": {
    "ordering": {
      "korean_name": "비빔밥",
      "pronunciation": "bee-bim-bap",
      "vegetarian_option": "Vegetable bibimbap (야채비빔밥)"
    },
    "eating": {
      "method": "Mix quickly while hot",
      "why": "Creates crispy rice bits (socarim) and enhances flavors",
      "warning": "Hot temperature - be careful when mixing"
    },
    "temperature": "Served piping hot",
    "pairing": "Kimchi on the side, rice wine (makgeolli) or beer"
  },

  // 🆕 유사 메뉴
  "similar_dishes": [
    {
      "name": "Dolsot Bibimbap",
      "description": "Stone pot version with crispy rice crust",
      "difference": "More textural contrast"
    },
    {
      "name": "Hoe Bibimbap",
      "description": "Premium version with raw fish",
      "difference": "Seafood-based, higher quality"
    }
  ],

  // 기존 필드
  "main_ingredients_ko": ["쌀", "고추장", "소고기"],
  "allergens": ["sesame", "soy", "beef"],
  "spice_level": 2,
  "difficulty_score": 1,

  // 메타데이터
  "source_references": [
    {
      "source": "Korea Tourism Organization",
      "url": "https://www.visitkorea.or.kr/",
      "accessed_date": "2026-02-18"
    },
    {
      "source": "Korean Wikipedia",
      "url": "https://ko.wikipedia.org/wiki/비빔밥",
      "accessed_date": "2026-02-18"
    }
  ],
  "last_updated_from": {
    "api": "korea_tourism",
    "date": "2026-02-18"
  },
  "content_completeness": 95,
  "verified_by": "Food Culture Expert",
  "verified_date": "2026-02-18"
}
```

---

## 📱 UI 업데이트 (이미지 + 콘텐츠)

### 검색 결과 - 프리미엄 레이아웃

```html
<div class="result-card premium">
  <!-- 이미지 섹션 -->
  <div class="result-image-container">
    <img src="bibimbap-primary.jpg"
         alt="Traditional Jeonju bibimbap in heated stone bowl"
         class="result-image-primary">
    <div class="image-carousel">
      <button class="carousel-btn prev">‹</button>
      <div class="carousel-thumbnails">
        <img src="bibimbap-1.jpg" class="thumbnail active">
        <img src="bibimbap-prep.jpg" class="thumbnail">
        <img src="bibimbap-regional.jpg" class="thumbnail">
      </div>
      <button class="carousel-btn next">›</button>
    </div>
    <span class="image-credit">Source: Korea Tourism Organization</span>
  </div>

  <!-- 기본 정보 -->
  <div class="result-header">
    <div class="result-title">
      <h2 class="korean-name">비빔밥</h2>
      <p class="english-name">Bibimbap (Mixed Rice Bowl)</p>
    </div>
    <div class="result-badges">
      <span class="badge-easy">Easy to Make</span>
      <span class="badge-popular">National Dish</span>
    </div>
  </div>

  <!-- 설명 -->
  <div class="result-description-section">
    <h3 class="subsection-title">What is it?</h3>
    <p class="short-description">Mixed rice bowl with vegetables and gochujang</p>
    <p class="long-description">A traditional Korean comfort food consisting of steamed rice topped with assorted sautéed vegetables, a fried egg, and minced meat, all beautifully arranged in a heated stone or regular bowl...</p>
  </div>

  <!-- 맛 프로필 -->
  <div class="result-flavor-profile">
    <div class="flavor-stat">
      <span class="flavor-label">🌶️ Spice Level:</span>
      <div class="spice-bar">
        <div class="spice-fill" style="width: 40%"></div>
      </div>
      <span class="spice-value">2/5 (Mild)</span>
    </div>
    <div class="flavor-notes">
      <strong>Taste Notes:</strong> Savory, Slightly Sweet, Umami Rich
    </div>
    <div class="texture-info">
      <strong>Texture:</strong> Mix of soft rice, tender vegetables, crispy sesame
    </div>
  </div>

  <!-- 영양정보 -->
  <div class="nutrition-section">
    <h3 class="subsection-title">Nutrition (per serving)</h3>
    <div class="nutrition-grid">
      <div class="nutrition-item">
        <div class="nutrition-value">650</div>
        <div class="nutrition-label">Calories</div>
      </div>
      <div class="nutrition-item">
        <div class="nutrition-value">25g</div>
        <div class="nutrition-label">Protein</div>
      </div>
      <div class="nutrition-item">
        <div class="nutrition-value">85g</div>
        <div class="nutrition-label">Carbs</div>
      </div>
      <div class="nutrition-item">
        <div class="nutrition-value">18g</div>
        <div class="nutrition-label">Fat</div>
      </div>
    </div>
  </div>

  <!-- 지역별 변종 -->
  <div class="regional-variants-section">
    <h3 class="subsection-title">Regional Variations</h3>
    <div class="variants-list">
      <div class="variant-card">
        <h4 class="variant-title">🏙️ Jeonju Bibimbap</h4>
        <p class="variant-description">Premium quality with aged gochujang and high-grade beef, served in a heated stone bowl</p>
      </div>
      <div class="variant-card">
        <h4 class="variant-title">🏞️ Namwon Bibimbap</h4>
        <p class="variant-description">Lighter version with fresh local vegetables, emphasis on freshness</p>
      </div>
    </div>
  </div>

  <!-- 조리법 -->
  <div class="preparation-section">
    <h3 class="subsection-title">How to Make (25 minutes)</h3>
    <div class="preparation-steps">
      <div class="step">
        <span class="step-number">1</span>
        <span class="step-text">Prepare and blanch vegetables separately</span>
      </div>
      <div class="step">
        <span class="step-number">2</span>
        <span class="step-text">Stir-fry each vegetable with salt and sesame oil</span>
      </div>
      <!-- ... more steps ... -->
    </div>
  </div>

  <!-- 방문자 팁 -->
  <div class="visitor-tips-section">
    <h3 class="subsection-title">💡 Tips for Visitors</h3>
    <div class="tips-grid">
      <div class="tip-card">
        <h4 class="tip-title">How to Order</h4>
        <p class="tip-content">Ask for "비빔밥" (bee-bim-bap). Vegetarian option: "야채비빔밥"</p>
      </div>
      <div class="tip-card">
        <h4 class="tip-title">How to Eat</h4>
        <p class="tip-content">Mix all ingredients quickly while hot - this creates crispy rice and enhances flavor</p>
      </div>
      <div class="tip-card">
        <h4 class="tip-title">Best Pairing</h4>
        <p class="tip-content">Serve with kimchi, rice wine (makgeolli), or cold beer</p>
      </div>
    </div>
  </div>

  <!-- 유사 메뉴 -->
  <div class="similar-dishes-section">
    <h3 class="subsection-title">Similar Dishes</h3>
    <div class="similar-grid">
      <div class="similar-card">
        <h4>Dolsot Bibimbap</h4>
        <p>Stone pot version with crispy rice crust</p>
      </div>
      <div class="similar-card">
        <h4>Hoe Bibimbap</h4>
        <p>Premium version with fresh raw fish</p>
      </div>
    </div>
  </div>

  <!-- 알레르기 정보 -->
  <div class="allergen-section">
    <h3 class="subsection-title">⚠️ Allergen Information</h3>
    <div class="allergen-tags">
      <span class="allergen-tag sesame">Sesame</span>
      <span class="allergen-tag soy">Soy</span>
      <span class="allergen-tag beef">Beef</span>
    </div>
    <p class="allergen-disclaimer">Information based on standard recipes. Always confirm with restaurant staff.</p>
  </div>

  <!-- 문화정보 -->
  <div class="cultural-section">
    <h3 class="subsection-title">🎭 Cultural Significance</h3>
    <p class="cultural-text">Bibimbap represents the Korean philosophy of harmony and balance. It originated in the Joseon Dynasty royal court as a creative way to use leftover vegetables and grains. Today, it's Korea's national representative dish.</p>
    <div class="cultural-quote">
      <em>"When tired, eat bibimbap"</em> - Korean Proverb
    </div>
  </div>

  <!-- 출처 -->
  <div class="sources-section">
    <h3 class="subsection-title">📚 Information Sources</h3>
    <div class="sources-list">
      <a href="https://www.visitkorea.or.kr/" target="_blank">Korea Tourism Organization</a>
      <a href="https://ko.wikipedia.org/wiki/비빔밥" target="_blank">Korean Wikipedia</a>
    </div>
    <p class="last-updated">Last updated: February 18, 2026 | Verified by: Food Culture Expert</p>
  </div>

  <!-- 피드백 -->
  <div class="feedback-section">
    <p class="feedback-prompt">Was this information helpful?</p>
    <button class="feedback-btn yes">👍 Yes</button>
    <button class="feedback-btn no">👎 No</button>
  </div>
</div>
```

---

## 📊 Sprint 2 상세 작업 분해

### 주차 1: 백엔드 (14시간)

| 작업 | 예상시간 | 설명 |
|------|---------|------|
| 한국관광공사 API 통합 | 3시간 | 공식 API 연결, 인증, 데이터 수집 |
| 위키피디아 API 통합 | 2시간 | 위키 페이지 크롤링, 이미지 추출 |
| 공공데이터포탈 연결 | 2시간 | 영양정보, 지역정보 통합 |
| DB 마이그레이션 작성 | 2시간 | JSONB 필드 추가, 인덱스 생성 |
| 이미지 수집 스크립트 | 3시간 | S3 업로드, 메타데이터 저장 |
| 초기 데이터 (100개 메뉴) | 2시간 | 자동화 스크립트 실행, 검증 |
| **소계** | **14시간** | |

### 주차 2: API + 프론트엔드 (14시간)

| 작업 | 예상시간 | 설명 |
|------|---------|------|
| API 엔드포인트 확장 | 2시간 | GET /canonical-menus 응답 확장 |
| 이미지 CDN 설정 | 1시간 | CloudFront 또는 S3 직접 서빙 |
| UI 컴포넌트 (이미지) | 4시간 | 반응형 이미지, 캐러셀, lazy loading |
| UI 컴포넌트 (콘텐츠) | 4시간 | 탭, 아코디언, 확장 가능 섹션 |
| CSS 스타일링 | 2시간 | 반응형 디자인, 모바일 최적화 |
| 성능 최적화 | 1시간 | 이미지 압축, 번들 크기 |
| **소계** | **14시간** | |

### 주차 3: 테스트 + 배포 (8시간)

| 작업 | 예상시간 | 설명 |
|------|---------|------|
| 데이터 정확성 검증 | 2시간 | 샘플 메뉴 10개 수동 검증 |
| API 응답 성능 테스트 | 1시간 | p95 응답시간 측정 |
| UI/UX 테스트 (모바일) | 2시간 | 다양한 디바이스 테스트 |
| 이미지 로딩 테스트 | 1시간 | 캐시, CDN 동작 확인 |
| 배포 및 모니터링 | 2시간 | FastComet 배포, 로그 확인 |
| **소계** | **8시간** | |

### **총 예상**: 36시간 (약 1주일 + 여유)

---

## 🎯 Phase 1 최종 목표

✅ **한국 공식 출처 중심** 이미지 수집
✅ **전문적 콘텐츠** (문화, 역사, 조리법, 영양정보)
✅ **3-5개 이미지** 메뉴당
✅ **100개 메뉴** 완전한 정보 제공
✅ **외국인 신뢰도** 극대화 (시각적 + 정보적)
✅ **모바일 최적화** 이미지 표시
✅ **저작권 투명성** 모든 이미지 출처 표시

---

**이 설계를 바탕으로 Sprint 2를 시작할 준비가 되었습니다!** 🚀

작성: Claude Code
날짜: 2026-02-18
우선순위: **P0 (Critical)**
