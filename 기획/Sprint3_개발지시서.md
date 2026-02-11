# Sprint 3 개발지시서: Knowledge Graph 강화 + OCR 통합

> 작성일: 2025-02-11
> 작성자: PM (Claude Opus)
> 대상: 개발자 (Claude Code)
> 상태: 실행 대기

---

## 📋 Sprint 3 개요

### 배경
Sprint 0-1에서 DB 스키마, 시드 데이터(112개), 매칭 엔진(68%)을 구축했고,
Sprint 2에서 B2C 모바일웹 프론트엔드를 완성했다.

**현재 가장 큰 병목은 OCR이 아니라 Knowledge Graph의 커버리지와 매칭 정확도다.**

```
OCR 90% + 매칭 95% = 실서비스 가능 ✅
OCR 99% + 매칭 60% = 실서비스 불가 ❌
```

### Sprint 3 목표

| 목표 | 현재 | 달성 기준 | 중요도 |
|------|------|----------|--------|
| Canonical 메뉴 DB | 112개 | **300개+** | ⭐⭐⭐⭐⭐ |
| 매칭 엔진 정확도 | 68% | **80%+** | ⭐⭐⭐⭐⭐ |
| Modifier 사전 | 54개 | **80개+** | ⭐⭐⭐⭐ |
| OCR 파이프라인 | 미구현 | **GPT-4o mini Vision 동작** | ⭐⭐⭐⭐ |
| 사진 업로드 UI | Coming Soon | **카메라/갤러리 연동** | ⭐⭐⭐ |

### 2단계 분리 실행

```
Sprint 3A (기반 강화) → Sprint 3B (OCR 통합)
순서 반드시 지킬 것. 3A 없이 3B 진행 금지.
```

---

## 🔷 Sprint 3A: Knowledge Graph 강화

> 예상 소요: 2~3시간
> 핵심: DB 확장 → 매칭 엔진 개선 → 검증 테스트

### Task 3A-1: Canonical 메뉴 DB 확장 (112개 → 300개+)

#### 목표
관광객이 실제로 마주치는 메뉴의 **80% 이상**을 DB 매칭만으로 처리할 수 있도록 커버리지 확대.

#### 추가할 카테고리별 메뉴 (약 190개 추가)

**현재 112개 구성:**
- 국물요리 25개, 밥류 12개, 면류 10개, 고기구이 12개
- 반찬류 10개, 분식류 8개, 해산물 8개, 치킨/튀김 7개
- 전/부침개 5개, 디저트/음료 8개, 기타 7개

**추가 필요 (관광객 빈도 기준):**

```python
# 1. 국물요리 추가 (15개)
추가_국물 = [
    "육개장", "우거지탕", "곰탕", "선지해장국", "내장탕",
    "추어탕", "아귀찜",  # 찜이지만 탕류로 분류
    "조개탕", "대구탕", "알탕",
    "동태찌개", "청국장찌개", "고추장찌개", "된장찌개",  # 이미 있는지 확인
    "매운탕"
]

# 2. 고기류 추가 (20개) — 관광객 최다 소비
추가_고기 = [
    "양념갈비", "LA갈비", "갈비찜", "소갈비살", "차돌박이",
    "우삼겹", "항정살", "가브리살", "토시살", "꽃살",
    "갈매기살", "뒷고기", "막창", "곱창", "대창",
    "족발", "보쌈", "수육", "편육", "제육볶음"
]

# 3. 면류 추가 (10개)
추가_면 = [
    "잔치국수", "콩국수", "쫄면", "막국수", "밀면",
    "칼국수",  # 이미 있는지 확인
    "수제비", "비빔국수", "물냉면", "회냉면"
]

# 4. 밥류 추가 (15개)
추가_밥 = [
    "제육덮밥", "오징어덮밥", "참치김치덮밥", "회덮밥", "낙지덮밥",
    "김치볶음밥", "새우볶음밥", "알밥", "전복죽", "호박죽",
    "누룽지", "솥밥", "영양밥", "곤드레밥", "보리밥"
]

# 5. 해산물 추가 (15개) — 한국 해산물 관광 중요
추가_해산물 = [
    "꽃게찜", "간장게장", "양념게장", "새우튀김", "오징어볶음",
    "낙지볶음", "주꾸미볶음", "조개구이", "전복구이", "굴구이",
    "산낙지", "회", "물회", "광어회", "연어회"
]

# 6. 분식/길거리 추가 (15개) — 관광객 인기
추가_분식 = [
    "순대", "떡꼬치", "어묵꼬치", "핫도그(한국식)", "계란빵",
    "호떡", "붕어빵", "타코야끼(한국식)", "치즈볼", "감자튀김",
    "김밥", "충무김밥", "라볶이", "쫄볶이", "컵밥"
]

# 7. 전/부침개 추가 (8개)
추가_전 = [
    "감자전", "녹두전", "동그랑땡", "떡갈비", "고기완자",
    "굴전", "새우전", "호박전"
]

# 8. 찜/조림 추가 (10개)
추가_찜 = [
    "안동찜닭", "닭볶음탕", "해물찜", "돼지갈비찜", "꽁치조림",
    "두부조림", "감자조림", "장조림", "고등어조림", "코다리조림"
]

# 9. 반찬/나물 추가 (10개)
추가_반찬 = [
    "시금치나물", "콩나물무침", "오이무침", "미역줄기볶음", "멸치볶음",
    "어묵볶음", "깍두기", "총각김치", "열무김치", "파김치"
]

# 10. 디저트/음료 추가 (10개)
추가_디저트 = [
    "수정과", "식혜", "매실차", "유자차", "쌍화차",
    "팥빙수", "인절미", "약과", "한과", "떡"
]

# 11. 주류/안주 추가 (10개) — 관광 야간 경제
추가_주류안주 = [
    "소주", "막걸리", "맥주", "동동주", "백세주",
    "치킨", "양념치킨", "간장치킨", "닭발", "골뱅이무침"
]

# 12. 카페/베이커리 추가 (12개) — 한국 카페 문화
추가_카페 = [
    "아메리카노", "카페라떼", "아이스티", "생과일주스", "스무디",
    "토스트(한국식)", "샌드위치", "크로플", "소금빵", "마카롱",
    "크림라떼", "아인슈페너"
]

# 13. 한정식/코스 (10개) — 관광 고급 시장
추가_한정식 = [
    "한정식", "백반", "정식", "불고기정식", "갈비정식",
    "생선구이정식", "돌솥비빔밥정식", "순두부정식", "삼계탕정식", "된장정식"
]
```

