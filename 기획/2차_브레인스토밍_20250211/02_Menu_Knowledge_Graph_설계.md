# 02. Menu Knowledge Graph 설계

## 1. 핵심 원칙

> **메뉴는 '문자열'이 아니라 '그래프 노드'다.**  
> **번역이 아니라 개념 매핑이다.**

한국 음식의 본질적 난이도: **"같은 음식인데 이름이 수백 가지"**

이를 해결하는 유일한 구조가 Knowledge Graph다.

---

## 2. 4계층 노드 구조

### Layer 1: Concept Node (개념) — 최상위 분류

음식의 본질적 카테고리. 가장 추상적인 층.

```json
{
  "id": "concept_001",
  "name": "해장국",
  "type": "concept",
  "definition": "술 마신 다음날 속을 풀기 위해 먹는 국물 요리 총칭",
  "superconcept": "국물요리",
  "cultural_context": "한국의 음주 문화와 깊이 연결된 음식 카테고리"
}
```

**대표 Concept 예시:**
- 국물요리 (탕/국/찌개)
- 구이류
- 밥류 (비빔밥, 덮밥, 볶음밥)
- 면류
- 반찬류
- 분식류
- 안주류

### Layer 2: Canonical Node (표준 메뉴) — DB의 핵심 단위

실제로 존재하는 대표 메뉴. 번역과 설명의 기준점.

```json
{
  "id": "canon_042",
  "name_ko": "뼈해장국",
  "name_en": "Pork Bone Hangover Soup",
  "name_ja": "ピョヘジャングク（豚骨スープ）",
  "name_zh": "骨头解酒汤",
  "parent_concept": "concept_001",
  "main_protein": "돼지등뼈",
  "cooking_method": "장시간 끓임",
  "spice_level": 2,
  "explanation_short_en": "Slow-simmered pork bone soup, a popular Korean hangover cure",
  "explanation_long_en": "A hearty Korean soup made by simmering pork spine bones for hours until the broth turns rich and milky. Often served with napa cabbage, perilla seeds, and green onions. Traditionally eaten the morning after drinking.",
  "dietary_tags": ["pork", "spicy_mild", "gluten_free"],
  "allergens": ["pork"],
  "similar_dishes": ["canon_043_감자탕"],
  "image_reference": "pork_bone_soup_01.jpg"
}
```

### Layer 3: Variant Node (변형) — 실제 식당에서 쓰는 이름

개별 식당의 메뉴판에 나타나는 실제 메뉴명. Canonical에 연결.

```json
{
  "id": "var_187",
  "display_name_ko": "할머니뼈해장국",
  "canonical_id": "canon_042",
  "modifiers": ["brand_emotional_homestyle"],
  "modifier_meaning": "'할머니' = 가정식 느낌, 정성스러운 조리 암시",
  "shop_id": "shop_0042",
  "price": 9000,
  "first_seen": "2025-02-11",
  "ai_confirmed": true,
  "ai_confidence": 0.95
}
```

### Layer 4: Modifier Dictionary (수식어 사전) — 그래프의 "문법"

메뉴명에 붙는 수식어를 분류하고 의미를 정의. **이것이 자동 분해의 핵심.**

```json
[
  {"modifier": "얼큰", "type": "taste", "meaning": "spicy_variant", "en": "Spicy"},
  {"modifier": "할머니", "type": "brand_emotion", "meaning": "homestyle", "en": "Grandma's / Homestyle"},
  {"modifier": "왕", "type": "size", "meaning": "large_serving", "en": "Large / King-size"},
  {"modifier": "특", "type": "grade", "meaning": "premium", "en": "Premium / Special"},
  {"modifier": "불", "type": "cooking", "meaning": "fire_grilled_or_extra_spicy", "en": "Flame-grilled / Extra spicy"},
  {"modifier": "옛날", "type": "brand_emotion", "meaning": "old_fashioned_traditional", "en": "Old-fashioned / Traditional"},
  {"modifier": "시골", "type": "brand_emotion", "meaning": "countryside_rustic", "en": "Country-style / Rustic"},
  {"modifier": "궁중", "type": "origin", "meaning": "royal_court_style", "en": "Royal court style"},
  {"modifier": "매운", "type": "taste", "meaning": "spicy", "en": "Spicy"},
  {"modifier": "순", "type": "taste", "meaning": "mild_plain", "en": "Mild / Plain"},
  {"modifier": "모듬", "type": "composition", "meaning": "assorted_mixed", "en": "Assorted"},
  {"modifier": "한우", "type": "ingredient_premium", "meaning": "korean_beef", "en": "Korean Beef (Hanwoo)"},
  {"modifier": "생", "type": "cooking", "meaning": "raw_fresh", "en": "Raw / Fresh"}
]
```

