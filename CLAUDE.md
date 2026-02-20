# Menu Knowledge Engine - 프로젝트 규칙

> 이 문서는 Menu Knowledge Engine 프로젝트의 개발 규칙을 정의합니다.
> 모든 개발자와 AI는 이 규칙을 반드시 따라야 합니다.

---

## 핵심 원칙

### 1. 지식 엔진 (Knowledge Engine)
**이 프로젝트는 "번역 서비스"가 아니라 "지식 엔진"이다**

- AI는 초기 메뉴 정체성 탐색에만 사용
- 확정된 지식은 DB에 저장하고, 이후 동일 메뉴는 AI 호출 없이 DB에서 서빙
- 비용 구조: 시간이 지날수록 AI 호출 비율 하락 → 비용 절감

### 2. Canonical 중심 설계
**canonical_menus 테이블이 핵심. 모든 메뉴는 canonical에 매핑된다**

- 메뉴는 문자열이 아니라 "개념"
- "할머니뼈해장국" = "할머니(수식어)" + "뼈해장국(canonical)"
- 변형 메뉴는 menu_variants에, 표준 메뉴는 canonical_menus에

### 3. AI 호출 최소화 원칙
**AI 호출은 최후의 수단. DB 매칭 → 수식어 분해 → AI fallback 순서를 반드시 지킨다**

```
단계 1: 정확 매칭 (canonical_menus.name_ko)
단계 2: 유사 검색 (pg_trgm)
단계 3: 수식어 분해 (modifiers 사전 활용)
단계 4: AI Discovery (GPT-4o) ← 최후의 수단
```

---

## 설계 및 배포 문서 위치

### 기획 & 설계 문서

| 문서 | 경로 | 용도 |
|------|------|------|
| **기획 문서** | `C:\project\menu\기획\3차_설계문서_20250211\` | 전체 설계 참조 |
| **DB 스키마** | `03_data_schema_v0.1.md` | **이 문서가 진실의 원천 (Single Source of Truth)** |
| **API 스펙** | `06_api_specification_v0.1.md` | REST API 엔드포인트 정의 |
| **시드 가이드** | `07_seed_data_guide.md` | 초기 데이터 구축 가이드 |
| **MVP 범위** | `05_mvp_scope_definition.md` | v0.1에 포함할 기능 |
| **개념 정의** | `01_concept_overview.md` | 엔진의 3단계 작동 원리 |

### 배포 & 운영 문서 (🆕 v0.1.0 최종)

| 문서 | 경로 | 용도 | 상태 |
|------|------|------|------|
| **최종 배포 완료** | `DEPLOYMENT_FINAL_V0.1.0_20260213.md` | **프로덕션 배포 완료** | ✅ |
| **uvicorn 설정** | 포트 8001, 0.0.0.0 바인딩 | 외부 접근 가능 | ✅ |
| **pg_trgm 설치** | PostgreSQL 확장 설치 완료 | 유사 검색 준비 | ✅ 2026-02-13 |
| **데이터베이스** | 214 records 초기 로드 | concepts, modifiers, canonical_menus | ✅ |
| **FastComet 가이드** | `C:\project\dev-reference\docs\FASTCOMET_DEPLOYMENT_GUIDE.md` | **다른 프로젝트도 참고 가능** | ✅ 최신화 |

---

## 기술 스택

### Backend
- **Python**: 3.11+ (현재 로컬: 3.13.5 / 서버: 3.13)
- **프레임워크**: FastAPI (비동기 지원)
- **ORM**: SQLAlchemy (async)
- **ASGI 서버**: uvicorn (0.0.0.0:8001, 2 workers)
- **DB**: PostgreSQL 13.23 (FastComet Managed VPS)
- **DB 확장**:
  - ✅ **pg_trgm** (설치 완료 2026-02-13) - 유사 검색 준비 완료
  - pgvector (v0.2에서 활성화 예정)

### AI/ML
- **OCR**: CLOVA OCR (네이버)
- **LLM**: GPT-4o (Identity Discovery)
- **번역 보조**: Papago API (일/중)

### Public Data APIs (🆕 Sprint 0 통합)
- **메뉴젠** (농촌진흥청): 음식 표준 분류 (1,500+ 음식코드)
- **서울 식당정보** (서울관광재단): 167,659개 메뉴 데이터
- **식품영양성분DB** (식품의약품안전처): 157개 영양항목
- **휴게소 푸드메뉴** (한국도로공사): 고속도로 경유지 메뉴 (선택)

### DevOps
- **호스팅**: Naver Cloud (CLOVA OCR 동일 네트워크)
- **스토리지**: S3 호환 (이미지/QR)

---

## 🆕 공공데이터 기반 아키텍처 (Sprint 0)

### 핵심 전략: Seoul-centric 국가 커버리지
**서울은 전국 모든 메뉴 문화가 모이는 곳 → 서울 데이터만으로 전국 90% 메뉴 커버 가능**

| 지표 | 값 | 의미 |
|------|---|----|
| **서울 식당 수** | 167,659개 | 전국 2.1M 중 8% |
| **대표메뉴 데이터** | 157,000개 | 공개된 유일한 메뉴 소스 |
| **전국 메뉴 커버리지** | 90%+ | 지역 특화 음식 서울 진출 |
| **AI 호출 절감** | 70% | $210,000/월 절감 |
| **초기 구축 비용** | $0 | 공공데이터 무료 활용 |

### 3단계 데이터 파이프라인

```
[1단계: 메뉴 표준화]
   ↓
   메뉴젠 API (음식코드, 분류, 중량정보)
   ↓ 자동 매핑
   canonical_menus.standard_code 입력

