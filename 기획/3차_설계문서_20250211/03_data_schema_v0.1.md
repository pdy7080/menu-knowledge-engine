# 03. Data Schema v0.1 — PostgreSQL 물리 스키마

> **이 문서가 이 프로젝트의 기준점(Single Source of Truth)이다.**
> UX, API, AI 프롬프트, 특허 문서는 모두 이 스키마를 참조한다.

---

## 🆕 Sprint 0 공공데이터 통합 업데이트 (2026-02-19)

**변경 사항:**
- `canonical_menus` 테이블에 5개 필드 추가: `standard_code`, `category_1`, `category_2`, `serving_size`, `nutrition_info`, `last_nutrition_updated`
- 서울 중심 국가 커버리지 전략: 167,659개 메뉴 자동 구축 → 90%+ 전국 메뉴 커버리지
- 3단계 공공데이터 파이프라인: 메뉴젠(표준화) → 서울 식당(데이터) → 영양정보(캐싱)
- AI 호출 70% 절감: 월 $210,000 절감
- 초기 구축 비용: $0 (공공데이터 무료)

---

## 0. 설계 결정

### DB 선택: PostgreSQL

| 고려 사항 | 결정 | 이유 |
|---|---|---|
| Graph DB vs RDB | **RDB** | 노드 6종, 관계 8종 수준. Graph DB는 오버엔지니어링 |
| 벡터 검색 | **pgvector 확장** | RAG 검색 + 유사 메뉴 탐색에 필요 |
| JSON 필드 | **JSONB 활용** | 다국어 번역, 태그 등 유연한 데이터 저장 |
| 전문 검색 | **pg_trgm 확장** | 한국어 메뉴명 유사 검색 (수식어 분해 보조) |

### 네이밍 규칙
- 테이블: `snake_case`, 복수형 (e.g., `canonical_menus`)
- 컬럼: `snake_case`
- ID: `UUID` (외부 노출 시 추측 불가)
- 타임스탬프: `timestamptz` (UTC)

---

## 1. 테이블 정의

### 1-1. `concepts` — 개념 (최상위 분류)

```sql
CREATE TABLE concepts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_ko         VARCHAR(100) NOT NULL,
    name_en         VARCHAR(200),
    parent_id       UUID REFERENCES concepts(id),  -- 상위 개념 (self-reference)
    definition_ko   TEXT,
    definition_en   TEXT,
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_concepts_name_ko ON concepts(name_ko);
CREATE INDEX idx_concepts_parent ON concepts(parent_id);
```

**초기 데이터 예시:**
```
(국물요리, Soup/Stew, null)
  ├── (탕, Tang - Rich Soup, 국물요리)
  ├── (국, Guk - Light Soup, 국물요리)
  ├── (찌개, Jjigae - Stew, 국물요리)
  └── (해장국, Hangover Soup, 국물요리)
```

---

### 1-2. `canonical_menus` — 표준 메뉴 (핵심 테이블)