---

## 3. 관계(Edge) 타입 정의

| 관계 타입 | 설명 | 예시 | 용도 |
|---|---|---|---|
| `is_variant_of` | 표준 메뉴의 변형 | 얼큰뼈해장국 → 뼈해장국 | 변형 추적/분해 |
| `belongs_to_concept` | 개념 카테고리 소속 | 뼈해장국 → 해장국 | 분류 |
| `similar_to` | 유사하지만 다른 음식 | 감자탕 ↔ 뼈해장국 | 추천/비교 |
| `often_confused_with` | 자주 혼동되는 음식 | 곰탕 ↔ 설렁탕 | 오해 방지 설명 |
| `served_with` | 함께 제공되는 것 | 김치찌개 → 공기밥 | 문화적 맥락 |
| `evolved_from` | 역사적 기원 | 부대찌개 → (미군 부대 음식 역사) | 스토리텔링 |
| `regional_variant` | 지역별 변형 | 전주비빔밥 ↔ 진주비빔밥 | 지역 특색 |
| `cooking_variant` | 조리법 변형 | 등뼈찜 ↔ 뼈해장국 | 조리법 비교 |

---

## 4. 자동 분해 알고리즘 (Modifier Decomposition)

### 핵심 로직

처음 보는 메뉴명도 **수식어 사전 + 표준 메뉴 그래프**로 분해 가능.

```
입력: "왕얼큰순두부뼈해장국"

Step 1: 수식어 사전 매칭 (앞에서부터 탐욕적 매칭)
  왕 → size:large
  얼큰 → taste:spicy_variant

Step 2: 나머지에서 표준 메뉴 역순 매칭 (뒤에서부터)
  뼈해장국 → canon_042 (매칭!)
  순두부 → ingredient:soft_tofu

Step 3: 조합
  Large + Spicy + Soft Tofu + Pork Bone Hangover Soup

Step 4: 자연어 설명 생성 (템플릿 기반, AI 불필요)
  "Large serving of spicy soft tofu & pork bone soup,
   a popular Korean hangover cure"
```

### 분해 성공률 목표

- 수식어 사전 100개 + 표준 메뉴 500개 → 일반 메뉴 70~80% 자동 처리
- 수식어 사전 300개 + 표준 메뉴 3,000개 → 90% 이상 자동 처리
- 나머지 10%만 AI 호출 → 비용 극소화

### 분해 실패 시 Fallback

```
분해 실패 → AI Identity Discovery 호출
→ 결과를 검증 후 DB 추가
→ 다음부터는 자동 처리
```

---

## 5. 그래프가 만드는 부가 가치

### 5-1. 외국인 질문에 자동 답변

- "곰탕이랑 설렁탕 뭐가 달라요?" → `often_confused_with` 관계 → 차이점 설명 자동 생성
- "I liked Galbi-tang, what else?" → `similar_to` 관계 → 유사 메뉴 추천
- "Is this spicy?" → `dietary_tags` + `spice_level` → 즉시 답변

### 5-2. 메뉴 설명에 자동 삽입 가능한 문구

- "If you enjoyed bulgogi, you might like this" (similar_to 기반)
- "This is a milder version of..." (variant 관계 기반)
- "Best paired with rice and kimchi" (served_with 기반)
- "A dish with royal court origins" (evolved_from 기반)

### 5-3. 데이터 분석

- 가장 많은 변형이 존재하는 메뉴 = 가장 인기 있는 메뉴
- 지역별 canonical 분포 = 지역 음식 특색 지도
- 외국인 조회 빈도 × 난이도 = 우선 개선 대상

---

## 6. 메뉴 난이도 스코어 (Menu Difficulty Score)

그래프 데이터를 활용해 각 메뉴의 **"외국인 이해 난이도"**를 자동 산정.

### 점수 산정 기준

| 요소 | 점수 영향 |
|---|---|
| 글로벌 인지도 (비빔밥, 김치 등) | 난이도 ↓ |
| 메뉴명에 직역 함정 존재 (곰탕→Bear) | 난이도 ↑ |
| 합성어/수식어 다수 포함 | 난이도 ↑ |
| 조리법이 외국에 없는 것 (쌈, 찜질) | 난이도 ↑ |
| 재료가 서양에 없는 것 (들깨, 고추장) | 난이도 ↑ |

### 활용처

- **식당 대시보드:** "당신 메뉴의 외국인 접근성 점수: 62/100" → 유료 전환 동기
- **지자체 리포트:** "이 지역 평균 메뉴 접근성: 45점 (개선 필요)"
- **외국인 앱:** "초보자 추천 메뉴" 필터, 난이도별 정렬