[2단계: 메뉴 데이터 확보]
   ↓
   서울 식당정보 CSV (167,659개 메뉴명)
   ↓ 정규화 + 중복 제거
   canonical_menus.name_ko 확보

[3단계: 영양정보 연계]
   ↓
   식품영양성분DB API (157개 항목)
   ↓ 메뉴명 매칭 + Redis 캐싱
   canonical_menus.nutrition_info (JSONB)
```

### DB 스키마 확장 (v0.1.0 이후)

```sql
-- canonical_menus 테이블 새 필드
ALTER TABLE canonical_menus ADD COLUMN (
  standard_code VARCHAR(10),           -- 음식코드 (메뉴젠)
  category_1 VARCHAR(50),              -- 대분류 (예: 육류, 밥, 찌개)
  category_2 VARCHAR(50),              -- 중분류 (예: 구이, 비빔밥류)
  serving_size VARCHAR(20),            -- 1인분 기준 (예: 200g)
  nutrition_info JSONB,                -- 영양정보 (캐싱)
  last_nutrition_updated TIMESTAMPTZ   -- 영양정보 갱신일
);

-- 인덱스 추가
CREATE INDEX idx_canonical_standard_code ON canonical_menus(standard_code);
CREATE INDEX idx_canonical_category ON canonical_menus(category_1, category_2);
```

### API 호출 워크플로우 (순서 중요!)

```python
# 1. 메뉴명 정규화 (OCR 결과)
menu_raw = "  한우  불고기  "
menu_normalized = normalize_menu_name(menu_raw)  # → "한우불고기"

# 2. DB 캐시 확인 (최우선)
menu = db.query(canonical_menus).filter_by(name_ko=menu_normalized).first()
if menu:
    return menu  # ← AI 호출 회피!

# 3. 메뉴젠 API 호출 (표준화)
food_code = query_menu_gen_api(menu_normalized)
if not food_code:
    # 4. AI Discovery (최후의 수단)
    result = gpt4o_discover_menu(menu_normalized)
else:
    # 5. 영양정보 자동 조회
    nutrition = query_nutrition_api(food_code)
    result = {
        "name_ko": menu_normalized,
        "standard_code": food_code,
        "category_1": nutrition.get("category_1"),
        "nutrition_info": nutrition  # ← 캐싱 (Redis TTL 90일)
    }

return result
```

---

## 코딩 규칙

### Python 표준
```python
# 들여쓰기: 4 spaces
# 타입 힌트 필수
from typing import Optional, List
from uuid import UUID

async def get_menu(menu_id: UUID) -> Optional[dict]:
    ...

# async/await 적극 활용
# FastAPI + SQLAlchemy (async)
```

### 환경변수 관리
- `.env` 파일로 관리 (절대 Git에 커밋 금지)
- `.env.example`에 키 이름만 기록
- 환경변수 하드코딩 절대 금지

### 데이터베이스
- **UUID 기본키** 사용 (외부 노출 시 추측 불가)
- **JSONB 적극 활용** (다국어 번역, 태그, 유연한 데이터)
- **created_at, updated_at 자동 관리**

---

## DB 규칙

### 확장 (Extensions)

#### ✅ 설치 완료 (v0.1.0)
```sql
-- 유사 검색 (2026-02-13 FastComet 지원팀에서 설치 완료)
CREATE EXTENSION IF NOT EXISTS pg_trgm;        -- 버전: 1.6