```sql
CREATE TABLE canonical_menus (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_id          UUID REFERENCES concepts(id),

    -- 이름 (다국어)
    name_ko             VARCHAR(100) NOT NULL,
    name_en             VARCHAR(200) NOT NULL,
    name_ja             VARCHAR(200),
    name_zh_cn          VARCHAR(200),
    name_zh_tw          VARCHAR(200),
    romanization        VARCHAR(200),

    -- 설명 (다국어, 짧은/긴)
    explanation_short    JSONB NOT NULL DEFAULT '{}',
    -- 구조: {"en": "...", "ja": "...", "zh_cn": "...", "zh_tw": "..."}
    explanation_long     JSONB DEFAULT '{}',
    cultural_context     JSONB DEFAULT '{}',

    -- 공공데이터 표준화 (🆕 Sprint 0)
    standard_code        VARCHAR(10),                    -- 메뉴젠 API 음식코드 (e.g., "K001234")
    category_1           VARCHAR(50),                    -- 정부 분류 대분류 (e.g., "육류", "밥", "찌개")
    category_2           VARCHAR(50),                    -- 정부 분류 중분류 (e.g., "구이", "비빔밥류")
    serving_size         VARCHAR(20),                    -- 1인분 기준 (e.g., "200g", "300ml")
    nutrition_info       JSONB DEFAULT '{}',            -- 영양정보 (캐싱, 157개 항목)
    -- 구조: {"energy": 250, "protein": 25.5, "fat": 15.2, "carbs": 0.5, ...}
    last_nutrition_updated TIMESTAMPTZ,                 -- 영양정보 갱신일 (Redis TTL용)

    -- 식재료 & 식이 정보
    main_ingredients     JSONB DEFAULT '[]',
    -- 구조: [{"ko": "돼지등뼈", "en": "pork spine"}, ...]
    allergens            VARCHAR(50)[] DEFAULT '{}',
    -- 값: pork, beef, chicken, seafood, shellfish, eggs, milk,
    --      wheat, soy, peanuts, tree_nuts, sesame, etc.
    dietary_tags         VARCHAR(50)[] DEFAULT '{}',
    -- 값: contains_pork, contains_beef, spicy, mild, vegan,
    --      vegetarian, gluten_free, halal, etc.
    spice_level          SMALLINT DEFAULT 0 CHECK (spice_level BETWEEN 0 AND 5),
    serving_style        VARCHAR(100),  -- "국물+밥 세트", "단품", "코스"

    -- 가격 & 이미지
    typical_price_min    INTEGER,  -- 원 단위
    typical_price_max    INTEGER,
    image_url            TEXT,
    image_ai_prompt      TEXT,  -- KIMCHI 모델용 이미지 생성 프롬프트

    -- 난이도 & 신뢰도
    difficulty_score     SMALLINT DEFAULT 3 CHECK (difficulty_score BETWEEN 1 AND 5),
    difficulty_factors   JSONB DEFAULT '{}',
    -- 구조: {"name_trap": true, "compound_count": 2, "unknown_ingredients": ["들깨"]}
    ai_confidence        REAL DEFAULT 0 CHECK (ai_confidence BETWEEN 0 AND 1),
    verified_by          VARCHAR(20) DEFAULT 'ai',
    -- 값: 'ai', 'human', 'both', 'public_db'

    -- 벡터 (유사 메뉴 검색용)
    embedding            vector(1536),  -- pgvector, OpenAI embedding 차원

    -- 메타
    status               VARCHAR(20) DEFAULT 'active',
    -- 값: 'draft', 'active', 'deprecated', 'merged'
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_cm_name_ko ON canonical_menus(name_ko);
CREATE INDEX idx_cm_name_en ON canonical_menus(name_en);
CREATE INDEX idx_cm_concept ON canonical_menus(concept_id);
CREATE INDEX idx_cm_spice ON canonical_menus(spice_level);
CREATE INDEX idx_cm_difficulty ON canonical_menus(difficulty_score);
CREATE INDEX idx_cm_status ON canonical_menus(status);
CREATE INDEX idx_cm_allergens ON canonical_menus USING GIN(allergens);
CREATE INDEX idx_cm_dietary ON canonical_menus USING GIN(dietary_tags);

-- 공공데이터 표준화 인덱스 (🆕 Sprint 0)
CREATE INDEX idx_cm_standard_code ON canonical_menus(standard_code);  -- 메뉴젠 API 조회
CREATE INDEX idx_cm_category ON canonical_menus(category_1, category_2);  -- 분류별 검색

-- 벡터 유사도 인덱스 (pgvector)
CREATE INDEX idx_cm_embedding ON canonical_menus
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 한국어 유사 검색 (pg_trgm)
CREATE INDEX idx_cm_name_ko_trgm ON canonical_menus
    USING gin (name_ko gin_trgm_ops);
```

**JSONB 필드 구조 상세:**

```json
// explanation_short
{
  "en": "Slow-simmered pork bone soup, a popular Korean hangover cure",
  "ja": "豚の背骨を長時間煮込んだスープ、二日酔いの朝に人気",
  "zh_cn": "猪脊骨长时间熬煮的汤，是韩国人解酒的热门选择",
  "zh_tw": "豬脊骨長時間熬煮的湯，是韓國人解酒的熱門選擇"
}

// main_ingredients
[
  {"ko": "돼지등뼈", "en": "pork spine bones"},
  {"ko": "배추", "en": "napa cabbage"},
  {"ko": "들깨가루", "en": "perilla seed powder"},
  {"ko": "대파", "en": "green onions"}
]

// difficulty_factors
{
  "name_trap": false,
  "compound_count": 0,
  "unknown_ingredients": ["들깨가루"],
  "unknown_cooking_method": false,
  "global_awareness": "low"
}

// nutrition_info (🆕 Sprint 0 - 식품영양성분DB API)
{
  "energy": 250,              // kcal
  "protein": 25.5,            // g
  "fat": 15.2,                // g
  "carbs": 0.5,               // g
  "fiber": 0.2,               // g
  "calcium": 150,             // mg
  "iron": 2.5,                // mg
  "sodium": 1200,             // mg
  "potassium": 450,           // mg
  "magnesium": 85,            // mg
  "phosphorus": 320,          // mg
  "zinc": 4.5,                // mg
  "vitamin_a": 150,           // mcg
  "vitamin_c": 8,             // mg
  "vitamin_d": 0.5,           // mcg
  "vitamin_e": 2.1,           // mg
  "vitamin_b1": 0.15,         // mg
  "vitamin_b2": 0.25,         // mg
  "niacin": 4.2,              // mg
  "vitamin_b6": 0.45,         // mg
  "folate": 25,               // mcg
  "vitamin_b12": 1.2,         // mcg
  "cholesterol": 85,          // mg
  "saturated_fat": 5.8        // g
}
```

