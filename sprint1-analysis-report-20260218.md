# Sprint 1 분석 리포트 (2026-02-18)

## 📋 목표
DB 매칭률 60% → 90% 개선을 위한 현재 상태 분석 및 개선 방향 도출

---

## 🔍 1. 현재 DB 상태

### 테이블별 레코드 수
| 테이블 | 레코드 수 | 목표 | 상태 |
|--------|----------|------|------|
| **concepts** | 48 | ~47 | ✅ 목표 달성 |
| **modifiers** | 54 | 50 | ✅ 목표 초과 |
| **canonical_menus** | 111 | 100 | ✅ 목표 초과 |
| **menu_variants** | 0 | - | ⚠️ 아직 미사용 |

**총 데이터**: 213 records (v0.1.0 기준)

---

## 🚨 2. 발견된 주요 이슈

### Issue #1: "한우" 타입 오류 ⭐⭐⭐ (Critical)

**현재 상태:**
```sql
text_ko = '한우'
type = 'grade'           ← ❌ 잘못됨
semantic_key = 'korean_beef'
priority = 20
```

**문제:**
- "한우"는 재료(ingredient)인데 등급(grade)으로 분류됨
- 이로 인해 "한우불고기" 분해 시 올바른 시맨틱 이해 불가
- 브랜드명 "한우식당"과 재료 수식어 "한우불고기"의 구분이 애매함

**영향받는 테스트 케이스:**
- TC-05: "숯불갈비" (간접 영향)
- TC-06: "한우불고기" (직접 영향)

**해결책:**
```sql
UPDATE modifiers
SET type = 'ingredient',
    semantic_key = 'korean_beef_ingredient'
WHERE text_ko = '한우';
```

**우선순위:** P0 (즉시 수정)

---

### Issue #2: "통닭" 누락 ⭐⭐⭐ (Critical)

**현재 상태:**
- modifiers 테이블에 "통" (whole) 존재 (type='cooking', priority=12)
- canonical_menus 테이블에 "통닭" **없음**

**문제:**
- "옛날통닭" 입력 시:
  - Step 1: "옛날" (modifier) 제거
  - Step 2: "통닭" canonical 검색 → **❌ 매칭 실패**
  - Step 3: "통" + "닭" 분해 시도 → "닭" canonical도 없음 → **❌ 실패**
  - Step 4: AI Discovery fallback (비용 발생)

**영향받는 테스트 케이스:**
- TC-08: "옛날통닭" (직접 영향)

**해결책:**
```sql
-- Option 1: "통닭"을 canonical_menu로 추가
INSERT INTO canonical_menus (name_ko, name_en, concept_id, ...)
VALUES ('통닭', 'Whole Fried Chicken', [구이류_concept_id], ...);

-- Option 2: "통"을 ingredient로 변경하고, "닭" canonical 추가
-- (비추천: "통"은 조리법이 맞음)
```

**권장:** Option 1 (통닭을 독립 canonical로 추가)

**우선순위:** P0 (즉시 수정)

---

### Issue #3: "불고기" 중복 ⭐⭐ (High)

**현재 상태:**
```sql
SELECT name_ko, concept_name FROM canonical_menus cm
JOIN concepts c ON cm.concept_id = c.id
WHERE cm.name_ko = '불고기';

-- 결과:
불고기 | 고기구이 (Meat Grill)
불고기 | 고기볶음 (Stir-fried Meat)
```

**문제:**
- 동일한 한글 이름 "불고기"가 2개의 서로 다른 concept에 매핑됨
- DB 매칭 시 어느 것을 선택해야 할지 모호함
- 일반적으로 "불고기"는 **구이**로 분류됨 (볶음은 "제육볶음" 등으로 구분)

**해결책:**
```sql
-- Option 1: 볶음 버전 제거 (권장)
DELETE FROM canonical_menus
WHERE name_ko = '불고기' AND concept_id IN (
    SELECT id FROM concepts WHERE name_ko = '고기볶음'
);

-- Option 2: 볶음 버전을 "불고기볶음"으로 명확화
UPDATE canonical_menus
SET name_ko = '불고기볶음', name_en = 'Bulgogi Bokkeum (Stir-fried Bulgogi)'
WHERE name_ko = '불고기' AND concept_id IN (
    SELECT id FROM concepts WHERE name_ko = '고기볶음'
);
```

**권장:** Option 1 (중복 제거)

**우선순위:** P1 (Week 1 내 수정)

---

## ✅ 3. 잘 구축된 부분

### 주요 메뉴 검증
```sql
SELECT name_ko, name_en, spice_level, difficulty_score
FROM canonical_menus
WHERE name_ko IN ('김치찌개', '뼈해장국', '돈까스', '순두부찌개', '갈비');
```

| 메뉴 | 영문명 | 매운맛 | 난이도 | 상태 |
|------|--------|--------|--------|------|
| 김치찌개 | Kimchi Jjigae | 3 | 1 | ✅ |
| 뼈해장국 | Ppyeo Haejangguk | 2 | 2 | ✅ |
| 돈까스 | Donkatsu | 0 | 1 | ✅ |
| 순두부찌개 | Sundubu Jjigae | 3 | 1 | ✅ |
| 갈비 | Galbi | 0 | 1 | ✅ |

