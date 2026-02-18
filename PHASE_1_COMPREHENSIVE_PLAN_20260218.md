# Sprint 2: Phase 1 최종 종합 기획서
## 한국 중심 이미지 수집 + AI 생성 이미지 + 전문적 콘텐츠

**작성일**: 2026-02-18
**검토자**: User + Claude Code
**상태**: ✅ **최종 검토 완료 및 승인 대기**
**우선순위**: **P0 (Critical)**

---

## 📌 Executive Summary

### 핵심 목표
외국인들이 "메뉴를 알 수 없다"는 문제를 **시각적 + 정보적으로 완전히 해결**

### 3가지 전략
1. **한국 공식 출처 중심** - 한국관광공사, 문화부, 공공데이터
2. **생성형 AI 보완** - 저작권 확보 + 부족한 이미지 채우기
3. **전문적 콘텐츠** - 단순 번역 → 문화, 역사, 조리법, 영양정보

### 예상 결과
✅ 메뉴당 **3-5개 고품질 이미지** (공식 + AI)
✅ **100개 메뉴** 완전한 정보
✅ **외국인 신뢰도** 극대화
✅ **우리만의 저작권** 확보 (AI 생성 이미지)

---

## 🎯 Part 1: 한국 공식 출처 이미지 수집 전략

### Tier 1: 공식 한국 정부 API (우선순위 1순위)

#### 1-1. 한국관광공사 (Korea Tourism Organization)
**API**: https://api.visitkorea.or.kr/
**라이선스**: 공공데이터 (CC 라이선스 또는 공개)
**품질**: ⭐⭐⭐⭐⭐

**수집 항목**:
- 각 지역 특산 음식 사진 (고품질)
- 조리 과정 사진
- 레스토랑/음식 축제 사진
- 한영 설명 포함

**API 사용 방법**:
```python
# 1. API 키 신청 (무료)
# https://www.visitkorea.or.kr/ksf/main/main.do

# 2. Python 통합
import requests

api_key = "YOUR_API_KEY"
url = "https://api.visitkorea.or.kr/openapi/service/rest/KorService"

# 음식/축제 검색
params = {
    "serviceKey": api_key,
    "numOfRows": 50,
    "pageNo": 1,
    "listYN": "Y",
    "MobileOS": "ETC",
    "MobileApp": "AppTest",
    "_type": "json"
}

# 모든 음식 항목 검색
response = requests.get(f"{url}/searchKeyword", params=params)
food_items = response.json()
```

**예상 수집 가능 이미지**: **50-70개 메뉴**

---

#### 1-2. 한국문화정보원 (Korean Culture Information Service)
**사이트**: https://www.culturecontent.com/
**라이선스**: CC 라이선스 (공개)
**품질**: ⭐⭐⭐⭐⭐

**특징**:
- 전통음식 공식 정보
- 메뉴명 + 사진 + 역사 + 조리법 함께 제공
- 대한민국 정부 공식 자료

**예상 수집 가능 이미지**: **30-40개 메뉴**

---

#### 1-3. 공공데이터포탈 (Public Data Portal)
**사이트**: https://www.data.go.kr/
**라이선스**: 공개 (공공데이터)
**품질**: ⭐⭐⭐⭐

**포함 데이터**:
- 한국음식 표준 분류
- 음식 영양정보 (식약청)
- 지역별 특산 음식 목록
- 음식 문화유산 정보

**예상 수집 가능**: 이미지 자체는 적지만 **메타데이터 풍부**

---

### Tier 2: 한국 학술/백과 (우선순위 2순위)

#### 2-1. 위키피디아 한국어 (Korean Wikipedia)
**사이트**: https://ko.wikipedia.org/
**라이선스**: CC-BY-SA-4.0 (명확한 저작권)
**품질**: ⭐⭐⭐⭐

**한국 음식 항목**: 100+ 개

**API 활용**:
```python
import requests

url = "https://ko.wikipedia.org/w/api.php"

# 비빔밥 항목 조회
params = {
    "action": "query",
    "titles": "비빔밥",
    "prop": "extracts|pageimages",
    "format": "json",
    "pithumbsize": 500
}

response = requests.get(url, params=params)
page = response.json()['query']['pages']
```