---

### 1-3. `menu_variants` — 변형 메뉴 (실제 식당 메뉴명)

```sql
CREATE TABLE menu_variants (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_id        UUID NOT NULL REFERENCES canonical_menus(id),
    shop_id             UUID REFERENCES shops(id),

    -- 실제 표시 이름
    display_name_ko     VARCHAR(200) NOT NULL,
    display_name_original TEXT,  -- OCR 원본 텍스트 (오타 포함)

    -- 수식어 연결
    modifier_ids        UUID[] DEFAULT '{}',
    decomposition       JSONB DEFAULT '{}',
    -- 구조: {"modifiers": ["왕", "얼큰"], "base": "뼈해장국", "method": "auto"}

    -- 식당별 정보
    price               INTEGER,  -- 원 단위
    description_ko      TEXT,  -- 식당 고유 설명 ("24시간 푹 고은 사골")
    is_popular          BOOLEAN DEFAULT FALSE,
    is_seasonal         BOOLEAN DEFAULT FALSE,

    -- 출처 & 신뢰도
    source              VARCHAR(30) NOT NULL,
    -- 값: 'b2b_upload', 'b2c_scan', 'manual', 'crawl'
    ai_match_confidence REAL DEFAULT 0,
    human_verified      BOOLEAN DEFAULT FALSE,

    -- 메타
    first_seen_at       TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at        TIMESTAMPTZ DEFAULT NOW(),
    scan_count          INTEGER DEFAULT 1,  -- B2C에서 조회된 횟수
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_mv_canonical ON menu_variants(canonical_id);
CREATE INDEX idx_mv_shop ON menu_variants(shop_id);
CREATE INDEX idx_mv_display_name ON menu_variants(display_name_ko);
CREATE INDEX idx_mv_source ON menu_variants(source);
CREATE INDEX idx_mv_scan_count ON menu_variants(scan_count DESC);

-- 한국어 유사 검색
CREATE INDEX idx_mv_name_trgm ON menu_variants
    USING gin (display_name_ko gin_trgm_ops);
```

---

### 1-4. `modifiers` — 수식어 사전

```sql
CREATE TABLE modifiers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text_ko             VARCHAR(30) NOT NULL UNIQUE,
    type                VARCHAR(30) NOT NULL,
    -- 값: taste, size, emotion, ingredient, cooking, grade, origin, composition
    semantic_key        VARCHAR(50) NOT NULL,
    -- 값: spicy_variant, large_serving, homestyle, korean_beef, etc.

    -- 번역
    translation_en      VARCHAR(100),
    translation_ja      VARCHAR(100),
    translation_zh      VARCHAR(100),

    -- 효과
    affects_spice       SMALLINT,  -- +1, +2, -1, null
    affects_size        VARCHAR(20),  -- 'large', 'small', 'double', null
    affects_price       VARCHAR(20),  -- 'premium', 'budget', null

    -- 분해 알고리즘용
    priority            INTEGER DEFAULT 10,  -- 높을수록 먼저 매칭
    min_length          INTEGER DEFAULT 1,   -- 최소 글자 수
    is_prefix           BOOLEAN DEFAULT TRUE, -- 앞에 붙는가 뒤에 붙는가

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_mod_text ON modifiers(text_ko);
CREATE INDEX idx_mod_type ON modifiers(type);
CREATE INDEX idx_mod_priority ON modifiers(priority DESC);
```

---

### 1-5. `menu_relations` — 메뉴 간 관계