-- 테스트
SELECT similarity('김치찌개', '김치찌게');    -- 0.857 (85.7%)
```

#### 🔮 예정 (v0.2)
```sql
-- 임베딩 기반 검색
CREATE EXTENSION IF NOT EXISTS vector;         -- pgvector
```

#### 📝 설치 요청 방법 (FastComet)

FastComet 지원팀에 이메일로 요청:
```
Subject: Install PostgreSQL Extension [extension_name]

Content:
- Database: chargeap_menu_knowledge
- Extension: pg_trgm (또는 필요한 확장명)
- Purpose: [용도]
```

**응답 시간**: 1-2일 (실제 사례: pg_trgm 설치 2026-02-13 완료)

### 테이블 우선순위
1. **concepts** — 개념 트리 (대분류/중분류)
2. **modifiers** — 수식어 사전 (50개)
3. **canonical_menus** — 표준 메뉴 (100개) ← **핵심**
4. menu_variants, menu_relations, shops, scan_logs, evidences, cultural_concepts

### 네이밍 규칙
- 테이블: `snake_case`, 복수형 (`canonical_menus`)
- 컬럼: `snake_case`
- ID: `UUID`
- 타임스탬프: `timestamptz` (UTC)

---

## 테스트 데이터 기준

### 핵심 검증 케이스
**"왕얼큰순두부뼈해장국"을 올바르게 분해할 수 있으면 엔진이 작동하는 것**

```
입력: "왕얼큰순두부뼈해장국"
기대 분해:
  - 수식어 1: "왕" (size, x_large)
  - 수식어 2: "얼큰" (taste, spicy_hearty, +1 spice)
  - 수식어 3: "순두부" (ingredient, soft_tofu)
  - 기본 메뉴: "뼈해장국" (canonical)
```

### 10대 테스트 케이스
1. 김치찌개 (정확 매칭)
2. 할머니김치찌개 (단일 수식어)
3. 왕돈까스 (크기 수식어)
4. 얼큰순두부찌개 (맛 수식어)
5. 숯불갈비 (조리법 수식어)
6. 한우불고기 (재료 수식어)
7. **왕얼큰뼈해장국** (다중 수식어)
8. 옛날통닭 (다중 수식어)
9. 시래기국 (AI Discovery)
10. 고씨네묵은지감자탕 (복합)

**목표: 10개 중 7개 이상 정확 분해 (70%+)**

---

## 개발 워크플로우

### Sprint 구조 (🆕 공공데이터 기반)

#### Sprint 0: 공공데이터 기반 기초 구축 (3주, 110시간)
```
Week 1: 메뉴젠 API + 서울 식당 데이터 통합 (40시간)
  ├─ 메뉴젠 1,500개 식품코드 API 파싱
  ├─ 서울 관광재단 CSV 167,659개 메뉴 임포트
  └─ canonical_menus 테이블 자동 생성 (157,000개)

Week 2: 영양정보 API + 캐싱 구축 (40시간)
  ├─ 식품영양성분DB API 연동
  ├─ 메뉴명-영양정보 자동 매칭
  ├─ Redis 캐싱 (TTL 90일)
  └─ 테스트 데이터 10대 케이스 검증

Week 3: 문서화 + 배포 (30시간)
  ├─ CLAUDE.md 업데이트 (현재 작업)
  ├─ DB 스키마 문서화
  ├─ API 통합 가이드 작성
  └─ FastComet 배포 + 모니터링

목표: 157,000개 메뉴 DB 준비 완료, AI 호출 70% 절감
```

#### Sprint 1: OCR 파이프라인 + 매칭 엔진
```
Sprint 0 결과물을 기반으로 실제 OCR 결과 처리
- CLOVA OCR (Tier 1) → 메뉴명 추출
- 메뉴젠 API 자동 매칭
- 불일치 시에만 GPT-4o Discovery (최후의 수단)
```

#### Sprint 2: B2B/B2C 프론트엔드 + 배포
```
- 영양정보 대시보드
- 음식점 메뉴 검색
- 다국어 지원 (향후)
```

#### Sprint 3: 현장 테스트 + 최적화
```
- 실제 음식점에서 OCR 테스트
- 메뉴 분해 정확도 개선
- 시스템 성능 최적화
```

### Git 규칙
- 커밋 메시지: 영문, 현재형 동사 ("Add feature", "Fix bug")
- 디버깅 코드 커밋 금지 (`print()`, 주석 처리된 코드)
- `.env` 파일 커밋 금지

### 코드 검증 (Sprint 1에서 자동화)
```bash
# 타입 체크
mypy app/backend