#### 시드 데이터 형식

기존 `seed_canonical_menus.py`와 **동일한 형식**을 유지할 것:

```python
{
    "name_ko": "육개장",
    "name_en": "Yukgaejang (Spicy Beef Soup)",
    "concept": "탕",                              # concepts 테이블의 name_ko와 매칭
    "description_ko": "소고기와 대파를 넣고 고춧가루로 얼큰하게 끓인 국물 요리",
    "description_en": "Spicy shredded beef soup with green onions and vegetables",
    "primary_ingredients": ["beef", "green onion", "bean sprouts", "bracken", "taro stem"],
    "allergens": ["beef"],
    "spice_level": 3,                             # 0~5
    "difficulty_score": 2,                        # 1~5 (1=쉬움, 5=도전적)
}
```

#### 작업 방법

1. **기존 시드 파일 확장이 아니라 별도 파일로 추가**
   ```
   seeds/
   ├── seed_canonical_menus.py         # 기존 112개 (수정 금지)
   ├── seed_canonical_menus_ext.py     # 신규 190개+
   └── run_seeds.py                    # 둘 다 실행하도록 수정
   ```

2. **중복 체크 필수**: 기존 112개와 name_ko 중복되는 항목이 있으면 신규 파일에서 제거
3. **concept 연결**: 기존 concepts 테이블에 없는 concept가 필요하면 `seed_concepts.py`에도 추가
4. **영어 설명 품질**: `name_en`에 한국어 로마자 표기 + 영어 설명 포함 (예: "Yukgaejang (Spicy Beef Soup)")
5. **explanation_short 추가**: 결과 카드에 보여줄 1~2문장 문화적 설명 (영문)

#### 검증 기준

```bash
# 시드 실행 후 확인
SELECT COUNT(*) FROM canonical_menus;  -- 300 이상이어야 함
SELECT concept_id, COUNT(*) FROM canonical_menus GROUP BY concept_id;  -- 골고루 분포
```

---

### Task 3A-2: Modifier 사전 확장 (54개 → 80개+)

#### 추가할 수식어 (약 30개)