**예상 수집 가능 이미지**: **50-60개 메뉴**

---

#### 2-2. 한국학중앙연구원
**사이트**: https://www.koreandb.net/
**라이선스**: 학술 자료 (저작권 확인 필요)
**품질**: ⭐⭐⭐⭐

**학술적 신뢰도 높음** (대학교, 연구소 인용용)

---

### Tier 3: 한국 전문 사이트

#### 3-1. 농촌진흥청 (Rural Development Administration)
**사이트**: https://www.rda.go.kr/
**라이선스**: 공개
**품질**: ⭐⭐⭐

**특징**:
- 식재료 정보
- 조리 가이드
- 영양정보
- 고품질 음식 사진

**예상 수집 가능 이미지**: **20-30개 메뉴**

---

#### 3-2. 네이버 지식백과
**사이트**: https://terms.naver.com/
**라이선스**: ⚠️ 저작권 확인 필수
**품질**: ⭐⭐⭐⭐

**주의**: 일부 사용자 제작 콘텐츠 포함
→ 저작권 명확한 항목만 수집

---

### 📊 Tier별 수집 예상

| Tier | 출처 | 예상 이미지 | 품질 | 저작권 | 합계 |
|------|------|----------|------|--------|------|
| **1** | 한국관광공사 | 50-70 | ⭐⭐⭐⭐⭐ | ✅ 명확 | **70** |
| **1** | 문화정보원 | 30-40 | ⭐⭐⭐⭐⭐ | ✅ 명확 | **40** |
| **2** | 위키피디아 | 50-60 | ⭐⭐⭐⭐ | ✅ CC-BY-SA | **60** |
| **3** | 농촌진흥청 | 20-30 | ⭐⭐⭐ | ✅ 공개 | **30** |
| **합계** | | | | | **200** |

**현황**: 공식 출처에서 **70-100개 메뉴 이미지 확보 가능** ✅

---

## 🤖 Part 2: AI 생성 이미지 전략 (저작권 확보)

### 사용 시나리오

```
┌─────────────────────────────────┐
│ 공식 출처 이미지 수집 (100개)    │
│ 성공률: 70-100개                │
└────────────┬────────────────────┘
             │
    ┌────────▼────────┐
    │ 충분한가?         │
    └─┬──────────┬────┘
      │          │
   YES│          │NO
      │          │
      │     ┌────▼──────────────────────┐
      │     │ AI 생성 이미지로 보충      │
      │     │ - 부족한 메뉴 (0-30개)    │
      │     │ - 대체 이미지 필요         │
      │     │ - 지역별 변종 이미지       │
      │     └────┬──────────────────────┘
      │          │
      └──────────┬───────────────────────┐
                 │                       │
          최종 결과: 100개 메뉴 × 3-5개 이미지
```

### AI 생성 이미지 도구 비교

#### 옵션 1: DALL-E 3 (OpenAI)
**가격**: $0.04-0.12 / 이미지 (고해상도)
**품질**: ⭐⭐⭐⭐⭐
**속도**: 중간 (30-60초)
**저작권**: ✅ 우리 소유 (상업 사용 가능)
**통합**: OpenAI API 쉬움

**장점**:
- 높은 품질
- 정확한 음식 표현
- API 통합 간단
- 상업 사용 허용

**단점**:
- 비용 (대량 생성 시)
- 국내 서비스 제한 없음

**사용 예시**:
```python
from openai import OpenAI

client = OpenAI(api_key="YOUR_KEY")

menus_need_image = [
    "떡국", "배추김치", "팔보채", ...  # 30-40개
]

for menu in menus_need_image:
    prompt = f"""
    Create a professional food photography image of {menu}, a traditional Korean dish.
    - Studio lighting
    - Warm, appetizing colors
    - Professional plating
    - Medium close-up view
    - No text or watermarks
    - Ultra high quality, 4K
    """

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="hd",
        n=1
    )

    image_url = response.data[0].url
    save_image_to_s3(menu, image_url)
```

**예상 비용**: 30-40개 × $0.08 = **$2.40-3.20** (매우 저렴)

---

