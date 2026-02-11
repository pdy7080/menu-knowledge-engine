# 07. Seed Data Guide — 초기 데이터 구축 실행 가이드

> **이 문서는 "내일부터 실제로 무엇을 만드느냐"를 정의한다.**  
> 03_data_schema의 테이블에 들어갈 최초 데이터를 어떻게 만들지의 구체적 실행 안내.

---

## 1. 구축 순서 (의존성 기반)

```
Step 1: concepts (개념 트리)         ← 다른 테이블의 기반
    ↓
Step 2: modifiers (수식어 사전)      ← 분해 알고리즘의 기반
    ↓
Step 3: canonical_menus (표준 메뉴)  ← 핵심 데이터
    ↓
Step 4: menu_relations (관계)        ← canonical 간 연결
    ↓
Step 5: cultural_concepts (문화)     ← 보조 데이터
    ↓
Step 6: evidences (출처 기록)        ← 자동 생성
```

> **Step 1~3이 MVP의 생사를 결정한다.** Step 4~6은 보조적.

---

## 2. Step 1: Concept 트리 시드 데이터

### 구조: 2레벨 (대분류 → 중분류)

```json
[
  {
    "name_ko": "국물요리",
    "name_en": "Soups & Stews",
    "definition_ko": "국물이 주가 되는 한국 요리 총칭",
    "definition_en": "Korean dishes where broth or soup is the main component",
    "children": [
      {
        "name_ko": "탕",
        "name_en": "Tang (Rich Soup)",
        "definition_ko": "오랜 시간 끓여 진한 국물을 낸 요리",
        "definition_en": "Deeply simmered soups with rich, concentrated broth"
      },
      {
        "name_ko": "국",
        "name_en": "Guk (Light Soup)",
        "definition_ko": "가볍게 끓인 맑은 국물 요리, 밥과 함께 먹음",
        "definition_en": "Light soups typically served with rice as part of a meal"
      },
      {
        "name_ko": "찌개",
        "name_en": "Jjigae (Stew)",
        "definition_ko": "국보다 걸쭉하고 양념이 진한 국물 요리",
        "definition_en": "Thicker and more heavily seasoned than guk, served bubbling hot"
      },
      {
        "name_ko": "전골",
        "name_en": "Jeongol (Hot Pot)",
        "definition_ko": "여러 재료를 넣고 식탁에서 끓이는 냄비 요리",
        "definition_en": "Elaborate hot pot cooked at the table with various ingredients"
      },
      {
        "name_ko": "해장국",
        "name_en": "Haejangguk (Hangover Soup)",
        "definition_ko": "술 마신 다음날 해장을 위해 먹는 국물 요리 총칭",
        "definition_en": "Category of soups traditionally consumed to cure hangovers"
      }
    ]
  },
  {
    "name_ko": "밥류",
    "name_en": "Rice Dishes",
    "definition_ko": "쌀밥을 주식으로 하는 요리 총칭",
    "definition_en": "Dishes centered around cooked rice",
    "children": [
      {"name_ko": "비빔밥", "name_en": "Bibimbap (Mixed Rice)"},
      {"name_ko": "덮밥", "name_en": "Deopbap (Rice Bowl)"},
      {"name_ko": "볶음밥", "name_en": "Bokkeumbap (Fried Rice)"},
      {"name_ko": "죽", "name_en": "Juk (Porridge)"},
      {"name_ko": "국밥", "name_en": "Gukbap (Soup with Rice)"},
      {"name_ko": "정식/백반", "name_en": "Jeongsik/Baekban (Set Meal)"}
    ]
  },
  {
    "name_ko": "면류",
    "name_en": "Noodle Dishes",
    "children": [
      {"name_ko": "국수", "name_en": "Guksu (Noodle Soup)"},
      {"name_ko": "냉면", "name_en": "Naengmyeon (Cold Noodles)"},
      {"name_ko": "라면", "name_en": "Ramyeon (Ramen)"},
      {"name_ko": "칼국수", "name_en": "Kalguksu (Knife-cut Noodles)"}
    ]
  },
  {
    "name_ko": "구이류",
    "name_en": "Grilled Dishes",
    "children": [
      {"name_ko": "고기구이", "name_en": "Meat Grill (BBQ)"},
      {"name_ko": "생선구이", "name_en": "Grilled Fish"}
    ]
  },
  {
    "name_ko": "찜/조림류",
    "name_en": "Braised & Steamed",
    "children": [
      {"name_ko": "찜", "name_en": "Jjim (Steamed/Braised)"},
      {"name_ko": "조림", "name_en": "Jorim (Simmered)"}
    ]
  },
  {
    "name_ko": "볶음류",
    "name_en": "Stir-fried Dishes",
    "children": []
  },
  {
    "name_ko": "전/부침류",
    "name_en": "Pancakes & Fritters",
    "children": [
      {"name_ko": "전", "name_en": "Jeon (Savory Pancake)"},
      {"name_ko": "부침개", "name_en": "Buchimgae (Fritter)"}
    ]
  },
  {
    "name_ko": "반찬류",
    "name_en": "Side Dishes",
    "children": [
      {"name_ko": "나물", "name_en": "Namul (Seasoned Vegetables)"},
      {"name_ko": "김치", "name_en": "Kimchi"},
      {"name_ko": "젓갈", "name_en": "Jeotgal (Fermented Seafood)"}
    ]
  },
  {
    "name_ko": "분식류",
    "name_en": "Snack Foods",
    "children": []
  },
  {
    "name_ko": "안주류",
    "name_en": "Drinking Snacks (Anju)",
    "children": []
  },
  {
    "name_ko": "음료류",
    "name_en": "Beverages",
    "children": [
      {"name_ko": "술", "name_en": "Alcoholic Beverages"},
      {"name_ko": "비알콜", "name_en": "Non-Alcoholic Beverages"}
    ]
  },
  {
    "name_ko": "디저트류",
    "name_en": "Desserts & Sweets",
    "children": []
  }
]
```