```sql
CREATE TABLE menu_relations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    relation_type       VARCHAR(30) NOT NULL,
    -- 값: similar_to, often_confused_with, served_with,
    --      evolved_from, regional_variant, cooking_variant

    from_type           VARCHAR(30) NOT NULL,  -- 'canonical' or 'concept'
    from_id             UUID NOT NULL,
    to_type             VARCHAR(30) NOT NULL,
    to_id               UUID NOT NULL,

    is_bidirectional    BOOLEAN DEFAULT TRUE,
    description_ko      TEXT,
    description_en      TEXT,
    strength            REAL DEFAULT 0.5,  -- 관계 강도 (0~1)

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_rel_from ON menu_relations(from_type, from_id);
CREATE INDEX idx_rel_to ON menu_relations(to_type, to_id);
CREATE INDEX idx_rel_type ON menu_relations(relation_type);

-- 복합 유니크 (중복 관계 방지)
CREATE UNIQUE INDEX idx_rel_unique
    ON menu_relations(relation_type, from_type, from_id, to_type, to_id);
```

---

### 1-6. `cultural_concepts` — 식당 문화 개념

```sql
CREATE TABLE cultural_concepts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_ko             VARCHAR(100) NOT NULL,
    name_en             VARCHAR(200),
    type                VARCHAR(30) NOT NULL,
    -- 값: ordering, serving, payment, etiquette

    explanation          JSONB NOT NULL DEFAULT '{}',
    -- 구조: {"en": "...", "ja": "...", "zh_cn": "..."}

    related_menu_ids     UUID[] DEFAULT '{}',  -- 관련 canonical_menus
    icon                 VARCHAR(10),  -- 이모지 아이콘
    sort_order           INTEGER DEFAULT 0,

    created_at           TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cc_type ON cultural_concepts(type);
```

---

### 1-7. `evidences` — 출처/근거

```sql
CREATE TABLE evidences (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_type         VARCHAR(30) NOT NULL,
    -- 값: canonical, variant, modifier, concept
    target_id           UUID NOT NULL,

    source_type         VARCHAR(30) NOT NULL,
    -- 값: public_db, ai_discovery, human_review, web_search, user_report
    source_name         VARCHAR(200),
    source_url          TEXT,
    content_summary     TEXT,

    confidence_contribution REAL DEFAULT 0,
    ai_model            VARCHAR(50),  -- "gpt-4o", "hyperclova-x"
    ai_prompt_hash      VARCHAR(64),  -- 프롬프트 추적용

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ev_target ON evidences(target_type, target_id);
CREATE INDEX idx_ev_source ON evidences(source_type);
```

---

### 1-8. `shops` — 식당 (연동 테이블)

```sql
CREATE TABLE shops (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_ko             VARCHAR(200) NOT NULL,
    name_en             VARCHAR(200),

    -- 위치
    address_ko          TEXT,
    latitude            DECIMAL(10, 7),
    longitude           DECIMAL(10, 7),
    area_tag            VARCHAR(50),  -- "명동", "홍대", "성수"

    -- 외부 연동
    seongsuya_id        VARCHAR(50),  -- 성수야 가게 ID
    naver_place_id      VARCHAR(50),
    google_place_id     VARCHAR(50),

    -- 메뉴 현황
    menu_count          INTEGER DEFAULT 0,
    has_multilingual     BOOLEAN DEFAULT FALSE,
    difficulty_avg       REAL,  -- 메뉴 평균 난이도

    -- QR
    qr_page_url         TEXT,
    qr_page_generated_at TIMESTAMPTZ,

    -- 출처
    source              VARCHAR(30),  -- 'seongsuya', 'b2c_discover', 'manual'
    status              VARCHAR(20) DEFAULT 'active',

    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_shop_area ON shops(area_tag);
CREATE INDEX idx_shop_location ON shops USING gist (
    ST_MakePoint(longitude, latitude)  -- PostGIS
);
CREATE INDEX idx_shop_seongsuya ON shops(seongsuya_id);
```

---

### 1-9. `scan_logs` — B2C 스캔 로그 (행동 데이터)

