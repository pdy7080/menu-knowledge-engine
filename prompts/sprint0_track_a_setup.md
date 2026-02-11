# 🔧 Sprint 0 / Track A — 프로젝트 기반 구축

## 너의 역할
너는 "Menu Knowledge Engine" 프로젝트의 개발자야.
이 프로젝트는 한국 음식 메뉴판을 AI/OCR로 인식하고, 자체 DB에서 매칭해서 외국인에게 문화적 맥락이 포함된 설명을 제공하는 서비스야.

## 지금 할 일: 프로젝트 초기 구조 + DB 생성

### 1단계: 프로젝트 디렉토리 구조 생성

```
C:\project\menu\app\
├── backend/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── requirements.txt        # Python 의존성
│   ├── config.py               # 환경 변수/설정
│   ├── database.py             # DB 연결 (SQLAlchemy)
│   ├── models/                 # SQLAlchemy 모델
│   │   ├── __init__.py
│   │   ├── concept.py          # concepts 테이블
│   │   ├── canonical_menu.py   # canonical_menus 테이블
│   │   ├── modifier.py         # modifiers 테이블
│   │   ├── menu_variant.py     # menu_variants 테이블
│   │   ├── menu_relation.py    # menu_relations 테이블
│   │   ├── shop.py             # shops 테이블
│   │   ├── scan_log.py         # scan_logs 테이블
│   │   ├── evidence.py         # evidences 테이블
│   │   └── cultural_concept.py # cultural_concepts 테이블
│   ├── api/
│   │   ├── __init__.py
│   │   ├── menu.py             # /api/v1/menu/* 라우터
│   │   ├── shop.py             # /api/v1/shop/* 라우터
│   │   └── admin.py            # /api/v1/admin/* 라우터
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr_service.py      # CLOVA OCR 연동
│   │   ├── matching_engine.py  # DB 매칭 + 수식어 분해
│   │   ├── ai_discovery.py     # GPT-4o Identity Discovery
│   │   └── translation.py     # 다국어 번역
│   ├── seeds/
│   │   ├── seed_concepts.py    # Concept 시드 데이터
│   │   ├── seed_modifiers.py   # Modifier 시드 데이터
│   │   ├── seed_canonical.py   # Canonical 시드 데이터 (빈 템플릿)
│   │   └── run_seeds.py        # 시드 실행 스크립트
│   └── tests/
│       ├── __init__.py
│       └── test_matching.py    # 수식어 분해 테스트
├── frontend/                   # (Sprint 2에서 구현)
│   └── .gitkeep
└── data/
    ├── menu_photos/            # 수집된 메뉴판 사진
    ├── test_results/           # 테스트 결과 로그
    └── .gitkeep
```

### 2단계: PostgreSQL 테이블 생성

아래 설계 문서를 읽고 SQLAlchemy 모델을 생성해:
- 스키마 파일: `C:\project\menu\기획\3차_설계문서_20250211\03_data_schema_v0.1.md`

핵심 테이블 9개:
1. concepts — 한식 개념 트리 (대분류/중분류)
2. canonical_menus — 표준 메뉴 (핵심!)
3. modifiers — 수식어 사전
4. menu_variants — 실제 식당 메뉴 변형
5. menu_relations — 메뉴 간 관계
6. shops — 식당 정보
7. scan_logs — 스캔 행동 로그
8. evidences — 출처 기록
9. cultural_concepts — 문화적 개념

**주의사항:**
- PostgreSQL 16+ 사용
- pgvector 확장은 설치만 하고 v0.2에서 활성화
- pg_trgm 확장 활성화 (유사 검색용)
- UUID 기본키 사용
- JSONB 필드 활용 (translations, allergens 등)
- created_at, updated_at 자동 관리

### 3단계: Concept 시드 데이터 입력

아래 파일을 읽고 Concept 시드 데이터를 생성해:
- 시드 가이드: `C:\project\menu\기획\3차_설계문서_20250211\07_seed_data_guide.md`

대분류 12개 + 중분류 ~35개 = 약 47개 레코드
- 국물요리 (탕/국/찌개/전골/해장국)
- 밥류 (비빔밥/덮밥/볶음밥/죽/국밥/정식)
- 면류 (국수/냉면/라면/칼국수)
- 구이류 (고기구이/생선구이)
- 찜/조림류
- 볶음류
- 전/부침류
- 반찬류 (나물/김치/젓갈)
- 분식류
- 안주류
- 음료류 (술/비알콜)
- 디저트류

### 4단계: Modifier 시드 데이터 입력

07_seed_data_guide.md의 50개 수식어를 입력해:
- taste (맛) 12개: 얼큰, 매운, 순, 담백한...
- size (크기) 7개: 왕, 대, 소, 곱빼기...
- emotion (감성) 10개: 할머니, 옛날, 시골...
- ingredient (재료) 10개: 한우, 해물, 야채...
- cooking (조리법) 6개: 불, 숯불, 직화...
- grade (등급) 3개: 특, 프리미엄, 스페셜
- origin (지역) 2개: 궁중, 부산

### 5단계: 기본 FastAPI 앱 구동 확인

- `main.py`에서 FastAPI 앱 생성
- DB 연결 확인
- `/health` 엔드포인트로 서버 상태 확인
- `/api/v1/concepts` 엔드포인트로 시드 데이터 조회 확인

### 완료 기준
- [ ] 프로젝트 디렉토리 구조 생성됨
- [ ] 9개 테이블 모두 PostgreSQL에 생성됨
- [ ] Concept 47개 레코드 입력됨
- [ ] Modifier 50개 레코드 입력됨
- [ ] FastAPI 서버가 localhost에서 구동됨
- [ ] /health 응답 정상
- [ ] /api/v1/concepts 응답에 47개 concept 반환됨

### 참조할 설계 문서 (반드시 읽어)
1. `C:\project\menu\기획\3차_설계문서_20250211\03_data_schema_v0.1.md` — DB 스키마
2. `C:\project\menu\기획\3차_설계문서_20250211\07_seed_data_guide.md` — 시드 데이터

질문 있으면 물어봐. 없으면 바로 시작해.
