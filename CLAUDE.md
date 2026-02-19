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

**최종 수정**: 2026-02-19 (Sprint 0 공공데이터 기반 전환)
**관리**: Menu Knowledge Engine 개발팀
**배포 상태**: 🟡 Sprint 0 기초 구축 중 (공공데이터 통합)
**다음 단계**: DB 스키마 문서 업데이트 (Task 3/8)