#### 옵션 2: Midjourney
**가격**: $10-30/월 (무제한 생성)
**품질**: ⭐⭐⭐⭐⭐ (가장 아름다움)
**속도**: 빠름 (30초)
**저작권**: ✅ 우리 소유 (유료 요금제)
**통합**: Discord API (복잡)

**장점**:
- 가장 아름다운 결과물
- 빠른 생성
- 월정액 (대량 생성 유리)

**단점**:
- API 통합 복잡 (Discord 거쳐야 함)
- 월정액 비용

---

#### 옵션 3: Stable Diffusion (자체 호스팅)
**가격**: 0원 (설치 후 무료) + 클라우드 비용
**품질**: ⭐⭐⭐⭐
**속도**: 빠름 (10-20초)
**저작권**: ✅ 우리 소유
**통합**: ComfyUI, WebUI (자체 개발 가능)

**장점**:
- 완전 무료 (라이선스)
- 장기적으로 저렴
- 완전 제어 가능
- 개인정보 보호 (로컬)

**단점**:
- 초기 설정 복잡
- GPU 필요 (또는 클라우드 비용)
- 품질이 DALL-E/Midjourney보다 약간 낮음

---

#### 옵션 4: Leonardo.AI
**가격**: $10-50/월
**품질**: ⭐⭐⭐⭐
**속도**: 매우 빠름 (5-10초)
**저작권**: ✅ 우리 소유
**통합**: API (간단)

**특징**: 음식 생성 특화

---

### 💡 추천 전략

#### Phase 1a: 공식 출처 이미지 수집 (무료)
```
1. 한국관광공사 API → 70개 이미지
2. 문화정보원 → 30개 이미지
3. 위키피디아 → 60개 이미지 중 30개
합계: 130개 이미지 (100개 메뉴 × 1-2개씩)
```

#### Phase 1b: AI 생성으로 보충 (저렴)
```
부족한 부분:
1. 지역별 변종 이미지 (30개 메뉴 × 2-3개 추가)
   → AI로 "Jeonju Bibimbap", "Namwon Bibimbap" 등 생성

2. 조리 과정 사진 (부족한 경우)
   → AI로 "Step 1: Preparing vegetables", "Step 2: Cooking beef" 등

3. 메뉴 고유의 모습 강화
   → AI로 최고 품질 버전 생성

선택:
- 대량 생성 필요 → Midjourney ($20/월)
- 소량, 저비용 → DALL-E 3 ($1-2)
- 자체 컨트롤 원함 → Stable Diffusion (초기 설정만)
```

**추천**: **DALL-E 3** (빠른 구현 + 저비용)

---

### AI 생성 이미지 품질 보장

#### 프롬프트 템플릿 (고품질)

```python
HIGH_QUALITY_PROMPT = """
Create a professional food photography image of {menu_name},
a traditional Korean dish.

Visual Requirements:
- Professional studio lighting with warm, golden tones
- Authentic, appetizing presentation
- Medium close-up view (45-degree angle)
- Traditional Korean bowl/plating when appropriate
- Fine details visible (textures, colors, ingredients)
- Rich color saturation without oversaturation
- Cinematic depth of field with slight blur on background

Style:
- High-end restaurant food photography
- Michelin-guide quality
- Ultra high resolution (4K equivalent)
- No text, watermarks, or artifacts
- No artificial elements or styling
- Professional food stylist result

Composition:
- Rule of thirds composition
- Natural, non-manipulated appearance
- Balanced lighting without harsh shadows
- Background subtly blurred (supports main dish)

Details:
- Show the essence of the dish
- Clearly identifiable as {menu_name}
- Appealing to international audience
- Looks fresh and delicious
- Professional quality suitable for website/marketing
"""
```

#### 검증 프로세스

```python
def validate_ai_image(image_url, menu_name):
    """AI 생성 이미지 품질 검증"""

    checks = {
        "is_food_visible": True,        # 음식이 명확한가?
        "is_high_quality": True,        # 품질이 높은가?
        "is_appetizing": True,          # 먹음직한가?
        "color_correct": True,          # 색상이 자연스러운가?
        "no_artifacts": True,           # 이상한 생성물은 없는가?
        "identifiable": True,           # {menu_name}을 식별할 수 있는가?
    }

    # 검증 실패 시:
    # 1. 프롬프트 개선 후 재생성
    # 2. 다른 AI 도구 시도
    # 3. 공식 출처에서 찾기 (fallback)
```