```python
추가_modifiers = [
    # taste 계열
    {"text_ko": "달콤", "type": "taste", "semantic_key": "sweet", "translation_en": "sweet", "affects_spice": 0},
    {"text_ko": "새콤", "type": "taste", "semantic_key": "sour", "translation_en": "tangy/sour", "affects_spice": 0},
    {"text_ko": "고소", "type": "taste", "semantic_key": "nutty", "translation_en": "nutty/savory", "affects_spice": 0},
    {"text_ko": "담백", "type": "taste", "semantic_key": "light", "translation_en": "light/mild", "affects_spice": 0},
    {"text_ko": "진한", "type": "taste", "semantic_key": "rich", "translation_en": "rich/intense", "affects_spice": 0},
    {"text_ko": "칼칼", "type": "taste", "semantic_key": "peppery", "translation_en": "peppery/hot", "affects_spice": 1},

    # cooking 계열
    {"text_ko": "직화", "type": "cooking", "semantic_key": "direct_fire", "translation_en": "direct-fire grilled"},
    {"text_ko": "장작", "type": "cooking", "semantic_key": "wood_fire", "translation_en": "wood-fired"},
    {"text_ko": "가마솥", "type": "cooking", "semantic_key": "iron_pot", "translation_en": "iron pot cooked"},
    {"text_ko": "수제", "type": "cooking", "semantic_key": "handmade", "translation_en": "handmade/artisan"},
    {"text_ko": "생", "type": "cooking", "semantic_key": "raw", "translation_en": "raw/fresh"},
    {"text_ko": "훈제", "type": "cooking", "semantic_key": "smoked", "translation_en": "smoked"},
    {"text_ko": "저온", "type": "cooking", "semantic_key": "low_temp", "translation_en": "slow-cooked"},

    # origin 계열
    {"text_ko": "제주", "type": "origin", "semantic_key": "jeju", "translation_en": "Jeju-style"},
    {"text_ko": "부산", "type": "origin", "semantic_key": "busan", "translation_en": "Busan-style"},
    {"text_ko": "전주", "type": "origin", "semantic_key": "jeonju", "translation_en": "Jeonju-style"},
    {"text_ko": "강릉", "type": "origin", "semantic_key": "gangneung", "translation_en": "Gangneung-style"},
    {"text_ko": "대구", "type": "origin", "semantic_key": "daegu", "translation_en": "Daegu-style"},
    {"text_ko": "안동", "type": "origin", "semantic_key": "andong", "translation_en": "Andong-style"},
    {"text_ko": "춘천", "type": "origin", "semantic_key": "chuncheon", "translation_en": "Chuncheon-style"},

    # size 계열
    {"text_ko": "미니", "type": "size", "semantic_key": "mini", "translation_en": "mini"},
    {"text_ko": "점보", "type": "size", "semantic_key": "jumbo", "translation_en": "jumbo"},
    {"text_ko": "반", "type": "size", "semantic_key": "half", "translation_en": "half portion"},

    # grade 계열
    {"text_ko": "프리미엄", "type": "grade", "semantic_key": "premium", "translation_en": "premium"},
    {"text_ko": "명품", "type": "grade", "semantic_key": "luxury", "translation_en": "luxury/finest"},
    {"text_ko": "1++", "type": "grade", "semantic_key": "grade_1pp", "translation_en": "highest grade"},
    {"text_ko": "1+", "type": "grade", "semantic_key": "grade_1p", "translation_en": "premium grade"},

    # ingredient 계열 (수식어 분해에서는 제외되지만 정보용)
    {"text_ko": "차돌", "type": "ingredient", "semantic_key": "brisket", "translation_en": "beef brisket"},
    {"text_ko": "곱창", "type": "ingredient", "semantic_key": "intestine", "translation_en": "intestine"},
    {"text_ko": "해물", "type": "ingredient", "semantic_key": "seafood", "translation_en": "seafood"},
]
```

#### 작업 방법

1. **기존 `seed_modifiers.py`에 추가** (기존 54개 뒤에 이어서)
2. 또는 별도 `seed_modifiers_ext.py` 생성
3. **중복 체크**: text_ko 기준으로 기존 목록과 겹치는지 확인

---

### Task 3A-3: 매칭 엔진 개선

#### 현재 문제점 (68% 정확도의 원인)

매칭 엔진 코드: `app/backend/services/matching_engine.py`

**문제 1: similarity 검색에서 길이 제한이 너무 엄격**
```python
# 현재: max_length_diff = 0 (길이 완전 동일만 허용)
# 문제: "된장찌게" (4글자) vs "된장찌개" (4글자) ✅ 통과
#       "뼈해장국" (4글자) vs "뼈 해장국" (5글자) ❌ 실패 (공백 포함)
```

**수정:**
```python
max_length_diff = 1  # 1글자 차이까지 허용
```

**문제 2: modifier_decomposition에서 재귀적 분해 부족**
```python
# 현재: greedy 방식으로 수식어 1개씩 제거하며 매칭 시도
# 문제: "전주비빔밥" → "전주" 제거 → "비빔밥" ✅ (성공)
#       "춘천닭갈비" → "춘천" 제거 → "닭갈비" ✅ (성공, 이건 OK)
#       "부산밀면" → "부산" 제거 → "밀면" → DB에 있으면 ✅
#
# 하지만:
#       "매운갈비찜" → "매운" 제거 → "갈비찜" → DB에 있어야 함
#       만약 DB에 "갈비찜"이 없으면 실패 → DB 커버리지가 핵심
```

**→ DB 확장 (Task 3A-1)이 매칭 정확도 향상의 가장 큰 레버**