**작업량:** 대분류 12개 + 중분류 ~35개 = **약 47개 레코드**  
**예상 소요:** 수동 입력 2~3시간

---

## 3. Step 2: Modifier 사전 시드 데이터

### 50개 수식어 (v0.1)

#### taste (맛) — 12개

| text_ko | semantic_key | translation_en | affects_spice | priority |
|---|---|---|---|---|
| 얼큰 | spicy_hearty | Extra Spicy | +1 | 10 |
| 매운 | spicy | Spicy | +2 | 10 |
| 순 | mild | Mild | -2 | 10 |
| 담백한 | light_clean | Light & Clean | 0 | 8 |
| 달콤한 | sweet | Sweet | 0 | 8 |
| 시원한 | refreshing | Refreshing | 0 | 8 |
| 새콤한 | tangy | Tangy/Sour | 0 | 8 |
| 고소한 | nutty_savory | Nutty & Savory | 0 | 8 |
| 짭짤한 | salty_savory | Savory & Salty | 0 | 8 |
| 칼칼한 | sharp_spicy | Sharp Spicy | +1 | 8 |
| 알싸한 | pungent | Pungent | 0 | 8 |
| 구수한 | deep_savory | Deep & Savory | 0 | 8 |

#### size (크기/양) — 7개

| text_ko | semantic_key | translation_en | affects_size | priority |
|---|---|---|---|---|
| 왕 | x_large | King-Size | x_large | 15 |
| 대 | large | Large | large | 12 |
| 소 | small | Small | small | 12 |
| 곱빼기 | double | Double Portion | double | 15 |
| 반 | half | Half Portion | half | 15 |
| 미니 | mini | Mini | mini | 12 |
| 점보 | jumbo | Jumbo | jumbo | 10 |