---

## 📚 Part 3: 전문적 콘텐츠 강화

### 콘텐츠 구조 (각 메뉴별)

```
메뉴명 (한글/영문)
│
├─ 📝 설명
│  ├─ 짧은 설명 (1줄)
│  ├─ 상세 설명 (3-4문장)
│  ├─ 역사/유래 (2-3문장)
│  └─ 문화적 의미 (1-2문장)
│
├─ 🗺️ 지역별 특징 (3-5개 지역)
│  └─ 각각: 특징 + AI 생성 이미지
│
├─ 👨‍🍳 조리법
│  ├─ 주요 재료 (한영 병기)
│  ├─ 단계별 조리 (7-10단계)
│  └─ 팁과 주의사항
│
├─ 🥗 영양정보
│  ├─ 칼로리, 단백질, 탄수화물, 지방
│  ├─ 건강상 이점
│  └─ 다이어트 고려사항
│
├─ 👅 맛 프로필
│  ├─ 매운맛 레벨 (1-5)
│  ├─ 맛 특성 (짜맛, 신맛 등)
│  ├─ 식감 설명
│  └─ 전체 인상
│
├─ 🎭 문화정보
│  ├─ 철학적 의미 (조화, 음양 등)
│  ├─ 먹는 장소/시기
│  ├─ 식사 에티켓
│  └─ 관련 속담/표현
│
├─ 🧳 방문자 팁
│  ├─ 주문법 (발음 포함)
│  ├─ 먹는 법
│  ├─ 온도/신선도
│  └─ 추천 곁반찬/음료
│
├─ 🔗 유사 메뉴 (3-5개)
│  └─ 각각 간단 설명
│
└─ 📷 이미지 (3-5개)
   ├─ 완성된 요리 (공식 출처)
   ├─ 조리 과정 (공식 또는 AI)
   ├─ 지역 특화 버전 (AI)
   └─ 필요시 추가 이미지 (AI)
```

### 콘텐츠 출처

#### 자동 수집 (API)
```
1. 한국관광공사 → 설명, 역사
2. 문화정보원 → 문화적 의미, 조리법
3. 위키피디아 → 역사, 지역별 정보
4. 농촌진흥청 → 영양정보
```

#### 수동 작성 (전문가)
```
1. 맛 프로필 → 음식 전문가 (1시간)
2. 방문자 팁 → 한국 거주 외국인 또는 관광 가이드 (1시간)
3. 문화 인사이트 → 한국 문화 전문가 (1시간)
```

#### AI 보조 (생성)
```
1. 영어 번역 → GPT-4 (자동)
2. 추가 설명 → Claude API (자동)
3. 조리법 세부사항 → ChatGPT (자동 초안 → 검수)
```

---

## 🗄️ Part 4: 데이터베이스 스키마 확장

### canonical_menus 테이블 (ALTER)

```sql
ALTER TABLE canonical_menus ADD COLUMN (
    -- 🆕 이미지 (공식 + AI)
    primary_image JSONB,
    images JSONB[],           -- 3-5개 이미지 배열
    ai_generated_images JSONB[], -- AI 생성 이미지 추적

    -- 🆕 상세 설명
    description_long_en TEXT,
    description_long_ko TEXT,
    origin_story TEXT,
    cultural_significance TEXT,

    -- 🆕 지역별 정보
    regional_variants JSONB,  -- [{region, name, characteristics, ai_image}]

    -- 🆕 조리정보
    preparation_steps JSONB,
    main_ingredients JSONB,
    cooking_tips TEXT,

    -- 🆕 영양정보 (상세)
    nutrition_detail JSONB,
    health_benefits TEXT[],

    -- 🆕 맛 프로필
    flavor_profile JSONB,

    -- 🆕 방문자 정보
    visitor_tips JSONB,
    etiquette TEXT,

    -- 🆕 유사 메뉴
    similar_dishes JSONB[],

    -- 🆕 메타데이터
    source_references JSONB,
    content_completeness DECIMAL,
    verified_by TEXT,
    verified_date TIMESTAMP,
    image_sources JSONB      -- {official_sources: [...], ai_generated: [...]}
);
```

