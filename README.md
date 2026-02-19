# Menu Knowledge Engine

> 🆕 **공공데이터 기반 한국 음식 메뉴 지식 엔진** — AI 호출 70% 절감, 초기 구축 비용 $0
>
> *by Claude (Senior Developer), Menu Knowledge Engine Team*

## 개요

Menu Knowledge Engine은 한국 음식 메뉴를 "번역 대상"이 아닌 "정의된 지식 객체"로 전환하여, 다국어 설명·문화적 맥락·식이 정보를 구조화된 API로 제공하는 지식 엔진입니다.

### 🆕 Sprint 0 공공데이터 통합 (2026-02-19 최종 승인)

**Seoul-Centric 국가 커버리지 전략**
- 서울 식당 167,659개 메뉴 자동 구축 → 전국 메뉴 90%+ 커버리지
- 3단계 공공데이터 파이프라인: 메뉴젠(표준화) → 서울 식당(데이터) → 영양정보(캐싱)
- **AI 호출 70% 절감**: 월 $210,000 절감 (OpenAI 기준)
- **초기 구축 비용**: $0 (공공데이터 무료)
- **배포 타임라인**: 3주 (Week 1~3 of Feb 2026)

**3개 필수 공공데이터 API**
| API | 기관 | 데이터 | 용도 |
|-----|-----|--------|------|
| 메뉴젠 | 농촌진흥청 | 1,500개 음식코드 | 메뉴 표준화 (정부 분류) |
| 서울 식당정보 | 서울관광재단 | 167,659개 메뉴 | 메뉴 데이터 확보 |
| 식품영양성분DB | 식품의약품안전처 | 157개 영양항목 | 영양정보 자동 연계 |

### 핵심 차별점
- **Knowledge Graph 기반**: 메뉴를 개념 단위로 구조화
- **수식어 분해 시스템**: "할머니뼈해장국" → "할머니" + "뼈해장국"
- **공공데이터 통합**: AI 없이도 157,000개 메뉴 DB 자동 구축
- **자기강화 루프**: B2B(식당) + B2C(관광객) 양방향 데이터 수집
- **비용 절감 구조**: 공공데이터 + Redis 캐싱으로 AI 호출 70% 절감

## 기술 스택

### Backend
- **Framework**: FastAPI + SQLAlchemy (async)
- **Database**: PostgreSQL 16+ with pg_trgm (유사 검색), pgvector (v0.2+)
- **Cache**: Redis (TTL 90일, 영양정보 캐싱)
- **Python**: 3.11+
- **Server**: uvicorn (0.0.0.0:8001), Nginx reverse proxy

### AI/ML
- **OCR**: CLOVA OCR (메뉴판 이미지 → 텍스트)
- **LLM**: GPT-4o (Identity Discovery, 최후의 수단)
- **Translation**: Papago API (일어, 중국어)
- **Fallback**: Google Gemini (무료, billing limit 대체)

### 공공데이터 API (🆕 Sprint 0)
- **메뉴젠**: 농촌진흥청 국립식량과학원 (1,500개 음식코드)
- **서울 식당정보**: 서울관광재단 (167,659개 메뉴)
- **식품영양성분DB**: 식품의약품안전처 (157개 영양항목)

---

## 📊 프로젝트 상태

### Sprint 0 진행 현황 (2026-02-19)

| 단계 | 상태 | 완료율 | 담당 |
|------|------|--------|------|
| **기획 및 설계** | ✅ 완료 | 100% | Claude (Senior Dev) |
| **문서화** | ✅ 완료 | 100% | Claude |
| **Week 1: 메뉴젠 + 서울 식당 임포트** | 🔄 시작 예정 | 0% | Backend Lead |
| **Week 2: 영양정보 API + 테스트** | 🔮 예정 | 0% | Backend Lead |
| **Week 3: 배포 + 모니터링** | 🔮 예정 | 0% | DevOps Lead |

### 최종 목표 (Sprint 0 완료 시)
- ✅ 157,000개 메뉴 자동 구축 (서울 식당 데이터)
- ✅ 영양정보 157개 항목 모두 연계
- ✅ AI 호출 70% 절감 (월 $210,000)
- ✅ 전국 메뉴 90%+ 커버리지
- ✅ FastComet 라이브 배포 완료

---

## 📋 프로젝트 구조

```
app/
├── backend/
│   ├── main.py              # FastAPI 진입점
│   ├── config.py            # 환경 설정
│   ├── database.py          # DB 연결
│   ├── models/              # SQLAlchemy 모델 (9개 테이블)
│   ├── api/
│   │   └── menu.py          # API 라우터 (/identify, /recognize)
│   ├── services/
│   │   ├── matching_engine.py   # 3단계 매칭 파이프라인
│   │   └── ocr_service.py       # CLOVA OCR + GPT-4o 파싱
│   ├── seeds/               # 시드 데이터 (112 canonical, 54 modifiers)
│   └── tests/               # 테스트
├── frontend/                # B2C 모바일 웹 (Sprint 2)
│   ├── index.html           # 검색 UI
│   ├── css/style.css        # 모바일 최적화 디자인
│   └── js/app.js            # API 통합
├── frontend-b2b/            # B2B 관리자 (Sprint 3)
│   ├── index.html           # 메뉴판 업로드 + 검수 UI
│   ├── css/style.css        # Admin 디자인
│   └── js/app.js            # OCR + 매칭 워크플로우
└── data/                    # 메뉴판 사진, 테스트 결과
```

