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

### DevOps
- **호스팅**: Naver Cloud (CLOVA OCR 동일 네트워크)
- **스토리지**: S3 호환 (이미지/QR)

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

### Sprint 구조
```
Sprint 0 (현재): 프로젝트 기반 구축 (DB + 시드 + 기본 API)
Sprint 1: OCR 파이프라인 + 매칭 엔진
Sprint 2: B2B/B2C 프론트엔드
Sprint 3: 현장 테스트 + 최적화
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

| 지표 | 목표 | 의미 |
|------|------|------|
| **DB 매칭률** | 70%+ | AI 호출 없이 DB만으로 처리 비율 |
| **OCR 인식률** | 80%+ | 메뉴명 추출 성공률 |
| **외국인 이해도** | 4/5+ | "Was this helpful?" 피드백 |
| **응답 시간** | 3초 이내 | DB 히트 시 p95 |
| **AI 비용/스캔** | < 50원 | 비용 구조 지속가능성 |

---

## 참조 자료

- **상위 CLAUDE.md**: `C:\project\CLAUDE.md` (전체 프로젝트 공통 규칙)
- **설계 문서**: `C:\project\menu\기획\3차_설계문서_20250211\`
- **dev-reference**: `C:\project\dev-reference\` (코딩 표준, 에이전트)

---

**최종 수정**: 2026-02-13 (v0.1.0 배포 완료)
**관리**: Menu Knowledge Engine 개발팀
**배포 상태**: 🟢 프로덕션 운영 중