### images_generation_log 테이블 (NEW)

```sql
CREATE TABLE images_generation_log (
    id UUID PRIMARY KEY,
    menu_id UUID REFERENCES canonical_menus(id),

    -- AI 생성 정보
    ai_provider VARCHAR(50),     -- 'dall-e-3', 'midjourney', 'stable-diffusion'
    prompt TEXT,
    image_url VARCHAR(500),
    s3_key VARCHAR(500),

    -- 품질 평가
    quality_score DECIMAL(3,2),  -- 0-10
    approved BOOLEAN,
    rejected_reason TEXT,

    -- 메타데이터
    generated_at TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by VARCHAR(100),

    cost_usd DECIMAL(10,4),

    created_at TIMESTAMP
);
```

### 인덱스 추가

```sql
CREATE INDEX idx_canonical_verified ON canonical_menus(verified_date DESC);
CREATE INDEX idx_canonical_completeness ON canonical_menus(content_completeness DESC);
CREATE INDEX idx_images_approved ON images_generation_log(approved, menu_id);
```

---

## 📊 Part 5: 구현 일정 및 리소스

### 주차별 분해

#### 주차 1: 데이터 수집 (12시간)

| 일자 | 작업 | 예상시간 | 담당 | 비고 |
|------|------|---------|------|------|
| Day 1 | 한국관광공사 API 통합 | 3시간 | Backend | API 키 신청 필요 |
| Day 2 | 위키피디아 크롤링 | 2시간 | Backend | 저작권 확인 |
| Day 2 | 공공데이터포탈 연결 | 2시간 | Backend | 메타데이터 추출 |
| Day 3 | 이미지 다운로드 & S3 업로드 | 3시간 | DevOps | 약 100-130개 |
| Day 4 | 테스트 및 정리 | 2시간 | QA | 이미지 품질 검증 |

**소계**: 12시간

---

#### 주차 2: AI 이미지 생성 (6시간)

| 일자 | 작업 | 예상시간 | 담당 | 비고 |
|------|------|---------|------|------|
| Day 5 | DALL-E 3 API 통합 | 1시간 | Backend | OpenAI 설정 |
| Day 5 | 프롬프트 최적화 | 1시간 | Backend | 고품질 프롬프트 작성 |
| Day 6 | 부족한 이미지 생성 (30-40개) | 2시간 | Backend | 자동화 스크립트 |
| Day 6 | 지역별 변종 이미지 (30개) | 1시시간 | Backend | "Jeonju", "Namwon" 등 |
| Day 7 | 품질 검증 및 필터링 | 1시간 | QA | 부적절한 이미지 제거 |

**소계**: 6시간
**예상 비용**: DALL-E 3 (60개 × $0.08) = **$4.80** ✅ 매우 저렴

---

#### 주차 3: 콘텐츠 강화 (14시간)

| 일자 | 작업 | 예상시간 | 담당 | 비고 |
|------|------|---------|------|------|
| Day 8 | 설명 자동 추출 (API) | 2시간 | Backend | 한국관광공사, 위키 |
| Day 8 | 콘텐츠 번역 및 정리 | 3시간 | Content | 한영 병기 |
| Day 9 | 지역별 특징 조사 (100개 메뉴) | 2시간 | Data | 온라인 조사 |
| Day 9 | 영양정보 정리 (공공데이터) | 2시간 | Data | 식약청 데이터 |
| Day 10 | 맛 프로필 작성 (전문가 검수) | 3시간 | Expert | 음식 문화 전문가 |
| Day 10 | 방문자 팁 + 문화정보 | 2시간 | Expert | 한국 거주 외국인 또는 가이드 |

**소계**: 14시간

---

#### 주차 4: API + 프론트엔드 + 배포 (14시간)

