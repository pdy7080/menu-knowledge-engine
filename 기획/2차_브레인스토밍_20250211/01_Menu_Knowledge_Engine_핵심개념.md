# 01. Menu Knowledge Engine — 핵심 개념

## 1. 한 줄 정의

> **AI를 '결과 생성기'가 아니라 '초기 지식 수집·정규화 엔진'으로 투입하여,  
> 메뉴를 "번역 대상"이 아닌 "정의된 지식"으로 전환하는 시스템**

---

## 2. 기존 방식 vs Menu Knowledge Engine

### 기존 방식 (일반적인 AI 번역 서비스)

```
메뉴 이미지 → OCR → AI가 매번 번역/설명 생성 → 사용자 노출
```

**문제점:**
- ❌ 매 요청마다 AI 호출 (비용 누적)
- ❌ 설명 품질 편차 큼 (동일 메뉴도 매번 다른 결과)
- ❌ 데이터가 쌓여도 "지식"이 남지 않음
- ❌ SaaS로 팔기엔 원가 구조 불리

### Menu Knowledge Engine 방식 (플랫폼형)

```
메뉴 이미지
 → OCR
 → 메뉴 후보 추출
 → AI + 웹 서치 기반 "메뉴 정체성 탐색" (초기 1회)
 → 메뉴 개념 확정 (정규화)
 → 구조화 DB 저장
 → 이후엔 DB 기반 서비스 (AI 호출 불필요)
```

**핵심 이점:**
- ✅ AI는 '초기 학습/확정 단계'에서만 사용
- ✅ DB가 쌓일수록 AI 호출 비용 ↓ (비용 곡선이 하강)
- ✅ 설명 품질 일관성 ↑
- ✅ "한식 메뉴 지식 DB"라는 자산이 생김
- ✅ SaaS / API / 라이선싱 모두 가능

> **이건 "AI를 쓰는 서비스"가 아니라 "AI로 지식을 만들고, 그 지식을 파는 플랫폼"**

---

## 3. "메뉴를 정확히 파악한다"는 것의 의미

### 예시: "할머니뼈해장국"

**단순 번역 시:**
- ❌ "Grandmother Bone Hangover Soup" → 완전히 실패

**Menu Knowledge Engine이 하는 일:**

AI가 던지는 질문들:
1. 이 메뉴는 기존 한식 분류 중 어디에 속하는가?
2. "뼈해장국"과의 관계는?
3. "할머니"는 브랜드/정서/스토리 요소인가?
4. 지역적 특성이 있는가?
5. 외국인에게 어떤 개념으로 설명해야 이해가 빠른가?

**결과로 생성되는 "메뉴 개념 객체":**

```json
{
  "canonical_name_ko": "뼈해장국",
  "display_name_ko": "할머니뼈해장국",
  "category": ["국물요리", "해장국", "돼지고기"],
  "concept": "Slow-simmered pork bone soup traditionally eaten after drinking",
  "cultural_note": "'Grandmother-style' implies homestyle, rich broth",
  "translation_en": "Traditional Pork Bone Soup (Gamjatang-style)",
  "image_concept": "Korean pork bone soup with napa cabbage and spicy broth"
}
```

> **이 순간부터 이 메뉴는 '번역 대상'이 아니라 '정의된 지식'이 된다**

---

## 4. AI 비용 곡선 — 이 구조가 사업적으로 강력한 이유

```
AI 비용
  ▲
  │ ■■■■■
  │ ■■■
  │  ■■
  │   ■■
  │    ■■■■■■■■■■■■ (거의 0에 수렴)
  └──────────────────────→ 시간/가게 수
    초기    중기    후기
```

**왜 비용이 하강하는가:**
- 같은 메뉴는 전국 식당에서 반복 등장
- 관광지/프랜차이즈 메뉴는 특히 중복률 높음 (김치찌개, 된장찌개, 비빔밥...)
- AI는 신규 메뉴 / 특이 메뉴에만 쓰면 됨
- 수식어 사전이 쌓이면 합성어도 규칙 기반으로 분해 가능

**SaaS 관점에서의 의미:**
- 월 1.9만 원 가격 vs 실제 원가 → 마진율 시간에 따라 90% → 95% → 98%로 상승
- 같은 엔진으로 B2B SaaS + API를 동시 운영 → 고정비 분산 극대화

---

## 5. 엔진의 3단계 작동 구조

### Stage 1: Menu Identity Discovery (초기 AI 집중 구간)

- OCR 결과에서 메뉴명 후보 추출
- AI에게 "이 메뉴가 무엇인지" 서치 기반 조사
  - 위키, 블로그, 공공 데이터, 기존 음식 DB 종합
- 여러 출처를 종합해 의미를 확정
- 확신도(confidence score) 계산
- **한 메뉴당 1회만 수행 → 비용을 쓰더라도 "자산"으로 전환**

### Stage 2: Canonicalization (정규화)

- 유사 메뉴 묶기 (뼈해장국 / 감자탕 / 얼큰뼈국 → 관계 정의)
- "이상한 이름"을 의미 + 감성 요소로 분리
- 번역 금지어 / 직역 위험 단어 태깅
- **같은 메뉴가 다른 가게에 등장해도 AI 재호출 불필요**

### Stage 3: Structured Menu DB (진짜 자산)

```
Menu
 ├─ canonical_id
 ├─ names (ko / en / ja / zh)
 ├─ explanation_short
 ├─ explanation_long
 ├─ cultural_context
 ├─ similar_dishes
 ├─ image_concept
 ├─ dietary_tags (spicy, pork, vegan false)
 ├─ ai_confidence
 └─ last_verified
```

> **이 순간부터: 번역은 AI 생성 ❌ / DB 조회 ⭕**

---

## 6. 본질적 포지셔닝

이 서비스를 설명하는 한 문장:

> **"우리는 메뉴를 번역하는 게 아니라, '음식 개념을 정규화한 글로벌 메뉴 지식 API'를 제공합니다."**

판매 가능 대상:
- 음식점용 다국어 메뉴 SaaS
- 관광 플랫폼 (트립어드바이저, 클룩, 마이리얼트립)
- 배달앱 (배민, 요기요, 쿠팡이츠 — 외국인 사용자용)
- 호텔 / 리조트
- 공공 관광 시스템
- LLM 회사에 도메인 데이터 공급
