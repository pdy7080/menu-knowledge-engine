# 02. Menu Knowledge Graph — 논리 모델

> **이 문서는 "무엇을 담을 것인가"를 정의한다.**  
> **"어떻게 저장할 것인가"는 03_data_schema에서 다룬다.**

---

## 1. 노드(Node) 타입 — 6종

### 1-1. Concept (개념)

음식의 가장 추상적인 분류. "이 음식이 무엇의 일종인가"를 정의.

```
예시:
  해장국 — "술 마신 뒤 해장을 위해 먹는 국물 요리 총칭"
  구이   — "재료를 직접 불에 굽는 조리법 요리 총칭"
  밥류   — "쌀밥을 주식으로 하는 요리 총칭"
```

**필드:**
| 필드 | 설명 | 예시 |
|---|---|---|
| id | 고유 ID | `concept_001` |
| name_ko | 한국어명 | 해장국 |
| name_en | 영어명 | Hangover Soup |
| definition_ko | 한국어 정의 | 술 마신 다음날... |
| definition_en | 영어 정의 | A category of Korean soups... |
| parent_concept_id | 상위 개념 (nullable) | concept_000_국물요리 |

**Concept 분류 체계 (v0.1 기준, 대분류 12종):**
```
국물요리 (탕/국/찌개/전골)
밥류 (비빔밥/덮밥/볶음밥/죽)
면류 (국수/냉면/라면)
구이류 (고기구이/생선구이)
찜/조림류
볶음류
전/부침류
반찬류 (나물/김치/젓갈)
분식류 (떡볶이/만두/순대)
안주류
음료류 (술/음료)
디저트류
```

---

### 1-2. CanonicalMenu (표준 메뉴)

실제 존재하는 대표적 메뉴. **번역과 설명의 기준점.** DB의 핵심 단위.

```
예시:
  뼈해장국  — concept "해장국"에 속하는 구체적 메뉴
  김치찌개  — concept "찌개"에 속하는 구체적 메뉴
  삼겹살구이 — concept "구이"에 속하는 구체적 메뉴
```

**필드:**
| 필드 | 설명 | 예시 |
|---|---|---|
| id | 고유 ID | `canon_042` |
| name_ko | 한국어 표준명 | 뼈해장국 |
| name_en | 영어 표준명 | Pork Bone Hangover Soup |
| name_ja | 일본어 표준명 | ピョヘジャングク |
| name_zh_cn | 중국어(간체) 표준명 | 骨头解酒汤 |
| romanization | 로마자 표기 | Ppyeo-haejangguk |
| concept_id | 소속 개념 | concept_001 |
| explanation_short_en | 짧은 설명 (1문장) | Slow-simmered pork bone soup... |
| explanation_long_en | 긴 설명 (3~5문장) | A hearty Korean soup made by... |
| explanation_short_ja | 일본어 짧은 설명 | 豚の背骨を長時間煮込んだ... |
| explanation_short_zh | 중국어 짧은 설명 | 将猪脊骨长时间熬煮的... |
| cultural_context_en | 문화적 맥락 | Traditionally eaten the morning after... |
| main_ingredients | 주재료 리스트 | ["돼지등뼈", "배추", "들깨"] |
| allergens | 알레르기 유발 물질 | ["pork"] |
| dietary_tags | 식이 태그 | ["contains_pork", "spicy_mild", "gluten_free"] |
| spice_level | 맵기 (0~5) | 2 |
| serving_style | 제공 형태 | "국물+밥 세트" |
| typical_price_range | 일반 가격대 | "8000~12000" |
| image_reference | 대표 이미지 경로 | "images/canon_042.jpg" |
| difficulty_score | 외국인 이해 난이도 (1~5) | 3 |
| ai_confidence | AI 확정 확신도 (0~1) | 0.95 |
| verified_by | 검증 주체 | "ai" / "human" / "both" |
| source_references | 참조 출처 | ["한식재단", "foodtrip.or.kr"] |
| created_at | 생성 시점 | 2025-02-11 |
| updated_at | 최종 수정 시점 | 2025-02-11 |

---

### 1-3. MenuVariant (변형)

개별 식당 메뉴판에 등장하는 실제 메뉴명. CanonicalMenu에 연결.

```
예시:
  "할머니뼈해장국" → canonical: 뼈해장국 + modifier: 할머니
  "얼큰순두부뼈해장국" → canonical: 뼈해장국 + modifiers: [얼큰, 순두부]
  "왕갈비탕" → canonical: 갈비탕 + modifier: 왕
```

