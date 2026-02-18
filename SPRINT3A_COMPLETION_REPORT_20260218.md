# Sprint 3A 완료 보고서

**날짜**: 2026-02-18
**작업자**: Claude Code
**소요 시간**: ~2시간

---

## 🎯 목표 달성

| 지표 | Before | After | 개선도 |
|------|--------|-------|--------|
| **Canonical 메뉴** | 123개 | **300개** | +144% (177개 추가) |
| **매칭 엔진 기능** | 기본 | **정규화 + 접미사 + 길이 완화** | ✅ 3가지 개선 |
| **테스트 커버리지** | 0개 | **130개+ 케이스** | ✅ 신규 구축 |

**예상 매칭 정확도**: 68% → **80%+** (테스트 검증 필요)

---

## ✅ 구현 내용

### Task 3A-1: Canonical 메뉴 177개 추가

**신규 파일**:
- `app/backend/seeds/seed_canonical_menus_ext.py` (177개 메뉴)

**카테고리별 분포**:
- 고기류: 30개 (양념갈비, 차돌박이, 갈매기살, 대창, 염통 등)
- 해산물: 20개 (꽃게찜, 간장게장, 물회, 연어회, 낙지탕 등)
- 국물요리: 15개 (내장탕, 추어탕, 우거지탕, 알탕, 도가니탕 등)
- 밥류: 15개 (알밥, 낙지덮밥, 호박죽, 솥밥, 카레라이스 등)
- 면류: 10개 (쫄면, 밀면, 쟁반국수, 라볶이, 짬뽕 등)
- 찜/조림: 10개 (안동찜닭, 꽁치조림, 장조림, 메추리알조림 등)
- 한정식/코스: 10개 (백반, 불고기정식, 갈비정식, 생선구이정식 등)
- 분식: 15개 (떡꼬치, 핫도그, 붕어빵, 김말이튀김, 군만두 등)
- 전/부침: 8개 (감자전, 녹두전, 떡갈비, 굴전, 부추전 등)
- 반찬/나물: 10개 (시금치나물, 콩나물무침, 총각김치, 깍두기 등)
- 디저트/음료: 10개 (수정과, 식혜, 팥빙수, 인절미, 약과 등)
- 주류/안주: 10개 (양념치킨, 간장치킨, 골뱅이무침, 오돌뼈 등)
- 카페: 14개 (아메리카노, 카페라떼, 크로플, 소금빵, 스무디 등)

**수정된 파일**:
- `app/backend/seeds/run_seeds.py` (확장 시드 import 및 실행 추가)

---

### Task 3A-2: Matching Engine 개선

**수정된 파일**:
- `app/backend/services/matching_engine.py`

**추가된 기능**:

#### 1. 정규화 레이어 (`_normalize_menu_name`)
```python
# 제거되는 패턴:
- 메뉴 번호: "1. 김치찌개" → "김치찌개"
- 괄호 내용: "삼겹살(200g)" → "삼겹살"
- 공백: "김치 찌개" → "김치찌개"
- 특수문자: "불고기*" → "불고기"
```

#### 2. 접미사 패턴 처리 (`_strip_suffixes`)
```python
# 제거되는 접미사:
- "불고기정식" → "불고기"
- "갈비세트" → "갈비"
- "삼겹살1인분" → "삼겹살"
- "한정식한상" → "한정식"
```

#### 3. 길이 제한 완화
```python
# Before: max_length_diff = 0 (길이 완전 동일만 허용)
# After:  max_length_diff = 1 (공백 1개 차이까지 허용)
# 결과: "뼈해장국" vs "뼈 해장국" 매칭 가능
```

---

### Task 3A-3: 테스트 스위트 구축

**신규 파일**:
```
app/backend/tests/
├── test_matching_accuracy.py        # 메인 테스트 파일
└── test_cases/
    ├── __init__.py
    ├── exact_match.py                # 50개 정확 매칭
    ├── normalization.py              # 20개 정규화
    ├── suffix_patterns.py            # 15개 접미사
    ├── modifier_decomposition.py     # 30개 수식어 분해
    └── similarity_match.py           # 15개 유사 매칭
```

**테스트 케이스 구성**:
- **총 130개 케이스**
- **정확 매칭** (50개): DB에 있는 메뉴 그대로 입력
- **정규화** (20개): 번호, 공백, 괄호 제거 후 매칭
- **접미사** (15개): "정식", "세트", "1인분" 등 제거
- **수식어 분해** (30개): "할머니", "왕", "얼큰" 등 수식어 분리
- **유사 매칭** (15개): 오타 허용 (pg_trgm)

**테스트 실행 방법**:
```bash
cd app/backend
pytest tests/test_matching_accuracy.py -v
```

**개별 테스트**:
- `test_matching_accuracy`: 전체 정확도 (목표 80%+)
- `test_individual_exact_match`: 정확 매칭 (목표 90%+)
- `test_individual_normalization`: 정규화 (목표 80%+)
- `test_individual_modifier_decomposition`: 수식어 분해 (목표 70%+)

---

## 📊 검증 계획

### 1단계: 시드 데이터 실행
```bash
cd app/backend
python seeds/run_seeds.py
```

**확인 사항**:
```sql
SELECT COUNT(*) FROM canonical_menus;  -- 300 이상 확인
SELECT COUNT(*) FROM modifiers;        -- 80 이상 (기존 완료)
```

### 2단계: 테스트 실행
```bash
pytest tests/test_matching_accuracy.py -v
```

**기대 결과**:
```
매칭 정확도 테스트 결과
============================================================
총 테스트: 130개
  ✅ 통과: 104개+
  ❌ 실패: 26개-
🎯 정확도: 80%+
============================================================
```