## 설치 및 실행

### 1. 가상환경 생성
```bash
cd app/backend
python -m venv venv
venv\Scripts\activate  # Windows
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 열어서 실제 값으로 수정
```

### 4. 데이터베이스 설정
```bash
# PostgreSQL 설치 후
createdb menu_knowledge_db

# 시드 데이터 입력
python seeds/run_seeds.py
```

### 5. 서버 실행
```bash
# Backend API 서버
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend 서버 (B2C)
cd ../frontend
python -m http.server 8080

# Frontend 서버 (B2B)
cd ../frontend-b2b
python -m http.server 8081
```

**접속 URL:**
- API 문서: http://localhost:8000/docs
- B2C 웹: http://localhost:8080
- B2B 관리자: http://localhost:8081

## API 엔드포인트

### B2C - 메뉴 식별
```http
POST /api/v1/menu/identify
Content-Type: application/json

{
  "menu_name_ko": "김치찌개"
}
```

**응답:**
```json
{
  "match_type": "exact",
  "canonical": {
    "name_ko": "김치찌개",
    "name_en": "Kimchi Jjigae (Kimchi Stew)",
    "explanation_short": {"en": "Spicy stew made with kimchi and pork"},
    "allergens": ["pork", "soy"],
    "spice_level": 3
  },
  "modifiers": [],
  "confidence": 1.0
}
```

### B2B - 메뉴판 OCR 인식
```http
POST /api/v1/menu/recognize
Content-Type: multipart/form-data

file: [image file]
```

**응답:**
```json
{
  "success": true,
  "menu_items": [
    {"name_ko": "김치찌개", "price_ko": "8,000"},
    {"name_ko": "순두부찌개", "price_ko": "9,500"}
  ],
  "raw_text": "김치찌개 8,000원\n순두부찌개 9,500원",
  "ocr_confidence": 0.92,
  "count": 2
}
```

## 개발 가이드

### 코딩 규칙
- 타입 힌트 필수
- async/await 적극 활용
- 환경변수 하드코딩 금지
- 자세한 내용: `CLAUDE.md` 참조

### 테스트
```bash
pytest
```

### 코드 검증 (Sprint 1에서 자동화 예정)
```bash
# 타입 체크
mypy app/backend

# 린트
ruff check app/backend

# 포맷
black app/backend
```

## 📚 문서

### 필수 문서 (Sprint 0 기준)
1. **프로젝트 규칙**: `CLAUDE.md` ⭐ 가장 먼저 읽기
2. **개발 로드맵**: `ROADMAP.md` (3주 Sprint 0 상세 계획)
3. **최종 기획**: `SPRINT0_FINAL_PLAN_20260219.md` (전략 및 배경)

### 설계 문서
- **설계 폴더**: `기획/3차_설계문서_20250211/`
- **DB 스키마**: `03_data_schema_v0.1.md` (9개 테이블, 공공데이터 필드 추가)
- **API 스펙**: `06_api_specification_v0.1.md` (4개 새 공공데이터 엔드포인트 포함)
- **데이터 흐름**: `04_data_flow_scenarios.md`
- **MVP 범위**: `05_mvp_scope_definition.md`

### 참고 자료
- **개발 환경 설정**: `C:\project\dev-reference\docs\FASTCOMET_DEPLOYMENT_GUIDE.md`
- **메모리 기록**: `.claude/projects/c--project-menu/memory/MEMORY.md` (API 키, 팀 결정)

## 🚀 로드맵

### **Sprint 0** 🆕 공공데이터 기반 기초 구축 (3주, 2026-02)
**상태**: 기획/설계 완료, 개발 시작 예정
**목표**: 157,000개 메뉴 자동 구축 + AI 호출 70% 절감

- **Week 1**: 메뉴젠 API (1,500개) + 서울 식당 (167,659개) 임포트
- **Week 2**: 영양정보 DB API (157개) + Redis 캐싱 + 검증
- **Week 3**: 문서화 + FastComet 배포

✅ **성과**:
- 157,000개 canonical_menus 자동 생성
- 정부 표준 음식코드 통합
- 영양정보 완전 연계 (JSONB + 캐싱)
- AI 호출 필요 감소 (DB 매칭률 ↑)
- **예상 절감**: 월 $210,000

---

### Sprint 1 (4주, 이후)
**목표**: OCR 파이프라인 최적화 + 실제 메뉴판 테스트

- CLOVA OCR 통합 최적화
- Matching Engine 고도화 (현장 오류 케이스 수집)
- 수식어 분해 정확도 > 80%

---

### Sprint 2 (3주, 이후)
**목표**: B2C 모바일 웹 + QR 배포

- 모바일 최적화 반응형 디자인
- 영양정보 시각화 (차트)
- QR 코드 자동 생성
- "Was this helpful?" 피드백 시스템

---

### Sprint 3 (장기)
**목표**: B2B 관리자 UI + 현장 운영

- Admin 화면 (신규 메뉴 큐 관리)
- 다국어 번역 (Papago 일/중)
- 성능 최적화 (응답 시간 < 3초)

## 라이선스

Proprietary