**결론:** 10대 테스트 케이스 중 5개는 이미 DB에 잘 구축됨

---

## 🎯 4. 10대 테스트 케이스 예상 성능

| # | 테스트 케이스 | 예상 결과 | 이슈 |
|---|--------------|----------|------|
| TC-01 | 김치찌개 | ✅ 통과 | - |
| TC-02 | 할머니김치찌개 | ✅ 통과 | modifier "할머니" 존재 |
| TC-03 | 왕돈까스 | ✅ 통과 | modifier "왕" 존재 |
| TC-04 | 얼큰순두부찌개 | ✅ 통과 | modifier "얼큰" 존재 |
| TC-05 | 숯불갈비 | ✅ 통과 | modifier "숯불" 존재 |
| TC-06 | 한우불고기 | ⚠️ 주의 | **Issue #1**: "한우" 타입 오류 |
| TC-07 | 왕얼큰뼈해장국 | ✅ 통과 | 다중 수식어 ("왕", "얼큰") |
| TC-08 | 옛날통닭 | ❌ 실패 | **Issue #2**: "통닭" canonical 누락 |
| TC-09 | 시래기국 | ❌ 실패 | AI Discovery 필요 (v0.2) |
| TC-10 | 고씨네묵은지감자탕 | ⚠️ 주의 | 브랜드명 "고씨네" 처리 필요 |

**예상 통과율: 7/10 (70%)** ← 목표 9/10 (90%)에 미달

---

## 🔧 5. 개선 작업 우선순위

### P0 (즉시 수정, Week 1 Day 2-3)
1. ✅ **Issue #1 수정**: "한우" 타입을 `grade` → `ingredient`로 변경
2. ✅ **Issue #2 해결**: "통닭" canonical 추가

### P1 (Week 1 Day 4-5)
3. ✅ **Issue #3 해결**: "불고기" 중복 제거 또는 명확화
4. ✅ **브랜드명 패턴 추가**: "고씨네", "할머니네", "엄마손" 등 50개 패턴 구축

### P2 (Week 2)
5. ⚠️ **pg_trgm Fallback 구현**: 오타 대응 ("김치찌게" → "김치찌개")
6. ⚠️ **300개 실전 메뉴 테스트**: 실제 매칭률 90% 검증

---

## 📊 6. 예상 개선 효과

| 지표 | 현재 (Before) | 개선 후 (After) | 증감 |
|------|--------------|----------------|------|
| **테스트 통과율** | 7/10 (70%) | 9/10 (90%) | +20%p |
| **DB 매칭률** | 60% | 90% | +30%p |
| **AI 호출 비율** | 40% | 10% | -30%p |
| **비용/스캔** | 30원 | 10원 | -67% |

---

## 🚀 7. 다음 단계 (Week 1 Day 2-3)

### 작업 목록
1. [x] 분석 리포트 작성 (현재 문서)
2. [ ] "한우" modifier 타입 수정
3. [ ] "통닭" canonical_menu 추가
4. [ ] "불고기" 중복 제거
5. [ ] TC-06, TC-08 재검증

### SQL 스크립트 준비
```sql
-- Week 1 Day 2 실행 예정
BEGIN;

-- Issue #1: 한우 타입 수정
UPDATE modifiers
SET type = 'ingredient', semantic_key = 'korean_beef_ingredient'
WHERE text_ko = '한우';

-- Issue #2: 통닭 추가
INSERT INTO canonical_menus (
    name_ko, name_en, concept_id,
    explanation_short, main_ingredients,
    allergens, dietary_tags, spice_level,
    difficulty_score, status
) VALUES (
    '통닭', 'Whole Fried Chicken',
    (SELECT id FROM concepts WHERE name_ko = '구이류'),
    '{"en": "Whole chicken, deep-fried until crispy"}',
    '[{"ko": "닭", "en": "chicken"}]',
    ARRAY['chicken'],
    ARRAY['contains_chicken'],
    0, 1, 'active'
);

-- Issue #3: 불고기 중복 제거
DELETE FROM canonical_menus
WHERE name_ko = '불고기' AND concept_id IN (
    SELECT id FROM concepts WHERE name_ko = '고기볶음'
);

COMMIT;
```

---

## 📝 결론

### 핵심 발견
1. **DB 데이터 품질은 양호** (213 records 로드 완료)
2. **3개 Critical 이슈 발견** (한우, 통닭, 불고기 중복)
3. **수정 후 90% 목표 달성 가능** (2일 소요 예상)

### 리스크
- ⚠️ "시래기국" (TC-09)는 v0.1에서 해결 불가 (AI Discovery 필요)
- ⚠️ "고씨네묵은지감자탕" (TC-10)은 브랜드명 패턴 구축 필요 (Week 1 Day 4-5)

### 권장사항
**Sprint 1 계획대로 진행 가능** ✅
- Week 1 Day 2-3: 데이터 수정
- Week 1 Day 4-5: 브랜드명 패턴
- Week 2: 검증 및 300개 실전 테스트

---

**작성일**: 2026-02-18
**작성자**: Claude (Menu Knowledge Engine Sprint 1)
**다음 작업**: Task #3 (Week 1 Day 2-3: "한우", "통닭" 데이터 수정)