| 일자 | 작업 | 예상시간 | 담당 | 비고 |
|------|------|---------|------|------|
| Day 11 | DB 마이그레이션 실행 | 2시간 | Backend | JSONB 필드 추가 |
| Day 11 | 데이터 마이그레이션 (100개 메뉴) | 2시간 | Backend | 자동화 스크립트 |
| Day 12 | API 응답 확장 | 2시간 | Backend | 새 필드 포함 |
| Day 12 | 이미지 CDN 설정 | 1시간 | DevOps | CloudFront 또는 S3 |
| Day 13 | UI 컴포넌트 (이미지) | 4시간 | Frontend | 이미지 캐러셀, lazy loading |
| Day 13 | UI 컴포넌트 (콘텐츠) | 3시간 | Frontend | 탭, 아코디언 |

**소계**: 14시간

---

#### 주차 5: 테스트 및 배포 (10시간)

| 일자 | 작업 | 예상시간 | 담당 | 비고 |
|------|------|---------|------|------|
| Day 14 | 데이터 정확성 검증 (샘플 10개) | 2시간 | QA | 수동 검증 |
| Day 15 | 이미지 로딩 테스트 | 1시간 | QA | CDN, 캐시 확인 |
| Day 15 | UI/UX 테스트 (모바일) | 2시간 | QA | iOS, Android |
| Day 15 | API 성능 테스트 | 1시간 | Backend | p95 응답시간 |
| Day 16 | 배포 준비 (FastComet) | 2시간 | DevOps | 마이그레이션 스크립트 |
| Day 16 | 배포 및 모니터링 | 2시간 | DevOps | 실시간 모니터링 |

**소계**: 10시간

---

### 📋 전체 리소스 계획

| 역할 | 인원 | 시간 | 예상 비용 |
|------|------|------|----------|
| Backend | 1 | 32시간 | - |
| Frontend | 1 | 7시간 | - |
| DevOps | 1 | 5시간 | - |
| QA | 1 | 6시간 | - |
| Content/Expert | 2 | 10시간 | - |
| **합계** | **6** | **60시간** | **$4.80** (DALL-E) |

**예상 기간**: 4-5주 (1주 = 40시간 기준)

---

## 🎯 Part 6: 콘텐츠 예시 (비빔밥)