```sql
CREATE TABLE scan_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          VARCHAR(100),  -- 익명 세션
    language            VARCHAR(10) NOT NULL,  -- "en", "ja", "zh_cn"

    -- 스캔 정보
    image_url           TEXT,
    ocr_raw_text        TEXT,
    matched_variant_ids UUID[] DEFAULT '{}',
    unmatched_texts     TEXT[] DEFAULT '{}',

    -- 위치 (대략적)
    area_tag            VARCHAR(50),
    shop_id             UUID REFERENCES shops(id),

    -- AI 호출 여부
    ai_called           BOOLEAN DEFAULT FALSE,
    ai_new_entries      INTEGER DEFAULT 0,  -- AI로 신규 생성된 항목 수

    -- 시간
    scanned_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scan_language ON scan_logs(language);
CREATE INDEX idx_scan_area ON scan_logs(area_tag);
CREATE INDEX idx_scan_time ON scan_logs(scanned_at);
CREATE INDEX idx_scan_ai ON scan_logs(ai_called);
```

---

## 2. ER 다이어그램 (텍스트 표현)

```
                        ┌─────────────┐
                        │  concepts   │
                        │  (개념)      │
                        └──────┬──────┘
                               │ belongs_to_concept
                               │
┌──────────────┐       ┌──────▼──────┐       ┌────────────────┐
│  modifiers   │◄──────│ canonical   │──────►│ menu_relations │
│  (수식어)     │ used  │  _menus     │       │ (메뉴 간 관계)  │
└──────────────┘  by   │ (표준메뉴)   │       └────────────────┘
       │               └──────┬──────┘
       │                      │ is_variant_of
       │               ┌──────▼──────┐       ┌────────────────┐
       └──────────────►│ menu        │──────►│  shops         │
         decomposed    │ _variants   │       │  (식당)         │
         into          │ (변형메뉴)   │       └────────┬───────┘
                       └─────────────┘                │
                                                      │
┌──────────────┐       ┌─────────────┐       ┌───────▼───────┐
│  cultural    │       │ evidences   │       │  scan_logs    │
│  _concepts   │       │ (출처/근거)  │       │  (스캔 로그)   │
│ (문화 개념)   │       └─────────────┘       └───────────────┘
└──────────────┘
```

---

## 3. 핵심 쿼리 패턴

### Q1: 메뉴명으로 Canonical 찾기 (수식어 분해 전)

```sql
-- 정확히 일치하는 Canonical
SELECT * FROM canonical_menus WHERE name_ko = '뼈해장국';

-- 유사 검색 (pg_trgm)
SELECT *, similarity(name_ko, '뼈해장국') AS sim
FROM canonical_menus
WHERE name_ko % '뼈해장국'
ORDER BY sim DESC LIMIT 5;
```

### Q2: 특정 Canonical의 모든 변형 조회

```sql
SELECT mv.display_name_ko, mv.price, s.name_ko AS shop_name
FROM menu_variants mv
LEFT JOIN shops s ON mv.shop_id = s.id
WHERE mv.canonical_id = :canonical_id
ORDER BY mv.scan_count DESC;
```

### Q3: 유사 메뉴 조회 (관계 기반)

```sql
SELECT cm2.name_ko, cm2.name_en, mr.relation_type, mr.description_en
FROM menu_relations mr
JOIN canonical_menus cm2
  ON (mr.to_id = cm2.id AND mr.to_type = 'canonical')
WHERE mr.from_id = :canonical_id
  AND mr.from_type = 'canonical'
  AND mr.relation_type IN ('similar_to', 'often_confused_with');
```

### Q4: 유사 메뉴 조회 (벡터 기반)

```sql
SELECT name_ko, name_en,
       1 - (embedding <=> :target_embedding) AS similarity
FROM canonical_menus
WHERE id != :canonical_id
  AND status = 'active'
ORDER BY embedding <=> :target_embedding
LIMIT 5;
```

### Q5: 지역별 외국인 스캔 통계

```sql
SELECT area_tag, language, COUNT(*) AS scan_count,
       COUNT(DISTINCT session_id) AS unique_users
FROM scan_logs
WHERE scanned_at >= NOW() - INTERVAL '30 days'
GROUP BY area_tag, language
ORDER BY scan_count DESC;
```

### Q6: AI 호출 없이 처리된 비율 (비용 효율 추적)

```sql
SELECT
  COUNT(*) AS total_scans,
  COUNT(*) FILTER (WHERE ai_called = FALSE) AS db_only,
  ROUND(
    COUNT(*) FILTER (WHERE ai_called = FALSE)::NUMERIC / COUNT(*) * 100, 1
  ) AS db_hit_rate_pct
FROM scan_logs
WHERE scanned_at >= NOW() - INTERVAL '7 days';
```

---

## 4. 확장 확장 전략 (v0.2+)