**문제 3: 접미사/접두사 패턴 미지원**
```python
# "~정식", "~세트", "~1인분" 등은 수식어가 아니라 접미사
# 현재 처리 불가

# 추가할 것: suffix_patterns
SUFFIX_PATTERNS = [
    "정식", "세트", "셋트", "1인분", "2인분", "1인",
    "한상", "상차림", "(대)", "(중)", "(소)",
    "A세트", "B세트", "스페셜",
]
```

**수정 방향: `_modifier_decomposition` 메서드에 접미사 처리 추가**

```python
async def _modifier_decomposition(self, menu_name: str) -> Optional[MatchResult]:
    # 0. 접미사 제거 (정식, 세트 등)
    cleaned_name, suffix_info = self._strip_suffixes(menu_name)

    # 1. 접미사 제거 후 정확 매칭 시도
    if cleaned_name != menu_name:
        canonical = await self._try_canonical_match(cleaned_name)
        if canonical:
            return MatchResult(...)

    # 2. 기존 수식어 분해 로직 (cleaned_name에 대해)
    ...
```

```python
def _strip_suffixes(self, menu_name: str) -> tuple[str, list]:
    """접미사 패턴 제거"""
    SUFFIX_PATTERNS = [
        "정식", "세트", "셋트", "1인분", "2인분", "3인분",
        "1인", "2인", "3인", "한상", "상차림",
        "(대)", "(중)", "(소)", "스페셜",
    ]
    found_suffixes = []
    cleaned = menu_name

    for suffix in SUFFIX_PATTERNS:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)].strip()
            found_suffixes.append(suffix)

    return cleaned, found_suffixes
```

**문제 4: 정규화(Normalization) 레이어 부재**
```python
# 띄어쓰기, 특수문자, 숫자 처리가 없음
# "김치 찌개" → "김치찌개" 변환 필요
# "삼겹살(200g)" → "삼겹살" 변환 필요
# "1. 김치찌개" → "김치찌개" 변환 필요 (메뉴판 번호)

def _normalize_menu_name(self, menu_name: str) -> str:
    """메뉴명 정규화"""
    import re
    s = menu_name.strip()
    s = re.sub(r'^\d+[\.\)\-\s]+', '', s)  # 메뉴 번호 제거: "1. 김치찌개" → "김치찌개"
    s = re.sub(r'\(.*?\)', '', s)           # 괄호 내용 제거: "삼겹살(200g)" → "삼겹살"
    s = re.sub(r'[\s]+', '', s)             # 모든 공백 제거: "김치 찌개" → "김치찌개"
    s = re.sub(r'[~!@#$%^&*]', '', s)      # 특수문자 제거
    return s.strip()
```

#### 매칭 엔진 수정 요약

| 수정 | 내용 | 예상 정확도 향상 |
|------|------|-----------------|
| 정규화 레이어 추가 | 공백/특수문자/번호 제거 | +5% |
| 길이 제한 완화 | max_length_diff 0 → 1 | +3% |
| 접미사 패턴 | "정식", "세트" 등 제거 | +5% |
| DB 확장 (112→300) | 커버리지 증가 | +10~15% |

**예상 합산: 68% → 85~90%**

#### 수정 파일

```
수정: app/backend/services/matching_engine.py
  - _normalize_menu_name() 추가
  - _strip_suffixes() 추가
  - match_menu()에서 정규화 호출
  - _exact_match()에서 max_length_diff = 1
추가: app/backend/seeds/seed_canonical_menus_ext.py
추가: app/backend/seeds/seed_modifiers_ext.py (또는 기존 파일 확장)
수정: app/backend/seeds/run_seeds.py (신규 시드 포함)
```

---

### Task 3A-4: 검증 테스트 (300개 메뉴 테스트)

#### 테스트 데이터 작성

```python
# app/backend/tests/test_matching_accuracy.py

TEST_CASES = [
    # === 정확 매칭 (50개) ===
    ("김치찌개", "exact", "김치찌개"),
    ("비빔밥", "exact", "비빔밥"),
    ("삼겹살", "exact", "삼겹살"),
    ("육개장", "exact", "육개장"),
    # ... 50개

    # === 오타/유사 매칭 (20개) ===
    ("김치찌게", "similarity", "김치찌개"),
    ("비빔밥", "exact", "비빔밥"),
    ("삼겹살", "exact", "삼겹살"),
    # ... 20개

    # === 수식어 분해 (30개) ===
    ("왕돈까스", "modifier_decomposition", "돈까스"),
    ("매운김치찌개", "modifier_decomposition", "김치찌개"),
    ("전주비빔밥", "modifier_decomposition", "비빔밥"),
    ("춘천닭갈비", "modifier_decomposition", "닭갈비"),
    ("숯불삼겹살", "modifier_decomposition", "삼겹살"),
    ("얼큰순두부찌개", "modifier_decomposition", "순두부찌개"),
    # ... 30개

    # === 접미사 처리 (10개) ===
    ("불고기정식", "modifier_decomposition", "불고기"),  # "정식" 접미사
    ("갈비세트", "modifier_decomposition", "갈비"),
    ("삼겹살1인분", "modifier_decomposition", "삼겹살"),
    # ... 10개

    # === 정규화 (10개) ===
    ("1. 김치찌개", "exact", "김치찌개"),
    ("김치 찌개", "exact", "김치찌개"),
    ("삼겹살(200g)", "exact", "삼겹살"),
    # ... 10개

    # === AI Discovery (10개) — 매칭 실패 정상 ===
    ("알 수 없는 메뉴", "ai_discovery_needed", None),
    # ... 10개
]
```