### 최종 API 응답 구조

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name_ko": "비빔밥",
  "name_en": "Bibimbap",

  "images": {
    "primary": {
      "url": "https://s3.korea-tourism.go.kr/bibimbap-primary.jpg",
      "source": "Korea Tourism Organization",
      "license": "CC-BY-4.0",
      "alt_text": "Traditional Jeonju bibimbap in heated stone bowl"
    },
    "additional": [
      {
        "url": "https://s3.korean-culture.go.kr/bibimbap-prep.jpg",
        "source": "Korean Culture Information Service",
        "type": "preparation",
        "alt_text": "Preparing vegetables for bibimbap"
      },
      {
        "url": "https://ai-images.menu-knowledge.com/bibimbap-regional-jeonju.jpg",
        "source": "AI Generated (DALL-E 3)",
        "type": "regional_variant",
        "region": "Jeonju",
        "alt_text": "Jeonju bibimbap with premium beef and aged gochujang"
      },
      {
        "url": "https://ai-images.menu-knowledge.com/bibimbap-regional-namwon.jpg",
        "source": "AI Generated (DALL-E 3)",
        "type": "regional_variant",
        "region": "Namwon",
        "alt_text": "Namwon bibimbap with fresh local vegetables"
      }
    ]
  },

  "description": {
    "short": "Mixed rice bowl with vegetables and gochujang",
    "long": "A traditional Korean comfort food consisting of steamed rice topped with assorted sautéed vegetables, a fried egg, and minced meat, all beautifully arranged in a heated stone or regular bowl. The dish is mixed together with gochujang (red chili pepper paste), sesame oil, and soy sauce, creating a harmonious blend of flavors.",
    "origin": "Originated in the Joseon Dynasty royal court as a creative way to use leftover vegetables and grains. It became a popular home-style meal due to its convenience and delicious combination of flavors.",
    "cultural_significance": "Korea's representative national dish, symbolizing harmony and balance (조화). The various colors represent the yin-yang principle in Korean cuisine."
  },

  "regional_variants": [
    {
      "region": "Jeonju, Jeollabuk-do",
      "name": "Jeonju Bibimbap",
      "characteristics": "Premium quality with aged gochujang (fermented for years), high-grade beef, traditional stone bowl",
      "speciality": "Uses the finest local ingredients and traditional fermentation methods",
      "image": { "url": "...", "source": "AI Generated" }
    },
    {
      "region": "Namwon, Jeollabuk-do",
      "name": "Namwon Bibimbap",
      "characteristics": "Lighter version emphasizing fresh local vegetables",
      "specialty": "Freshness of vegetables is prioritized",
      "image": { "url": "...", "source": "AI Generated" }
    }
  ],

  "preparation": {
    "time_minutes": 25,
    "difficulty": "Easy",
    "ingredients": [
      { "name": "Steamed rice", "amount": "1 bowl", "korean": "밥" },
      { "name": "Gochujang", "amount": "1-2 tbsp", "korean": "고추장" },
      { "name": "Ground beef", "amount": "50g", "korean": "소고기" },
      { "name": "Fried egg", "amount": "1", "korean": "계란" }
    ],
    "steps": [
      { "number": 1, "description": "Blanch spinach separately, squeeze out water" },
      { "number": 2, "description": "Stir-fry mushrooms with salt and sesame oil" },
      { "number": 3, "description": "Brown ground beef with soy sauce" },
      { "number": 4, "description": "Fry egg sunny-side up" },
      { "number": 5, "description": "Arrange all components on hot rice in stone bowl" }
    ],
    "tips": "Mix quickly while hot to create crispy rice bits (socarim). The sizzling sound enhances the experience."
  },

  "nutrition": {
    "calories": 650,
    "protein_g": 25,
    "carbs_g": 85,
    "fat_g": 18,
    "fiber_g": 8,
    "health_benefits": [
      "High in vegetables providing vitamins and minerals",
      "Good protein source",
      "Capsaicin has potential anti-inflammatory properties"
    ]
  },

  "flavor_profile": {
    "spice_level": 2,
    "spice_description": "Mildly spicy, adjustable by amount of gochujang",
    "taste_notes": ["savory", "slightly sweet", "umami"],
    "texture": "Mix of soft rice, tender vegetables, crispy sesame"
  },

  "cultural_info": {
    "philosophy": "Represents harmony (조화) and balance in Korean cuisine",
    "occasions": "Everyday meal, celebrations, healing food",
    "etiquette": "Mix all ingredients with gochujang before eating",
    "saying": "'피곤하면 비빔밥' (When tired, eat bibimbap) - Korean proverb"
  },

  "visitor_tips": {
    "ordering": {
      "korean": "비빔밥",
      "pronunciation": "bee-bim-bap",
      "vegetarian": "야채비빔밥"
    },
    "eating": {
      "method": "Mix quickly while hot",
      "why": "Creates crispy rice and enhances flavors",
      "warning": "Very hot - be careful"
    },
    "pairing": "Kimchi on the side, rice wine (makgeolli) or beer"
  },

  "similar_dishes": [
    { "name": "Dolsot Bibimbap", "description": "Stone pot version with crispy rice crust" },
    { "name": "Hoe Bibimbap", "description": "Premium version with raw fish" }
  ],

  "metadata": {
    "content_completeness": 98,
    "verified_by": "Food Culture Expert",
    "verified_date": "2026-02-18",
    "image_sources": {
      "official": [
        { "source": "Korea Tourism Organization", "count": 1 },
        { "source": "Korean Culture Information Service", "count": 1 }
      ],
      "ai_generated": [
        { "provider": "DALL-E 3", "count": 2 }
      ]
    },
    "sources": [
      { "name": "Korea Tourism Organization", "url": "..." },
      { "name": "Korean Wikipedia", "url": "..." },
      { "name": "Korean Culture Information Service", "url": "..." }
    ]
  }
}
```

---

## ✅ Part 7: 최종 검증 체크리스트

### Pre-Implementation

- [ ] 한국관광공사 API 키 신청 완료
- [ ] 위키피디아 데이터 수집 권한 확인
- [ ] DALL-E 3 API 계정 생성
- [ ] S3 버킷 생성 (menu-knowledge-images)
- [ ] DB 백업 확인

### Data Collection Phase

- [ ] 한국관광공사: 70개 이미지 수집 완료
- [ ] 문화정보원: 30개 이미지 수집 완료
- [ ] 위키피디아: 50개 이미지 수집 완료
- [ ] 저작권 확인 완료 (모든 출처)
- [ ] S3 업로드 완료

### AI Generation Phase

- [ ] DALL-E 3: 30-40개 이미지 생성
- [ ] 지역별 변종: 30개 이미지 생성
- [ ] 품질 검증 (모든 AI 이미지)
- [ ] 부적절한 이미지 제거
- [ ] S3 업로드 완료

### Content Enrichment Phase

- [ ] API 데이터 자동 수집 완료
- [ ] 콘텐츠 번역 완료
- [ ] 지역별 특징 정리 완료
- [ ] 영양정보 정리 완료
- [ ] 맛 프로필 작성 완료 (전문가 검수)
- [ ] 방문자 팁 작성 완료

### Implementation Phase

- [ ] DB 마이그레이션 스크립트 테스트 완료
- [ ] 데이터 마이그레이션 완료 (100개 메뉴)
- [ ] API 응답 확장 완료
- [ ] UI 컴포넌트 개발 완료
- [ ] CSS 스타일링 완료

### Testing Phase

- [ ] 데이터 정확성 검증 (샘플 10개)
- [ ] 이미지 로딩 테스트 완료
- [ ] 이미지 품질 확인 (모바일/데스크톱)
- [ ] API 성능 테스트 (p95 < 500ms)
- [ ] UI/UX 테스트 (모바일)

### Deployment Phase

- [ ] FastComet 배포 준비
- [ ] 마이그레이션 스크립트 준비
- [ ] 롤백 계획 수립
- [ ] 배포 실행
- [ ] 실시간 모니터링 (1시간)
- [ ] 최종 보고서 작성

---

## 🎯 최종 목표 및 성공 지표

### Phase 1 완료 시 달성할 것

| 항목 | 목표 | 달성 기준 |
|------|------|----------|
| **메뉴 수** | 100개 | 완전한 정보 (이미지 + 콘텐츠) |
| **이미지 개수** | 3-5개/메뉴 | 300-500개 총 이미지 |
| **이미지 출처 다양화** | 공식 + AI | 60% 공식, 40% AI |
| **콘텐츠 품질** | 전문가 수준 | 문화, 역사, 영양정보 포함 |
| **저작권 투명성** | 100% | 모든 이미지 출처 명시 |
| **외국인 신뢰도** | 극대화 | 시각적 + 정보적 신뢰 |
| **모바일 최적화** | 완벽 | 반응형 이미지 표시 |
| **API 성능** | p95 < 500ms | 이미지 포함 응답 |

### 예상 결과

✅ **외국인이 메뉴를 "보고 이해"할 수 있음**
✅ **한국 공식 출처 + 우리 저작권 이미지 혼합**
✅ **전문적이고 신뢰할 수 있는 정보**
✅ **세계 어디서든 접근 가능 (CDN 배포)**

---

## 📌 최종 승인 및 다음 단계

### ✅ 계획 검토 완료

이 종합 기획서는 다음을 포함합니다:
1. ✅ 한국 중심 이미지 수집 루트 (4개 Tier)
2. ✅ AI 생성 이미지 전략 (저작권 확보)
3. ✅ 전문적 콘텐츠 강화 (문화, 영양, 조리법)
4. ✅ 상세한 구현 일정 (4-5주)
5. ✅ 리소스 계획 (6명, $4.80 예산)
6. ✅ 최종 검증 체크리스트

### 🚀 다음 단계

**승인 후 즉시 시작**:
1. 한국관광공사 API 키 신청
2. DALL-E 3 API 계정 생성
3. 주차 1: 데이터 수집 시작

**예상 완료**: 4-5주 후 (2026-03-18 경)

---

**작성**: Claude Code
**검토자**: User (승인 대기)
**상태**: 🟡 **최종 검토 완료 - 시작 승인 대기**
**우선순위**: **P0 (Critical)**

이 기획을 바탕으로 **Sprint 2를 시작할 준비가 되었습니다!** 🚀