# 린트
ruff check app/backend

# 포맷
black --check app/backend

# 테스트
pytest
```

---

## 핵심 지표 (KPI)

### Sprint 0 목표 (공공데이터 기반)

| 지표 | 목표 | 의미 |
|------|------|------|
| **DB 커버리지** | 157,000개 | 서울 식당 메뉴 자동 구축 |
| **메뉴 매칭률** | 90%+ | 정규화된 메뉴명 DB 매칭 |
| **AI 호출 절감** | 70% | 월 $210,000 절감 |
| **초기 구축 비용** | $0 | 공공데이터 무료 활용 |
| **영양정보 커버리지** | 157개 항목 | 정부 표준 DB 전체 |

### 운영 지표 (Sprint 1+)

| 지표 | 목표 | 의미 |
|------|------|------|
| **OCR 인식률** | 80%+ | 메뉴명 추출 성공률 |
| **응답 시간** | 3초 이내 | DB 히트 시 p95 |
| **캐시 히트율** | 85%+ | Redis 캐시 효율성 |
| **AI 비용/스캔** | < 15원 | Sprint 0 후 절감된 비용 |
| **외국인 이해도** | 4/5+ | "Was this helpful?" 피드백 |

---

## 개발 경험 및 주의사항

> 실제 개발 과정에서 발견된 이슈와 해결책을 기록합니다.
> 동일한 실수를 반복하지 않기 위한 교훈 모음입니다.

### 프론트엔드 개발 시 주의사항

#### 1. 브라우저 캐시 문제 (Critical)
**문제**: JS/CSS 파일 업데이트 후에도 브라우저가 캐시된 버전 사용

**증상**:
- 서버에 새 파일 업로드 완료
- 브라우저에서 여전히 이전 버전 실행
- Ctrl+F5 해도 해결 안 되는 경우 있음

**해결책**:
```html
<!-- ❌ 나쁜 예 -->
<script src="js/app.js"></script>

<!-- ✅ 좋은 예: 캐시 버스팅 -->
<script src="js/app.js?v=20260220"></script>
<script src="js/components.js?v=20260220-2"></script>  <!-- 수정 시 버전 증가 -->
```

**배포 체크리스트**:
- [ ] HTML에서 모든 JS/CSS에 `?v=날짜` 파라미터 추가
- [ ] 수정 시마다 버전 번호 증가 (`-2`, `-3`, ...)
- [ ] 배포 후 시크릿 모드로 테스트

**관련 이슈**: Sprint 2 Phase 2 배포 시 enriched-components.js 캐시 문제

---

#### 2. API 응답 구조 검증 필수
**문제**: 프론트엔드 기대 구조 ≠ 실제 API 응답 구조

**사례**:
```javascript
// 프론트엔드 기대
data.preparation_steps = [step1, step2, ...]  // 배열 직접 접근

// 실제 API 응답
data.preparation_steps = {
  steps: [step1, step2, ...],      // 중첩된 객체!
  etiquette: [],
  serving_suggestions: []
}
```

**에러**:
```
TypeError: steps.map is not a function
```

**해결책**:
```javascript
// ❌ 나쁜 예
const steps = data?.preparation_steps || [];

// ✅ 좋은 예: 중첩 구조 고려
const steps = data?.preparation_steps?.steps || data?.steps || [];
```

**교훈**:
1. **API 스펙 문서화**: DB 스키마 ≠ API 응답 형식
2. **curl로 먼저 검증**: 프론트 개발 전 실제 API 응답 확인
3. **방어적 코드**: optional chaining (`?.`) 적극 활용

**검증 명령어**:
```bash
# 실제 API 응답 확인
curl -s "https://menu-knowledge.chargeapp.net/api/v1/canonical-menus/{id}" | python -m json.tool
```

---

#### 3. Graceful Degradation 패턴
**원칙**: 점진적 기능 확장 시 기존 기능이 깨지지 않도록 폴백 전략 필수

**사례**: Enriched content 추가 시 non-enriched 메뉴 처리
```javascript
// ❌ 나쁜 예: enriched data 없으면 크래시
async function fetchMenuByName(menuName) {
    const id = await identify(menuName);
    return await fetchEnrichedData(id);  // 404 → 크래시!
}