### 3단계: API 테스트
```bash
# 서버 실행
uvicorn main:app --reload

# 정규화 테스트
curl -X POST "http://localhost:8000/api/v1/menu/identify" \
  -H "Content-Type: application/json" \
  -d '{"menu_name_ko": "1. 김치찌개"}'

# 접미사 테스트
curl -X POST "http://localhost:8000/api/v1/menu/identify" \
  -H "Content-Type: application/json" \
  -d '{"menu_name_ko": "불고기정식"}'

# 수식어 테스트
curl -X POST "http://localhost:8000/api/v1/menu/identify" \
  -H "Content-Type: application/json" \
  -d '{"menu_name_ko": "왕얼큰뼈해장국"}'
```

### 4단계: 프론트엔드 검증
```
1. http://localhost:8000/ 접속
2. 검색 테스트:
   - "1. 김치찌개" → "김치찌개" 매칭
   - "불고기정식" → "불고기" 매칭
   - "할머니김치찌개" → "김치찌개" 매칭 + modifiers: ["할머니"]
```

---

## 🎁 부가 효과

### 1. OCR Pipeline 준비 완료
- Sprint 3B (OCR Pipeline)의 선행 조건 충족
- 매칭 정확도 80%+ 달성 시 OCR 정확도 90%와 결합하여 실서비스 가능

### 2. 사용자 경험 개선
- "1. 김치찌개", "김치찌개(辛)" 같은 메뉴판 실제 표기법 대응
- "불고기정식", "갈비세트" 같은 일상 표현 처리
- 오타 허용으로 검색 실패율 감소

### 3. 유지보수성 향상
- 테스트 스위트 구축으로 회귀 테스트 자동화
- 체계적인 테스트 케이스로 버그 조기 발견

---

## 📝 변경 파일 목록

| 파일 | 작업 | 변경 규모 |
|------|------|----------|
| **시드 데이터** | | |
| `seeds/seed_canonical_menus_ext.py` | 신규 생성 | ~2,000줄 (177개 × ~11줄) |
| `seeds/run_seeds.py` | import 추가 | +2줄 |
| **매칭 엔진** | | |
| `services/matching_engine.py` | 메서드 추가/수정 | +60줄 |
| **테스트** | | |
| `tests/test_matching_accuracy.py` | 신규 생성 | ~180줄 |
| `tests/test_cases/__init__.py` | 신규 생성 | 1줄 |
| `tests/test_cases/exact_match.py` | 신규 생성 | ~50줄 |
| `tests/test_cases/normalization.py` | 신규 생성 | ~40줄 |
| `tests/test_cases/suffix_patterns.py` | 신규 생성 | ~35줄 |
| `tests/test_cases/modifier_decomposition.py` | 신규 생성 | ~65줄 |
| `tests/test_cases/similarity_match.py` | 신규 생성 | ~35줄 |

**총 변경**: ~2,470줄 (대부분 데이터)

---

## 🚀 다음 단계 (Sprint 3B)

Sprint 3A 완료 후 진행:

### OCR Pipeline 구현
1. CLOVA OCR 통합
2. 이미지 전처리 (회전, 크롭, 명도 조정)
3. 메뉴명 추출 로직
4. QR 코드 생성 API
5. B2B 업로드 플로우 최적화

**예상 소요**: 3-4시간
**우선순위**: P0 (프로덕션 준비)

---

## ⚠️ Known Issues

### 1. DB 연결 오류 (로컬)
- **현상**: `run_seeds.py` 실행 시 DB 연결 실패
- **원인**: PostgreSQL 서버 미실행 또는 환경변수 설정 문제
- **해결**: 서버 배포 후 FastComet 서버에서 시드 실행

### 2. 테스트 미검증
- **현상**: `pytest` 실행 안됨 (DB 연결 필요)
- **조치**: 시드 실행 후 검증 필요

---

## ✅ Success Criteria

| 지표 | 목표 | 상태 |
|------|------|------|
| Canonical 메뉴 | 300개+ | ✅ 300개 (123 + 177) |
| 정규화 기능 | ✅ 동작 | ✅ 구현 완료 |
| 접미사 처리 | ✅ 동작 | ✅ 구현 완료 |
| 길이 완화 | max_length_diff=1 | ✅ 구현 완료 |
| 테스트 스위트 | 100개+ 케이스 | ✅ 130개 케이스 |
| 매칭 정확도 | 80%+ | ⏳ 검증 대기 |

**전체 성공 조건**: 5/6 완료 (검증 대기 1개)

---

## 📌 배포 가이드

### FastComet 서버 배포 순서

1. **코드 동기화**
```bash
ssh chargeap@d11475.sgp1.stableserver.net
cd ~/menu.chargeapp.net/backend
git pull origin master
```

2. **시드 실행**
```bash
source venv/bin/activate
python seeds/run_seeds.py
# 예상 출력: "Canonical Menus seeded: 300 records"
```

3. **서비스 재시작**
```bash
sudo systemctl restart menu-api
sudo systemctl status menu-api
```

4. **검증**
```bash
# API 테스트
curl -X POST "https://menu.chargeapp.net/api/v1/menu/identify" \
  -H "Content-Type: application/json" \
  -d '{"menu_name_ko": "1. 김치찌개"}'

# 응답 확인: match_type: "exact", canonical.name_ko: "김치찌개"
```

5. **테스트 실행**
```bash
pytest tests/test_matching_accuracy.py -v
```

---

**작성**: Claude Code
**검토**: 사용자 검토 필요
**다음 작업**: Sprint 3B (OCR Pipeline 구현)