#### emotion (감성/브랜드) — 10개

| text_ko | semantic_key | translation_en | priority |
|---|---|---|---|
| 할머니 | homestyle_grandma | Grandma's / Homestyle | 5 |
| 옛날 | old_fashioned | Old-fashioned / Traditional | 5 |
| 시골 | countryside | Countryside-style | 5 |
| 원조 | original | The Original | 5 |
| 본가 | main_house | Main House / Authentic | 5 |
| 맛있는 | delicious | Delicious | 3 |
| 엄마손 | mothers_touch | Mother's Touch | 5 |
| 고향 | hometown | Hometown-style | 5 |
| 전통 | traditional | Traditional | 5 |
| 명품 | premium_brand | Premium | 5 |

#### ingredient (재료 강조) — 10개

| text_ko | semantic_key | translation_en | priority |
|---|---|---|---|
| 한우 | korean_beef | Korean Beef (Hanwoo) | 20 |
| 해물 | seafood | Seafood | 18 |
| 야채 | vegetable | Vegetable | 15 |
| 순두부 | soft_tofu | Soft Tofu | 18 |
| 치즈 | cheese | Cheese | 15 |
| 묵은지 | aged_kimchi | Aged Kimchi | 18 |
| 모듬 | assorted | Assorted | 15 |
| 날치알 | flying_fish_roe | Flying Fish Roe | 12 |
| 계란 | egg | Egg | 12 |
| 버섯 | mushroom | Mushroom | 15 |

#### cooking (조리법) — 6개

| text_ko | semantic_key | translation_en | priority |
|---|---|---|---|
| 불 | fire_grilled | Fire-Grilled | 12 |
| 숯불 | charcoal | Charcoal-Grilled | 15 |
| 직화 | direct_flame | Direct Flame | 12 |
| 수제 | handmade | Handmade | 10 |
| 생 | raw | Raw/Fresh | 15 |
| 통 | whole | Whole | 12 |

#### grade (등급) — 3개

| text_ko | semantic_key | translation_en | priority |
|---|---|---|---|
| 특 | special_grade | Special Grade | 10 |
| 프리미엄 | premium | Premium | 10 |
| 스페셜 | special | Special | 10 |

#### origin (지역) — 2개

| text_ko | semantic_key | translation_en | priority |
|---|---|---|---|
| 궁중 | royal_court | Royal Court | 8 |
| 부산 | busan_style | Busan-style | 8 |

**작업량:** 50개 레코드  
**예상 소요:** 수동 입력 1~2시간

---

## 4. Step 3: Canonical Menu 구축 전략

### 100개를 어떻게 만드느냐

**방법: AI 배치 생성 + 수동 검수**

```
1단계: GPT-4o에 Identity Discovery 프롬프트로 100개 일괄 요청
       (05_mvp_scope_definition의 프롬프트 A 사용)
       → JSON 배열로 100개 응답 받음

2단계: 수동 검수 (중요!)
       - explanation 자연스러운가
       - allergens 누락 없는가
       - spice_level 적절한가
       - 문화적 맥락이 정확한가

3단계: 공공 데이터와 교차 검증
       - 한식재단 아카이브에서 설명 보완
       - 식약처 DB에서 영양/알레르기 검증

4단계: DB INSERT
```

### AI 배치 프롬프트 (100개 일괄용)

```
System:
한국 음식 전문가로서, 아래 100개 한국 메뉴에 대해 각각 구조화된 정보를 JSON 배열로 제공하세요.
05_mvp_scope_definition.md의 Identity Discovery 프롬프트 형식을 따르세요.

User:
다음 100개 한국 메뉴에 대해 JSON 배열로 답변하세요:
김치찌개, 된장찌개, 순두부찌개, 부대찌개, 삼계탕, 감자탕, ...
(전체 100개 리스트)
```

> **주의: 한 번에 100개 요청은 토큰 한도 초과 가능. 20~25개씩 4~5번에 나눠 요청.**