// ✅ 좋은 예: fallback 전략
async function fetchMenuByName(menuName) {
    const basicData = await identify(menuName);
    const id = basicData.id;

    try {
        const enriched = await fetchEnrichedData(id);
        console.log('✅ Enriched data loaded');
        return enriched;
    } catch (error) {
        console.warn('⚠️ Using basic data:', error.message);
        return basicData;  // Fallback
    }
}
```

**체크리스트**:
- [ ] 새 기능 추가 시 기존 데이터 호환성 확인
- [ ] try-catch로 에러 처리
- [ ] 폴백 데이터로 최소 기능 제공
- [ ] Console에 상태 로그 남기기

---

### 백엔드 개발 시 주의사항

#### 4. JSONB 필드 구조 일관성
**문제**: JSONB 컬럼에 저장된 데이터 구조가 일관되지 않음

**사례**:
```sql
-- 메뉴 A: preparation_steps
{"steps": ["...", "..."], "etiquette": []}

-- 메뉴 B: preparation_steps
["...", "..."]  -- 직접 배열!
```

**해결책**:
1. **DB 스키마 문서에 JSONB 구조 명시**:
   ```markdown
   ### preparation_steps (JSONB)
   ```json
   {
     "steps": ["string", ...],           // 필수
     "etiquette": ["string", ...],       // 선택
     "serving_suggestions": ["string"]   // 선택
   }
   ```
   ```

2. **API Serializer에서 검증**:
   ```python
   def serialize_preparation_steps(data):
       if isinstance(data, list):
           # Legacy 형식 변환
           return {"steps": data, "etiquette": [], "serving_suggestions": []}
       return data
   ```

**교훈**: JSONB는 유연하지만, 구조 일관성은 개발자가 강제해야 함

---

#### 5. 배열 변환 시 DB 조회 추가 (Similar Dishes 패턴)
**요구사항**: API가 문자열 배열이 아닌 full object 배열 반환

**AS-IS**:
```json
{
  "similar_dishes": ["갈비구이 (Galbi Gui...)", "돼지갈비 (...)"]
}
```

**TO-BE**:
```json
{
  "similar_dishes": [
    {"id": "...", "name_ko": "갈비구이", "image_url": "...", "spice_level": 2},
    {"id": null, "name_ko": "돼지갈비", "image_url": null, "spice_level": 0}
  ]
}
```

**구현 패턴**:
```python
async def _resolve_similar_dishes(dishes: List[str], db: AsyncSession) -> List[Dict]:
    """문자열 배열을 full object로 변환"""
    resolved = []
    for dish_str in dishes:
        # 1. 문자열에서 한글 이름 추출
        name_ko = dish_str.split('(')[0].strip()

        # 2. DB에서 조회
        result = await db.execute(
            select(CanonicalMenu).where(CanonicalMenu.name_ko == name_ko).limit(1)
        )
        menu = result.scalar_one_or_none()

        # 3. 있으면 full object, 없으면 fallback
        if menu:
            resolved.append({
                "id": str(menu.id),
                "name_ko": menu.name_ko,
                "name_en": menu.name_en,
                "image_url": menu.image_url,
                "spice_level": menu.spice_level
            })
        else:
            # Fallback: 최소 정보만
            resolved.append({
                "id": None,
                "name_ko": name_ko,
                "name_en": dish_str.split('(')[1].split(')')[0] if '(' in dish_str else name_ko,
                "image_url": None,
                "spice_level": 0
            })

    return resolved
```

**주의사항**:
- N+1 쿼리 문제: 10개 similar dishes → 10번 DB 조회
- 성능 최적화: `asyncio.gather()` 또는 `IN` 쿼리 사용 검토
- DB에 없는 메뉴: fallback object로 안전하게 처리

---

### 배포 프로세스

#### 6. 단계별 검증 체크리스트
**교훈**: 파일 업로드 ≠ 정상 작동. 각 단계마다 검증 필수

**배포 체크리스트**:
```bash
# 1. 로컬 테스트
npm run build        # 빌드 성공 확인
npm run lint         # 린트 통과 확인

