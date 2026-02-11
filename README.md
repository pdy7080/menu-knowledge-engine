# Menu Knowledge Engine

> AI 기반 한국 음식 메뉴 다국어 변환 지식 엔진

## 개요

Menu Knowledge Engine은 한국 음식 메뉴를 "번역 대상"이 아닌 "정의된 지식 객체"로 전환하여, 다국어 설명·문화적 맥락·식이 정보를 구조화된 API로 제공하는 지식 엔진입니다.

### 핵심 차별점
- **Knowledge Graph 기반**: 메뉴를 개념 단위로 구조화
- **수식어 분해 시스템**: "할머니뼈해장국" → "할머니" + "뼈해장국"
- **자기강화 루프**: B2B(식당) + B2C(관광객) 양방향 데이터 수집
- **비용 절감 구조**: 1회 AI 학습 → DB 서빙

## 기술 스택

- **Backend**: FastAPI + SQLAlchemy (async)
- **Database**: PostgreSQL 16+ (pg_trgm, pgvector)
- **AI**: CLOVA OCR + GPT-4o + Papago
- **Python**: 3.11+

## 프로젝트 구조

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

## 문서

- **프로젝트 규칙**: `CLAUDE.md`
- **설계 문서**: `기획/3차_설계문서_20250211/`
- **DB 스키마**: `기획/3차_설계문서_20250211/03_data_schema_v0.1.md`
- **API 스펙**: `기획/3차_설계문서_20250211/06_api_specification_v0.1.md`

## 로드맵

- **Sprint 0-1** ✅: 프로젝트 기반 구축 (DB + 시드 + 기본 매칭 엔진)
  - PostgreSQL 스키마 9개 테이블
  - 시드 데이터: 112 canonical menus, 54 modifiers
  - 3단계 매칭 파이프라인 (Exact → Modifier Decomposition → AI Discovery)
  - 68% 매칭률 달성

- **Sprint 2** ✅: B2C 모바일 웹 프론트엔드
  - 모바일 최적화 반응형 디자인 (480px)
  - 단일/다중 메뉴 검색
  - AI Discovery 폴백 UI
  - API 통합 및 브라우저 테스트 통과

- **Sprint 3 P0** ✅: OCR 파이프라인 + AI 매칭 + B2B 프론트엔드
  - CLOVA OCR API 연동 + GPT-4o 메뉴 파싱
  - AI Discovery with GPT-4o (영문 번역 + 설명 생성)
  - B2B 관리자 페이지 (메뉴판 업로드 → OCR → 검수)
  - 신뢰도 기반 매칭 결과 시각화

- **Sprint 3 P1-P2** (진행 예정):
  - P1-1: Admin 화면 (신규 메뉴 큐 관리)
  - P1-2: 다국어 번역 (Papago 일/중)
  - P1-3: End-to-End 통합 테스트
  - P2-1: QR 메뉴 페이지
  - P2-2: 성능 최적화 (응답 시간 3초 이내)

## 라이선스

Proprietary