### 검수 체크리스트 (각 Canonical마다)

- [ ] name_en이 자연스러운 영어인가 (직역 아닌 의역)
- [ ] romanization이 국립국어원 표기법 준수인가
- [ ] explanation_short가 1문장, 핵심을 전달하는가
- [ ] allergens에 주요 알레르기 유발물질 포함했는가
- [ ] spice_level이 실제 경험과 일치하는가
- [ ] difficulty_score가 외국인 관점에서 적절한가
- [ ] main_ingredients가 3~7개 범위인가
- [ ] concept_id가 올바른 카테고리에 매핑되었는가

**작업량:** AI 생성 1~2시간 + 수동 검수 4~6시간 = **약 1~2일**

---

## 5. Step 4: 관계(Edge) 시드 데이터

### 관계 정의 우선순위

**Phase 1 (즉시):** similar_to, often_confused_with  
**Phase 2 (나중):** served_with, regional_variant, cooking_variant, evolved_from

### 핵심 혼동 쌍 (often_confused_with) — 즉시 필요

```
곰탕 ↔ 설렁탕       "둘 다 맑은 소고기 국물이지만 부위와 조리법이 다름"
감자탕 ↔ 뼈해장국    "둘 다 돼지뼈 국물이지만 감자탕은 감자가 핵심"
냉면 ↔ 막국수        "둘 다 차가운 면이지만 면의 재료와 지역이 다름"
된장찌개 ↔ 청국장     "둘 다 콩 발효 기반이지만 향과 발효도가 다름"
순대 ↔ 소시지         "외형이 비슷하지만 재료와 문화가 완전히 다름"
족발 ↔ 보쌈          "둘 다 돼지고기 안주지만 부위와 조리법이 다름"
비빔냉면 ↔ 비빔국수   "둘 다 비벼먹는 면이지만 면의 종류가 다름"
```

### 핵심 유사 쌍 (similar_to)

```
김치찌개 ~ 김치전골     (같은 재료, 다른 조리 형태)
삼겹살 ~ 목살          (같은 카테고리, 다른 부위)
돌솥비빔밥 ~ 비빔밥     (같은 개념, 다른 그릇)
물냉면 ~ 비빔냉면       (같은 면, 다른 제공 방식)
잔치국수 ~ 칼국수       (같은 국수, 다른 면 형태)
제육볶음 ~ 불고기       (같은 재료, 다른 조리법)
```

**작업량:** 약 30~50개 관계 = **수동 1~2시간**

---

## 6. Step 5: Cultural Concept 시드 데이터