# 2. 서버 업로드
scp -i ~/.ssh/menu_deploy file.js chargeap@server:~/path/

# 3. 서버에서 파일 확인 (중요!)
ssh chargeap@server "cat ~/path/file.js | head -20"   # 내용 검증
ssh chargeap@server "ls -lh ~/path/file.js"            # 크기/날짜 확인

# 4. 백엔드 재시작 (해당 시)
ssh chargeap@server "cd ~/app && pkill -f uvicorn && nohup python -m uvicorn ... &"
sleep 3
ssh chargeap@server "ps aux | grep uvicorn | grep -v grep"  # 프로세스 확인

# 5. API 테스트 (프론트엔드 전)
curl -s "https://api-url/endpoint" | python -m json.tool

# 6. 브라우저 테스트
# - 시크릿 모드로 테스트
# - F12 Console 에러 확인
# - Network 탭에서 파일 버전 확인 (200 vs 304)
```

**자주 하는 실수**:
- [ ] ❌ 파일 업로드만 하고 백엔드 재시작 안 함
- [ ] ❌ 브라우저만 테스트 (curl로 API 먼저 검증 안 함)
- [ ] ❌ 캐시 버스팅 없이 배포 (사용자가 Ctrl+F5 해야 함)
- [ ] ❌ Console 에러 확인 안 함

---

### 데이터 구조 설계

#### 7. API 스펙 vs DB 스키마 분리
**원칙**: DB 스키마와 API 응답 형식을 별도로 관리

**나쁜 예**: DB 컬럼을 그대로 API에 노출
```python
# DB 스키마와 API 응답이 동일 → 변경 시 하위 호환 깨짐
return {
    "id": menu.id,
    "name_ko": menu.name_ko,
    "preparation_steps": menu.preparation_steps  # JSONB 그대로 노출
}
```

**좋은 예**: Serializer 레이어에서 변환
```python
def serialize_menu(menu: CanonicalMenu, include_enriched: bool = False) -> Dict:
    base = {
        "id": str(menu.id),
        "name_ko": menu.name_ko,
        "name_en": menu.name_en,
        # ...
    }

    if include_enriched:
        # DB 구조를 API 형식으로 변환
        enriched = {
            "description": {
                "short_ko": menu.explanation_short.get("ko"),
                "short_en": menu.explanation_short.get("en"),
                "long_ko": menu.description_long_ko,
                "long_en": menu.description_long_en,
            },
            "preparation_steps": menu.preparation_steps.get("steps", []),  # 중첩 제거
            "similar_dishes": await _resolve_similar_dishes(menu.similar_dishes, db)
        }
        base.update(enriched)

    return base
```

**이점**:
1. DB 스키마 변경 시 API 하위 호환 유지
2. 프론트엔드 친화적 구조
3. 점진적 기능 확장 가능

---

## 참조 자료

### 기획 & 설계 (Sprint 0 공공데이터 기반)
- **🆕 Sprint 0 최종 기획**: `SPRINT0_FINAL_PLAN_20260219.md` ← 현재 기준 문서
- **이전 설계 문서**: `C:\project\menu\기획\3차_설계문서_20250211\`
- **상위 CLAUDE.md**: `C:\project\CLAUDE.md` (전체 프로젝트 공통 규칙)

### 개발 참고
- **dev-reference**: `C:\project\dev-reference\` (코딩 표준, 에이전트)
- **FastComet 배포 가이드**: `C:\project\dev-reference\docs\FASTCOMET_DEPLOYMENT_GUIDE.md`

### Public Data APIs
- **메뉴젠** (농촌진흥청): https://www.data.go.kr/data/15101046/
- **서울 식당정보** (서울관광재단): https://www.data.go.kr/data/15098046/
- **식품영양성분DB** (식품의약품안전처): https://www.data.go.kr/data/15127578/
- **휴게소 푸드메뉴** (한국도로공사): https://www.data.go.kr/data/

---

**최종 수정**: 2026-02-20 (개발 경험 및 주의사항 추가)
**관리**: Menu Knowledge Engine 개발팀
**배포 상태**: 🟢 Sprint 2 Phase 2 완료 (Enriched Content Display)
**최근 업데이트**: 브라우저 캐시, API 구조 검증, Graceful Degradation 패턴 추가