#### 테스트 실행 및 보고

```python
# pytest로 실행
async def test_matching_accuracy():
    passed = 0
    failed = []

    for input_text, expected_type, expected_canonical in TEST_CASES:
        result = await engine.match_menu(input_text)

        if result.match_type == expected_type:
            if expected_canonical is None or result.canonical["name_ko"] == expected_canonical:
                passed += 1
            else:
                failed.append((input_text, expected_type, result))
        else:
            failed.append((input_text, expected_type, result))

    accuracy = passed / len(TEST_CASES) * 100
    print(f"정확도: {accuracy:.1f}% ({passed}/{len(TEST_CASES)})")

    # 실패 케이스 출력
    for input_text, expected, result in failed:
        print(f"  ❌ {input_text}: expected={expected}, got={result.match_type}")

    assert accuracy >= 80.0, f"정확도 {accuracy}%: 목표 80% 미달"
```

#### 3A 완료 기준

- [ ] canonical_menus 300개 이상
- [ ] modifiers 80개 이상
- [ ] 매칭 정확도 80%+ (테스트 통과)
- [ ] 정규화 레이어 동작 확인
- [ ] 접미사 처리 동작 확인
- [ ] 모든 기존 API 정상 동작 (`/api/v1/menu/identify` 등)
- [ ] 음식 이미지 URL 80%+ 매핑률 달성
- [ ] 프론트엔드 이미지 표시 + 면책 문구 동작 확인

---

### Task 3A-5: 음식 이미지 URL 수집 + 프론트엔드 반영 (✅ 구현 완료)

> PM 지시: "음식사진 정보는 최대한 수집하도록 해줘. 그리고 반영해줘"

#### 이미지 소싱 전략

| 우선순위 | 소스 | 라이선스 | 비고 |
|----------|------|---------|------|
| 1 | Wikimedia Commons | CC BY-SA / CC0 | 무료, 상업적 사용 가능, API 지원 |
| 2 | AI Hub 공공데이터 | 공공누리 | 84만장 한식 이미지 |
| 3 | 크라우드픽 | 상업용 무료 | 보조 소스 |

#### 구현 완료 사항

**1. 이미지 URL 매핑 데이터** (`seeds/image_urls.py`)
- 110여 개 한식 메뉴의 위키미디어 커번즈 이미지 URL 매핑
- URL 패턴: `https://commons.wikimedia.org/wiki/Special:FilePath/{filename}?width=400`
- 카테고리: 국물요리, 찌개, 밥류, 면류, 고기구이, 찜/조림, 전/부침개, 반찬, 분식, 해산물, 치킨, 디저트, 주류 등

**2. 시드 스크립트 업데이트** (`seeds/run_seeds.py`)
- `get_image_url_map()` 함수로 메뉴명 → image_url 매핑
- `CanonicalMenu.image_url` 필드에 자동 저장
- 매핑률 로그 출력: `[OK] Image URLs mapped: N/112 menus`

**3. API 응답 수정**
- `matching_engine.py` → `_canonical_to_dict()`에 `image_url` 필드 추가
- `menu.py` → `/canonical-menus` 엔드포인트에 `image_url` 포함

**4. 프론트엔드 수정**
- `app.js` → `createMenuCard()`에 이미지 표시 로직 추가
  - 카드 상단에 200px 높이 이미지 표시
  - 이미지 로드 실패 시 숨김 처리 (onerror)
  - Wikimedia Commons 출처 표기
- `style.css` → 이미지 컨테이너, 크레딧, 호버 애니메이션 스타일

**5. 면책 문구 (Disclaimer)**
- **카드내**: 알레르기 정보가 있는 경우 "일반 레시피 기준이며 실제 식당과 다를 수 있음" 경고
- **페이지 하단 푸터**: 전체 면책 문구 + 이미지 출처 표기
- 법적 배경: 일반 음식점은 알레르기 표시 의무 없음. 자발적 제공 시 면책 조항 필수.