**필드:**
| 필드 | 설명 | 예시 |
|---|---|---|
| id | 고유 ID | `var_187` |
| display_name_ko | 식당에 표시된 이름 | 할머니뼈해장국 |
| canonical_id | 연결된 표준 메뉴 | canon_042 |
| modifier_ids | 적용된 수식어 목록 | [mod_012_할머니] |
| shop_id | 식당 ID (nullable) | shop_0042 |
| price | 가격 (nullable) | 9000 |
| additional_description | 식당 고유 설명 (nullable) | "24시간 푹 고은 사골 육수" |
| source | 데이터 출처 | "ocr_scan" / "manual" / "b2c_scan" |
| ai_confidence | 매칭 확신도 | 0.95 |
| first_seen_at | 최초 발견 시점 | 2025-02-11 |

---

### 1-4. Modifier (수식어)

메뉴명에 붙는 수식어. **자동 분해 알고리즘의 핵심.**

```
예시:
  얼큰 → taste / spicy_variant
  할머니 → emotion / homestyle
  왕 → size / large
  한우 → ingredient / korean_beef
```

**필드:**
| 필드 | 설명 | 예시 |
|---|---|---|
| id | 고유 ID | `mod_001` |
| text_ko | 한국어 텍스트 | 얼큰 |
| type | 수식어 유형 | taste / size / emotion / ingredient / cooking / grade / origin |
| semantic_key | 의미 키 | spicy_variant |
| translation_en | 영어 번역 | "Spicy" |
| translation_ja | 일본어 번역 | "辛い" |
| translation_zh | 중국어 번역 | "辣味" |
| affects_spice | 맵기 영향 (nullable) | +1 |
| affects_size | 크기 영향 (nullable) | null |
| affects_price | 가격 영향 (nullable) | null |
| priority | 분해 시 매칭 우선순위 | 10 (높을수록 먼저 매칭) |

**수식어 유형 분류 (v0.1):**
| 유형 | 설명 | 예시들 |
|---|---|---|
| `taste` | 맛 변형 | 얼큰, 매운, 순, 달콤, 담백, 시원한 |
| `size` | 크기/양 | 왕, 대, 소, 곱빼기, 반 |
| `emotion` | 감성/브랜드 | 할머니, 옛날, 시골, 원조, 맛있는 |
| `ingredient` | 재료 강조 | 한우, 해물, 야채, 순두부, 치즈 |
| `cooking` | 조리법 | 불, 숯불, 직화, 수제, 생 |
| `grade` | 등급 | 특, 프리미엄, 스페셜 |
| `origin` | 지역/기원 | 궁중, 부산, 전주, 제주 |
| `composition` | 구성 | 모듬, 세트, 정식 |

---

### 1-5. CulturalConcept (문화 개념)

메뉴 자체가 아닌 "한국 식당 문화" 요소. 주문 도우미 기능의 기반.

```
예시:
  반찬  — "무료 제공되는 작은 사이드 디시, 리필 가능"
  곱빼기 — "1.5~2배 양, 추가 요금 1,000~2,000원"
  셀프코너 — "물, 수저, 반찬을 직접 가져가는 곳"
```

**필드:**
| 필드 | 설명 | 예시 |
|---|---|---|
| id | 고유 ID | `culture_001` |
| name_ko | 한국어명 | 반찬 |
| name_en | 영어명 | Banchan (Side Dishes) |
| type | 유형 | ordering / serving / payment / etiquette |
| explanation_en | 영어 설명 | Free side dishes served with every meal... |
| explanation_ja | 일본어 설명 | 韓国の食堂で無料で提供される... |
| related_canonical_ids | 관련 메뉴 (nullable) | [canon_xxx_정식, canon_xxx_백반] |

**문화 개념 유형:**
| 유형 | 예시들 |
|---|---|
| `ordering` | 곱빼기, 1인분 최소주문, 공기밥 추가, 사리 추가 |
| `serving` | 반찬, 셀프코너, 상차림, 리필 |
| `payment` | 선불/후불, 테이블 결제, 더치페이 |
| `etiquette` | 신발 벗기, 바닥 좌석, 호출벨 |

---

### 1-6. Evidence (출처/근거)

모든 지식의 출처를 추적. AI 확정, 수동 검증, 공공 데이터 등.

```
예시:
  canon_042(뼈해장국)의 출처:
  - 한식재단 아카이브 (URL)
  - 식약처 영양 DB (API)
  - AI 분석 결과 (프롬프트 + 응답 해시)
```

**필드:**
| 필드 | 설명 | 예시 |
|---|---|---|
| id | 고유 ID | `ev_001` |
| target_type | 대상 노드 타입 | "canonical" / "variant" / "modifier" |
| target_id | 대상 노드 ID | canon_042 |
| source_type | 출처 유형 | "public_db" / "ai_discovery" / "human_review" / "web_search" |
| source_name | 출처명 | "한식재단 한식 아카이브" |
| source_url | 출처 URL (nullable) | "https://hansik.or.kr/..." |
| content_summary | 참조 내용 요약 | "돼지 등뼈를 우려낸 해장국의 일종..." |
| confidence_contribution | 확신도 기여 (0~1) | 0.3 |
| created_at | 수집 시점 | 2025-02-11 |

