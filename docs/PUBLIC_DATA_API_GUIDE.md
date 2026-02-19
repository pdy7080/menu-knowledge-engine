# 공공데이터 API 연동 가이드

> Menu Knowledge Engine의 공공데이터 연동 전체 가이드.
> API 신청부터 데이터 수집, 영양정보 매핑, 향후 확장까지 다룬다.

---

## 목차

1. [포털 개요 및 인증 체계](#1-포털-개요-및-인증-체계)
2. [data.go.kr 사용법 (식품영양성분DB)](#2-datagoKr-사용법)
3. [data.ex.co.kr 사용법 (고속도로 휴게소)](#3-dataexcokr-사용법)
4. [스크립트 실행 가이드](#4-스크립트-실행-가이드)
5. [검색어 매칭 최적화 전략](#5-검색어-매칭-최적화-전략)
6. [데이터 업데이트 절차](#6-데이터-업데이트-절차)
7. [콘텐츠 활용 방안](#7-콘텐츠-활용-방안)
8. [트러블슈팅](#8-트러블슈팅)
9. [참고 자료](#9-참고-자료)

---

## 1. 포털 개요 및 인증 체계

### 두 포털은 완전히 별개 시스템

| 항목 | data.go.kr (공공데이터포털) | data.ex.co.kr (한국도로공사) |
|------|---------------------------|---------------------------|
| **URL** | https://www.data.go.kr | https://data.ex.co.kr |
| **회원가입** | 별도 가입 필요 | 별도 가입 필요 |
| **인증키 형태** | 64자 hex 문자열 | 10자리 숫자 |
| **인증 파라미터** | `serviceKey` | `key` |
| **키 전파 시간** | 승인 후 **1~2시간** | 즉시 |
| **일일 트래픽** | 10,000건 (기본) | 제한 없음 (관측) |
| **데이터 유형** | API + 파일 다운로드 혼재 | API 전용 |
| **응답 형식** | JSON / XML (기본 XML) | JSON |

### 핵심 인사이트

```
⚠️ data.go.kr은 "포털"이지 API 제공자가 아니다.
   각 기관(식약처, 통계청 등)의 API를 중개하는 구조.
   → 기관마다 API 스펙, 응답 형식, 파라미터명이 다르다!
   → 같은 포털이라도 API별로 개별 신청이 필요하다.

⚠️ data.go.kr의 "일반 인증키"는 Encoding/Decoding 두 가지가 있다.
   - Encoding: URL 인코딩된 버전 (브라우저 주소창에 직접 넣을 때)
   - Decoding: 원본 키 (httpx/requests 등 라이브러리 사용 시)
   → Python httpx 사용 시 Decoding 키를 params에 넣으면 자동 인코딩됨
```

### .env 설정

```bash
# .env 파일 (app/backend/.env)

# 한국도로공사 API (data.ex.co.kr)
PUBLIC_DATA_API_KEY=4560754202

# 공공데이터포털 API (data.go.kr) - 별도 발급!
DATA_GO_KR_API_KEY=eb6b8ea961fb0c4f35785e2b37910f9fc1035244704b6e786fe3f979a8c49fb1
```

---

## 2. data.go.kr 사용법

### 2-1. API 활용 신청 절차

#### Step 1: 회원가입 및 로그인
1. https://www.data.go.kr 접속
2. 우측 상단 "회원가입" → 본인인증 완료
3. 로그인

#### Step 2: API 검색 및 신청
1. 검색창에 **"식품영양성분"** 입력
2. **"식품의약품안전처_식품영양성분DB정보"** (데이터번호: 15127578) 선택
3. **"활용신청"** 버튼 클릭
4. 활용 목적 입력 (예: "메뉴 지식 엔진 개발용 영양정보 조회")
5. 신청 완료

#### Step 3: 인증키 확인
1. 우측 상단 "마이페이지" → **"Open API"** → **"인증키 발급현황"**
2. 해당 API의 **"일반 인증키(Decoding)"** 값을 복사
3. `.env` 파일의 `DATA_GO_KR_API_KEY`에 붙여넣기

```
⚠️ 주의: "처리상태"가 "승인"이어도 키 전파에 1~2시간 소요!
   승인 직후 API 호출하면 HTTP 401 반환됨.
   → 1~2시간 후 재시도하면 정상 작동
```

#### Step 4: API 미리보기로 테스트
1. API 상세 페이지 (https://www.data.go.kr/data/15127578/openapi.do) 접속
2. 하단 **"미리보기"** 섹션에서 파라미터 입력:
   - `serviceKey`: (자동 입력됨)
   - `pageNo`: 1
   - `numOfRows`: 3
   - `type`: json
   - `FOOD_NM_KR`: 김치찌개
3. **"미리보기"** 버튼 클릭 → JSON 응답 확인
4. 미리보기가 동작하면 키가 활성화된 것

### 2-2. 식품영양성분DB API 상세

#### 엔드포인트
```
GET https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02
```

#### 요청 파라미터

| 파라미터 | 필수 | 타입 | 설명 | 예시 |
|---------|------|------|------|------|
| `serviceKey` | O | string | 인증키 (Decoding 값) | `eb6b8ea9...` |
| `pageNo` | O | int | 페이지 번호 | `1` |
| `numOfRows` | O | int | 페이지당 결과 수 | `5` |
| `type` | X | string | 응답 형식 (기본: xml) | `json` |
| `FOOD_NM_KR` | X | string | 음식명 (한글) | `김치찌개` |
| `FOOD_CAT1_NM` | X | string | 식품 대분류 | `찌개 및 전골류` |
| `DB_CLASS_NM` | X | string | DB 분류 | `품목대표` |

#### 응답 구조 (JSON)

```json
{
  "header": {
    "resultCode": "00",
    "resultMsg": "NORMAL SERVICE."
  },
  "body": {
    "totalCount": 326,
    "items": [
      {
        "FOOD_NM_KR": "김치찌개_돼지고기",
        "FOOD_CD": "D000006",
        "FOOD_CAT1_NM": "찌개 및 전골류",
        "FOOD_CAT2_NM": "해당없음(찌개 및 전골류)",
        "SERVING_SIZE": "100g",
        "AMT_NUM1": "45.00",
        "AMT_NUM3": "4.25",
        "AMT_NUM4": "1.50",
        "AMT_NUM7": "4.40",
        ...
      }
    ]
  }
}
```

#### 영양소 필드 매핑

| API 필드 | 영양소 | 단위 | 활용도 |
|----------|--------|------|--------|
| `AMT_NUM1` | 에너지 (kcal) | kcal | **핵심** - 칼로리 표시 |
| `AMT_NUM2` | 수분 | g | 참고용 |
| `AMT_NUM3` | 단백질 | g | **핵심** - 영양 밸런스 |
| `AMT_NUM4` | 지방 | g | **핵심** - 영양 밸런스 |
| `AMT_NUM5` | 회분 | g | 참고용 |
| `AMT_NUM7` | 탄수화물 | g | **핵심** - 영양 밸런스 |
| `AMT_NUM8` | 식이섬유 | g | 건강 정보 |
| `AMT_NUM9` | 칼슘 | mg | 미네랄 |
| `AMT_NUM10` | 철분 | mg | 미네랄 |
| `AMT_NUM11` | 인 | mg | 미네랄 |
| `AMT_NUM13` | 나트륨 | mg | **중요** - 건강 경고 |
| `AMT_NUM14` | 칼륨 | mg | 미네랄 |
| `AMT_NUM15` | 비타민 A | μg | 비타민 |
| `AMT_NUM18` | 비타민 C | mg | 비타민 |
| `AMT_NUM24` | 콜레스테롤 | mg | 건강 정보 |
| `AMT_NUM25` | 포화지방 | g | 건강 정보 |

> **참고**: `SERVING_SIZE`는 보통 `100g` 기준. 1인분 환산 시 별도 계산 필요.

#### 주요 카테고리 (FOOD_CAT1_NM)

우리 169개 메뉴 매핑 결과 기준:

| 카테고리 | 메뉴 수 | 대표 메뉴 |
|---------|---------|----------|
| 면류 | 30 | 우동, 라면, 짜장면 |
| 즉석식품류 | 26 | 라면(봉지), 냉동식품 |
| 면 및 만두류 | 21 | 만두, 칼국수, 냉면 |
| 식육가공품 및 포장육 | 21 | 돈가스, 핫도그, 소시지 |
| 찌개 및 전골류 | 10 | 김치찌개, 된장찌개, 순두부찌개 |
| 밥류 | 10 | 비빔밥, 볶음밥, 덮밥 |
| 국 및 탕류 | 8 | 갈비탕, 설렁탕, 해장국 |
| 튀김류 | 8 | 돈가스, 튀김 |
| 과자류·빵류 또는 떡류 | 8 | 호두과자, 츄러스 |
| 구이류 | 3 | 고등어구이, 삼겹살구이 |

---

## 3. data.ex.co.kr 사용법

### 3-1. API 키 발급

1. https://data.ex.co.kr 접속
2. 회원가입 → 로그인
3. "마이페이지" → API 키 확인 (10자리 숫자)
4. `.env`의 `PUBLIC_DATA_API_KEY`에 입력

### 3-2. 고속도로 휴게소 음식 API

#### 엔드포인트
```
GET https://data.ex.co.kr/openapi/restinfo/restBestfoodList
```

#### 요청 파라미터

| 파라미터 | 필수 | 타입 | 설명 |
|---------|------|------|------|
| `key` | O | string | API 인증키 |
| `type` | O | string | `json` |
| `numOfRows` | X | int | 결과 수 (기본 10, 최대 99999) |
| `pageNo` | X | int | 페이지 번호 |
| `foodNm` | X | string | 음식명 검색 |

#### 응답 필드

| 필드 | 설명 | 활용 |
|------|------|------|
| `foodNm` | 음식명 | canonical 메뉴 후보 |
| `foodCost` | 가격 (원) | 평균 가격 산출 |
| `stdRestNm` | 휴게소명 | 출처 정보 |
| `routeNm` | 노선명 | 지역 분포 |
| `bestfoodyn` | 대표음식 Y/N | 인기도 판단 |
| `recommendyn` | 추천음식 Y/N | 인기도 판단 |

### 3-3. 수집 데이터 규모

```
총 수집: 7,009건
고유 메뉴: 3,469개
휴게소 수: 238개
노선 수: 35개
canonical 후보: 169개 (정규화 후)
```

---

## 4. 스크립트 실행 가이드

### 실행 순서

```bash
cd c:\project\menu\app\backend

# Step 1: 고속도로 데이터 수집 (data.ex.co.kr)
python scripts/collect_highway_food_data.py

# Step 2: canonical 시드 데이터 생성 (169개 메뉴)
python scripts/generate_canonical_seed.py

# Step 3: 영양정보 매핑 (data.go.kr)
python scripts/enrich_canonical_nutrition.py

# Step 3-1: 실패 메뉴만 재시도
python scripts/enrich_canonical_nutrition.py --retry-failed
```

### 스크립트 상세

#### collect_highway_food_data.py
```bash
# 전체 수집 (7,009건)
python scripts/collect_highway_food_data.py

# 출력 파일:
#   data/highway_food_raw.json              → 원본 데이터 (7,009건)
#   data/highway_food_canonical_candidates.json → 정규화 후보
#   data/highway_food_unique_names.json     → 고유 메뉴명 목록
```

#### generate_canonical_seed.py
```bash
# canonical 시드 생성
python scripts/generate_canonical_seed.py

# 출력 파일:
#   data/canonical_seed_data.json           → JSON 시드 (169개)
#   migrations/sprint0_seed_canonical_menus.sql → INSERT SQL
```

#### enrich_canonical_nutrition.py
```bash
# 전체 실행 (169개)
python scripts/enrich_canonical_nutrition.py

# 테스트 (저장 안함)
python scripts/enrich_canonical_nutrition.py --dry-run --limit 5

# 10개만 처리
python scripts/enrich_canonical_nutrition.py --limit 10

# 실패 메뉴만 재시도 (기존 성공 데이터 유지)
python scripts/enrich_canonical_nutrition.py --retry-failed

# 출력 파일:
#   data/canonical_seed_enriched.json       → 영양정보 포함 시드
#   migrations/sprint0_update_nutrition.sql → UPDATE SQL (166건)
```

### API 호출량 계산

```
169개 메뉴 × (1차 직접검색 + 평균 1.5회 변형검색) ≈ 420회 호출
재시도(40개) × 평균 3회 변형검색 ≈ 120회 추가
─────────────────────────────────────────
총: ~540회 / 일일 한도 10,000회

→ 하루에 전체 재실행 약 18회 가능
→ Rate limiting: 0.3초 간격 (시간당 ~12,000건 속도 제한)
```

---

## 5. 검색어 매칭 최적화 전략

### 다단계 검색 (search_nutrition 함수)

```
1단계: 직접 검색         "콩나물황태해장국" → ✗
2단계: 공백 제거          (이미 제거됨)
3단계: 변형 검색어 생성
  ├─ 브랜드/상호명 제거    "남산치즈돈까스" → "치즈돈까스" → ✓
  ├─ 정식/세트 제거       "해장라면정식" → "해장라면" → ✓
  ├─ 수식어 제거          "콩나물황태해장국" → "황태해장국" → ✓
  └─ 핵심 음식명 추출     "꼬치어묵우동" → "우동" → ✓
```

### 실패 패턴 및 대응

| 패턴 | 예시 | 대응 전략 | 결과 |
|------|------|----------|------|
| **브랜드명 포함** | 남산치즈돈까스 | 브랜드 prefix 제거 | ✓ |
| **정식/세트** | 돈가스우동정식 | suffix 제거 | △ (복합은 실패) |
| **복합 수식어** | 콩나물황태해장국 | 수식어 순차 제거 | ✓ |
| **복합 메뉴** | 꼬치어묵우동 | 핵심 음식명 추출 | ✓ |
| **공백 포함** | 흑돼지 김치찌개 | 공백 제거 후 재검색 | ✓ |
| **특수문자** | 치즈돈가스+사이다세트 | '+' 기준 분리 | ✓ |
| **오타/변형** | 꼬지어묵우동 (꼬치) | mod_prefixes에 추가 | ✓ |

### 수식어 사전 (현재 등록)

```python
# 브랜드/상호명 (brand_prefixes)
["남산", "바우네", "새집", "이해윤", "샘밭", "농심", "놀부",
 "명동", "부산", "전주", "전복", "도깨비", "마포", "강남",
 "경양식", "실속", "몽글", "그냥", "어린이", "미니", "수제"]

# 일반 수식어 (mod_prefixes)
["왕", "특", "대", "매운", "얼큰", "해물", "치즈", "새우", "야채",
 "등심", "돌솥", "뚝배기", "숯불", "차돌", "통", "옛날", "흑돼지",
 "한우", "돈육", "소고기", "돼지고기", "콩나물", "당면", "계란",
 "햄", "모듬", "가락", "꼬치", "꼬지"]

# 핵심 음식명 (food_suffixes) - 길이 역순 정렬
["순두부찌개", "김치찌개", "된장찌개", "부대찌개",  # 4글자
 "해장국", "추어탕", "설렁탕", "갈비탕", "미역국",  # 3글자
 "볶음밥", "비빔밥", "막국수", "칼국수",
 "우동", "라면", "찌개", "국밥", "덮밥",            # 2글자
 "짬뽕", "냉면", "돈가스", "돈까스", "김밥",
 "핫도그", "불고기", "만두", "구이", "볶음", "탕"]
```

### 매칭률 추이

```
1차 실행 (직접 + 단순 수식어 제거): 129/169 = 76.3%
2차 실행 (다단계 fallback):          +37건 추가
─────────────────────────────────────────
최종: 166/169 = 98.2%

미매칭 3개: 떡만두라면정식, 돈가스우동정식, 순두부짬뽕밥
→ 복합메뉴+정식 조합. API DB에 해당 조합 자체가 없음
→ 구성 메뉴를 분리하여 개별 영양정보 합산하는 방식 고려 (Sprint 1)
```

---

## 6. 데이터 업데이트 절차

### 6-1. canonical 메뉴 추가 시

새로운 메뉴를 canonical에 추가하고 영양정보를 매핑하는 절차:

```bash
# 1. canonical_seed_data.json에 새 메뉴 추가
# 또는 collect_highway_food_data.py 재실행 후 generate_canonical_seed.py

# 2. 영양정보 매핑
python scripts/enrich_canonical_nutrition.py
# → canonical_seed_enriched.json 갱신
# → sprint0_update_nutrition.sql 갱신

# 3. DB 적용
psql -U menu_admin -d menu_knowledge_db -f migrations/sprint0_update_nutrition.sql
```

### 6-2. 영양정보 DB 업데이트 확인

식약처 영양성분DB는 분기/반기별 업데이트됨. 갱신 확인:

```bash
# data.go.kr API 페이지에서 "수정일자" 확인
# https://www.data.go.kr/data/15127578/openapi.do

# 전체 재매핑 (기존 데이터 덮어씌움)
python scripts/enrich_canonical_nutrition.py

# 또는 실패 메뉴만 재시도 (신규 데이터로 추가 매칭 가능)
python scripts/enrich_canonical_nutrition.py --retry-failed
```

### 6-3. API 키 갱신

```
data.go.kr 키 유효기간: 2년 (현재 2026-02-19 ~ 2028-02-19)
data.ex.co.kr 키: 별도 확인 필요

갱신 절차:
1. data.go.kr → 마이페이지 → 인증키 발급현황 → 키 재발급
2. .env 파일의 DATA_GO_KR_API_KEY 업데이트
3. 1~2시간 대기 후 테스트
   python scripts/test_data_go_kr_correct.py
```

---

## 7. 콘텐츠 활용 방안

### 7-1. 외국인 메뉴 이해도 향상

현재 확보된 영양정보를 활용한 콘텐츠:

#### 칼로리 표시
```json
{
  "name_ko": "김치찌개",
  "name_en": "Kimchi Stew",
  "calories": "89 kcal per 100g",
  "calories_per_serving": "~267 kcal (1인분 300g 기준)"
}
```

#### 영양 밸런스 시각화
```
김치찌개 (100g 기준)
━━━━━━━━━━━━━━━━━
🔥 에너지:   89 kcal
🥩 단백질:   7.14g   ████████░░
🧈 지방:     3.50g   ████░░░░░░
🍚 탄수화물: 4.40g   ████░░░░░░
🧂 나트륨:   N/A
```

#### 알레르기/건강 정보 (확장 가능)
```
- 나트륨 높음 ⚠️: 나트륨 > 600mg/100g인 메뉴 경고
- 고칼로리 ⚠️: 에너지 > 400kcal/100g인 메뉴 표시
- 고단백 💪: 단백질 > 15g/100g인 메뉴 하이라이트
```

### 7-2. 추가 공공데이터 API 후보

data.go.kr에서 활용 가능한 추가 API:

| API | 데이터번호 | 활용 | 우선순위 |
|-----|-----------|------|---------|
| **식품안전나라 영양성분** | 15100070 | 더 넓은 범위의 영양정보 | P1 |
| **외식영양성분** | 15084411 | 외식 메뉴 특화 (1인분 기준) | P1 |
| **식품첨가물정보** | 15127600 | 알레르기 정보 | P2 |
| **지역 맛집 정보** | 다수 | 식당 추천 | P3 |

#### 외식영양성분 API (우선 확장 후보)

현재 식품영양성분DB는 **100g 기준** 데이터. 외식영양성분은 **1인분 기준**이라 더 실용적.

```
신청 URL: https://www.data.go.kr/data/15084411/openapi.do
API명: 식품의약품안전처_외식영양성분DB정보
→ 활용신청 후 동일한 방식으로 연동 가능
```

### 7-3. 서빙 사이즈 추정 로직

현재 대부분 `SERVING_SIZE = "100g"`이므로 1인분 환산 필요:

```python
# 카테고리별 1인분 추정 (g)
SERVING_ESTIMATE = {
    "찌개 및 전골류": 300,   # 찌개 1인분 ~300g
    "국 및 탕류": 350,       # 국밥 1인분 ~350g
    "밥류": 400,             # 비빔밥 1인분 ~400g
    "면류": 450,             # 우동/라면 1인분 ~450g
    "구이류": 200,           # 고등어구이 1인분 ~200g
    "튀김류": 250,           # 돈가스 1인분 ~250g
    "김치류": 50,            # 반찬 1회 ~50g
}

# 1인분 칼로리 = (energy_kcal / 100) * serving_g
```

### 7-4. 메뉴 비교 기능

영양정보가 있으므로 메뉴 간 비교 콘텐츠 생성 가능:

```
"김치찌개 vs 된장찌개"
━━━━━━━━━━━━━━━━━━━━
         김치찌개    된장찌개
에너지:   89 kcal    46 kcal
단백질:   7.14g      3.38g
지방:     3.50g      1.50g
→ 김치찌개가 더 고단백, 된장찌개가 더 저칼로리
```

---

## 8. 트러블슈팅

### 8-1. HTTP 401 Unauthorized

```
원인 1: API 키 전파 미완료 (승인 후 1~2시간)
  → 대기 후 재시도

원인 2: 잘못된 키 사용 (data.ex.co.kr 키를 data.go.kr에 사용)
  → .env에서 DATA_GO_KR_API_KEY 확인

원인 3: Encoding 키를 사용 (URL 이중 인코딩)
  → Decoding 키를 사용해야 함 (Python httpx가 자동 인코딩)

확인 방법:
  python scripts/test_data_go_kr_correct.py
```

### 8-2. 검색 결과 0건

```
원인 1: 검색어가 너무 구체적
  → "남산매운치즈돈까스" 대신 "돈까스"로 검색

원인 2: API DB에 해당 음식 없음
  → "떡만두라면정식" 같은 복합 메뉴는 DB에 없을 수 있음

원인 3: 한글 인코딩 문제
  → httpx params에 직접 한글 전달 (URL 인코딩 자동)
```

### 8-3. 매칭 품질 저하

```
증상: "왕돈가스" 검색 시 "굿쉐프 왕돈가스소스" (소스 제품)가 매칭됨

원인: API가 부분 일치 검색이라 관련 없는 가공식품이 매칭

대응:
  - best_item 선택 시 정확 일치 우선
  - FOOD_CAT1_NM 기반 필터링 추가 (Sprint 1)
  - "즉석식품류", "조미식품" 등 비음식 카테고리 제외
```

### 8-4. Rate Limiting

```
일일 트래픽: 10,000건
현재 사용: ~540건/실행

초과 시: HTTP 429 또는 503 반환
→ asyncio.sleep(0.3) 으로 속도 제한 중
→ 대량 업데이트 시 여러 날에 걸쳐 분할 실행
```

---

## 9. 참고 자료

### 파일 위치

| 파일 | 경로 | 설명 |
|------|------|------|
| **이 문서** | `docs/PUBLIC_DATA_API_GUIDE.md` | 공공데이터 연동 가이드 |
| **수집 스크립트** | `app/backend/scripts/collect_highway_food_data.py` | 고속도로 데이터 수집 |
| **시드 생성** | `app/backend/scripts/generate_canonical_seed.py` | canonical 시드 생성 |
| **영양 매핑** | `app/backend/scripts/enrich_canonical_nutrition.py` | 영양정보 자동 매핑 |
| **API 클라이언트** | `app/backend/services/public_data_client.py` | 통합 API 클라이언트 |
| **시드 원본** | `app/backend/data/canonical_seed_data.json` | 169개 메뉴 (영양정보 없음) |
| **enriched 시드** | `app/backend/data/canonical_seed_enriched.json` | 166개 영양정보 포함 |
| **영양 SQL** | `app/backend/migrations/sprint0_update_nutrition.sql` | DB UPDATE SQL |
| **테스트** | `app/backend/scripts/test_data_go_kr_correct.py` | API 연결 테스트 |
| **환경변수** | `app/backend/.env` | API 키 (Git 미포함) |
| **환경변수 예시** | `app/backend/.env.example` | API 키 설명 |

### 외부 링크

| 리소스 | URL |
|--------|-----|
| 공공데이터포털 | https://www.data.go.kr |
| 식품영양성분DB API | https://www.data.go.kr/data/15127578/openapi.do |
| 한국도로공사 OpenAPI | https://data.ex.co.kr |
| 식품안전나라 | https://www.foodsafetykorea.go.kr |

### 데이터 현황 (2026-02-19 기준)

```
canonical 메뉴: 169개
영양정보 매핑: 166개 (98.2%)
미매칭: 3개 (떡만두라면정식, 돈가스우동정식, 순두부짬뽕밥)

영양소 커버리지:
  에너지 (kcal): 166/169
  단백질 (g):    165/169
  지방 (g):      160/169
  탄수화물 (g):  142/169
```

---

**최초 작성**: 2026-02-19
**관리**: Menu Knowledge Engine 개발팀
