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
│   ├── api/                 # API 라우터
│   ├── services/            # 비즈니스 로직
│   ├── seeds/               # 시드 데이터
│   └── tests/               # 테스트
├── frontend/                # (Sprint 2)
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
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API 문서: http://localhost:8000/docs

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

- **Sprint 0** (현재): 프로젝트 기반 구축 (DB + 시드 + 기본 API)
- **Sprint 1**: OCR 파이프라인 + 매칭 엔진
- **Sprint 2**: B2B/B2C 프론트엔드
- **Sprint 3**: 현장 테스트 + 최적화

## 라이선스

Proprietary