---

## 2. 관계(Edge) 타입 — 8종

### 관계 정의 테이블

| # | 관계 타입 | from → to | 설명 | 예시 |
|---|---|---|---|---|
| 1 | `belongs_to_concept` | Canonical → Concept | 개념 분류 소속 | 뼈해장국 → 해장국 |
| 2 | `is_variant_of` | Variant → Canonical | 변형 → 표준 연결 | 할머니뼈해장국 → 뼈해장국 |
| 3 | `similar_to` | Canonical ↔ Canonical | 유사 메뉴 (양방향) | 감자탕 ↔ 뼈해장국 |
| 4 | `often_confused_with` | Canonical ↔ Canonical | 자주 혼동 (양방향) | 곰탕 ↔ 설렁탕 |
| 5 | `served_with` | Canonical → Canonical/Cultural | 함께 제공 | 김치찌개 → 공기밥 |
| 6 | `evolved_from` | Canonical → (역사적 기원) | 역사적 유래 | 부대찌개 → 미군부대 역사 |
| 7 | `regional_variant` | Canonical ↔ Canonical | 지역별 변형 | 전주비빔밥 ↔ 진주비빔밥 |
| 8 | `cooking_variant` | Canonical ↔ Canonical | 조리법 변형 | 등뼈찜 ↔ 뼈해장국 |

### 관계 필드

| 필드 | 설명 |
|---|---|
| id | 고유 ID |
| relation_type | 위 8종 중 하나 |
| from_node_type | 출발 노드 타입 |
| from_node_id | 출발 노드 ID |
| to_node_type | 도착 노드 타입 |
| to_node_id | 도착 노드 ID |
| description | 관계 설명 (nullable) |
| bidirectional | 양방향 여부 |

---

## 3. 수식어 자동 분해 규칙

### 알고리즘 (Greedy Left-to-Right + Reverse Canonical Match)

```
Input: "왕얼큰순두부뼈해장국"

Step 1: Left-to-Right Modifier Match (앞에서부터 수식어 탐색)
  "왕" → mod_size_large ✓ (남은: "얼큰순두부뼈해장국")
  "얼큰" → mod_taste_spicy ✓ (남은: "순두부뼈해장국")
  "순두부" → mod_ingredient_soft_tofu ✓ (남은: "뼈해장국")

Step 2: Canonical Match (나머지로 표준 메뉴 매칭)
  "뼈해장국" → canon_042 ✓

Step 3: Confidence 계산
  모든 조각이 매칭됨 → confidence = 0.95

Step 4: 설명 조합 (템플릿 기반)
  "{size} {taste} {ingredient} {canonical.explanation}"
  → "Large serving of spicy soft tofu pork bone soup,
     a popular Korean hangover cure"
```

### 분해 실패 시 Fallback 전략

```
매칭 실패 (confidence < 0.5)
  → AI Identity Discovery 호출
  → 결과 검증 후 DB 추가 (새 Canonical 또는 새 Modifier)
  → 다음부터 자동 처리
```

### 목표 성공률

| 단계 | 수식어 수 | 표준 메뉴 수 | 자동 분해 성공률 |
|---|---|---|---|
| v0.1 (MVP) | 50~100 | 100~500 | 60~70% |
| v0.5 | 200 | 1,500 | 80~85% |
| v1.0 | 300+ | 3,000+ | 90%+ |

---

## 4. 난이도 스코어 산정 규칙

### 산정 공식 (v0.1)

```
difficulty = base_score
  + name_trap_bonus        (직역 함정: 곰탕→Bear +2)
  + compound_bonus          (합성어 수: 수식어 1개당 +0.5)
  + unknown_ingredient_bonus (서양에 없는 재료: +1)
  + unknown_method_bonus     (서양에 없는 조리법: +1)
  - global_awareness_discount (글로벌 인지도: 비빔밥 -2)
```

### 난이도 등급

| 점수 | 등급 | 설명 | 예시 |
|---|---|---|---|
| 1 | ⭐ | 글로벌하게 알려짐 | 비빔밥, 김치 |
| 2 | ⭐⭐ | 이름으로 추측 가능 | 불고기, 삼겹살 |
| 3 | ⭐⭐⭐ | 설명 필요 | 된장찌개, 냉면 |
| 4 | ⭐⭐⭐⭐ | 오해 가능성 높음 | 곰탕, 순대, 족발 |
| 5 | ⭐⭐⭐⭐⭐ | 합성어+문화 장벽 | 할머니뼈해장국, 시래기국 |