```json
[
  {
    "name_ko": "반찬",
    "name_en": "Banchan (Side Dishes)",
    "type": "serving",
    "explanation": {
      "en": "Free side dishes that come with every Korean meal. They are refillable — just ask! Common banchan include kimchi, seasoned vegetables (namul), pickled radish, and egg roll.",
      "ja": "韓国の食事に無料で付いてくるおかず。おかわり自由です！キムチ、ナムル、たくあん、卵焼きなどが一般的です。"
    },
    "icon": "🥬"
  },
  {
    "name_ko": "곱빼기",
    "name_en": "Gopbbaegi (Double Portion)",
    "type": "ordering",
    "explanation": {
      "en": "Double portion option available at most Korean restaurants. Usually costs ₩1,000~₩2,000 extra. Just say 'gopbbaegi' when ordering!"
    },
    "icon": "🍚🍚"
  },
  {
    "name_ko": "셀프코너",
    "name_en": "Self-Service Station",
    "type": "serving",
    "explanation": {
      "en": "A self-service area where you get your own water, utensils, and sometimes side dishes. Look for a counter or station near the entrance."
    },
    "icon": "🚰"
  },
  {
    "name_ko": "공기밥",
    "name_en": "Extra Rice",
    "type": "ordering",
    "explanation": {
      "en": "A separate bowl of steamed white rice. Costs ₩1,000. Most stews and soups come with rice, but you can order extra."
    },
    "icon": "🍚"
  },
  {
    "name_ko": "호출벨",
    "name_en": "Call Button",
    "type": "etiquette",
    "explanation": {
      "en": "A button on your table to call the server. Press it once and wait — no need to wave or shout. Very common in Korean restaurants."
    },
    "icon": "🔔"
  },
  {
    "name_ko": "선불/후불",
    "name_en": "Prepay / Pay After",
    "type": "payment",
    "explanation": {
      "en": "Some restaurants require payment when ordering (prepay, common at fast food and bunsik places), while others let you pay after eating (pay after, common at sit-down restaurants)."
    },
    "icon": "💳"
  },
  {
    "name_ko": "1인분 최소주문",
    "name_en": "Minimum Order Per Person",
    "type": "ordering",
    "explanation": {
      "en": "Most Korean BBQ and hot pot restaurants require a minimum order of 2 portions. '1인분' means one portion — you may see '2인분부터 주문가능' which means 'minimum 2 portions required.'"
    },
    "icon": "👥"
  },
  {
    "name_ko": "사리 추가",
    "name_en": "Sari (Extra Noodles/Rice Cake)",
    "type": "ordering",
    "explanation": {
      "en": "Extra noodles or rice cakes you can add to stews and hot pots. 'Ramyeon sari' adds ramen noodles, 'tteok sari' adds rice cakes. Usually ₩1,000~₩2,000."
    },
    "icon": "🍜"
  }
]
```

**작업량:** 8~15개 = **수동 1~2시간**

---

## 7. 전체 시드 데이터 작업 요약

| Step | 대상 | 건수 | 방법 | 소요 시간 |
|---|---|---|---|---|
| 1 | Concepts | ~47 | 수동 | 2~3시간 |
| 2 | Modifiers | 50 | 수동 | 1~2시간 |
| 3 | Canonical Menus | 100 | AI + 검수 | 1~2일 |
| 4 | Relations | 30~50 | 수동 | 1~2시간 |
| 5 | Cultural Concepts | 8~15 | 수동 | 1~2시간 |
| 6 | Evidences | 자동 | Step 3에서 자동 생성 | - |
| **합계** | | **~265건** | | **약 2~3일** |

> **3일이면 엔진의 "뇌"에 초기 지식이 채워진다.**

---

## 8. 검증: 시드 데이터로 수식어 분해 테스트

시드 데이터 구축 완료 후, 아래 10개 테스트 케이스로 분해 성공률을 측정:

| # | 입력 메뉴명 | 기대 결과 | 기대 분해 |
|---|---|---|---|
| 1 | 김치찌개 | 정확 매칭 | canonical: 김치찌개 |
| 2 | 할머니김치찌개 | 수식어 분해 | 할머니 + 김치찌개 |
| 3 | 왕돈까스 | 수식어 분해 | 왕 + 돈까스 |
| 4 | 얼큰순두부찌개 | 수식어 분해 | 얼큰 + 순두부찌개 |
| 5 | 숯불갈비 | 수식어 분해 | 숯불 + 갈비 |
| 6 | 한우불고기 | 수식어 분해 | 한우 + 불고기 |
| 7 | 왕얼큰뼈해장국 | 다중 수식어 | 왕 + 얼큰 + 뼈해장국 |
| 8 | 옛날통닭 | 수식어 분해 | 옛날 + 통 + 닭 |
| 9 | 시래기국 | AI Discovery | (DB에 없으면 AI 호출) |
| 10 | 고씨네묵은지감자탕 | 복합 | 고씨네(브랜드) + 묵은지 + 감자탕 |

**목표: 10개 중 7개 이상 정확 분해 (70%+)**

이 테스트에서 실패하는 케이스들이 곧 **v0.2 개선 방향**을 알려준다.