#### 파일 변경 목록

```
추가  app/backend/seeds/image_urls.py              # 110+ 메뉴 이미지 URL 매핑
수정  app/backend/seeds/run_seeds.py               # image_url 반영
수정  app/backend/services/matching_engine.py       # _canonical_to_dict에 image_url 추가
수정  app/backend/api/menu.py                      # /canonical-menus에 image_url 포함
수정  app/frontend/js/app.js                       # 이미지 표시 + 면책 문구
수정  app/frontend/css/style.css                   # 이미지/면책 스타일
수정  app/frontend/index.html                      # 글로벌 디스클레이머 푸터
```

---

## 🔶 Sprint 3B: OCR 파이프라인 + 사진 업로드

> 예상 소요: 2~3시간
> 선행 조건: Sprint 3A 완료
> 핵심: GPT-4o mini Vision OCR → 매칭 엔진 연동 → 프론트 사진 업로드

### Task 3B-1: OCR 서비스 구현

#### 파일 구조

```
app/backend/services/
├── matching_engine.py      # 기존 (3A에서 개선됨)
├── ocr_service.py          # 신규 ⭐
└── __init__.py
```

#### ocr_service.py 설계

```python
"""
OCR Service - 2-Tier 전략
Tier 1: GPT-4o mini Vision (메인)
Tier 2: CLOVA OCR (fallback, 월 100건 무료)
"""
import base64
import json
import re
from typing import List, Optional, Dict, Any
import httpx

from config import settings


class OCRResult:
    """OCR 결과"""
    def __init__(
        self,
        items: List[Dict[str, Any]],      # 추출된 메뉴 아이템들
        provider: str,                      # "gpt4o_mini" | "clova"
        confidence: float,                  # 전체 신뢰도
        raw_response: Optional[str] = None, # 디버깅용 원본 응답
        needs_fallback: bool = False,       # CLOVA fallback 필요 여부
    ):
        self.items = items
        self.provider = provider
        self.confidence = confidence
        self.raw_response = raw_response
        self.needs_fallback = needs_fallback


class MenuOCRService:
    """메뉴판 OCR 서비스 (2-Tier)"""

    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.clova_api_url = settings.CLOVA_OCR_API_URL
        self.clova_secret_key = settings.CLOVA_OCR_SECRET_KEY

    async def process_menu_image(self, image_data: bytes, filename: str = "menu.jpg") -> OCRResult:
        """
        메뉴판 이미지 → 구조화된 메뉴 데이터
        Tier 1: GPT-4o mini Vision
        Tier 2: CLOVA OCR (fallback)
        """
        # Tier 1: GPT-4o mini Vision
        result = await self._gpt4o_mini_vision(image_data)

        if result and not result.needs_fallback and result.confidence >= 0.7:
            return result

        # Tier 2: CLOVA OCR fallback
        clova_result = await self._clova_ocr(image_data, filename)
        if clova_result:
            return clova_result

        # 둘 다 실패
        return OCRResult(
            items=[],
            provider="none",
            confidence=0.0,
            needs_fallback=True,
        )

    async def _gpt4o_mini_vision(self, image_data: bytes) -> Optional[OCRResult]:
        """Tier 1: GPT-4o mini Vision"""
        base64_image = base64.b64encode(image_data).decode("utf-8")

        prompt = """You are a Korean restaurant menu parser.
Extract ALL menu items from this Korean menu image.

Return ONLY valid JSON (no markdown, no explanation):
{
  "items": [
    {
      "name_ko": "김치찌개",
      "price": 9000,
      "description_ko": "돼지고기 김치찌개",
      "section": "찌개류",
      "confidence": 0.95
    }
  ],
  "metadata": {
    "total_items": 5,
    "currency": "KRW",
    "has_handwriting": false,
    "image_quality": "good",
    "needs_fallback": false
  }
}

Rules:
- price: integer in KRW. "9,000원" → 9000. If unclear → null
- description_ko: if exists on menu. Otherwise → null
- section: menu section header if visible. Otherwise → null
- confidence: 0.0~1.0 per item
- needs_fallback: true if image too blurry/complex to parse reliably
- Handle "소/중/대" → note in description
- Handle "1인분 9,000원" → price per person, note in description
- If multi-column: read left column first, then right"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}",
                                            "detail": "high",
                                        },
                                    },
                                ],
                            }
                        ],
                        "max_tokens": 2000,
                        "temperature": 0,  # 비결정성 최소화
                    },
                )
                response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # JSON 파싱 (마크다운 코드블록 제거)
            content = content.strip()
            if content.startswith("```"):
                content = re.sub(r'^```(?:json)?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)

            parsed = json.loads(content)

            # 가격 검증
            for item in parsed.get("items", []):
                item["price"] = self._validate_price(item.get("price"))

            metadata = parsed.get("metadata", {})

            return OCRResult(
                items=parsed.get("items", []),
                provider="gpt4o_mini",
                confidence=self._calculate_confidence(parsed.get("items", [])),
                raw_response=content,
                needs_fallback=metadata.get("needs_fallback", False),
            )

        except Exception as e:
            print(f"GPT-4o mini Vision error: {e}")
            return None

    async def _clova_ocr(self, image_data: bytes, filename: str) -> Optional[OCRResult]:
        """Tier 2: CLOVA OCR + GPT-4o mini 파싱"""
        # TODO: CLOVA OCR API 연동
        # 1. CLOVA OCR로 텍스트 추출
        # 2. 추출된 텍스트를 GPT-4o mini로 구조화
        # Sprint 3B에서는 placeholder, Sprint 4에서 완성
        return None

    def _validate_price(self, price_raw) -> Optional[int]:
        """가격 검증/보정 — 필수 레이어"""
        if price_raw is None:
            return None

        try:
            price = int(price_raw)
        except (ValueError, TypeError):
            s = str(price_raw).replace(',', '').replace('.', '').replace(' ', '')
            s = s.replace('원', '').replace('₩', '')
            nums = re.findall(r'\d+', s)
            if not nums:
                return None
            price = int(nums[0])

        # 한국 식당 가격 범위 (1,000 ~ 300,000원)
        if price < 1000 or price > 300000:
            return None

        # 100원 단위 체크
        if price % 100 != 0:
            return None

        return price

    def _calculate_confidence(self, items: list) -> float:
        """전체 OCR 신뢰도 계산"""
        if not items:
            return 0.0
        confidences = [item.get("confidence", 0.5) for item in items]
        return sum(confidences) / len(confidences)
```

#### 환경변수 추가

```
# app/backend/.env에 추가
OPENAI_API_KEY=sk-...
CLOVA_OCR_API_URL=https://...   # 기존
CLOVA_OCR_SECRET_KEY=...        # 기존
```

#### config.py 수정

```python
# 기존 설정에 추가
class Settings:
    ...
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
```

---

### Task 3B-2: OCR → 매칭 엔진 연결 API

#### 새 API 엔드포인트

```python
# app/backend/api/menu.py에 추가

from fastapi import UploadFile, File

@router.post("/menu/scan")
async def scan_menu_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    메뉴판 사진 스캔 API
    1. OCR로 메뉴 항목 추출
    2. 각 메뉴를 매칭 엔진으로 식별
    3. 결합된 결과 반환
    """
    # 파일 검증
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        return {"error": "Supported formats: JPEG, PNG, WebP"}

    if file.size > 10 * 1024 * 1024:  # 10MB 제한
        return {"error": "File too large. Max 10MB"}

    image_data = await file.read()

    # 1. OCR 처리
    ocr_service = MenuOCRService()
    ocr_result = await ocr_service.process_menu_image(image_data, file.filename)

    if not ocr_result.items:
        return {
            "success": False,
            "error": "Could not read menu items from image",
            "ocr_provider": ocr_result.provider,
        }

    # 2. 각 메뉴를 매칭 엔진으로 식별
    engine = MenuMatchingEngine(db)
    results = []

    for item in ocr_result.items:
        name_ko = item.get("name_ko", "")
        if not name_ko:
            continue

        match_result = await engine.match_menu(name_ko)

        results.append({
            "ocr": {
                "name_ko": name_ko,
                "price": item.get("price"),
                "section": item.get("section"),
                "ocr_confidence": item.get("confidence", 0),
            },
            "match": match_result.to_dict(),
        })

    return {
        "success": True,
        "total_items": len(results),
        "ocr_provider": ocr_result.provider,
        "ocr_confidence": ocr_result.confidence,
        "items": results,
    }
```

---

### Task 3B-3: 프론트엔드 사진 업로드 활성화

#### index.html 수정

```html
<!-- 기존: disabled 제거 -->
<div class="photo-upload">
    <input type="file" id="photoInput" accept="image/*" capture="environment" hidden>
    <button class="photo-btn" id="photoBtn">
        📷 Scan Menu Photo
    </button>
    <p class="photo-hint">Take a photo or upload from gallery</p>
</div>
```

#### app.js 수정/추가

```javascript
// 사진 업로드 기능 추가
DOM.photoBtn = document.getElementById('photoBtn');
DOM.photoInput = document.getElementById('photoInput');

DOM.photoBtn.addEventListener('click', () => {
    DOM.photoInput.click();
});

DOM.photoInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // 파일 크기 체크 (10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('Image too large. Max 10MB.');
        return;
    }

    // 로딩 표시
    showLoading();

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${CONFIG.API_BASE_URL}/api/v1/menu/scan`, {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (data.success) {
            displayScanResults(data);
        } else {
            alert(data.error || 'Failed to scan menu');
        }
    } catch (error) {
        console.error('Scan error:', error);
        alert('Failed to connect to server');
    } finally {
        hideLoading();
        DOM.photoInput.value = ''; // 리셋
    }
});

function displayScanResults(data) {
    // 스캔 결과를 결과 카드로 표시
    // 기존 displayResults 함수를 재활용하되,
    // 가격 정보와 OCR 신뢰도를 추가 표시
    const results = data.items.map(item => ({
        ...item.match,
        price: item.ocr.price,
        ocr_confidence: item.ocr.ocr_confidence,
    }));

    // 기존 결과 화면으로 전환
    showResults(results);
}
```

#### CSS 수정

```css
/* 기존 .photo-upload.disabled 스타일 제거 */
/* 활성 상태 스타일 추가 */
.photo-btn {
    /* 기존 disabled 스타일 → 활성 스타일로 변경 */
    background: var(--primary-color);
    color: white;
    cursor: pointer;
    opacity: 1;
}

/* 스캔 결과 가격 표시 */
.menu-price {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--primary-color);
}
```

---

### Task 3B-4: 통합 테스트

#### 수동 테스트 시나리오

| # | 시나리오 | 검증 |
|---|---------|------|
| 1 | 인쇄체 메뉴판 사진 업로드 | OCR 추출 → 매칭 결과 표시 |
| 2 | 여러 메뉴 포함 사진 | 다수 메뉴 카드 표시 |
| 3 | 가격 포함 메뉴판 | 가격 정보 표시 |
| 4 | 흐릿한/저화질 사진 | 적절한 에러 메시지 |
| 5 | 10MB 초과 사진 | 파일 크기 경고 |
| 6 | 텍스트 검색 기존 기능 | 기존 기능 정상 동작 확인 |

#### 3B 완료 기준

- [ ] `POST /api/v1/menu/scan` 동작
- [ ] GPT-4o mini Vision으로 메뉴판 텍스트 추출
- [ ] 추출된 메뉴가 매칭 엔진을 통과해 결과 반환
- [ ] 가격 후처리 검증 동작
- [ ] 프론트에서 사진 촬영/업로드 → 결과 표시
- [ ] 기존 텍스트 검색 기능 정상 유지

---

## 📁 파일 변경 총정리

### Sprint 3A (신규/수정)

```
수정  app/backend/services/matching_engine.py     # 정규화, 접미사, 길이제한 개선
추가  app/backend/seeds/seed_canonical_menus_ext.py # 190개+ 신규 메뉴
수정  app/backend/seeds/seed_modifiers.py          # 30개+ 수식어 추가 (또는 별도 파일)
수정  app/backend/seeds/run_seeds.py               # 신규 시드 포함
추가  app/backend/tests/test_matching_accuracy.py  # 정확도 테스트
```

### Sprint 3B (신규/수정)

```
추가  app/backend/services/ocr_service.py          # OCR 2-Tier 서비스
수정  app/backend/api/menu.py                      # /menu/scan 엔드포인트 추가
수정  app/backend/config.py                        # OPENAI_API_KEY 추가
수정  app/backend/.env                             # API 키 추가
수정  app/frontend/index.html                      # 사진 업로드 활성화
수정  app/frontend/js/app.js                       # 사진 업로드 로직 추가
수정  app/frontend/css/style.css                   # 활성 버튼 스타일
```

---

## ⚠️ 주의사항

1. **Sprint 3A를 반드시 먼저 완료**한 후 3B 진행. DB 커버리지가 부족하면 OCR이 아무리 좋아도 결과가 나쁨
2. **기존 코드 깨뜨리지 말 것**: 기존 `/api/v1/menu/identify` 텍스트 검색은 그대로 동작해야 함
3. **시드 데이터 품질**: 영어 설명은 관광객이 이해할 수 있는 자연스러운 표현 사용
4. **.env 파일에 OPENAI_API_KEY 추가 필수** (Sprint 3B 시작 전 확인)
5. **커밋 단위**: 3A 완료 → 커밋 → 3B 완료 → 커밋 (각각 별도 커밋)

---

## 📊 성공 지표

| 지표 | Sprint 2 | Sprint 3 목표 |
|------|----------|--------------|
| Canonical 메뉴 | 112개 | **300개+** |
| Modifiers | 54개 | **80개+** |
| 매칭 정확도 | 68% | **80%+** |
| OCR 파이프라인 | ❌ | **✅ GPT-4o mini Vision** |
| 사진 업로드 | Coming Soon | **✅ 동작** |
| API 엔드포인트 | 4개 | **5개** (+/menu/scan) |