v0.1에는 넣지 않지만, 스키마가 수용할 수 있도록 설계된 미래 확장:

| 확장 | 방법 | 시점 | 상태 |
|---|---|---|---|
| **영양 정보** | canonical_menus.nutrition_info (JSONB) | **v0.1 (Sprint 0)** | ✅ **구현 중** |
| 추가 언어 (태국어, 베트남어 등) | JSONB 필드에 키 추가 | v0.2 | 🔮 계획 |
| 이미지 자동 매칭 | canonical_menus.embedding + 이미지 벡터 | v0.2 | 🔮 계획 |
| 사용자 리뷰/피드백 | 신규 테이블 `user_feedback` | v0.3 | 🔮 계획 |
| 해외 한식당 | shops.country 필드 추가 | v0.5 | 🔮 계획 |
| 다국가 음식 (일식, 중식) | concepts 트리 확장 | v1.0+ | 🔮 계획 |

---

## 5. 초기 데이터 마이그레이션 계획 (🆕 Sprint 0 공공데이터 통합)

### Seoul-Centric 국가 커버리지 전략

**핵심 인사이트**: 서울은 전국 모든 메뉴 문화가 모이는 곳
- 서울 식당: 167,659개 (전국 2.1M 중 8%)
- 전국 메뉴 커버리지: **90%+** (지역 특화 음식도 서울로 진출)
- 초기 구축 비용: **$0** (공공데이터 무료)
- AI 호출 절감: **70%** (월 $210,000)

### 공공데이터 API → DB 3단계 파이프라인

#### 1️⃣ 필수: 메뉴젠 식단정보 API (농촌진흥청)
```yaml
API ID: 15101046
데이터: 음식코드 ~1,500개 (정부 표준)
매핑:
  - canonical_menus.standard_code ← 음식코드
  - canonical_menus.category_1 ← 대분류
  - canonical_menus.category_2 ← 중분류
  - canonical_menus.serving_size ← 1인분 기준
예상 시간: 30시간
```

#### 2️⃣ 필수: 서울 식당운영정보 (서울관광재단)
```yaml
API ID: 15098046
형식: CSV 다운로드
데이터: 167,659개 서울 식당의 대표메뉴
매핑:
  - canonical_menus.name_ko ← 대표메뉴명
  - menu_variants + shops 테이블 연계
결과: 157,000개 canonical_menus 자동 생성
예상 시간: 40시간
```

#### 3️⃣ 필수: 식품영양성분DB API (식품의약품안전처)
```yaml
API ID: 15127578
데이터: 157개 영양항목 (정부 표준, 신뢰도 99%)
매핑:
  - canonical_menus.nutrition_info ← JSONB (캐싱)
  - canonical_menus.last_nutrition_updated
캐싱 전략:
  - Redis TTL: 90일
  - 3개월마다 자동 갱신
예상 시간: 40시간
```

### 초기 구축 순서 (Sprint 0, 3주)

```
Week 1: 메뉴 표준화 + 데이터 확보 (40시간)
  1-1. 메뉴젠 API 파싱 (30시간)
       └─ standard_code, category_1, category_2, serving_size 입력

  1-2. 서울 식당정보 CSV 임포트 (10시간)
       └─ 167,659개 메뉴명 정규화

Week 2: 영양정보 연계 + 테스트 (40시간)
  2-1. 식품영양성분DB API 연동 (30시간)
       └─ 메뉴명 매칭 → nutrition_info 자동 입력

  2-2. 10대 테스트 케이스 검증 (10시간)
       └─ "왕얼큰순두부뼈해장국" 정확 분해 확인

Week 3: 문서화 + 배포 (30시간)
  3-1. CLAUDE.md, DB 스키마, API 문서 업데이트
  3-2. FastComet 배포 + 모니터링 설정
  3-3. Redis 캐싱 구성 (TTL 90일)

결과: 157,000개 메뉴 DB 준비 완료
```

### 이전 데이터 소스 (선택, v0.2+)

| 공공 데이터 소스 | 데이터 | 용도 | 우선순위 |
|---|---|---|---|
| 한식재단 한식 아카이브 (9,083건) | 설명, 문화 맥락 | canonical_menus 추가 강화 | ⭐ 중간 |
| 관광공사 푸드트립 (8,500건) | 다국어 번역 | 번역 자동화 (v0.2) | ⭐ 낮음 |
| AI Hub 한식 이미지 (15만 장) | 대표 이미지 | embedding용 (v0.2) | ⭐ 낮음 |
