# 🚀 검증팀 병렬 작업 지시서

> **팀명:** menu-validation-team
> **목적:** Sprint 3 MVP 완전 검증 (설계 vs 구현 vs 브라우저)
> **방식:** 6명 병렬 독립 작업
> **기간:** ~2시간
> **산출:** 통합 검증 리포트

---

## 📋 Task Distribution

| 순번 | 팀원 | 역할 | 주요 검증 | 예상시간 | 산출물 |
|------|------|------|---------|---------|--------|
| 1️⃣ | **Architecture-Reviewer** | 설계 vs 코드 구조 | DB 스키마, API 구조, 인덱싱 | 30분 | 구조 일치도 리포트 |
| 2️⃣ | **Feature-Validator** | 기능 요구사항 검증 | 10대 기능, 포함/제외 기능 | 25분 | 기능 구현 현황 |
| 3️⃣ | **Backend-QA** | API 스펙 검증 | 11개 엔드포인트, 비즈니스 로직 | 35분 | API 일치도 리포트 |
| 4️⃣ | **Frontend-Tester** | 브라우저 동작 | UI 렌더링, 상호작용, 반응형 | 40분 | 스크린샷 + 이슈 |
| 5️⃣ | **I18n-Auditor** | 다국어 검증 | 번역 완성도, Papago, UI 표시 | 30분 | 번역 현황 리포트 |
| 6️⃣ | **Performance-Lead** | 성능 검증 | 응답시간, DB최적화, 비용 | 25분 | 성능 벤치마크 |

---

## 👤 Task 1: Architecture-Reviewer

### 📌 역할
설계 문서(03_data_schema, 06_api_specification)와 구현 코드의 구조적 일치도 검증

### 📂 검증 파일
```
설계: C:\project\menu\기획\3차_설계문서_20250211\
  - 03_data_schema_v0.1.md (DB 테이블 정의)
  - 06_api_specification_v0.1.md (API 엔드포인트)

구현: C:\project\menu\app\backend\
  - models/ (SQLAlchemy 모델)
  - api/ (라우터)
  - migrations/performance_optimization.sql (인덱싱)
```

### ✅ 검증 체크리스트

```
[ ] DB 테이블 설계 vs 구현

필수 9개 테이블:
  [✓/✗] concepts
  [✓/✗] modifiers
  [✓/✗] canonical_menus
  [✓/✗] menu_variants
  [✓/✗] shops
  [✓/✗] menu_relations
  [✓/✗] scan_logs
  [✓/✗] evidences
  [✓/✗] cultural_concepts

[ ] 테이블 관계 (ForeignKey)
  각 테이블의 PK/FK가 설계대로 구현됐는가?

[ ] 컬럼 정의 (데이터 타입, nullable)
  설계의 "VARCHAR", "JSONB", "UUID" 등이
  코드에서 올바른 타입으로 구현됐는가?

[ ] 타임스탐프 (created_at, updated_at)
  모든 테이블에 UTC 기준으로 자동 관리되는가?

[ ] 인덱싱 전략 (15개 인덱싱)
  performance_optimization.sql에서:
  - canonical_menus.name_ko (정확 매칭)
  - pg_trgm (유사 검색)
  - concept_id (조회 성능)
  - created_at (정렬)
  등이 모두 존재하는가?

[ ] API 엔드포인트 구조 (11개)
  설계 vs 코드:
  [✓/✗] GET /health
  [✓/✗] POST /api/v1/menu/identify
  [✓/✗] POST /api/v1/menu/recognize
  [✓/✗] GET /api/v1/admin/queue
  [✓/✗] POST /api/v1/admin/queue/{id}/approve
  [✓/✗] GET /api/v1/admin/stats
  [✓/✗] GET /qr/{shop_code}
  [✓/✗] GET /api/v1/concepts
  [✓/✗] GET /api/v1/modifiers
  [✓/✗] GET /api/v1/canonical-menus
  [✓/✗] GET /docs

[ ] 요청/응답 스키마
  각 엔드포인트의:
  - 요청 JSON 스키마 (06_api 설계와 일치?)
  - 응답 JSON 스키마 (필드명, 데이터타입)
```

### 📊 산출 포맷

```markdown
# Architecture Validation Report

## 1. DB 스키마 일치도
- 테이블 완성도: 9/9 (100%)
- 컬럼 일치도: XX/XX (XX%)
- ForeignKey 정합성: ✅/⚠️/❌

## 2. 인덱싱 전략
- 인덱스 수: 15개 ✅
- 성능 향상도: 10배 ✅

## 3. API 엔드포인트 구조
- 엔드포인트 수: 11/11 ✅
- 스키마 일치도: XX%

## 4. 불일치 항목
- 발견된 이슈: N개
- 우선순위:
  - P0 (배포 차단): N개
  - P1 (권장): N개
  - P2 (개선): N개

## 5. 최종 평가
- 구조 일치도: XX%
- 배포 준비도: GO/CONDITIONAL/NO-GO
```

---

## 👤 Task 2: Feature-Validator

### 📌 역할
설계된 10대 기능이 모두 구현되었는지, 추가 기능은 없는지 검증

### 📂 검증 파일
```
설계: C:\project\menu\기획\3차_설계문서_20250211\
  - 05_mvp_scope_definition.md (기능 범위 정의)

구현: C:\project\menu\app\
  - backend/services/ (비즈니스 로직)
  - frontend/ (B2C 기능)
  - frontend-b2b/ (B2B 기능)
```

### ✅ 검증 체크리스트

```
[ ] MVP 포함 기능 (10개) — 모두 구현됐나?

F1: 메뉴판 OCR
  [✓/✗] /api/v1/menu/recognize 엔드포인트 있음
  [✓/✗] CLOVA OCR 연동 코드 있음
  [✓/✗] 메뉴명/가격 파싱 로직 있음
  구현 여부: [완료/진행중/미포함]

F2: DB 매칭 (4단계 파이프라인)
  [✓/✗] 정확 매칭 (canonical_menus.name_ko)
  [✓/✗] 유사 검색 (pg_trgm)
  [✓/✗] 수식어 분해 (modifiers)
  [✓/✗] AI Discovery (GPT-4o)
  구현 여부: [완료/진행중/미포함]

F3: 수식어 분해
  [✓/✗] modifiers 테이블 데이터 있음 (54개)
  [✓/✗] 분해 로직 구현됨
  구현 여부: [완료/진행중/미포함]

F4: AI Identity Discovery
  [✓/✗] GPT-4o 호출 코드
  [✓/✗] 영문 설명 생성
  [✓/✗] confidence 점수
  구현 여부: [완료/진행중/미포함]

F5: 다국어 설명 출력
  [✓/✗] 영어 (GPT-4o)
  [✓/✗] 일본어 (Papago)
  [✓/✗] 중국어 (Papago)
  구현 여부: [완료/진행중/미포함]

F6: B2B 메뉴 등록
  [✓/✗] frontend-b2b/index.html 있음
  [✓/✗] 메뉴 업로드 UI
  [✓/✗] 검수 화면
  구현 여부: [완료/진행중/미포함]

F7: B2C 메뉴 스캔
  [✓/✗] frontend/index.html 있음
  [✓/✗] 검색 UI
  [✓/✗] 결과 표시
  구현 여부: [완료/진행중/미포함]

F8: 일/중 언어 지원
  [✓/✗] Papago 번역 서비스
  [✓/✗] UI에 언어 탭
  구현 여부: [완료/진행중/미포함]

F9: 스캔 로그 기록
  [✓/✗] scan_logs 테이블
  [✓/✗] 로깅 로직
  구현 여부: [완료/진행중/미포함]

F10: 사장님 수정 기능
  [✓/✗] menu_variants에 human_verified 필드
  [✓/✗] 수정 UI (B2B-2)
  구현 여부: [완료/진행중/미포함]

[ ] MVP 제외 기능 — 실수로 구현된 것 없나?

제외 기능 (v0.2+):
  [✓/✗] 동남아 언어 (없음 = 정상)
  [✓/✗] 난이도 스코어 대시보드 (없음 = 정상)
  [✓/✗] pgvector (활성화 안 됨 = 정상)
  [✓/✗] 결제/구독 시스템 (없음 = 정상)
  [✓/✗] 네이버/구글맵 연동 (없음 = 정상)
  [✓/✗] 성수야 완전 통합 (API만 = 정상)

실수 구현: [0개/N개]
```

### 📊 산출 포맷

```markdown
# Feature Implementation Report

## 1. MVP 기능 구현 현황
| # | 기능 | 상태 | 완성도 |
|---|------|------|--------|
| F1 | 메뉴판 OCR | ✅ 완료 | 100% |
| F2 | DB 매칭 | ✅ 완료 | 100% |
| ... | ... | ... | ... |
| F10 | 사장님 수정 | ✅ 완료 | 100% |

## 2. 기능 구현 현황 요약
- 예정 기능 (10개): 10개 ✅ (100%)
- 제외 기능: 0개 실수 구현 ✅
- 추가 기능: N개 (scope creep 확인)

## 3. 미완료 기능
- 없음 ✅

## 4. 최종 평가
- 기능 완성도: 100%
- 배포 준비도: GO ✅
```

---

## 👤 Task 3: Backend-QA

### 📌 역할
11개 API 엔드포인트의 스펙 일치도 및 비즈니스 로직 검증

### 📂 검증 파일
```
설계: C:\project\menu\기획\3차_설계문서_20250211\
  - 06_api_specification_v0.1.md (API 스펙)
  - 04_data_flow_scenarios.md (시나리오)

구현: C:\project\menu\app\backend\
  - api/menu.py, admin.py, qr_menu.py
  - services/matching_engine.py
```

### ✅ 검증 체크리스트

```
[ ] 각 엔드포인트별 스펙 검증

1. POST /api/v1/menu/identify
   요청:
   [✓/✗] {"menu_name_ko": "string"} 스키마
   응답:
   [✓/✗] match_type (exact|modifier|ai_discovery)
   [✓/✗] confidence (0.0~1.0)
   [✓/✗] canonical (메뉴 데이터)
   비즈니스:
   [✓/✗] 4단계 파이프라인 구현
   [✓/✗] 신뢰도 계산
   [✓/✗] 에러 처리 (400, 500)

2. POST /api/v1/menu/recognize
   요청:
   [✓/✗] multipart/form-data (file)
   응답:
   [✓/✗] menu_items (배열)
   [✓/✗] ocr_confidence
   [✓/✗] count
   비즈니스:
   [✓/✗] CLOVA OCR 호출
   [✓/✗] 메뉴명/가격 파싱
   [✓/✗] 타임아웃 (< 5초)

3. GET /api/v1/admin/queue
   요청:
   [✓/✗] status, source, limit, offset 파라미터
   응답:
   [✓/✗] 큐 항목 배열
   [✓/✗] 페이지네이션
   비즈니스:
   [✓/✗] 신규 메뉴 필터링
   [✓/✗] 정렬

4. POST /api/v1/admin/queue/{id}/approve
   요청:
   [✓/✗] action (approve|reject|edit)
   응답:
   [✓/✗] 승인 결과
   비즈니스:
   [✓/✗] scan_logs 업데이트
   [✓/✗] evidences 기록
   [✓/✗] 트랜잭션

5. GET /api/v1/admin/stats
   응답:
   [✓/✗] canonical_count
   [✓/✗] modifier_count
   [✓/✗] db_hit_rate_7d
   [✓/✗] ai_cost_7d
   [✓/✗] pending_queue_count

6. GET /qr/{shop_code}
   요청:
   [✓/✗] lang 파라미터 (en|ja|zh)
   응답:
   [✓/✗] HTML 렌더링
   캐싱:
   [✓/✗] Cache-Control 헤더

7-11. 기본 엔드포인트
   [✓/✗] /health
   [✓/✗] /api/v1/concepts
   [✓/✗] /api/v1/modifiers
   [✓/✗] /api/v1/canonical-menus
   [✓/✗] /docs (Swagger)

[ ] 4단계 매칭 파이프라인 로직

단계별 검증:
  단계1 (정확):
    [✓/✗] SELECT * FROM canonical_menus WHERE name_ko = ?
    [✓/✗] 신뢰도: 1.0
    [✓/✗] 응답: ~100ms

  단계2 (유사):
    [✓/✗] pg_trgm 사용
    [✓/✗] 신뢰도: >0.8
    [✓/✗] 응답: ~200ms

  단계3 (수식어):
    [✓/✗] modifiers 분해
    [✓/✗] 신뢰도: 0.6~0.8
    [✓/✗] 응답: ~300ms

  단계4 (AI):
    [✓/✗] GPT-4o 호출
    [✓/✗] confidence 점수
    [✓/✗] 응답: ~1.5s

[ ] 데이터 무결성

  [✓/✗] UUID 사용 (보안)
  [✓/✗] Timestamp (UTC, 자동 관리)
  [✓/✗] JSONB (다국어, 유연성)
  [✓/✗] Nullable 규칙 준수
  [✓/✗] Foreign Key 제약

[ ] 에러 처리

  [✓/✗] 400 Bad Request (잘못된 요청)
  [✓/✗] 404 Not Found
  [✓/✗] 500 Internal Server Error
  [✓/✗] 에러 메시지 (명확한가?)
```

### 📊 산출 포맷

```markdown
# Backend QA Report

## 1. API 엔드포인트 스펙 일치도
- 총 11개 엔드포인트
- 스펙 일치: XX/11 (XX%)
- 불일치 항목: N개

## 2. 4단계 매칭 파이프라인
- 단계 1 (정확): ✅ 구현
- 단계 2 (유사): ✅ 구현
- 단계 3 (수식어): ✅ 구현
- 단계 4 (AI): ✅ 구현

## 3. 응답 시간
- 평균: ~XXms ✅/⚠️
- 목표 (3초): 충족 여부

## 4. 발견 이슈
- P0: N개
- P1: N개
- P2: N개

## 5. 최종 평가
- API 완성도: XX%
- 배포 준비도: GO/CONDITIONAL/NO-GO
```

---

## 👤 Task 4: Frontend-Tester

### 📌 역할
실제 브라우저에서 UI/UX 동작 검증 (스크린샷 포함)

### 📂 검증 파일
```
설계: C:\project\menu\기획\3차_설계문서_20250211\
  - 08_wireframe_v0.1.md (와이어프레임)

구현: C:\project\menu\app\
  - frontend/index.html, css/, js/
  - frontend-b2b/index.html, admin.html, css/, js/
```

### ✅ 검증 체크리스트

```
[ ] B2C 페이지 테스트 (localhost:8080)

화면 1: Landing
  [✓/✗] 제목 표시 (🍲 Menu Lens Korea)
  [✓/✗] 언어 드롭다운 (기본: EN)
  [✓/✗] 사진 업로드 버튼
  [✓/✗] 갤러리 선택 옵션
  [✓/✗] 텍스트 검색 입력
  [✓/✗] 태그라인 표시

화면 2: 결과 리스트
  [✓/✗] 메뉴 카드 렌더링 (N개)
  [✓/✗] 카드 구성:
    - 영문명 (composed_name_en)
    - 한글명 + 로마자
    - 설명 (1문장, 영어)
    - 맵기 아이콘 (🟢/🔴)
    - 알레르기 아이콘
    - 난이도 (⭐⭐)
  [✓/✗] [More] 버튼 클릭 → 상세 설명 팝업
  [✓/✗] [Allergy] 버튼 → 알레르기 정보
  [✓/✗] "Analyzing..." 진행 표시 (AI Discovery 중)
  [✓/✗] 피드백 버튼 (Was this helpful?)
  [✓/✗] 식당 공유 버튼

[ ] B2B 페이지 테스트 (localhost:8081)

B2B-1 메뉴 업로드:
  [✓/✗] 사진 업로드 영역
  [✓/✗] "2분 내 완성" 문구
  [✓/✗] 또는 직접 추가 옵션
  [✓/✗] 업로드 진행 표시

B2B-2 검수 화면:
  [✓/✗] 인식 메뉴 카운트 (N개 인식됨)
  [✓/✗] 신뢰도 배지 표시:
    - ✅ (높은 신뢰도)
    - ⚠️ (확인 필요)
    - ❓ (낮은 신뢰도)
  [✓/✗] 각 메뉴 카드:
    - 인식된 이름
    - 매칭된 canonical
    - 수식어 분해 결과
    - 영/일/중 번역
    - 난이도, 알레르기
  [✓/✗] [수정] 버튼 → 모달 열림
  [✓/✗] [전체 승인] 버튼 → DB 저장

Admin 대시보드 (localhost:8081/admin.html):
  [✓/✗] 신규 메뉴 큐 (리스트)
  [✓/✗] 필터 탭 ([전체] [확인필요] [자동등록])
  [✓/✗] 각 항목:
    - 메뉴명, 소스, 분해 결과
    - 확신도 점수
  [✓/✗] 액션 버튼 ([승인] [수정] [신규])
  [✓/✗] 우측 통계 패널:
    - Canonical 수
    - Modifier 수
    - DB 히트율 (%)
    - AI 비용 (₩)
    - 미검토 큐 수
  [✓/✗] 통계는 5초마다 갱신

[ ] QR 메뉴 페이지 테스트

동적 페이지 (http://localhost:8000/qr/{shop_code}):
  [✓/✗] 식당명 표시 (한/영)
  [✓/✗] 언어 탭 (EN / JA / ZH)
  [✓/✗] 탭 클릭 → 해당 언어로 전환
  [✓/✗] 카테고리별 메뉴 섹션
  [✓/✗] 각 메뉴:
    - 이미지 (있으면)
    - 영어명
    - 한글명 + 로마자
    - 상세 설명 (3-5문장)
    - 맵기, 알레르기, 난이도
    - 가격
  [✓/✗] 문화 팁 섹션 (반찬, 호출벨 등)

[ ] 모바일 반응형 테스트

DevTools에서 480px로 축소하여 테스트:
  [✓/✗] 레이아웃 깨짐 없음
  [✓/✗] 텍스트 가독성 (폰트 크기)
  [✓/✗] 버튼 크기 (터치 용이)
  [✓/✗] 이미지 스케일 (로딩 속도)
  [✓/✗] 스크롤 (한 손 조작 가능)

[ ] 성능 테스트

DevTools 네트워크/성능 탭:
  [✓/✗] 페이지 로드 시간 (< 3초)
  [✓/✗] 번들 크기 (< 500KB)
  [✓/✗] Lighthouse 점수 (> 80)
  [✓/✗] 이미지 최적화 (webp, lazy loading)

[ ] 이상 현상

DevTools 콘솔:
  [✓/✗] JavaScript 에러 (없어야 함)
  [✓/✗] 경고 (최소화해야 함)
  [✓/✗] 네트워크 에러 (없어야 함)
```

### 📊 산출 포맷

```markdown
# Frontend Testing Report

## 1. UI 렌더링 일치도
- B2C 페이지: XX% ✅
- B2B 페이지: XX% ✅
- Admin 대시보드: XX% ✅
- QR 메뉴: XX% ✅

## 2. 모바일 반응형
- 480px 최적화: ✅/⚠️
- 터치 친화성: ✅/⚠️

## 3. 성능
- 페이지 로드: XXms ✅/⚠️
- Lighthouse: XXX ✅/⚠️

## 4. 콘솔 에러
- JavaScript 에러: 0개 ✅
- 네트워크 에러: 0개 ✅

## 5. 스크린샷
[이미지 첨부]

## 6. 최종 평가
- UI 완성도: XX%
- 배포 준비도: GO/CONDITIONAL/NO-GO
```

---

## 👤 Task 5: I18n-Auditor

### 📌 역할
다국어 번역 완성도 및 UI 표시 검증

### 📂 검증 파일
```
설계: C:\project\menu\기획\3차_설계문서_20250211\
  - 05_mvp_scope_definition.md (F8: 일/중 언어)

구현: C:\project\menu\app\
  - backend/services/translation_service.py
  - frontend/ (언어 탭 UI)
```

### ✅ 검증 체크리스트

```
[ ] 언어 지원 범위

  [✓/✗] 영어 (필수) - GPT-4o 생성
  [✓/✗] 일본어 (필수) - Papago 번역
  [✓/✗] 중국어 (필수) - Papago 번역
  [✓/✗] 기타 언어 (제외 확인) - 없어야 함

[ ] 번역 데이터 완성도

  각 canonical_menu에 대해:
    [✓/✗] explanation_short
      - en (존재)
      - ja (번역됨)
      - zh (번역됨)

    [✓/✗] explanation_long
      - en (존재)
      - ja (번역됨)
      - zh (번역됨)

    [✓/✗] cultural_context
      - en (존재)
      - ja (번역됨)
      - zh (번역됨)

    [✓/✗] main_ingredients
      - 모든 언어에서 표시됨

  완성도: XX/112 (xx%)

[ ] Papago 번역 검증

  [✓/✗] API 연동 (클라이언트 ID/시크릿 설정)
  [✓/✗] 배치 번역 (모든 메뉴 번역됨)
  [✓/✗] 캐싱 작동 (DB에 저장됨, 재번역 안 함)
  [✓/✗] 번역 품질 샘플 (3-5개 메뉴)
    - 메뉴 A: KO → EN ✅ → JA ✅ → ZH ✅
    - 메뉴 B: ...
    - 메뉴 C: ...

[ ] 프론트엔드 표시

  B2C 결과 (localhost:8080):
    [✓/✗] 언어 탭 (EN / JA / ZH)
    [✓/✗] 탭 클릭 → 즉시 언어 전환
    [✓/✗] 설명 텍스트 변경됨
    [✓/✗] 번역 누락 없음 (???)

  QR 메뉴:
    [✓/✗] ?lang=en|ja|zh 파라미터 작동
    [✓/✗] 전체 메뉴 해당 언어로 표시
    [✓/✗] 캐싱 (언어별)

[ ] 이모지 / 문화 표현

  [✓/✗] 맵기 아이콘:
    - 🟢 (mild)
    - 🟡 (medium)
    - 🔴 (spicy)

  [✓/✗] 알레르기 아이콘:
    - 🐷 (pork)
    - 🐄 (beef)
    - 🦐 (shellfish)
    - 🥜 (peanuts)

  [✓/✗] 난이도:
    - ⭐ (easy)
    - ⭐⭐ (medium)
    - ⭐⭐⭐⭐⭐ (hard)

  [✓/✗] 언어별 일관성 (모든 언어에서 동일)

[ ] 누락 확인

  다음이 번역되지 않았나?
  [✓/✗] 메인 메뉴명
  [✓/✗] 설명
  [✓/✗] 재료
  [✓/✗] 문화 팁
```

### 📊 산출 포맷

```markdown
# I18n Validation Report

## 1. 언어 지원
- 영어: ✅ (GPT-4o)
- 일본어: ✅ (Papago)
- 중국어: ✅ (Papago)

## 2. 번역 완성도
- 메뉴: 112/112 (100%)
- 설명: XX/112 (xx%)
- 재료: XX/112 (xx%)
- 종합: XX%

## 3. Papago 번역 품질
- 샘플 1 (메뉴명): 좋음/보통/나쁨
- 샘플 2: 좋음/보통/나쁨
- 샘플 3: 좋음/보통/나쁨

## 4. UI 표시
- B2C 언어 탭: ✅
- QR 메뉴 언어 전환: ✅
- 번역 누락: 0개 ✅

## 5. 최종 평가
- 번역 완성도: XX%
- 배포 준비도: GO/CONDITIONAL/NO-GO
```

---

## 👤 Task 6: Performance-Lead

### 📌 역할
응답 시간, DB 최적화, 비용 추정 검증

### 📂 검증 파일
```
설계: C:\project\menu\기획\3차_설계문서_20250211\
  - 05_mvp_scope_definition.md (비용 추정)

구현:  C:\project\menu\app\
  - backend/migrations/performance_optimization.sql
  - backend/scripts/benchmark.py
```

### ✅ 검증 체크리스트

```
[ ] 응답 시간 (목표: ≤3초)

API 응답 시간 측정:

  [✓/✗] POST /api/v1/menu/identify (정확)
        - 요청: {"menu_name_ko": "김치찌개"}
        - 예상: ~100ms
        - 실제: XXms
        - 상태: ✅/⚠️

  [✓/✗] POST /api/v1/menu/identify (수식어)
        - 요청: {"menu_name_ko": "할머니김치찌개"}
        - 예상: ~300ms
        - 실제: XXms
        - 상태: ✅/⚠️

  [✓/✗] POST /api/v1/menu/identify (AI)
        - 요청: {"menu_name_ko": "미등록메뉴"}
        - 예상: ~1.5s
        - 실제: XXms
        - 상태: ✅/⚠️

  [✓/✗] POST /api/v1/menu/recognize
        - 예상: ~2.5s
        - 실제: XXms
        - 상태: ✅/⚠️

  [✓/✗] GET /qr/{shop_code}
        - 예상: ~200ms (캐시)
        - 실제: XXms
        - 상태: ✅/⚠️

[ ] DB 최적화

  인덱싱:
    [✓/✗] 인덱스 생성 스크립트 실행됨
    [✓/✗] 총 15개 인덱스 확인:
      - canonical_menus.name_ko ✓
      - pg_trgm ✓
      - concept_id ✓
      - created_at ✓
      - (기타 12개)

  성능 개선:
    [✓/✗] 최적화 전: 3.2s
    [✓/✗] 최적화 후: ~500ms
    [✓/✗] 향상도: 6배 이상 ✅

[ ] 캐싱 전략

  [✓/✗] Redis 준비 (v0.1은 선택사항)
  [✓/✗] 캐싱 키 전략:
    - canonical:{menu_id}
    - translation:{lang}:{menu_id}
    - qr:{shop_code}

[ ] 비용 추정 (월간)

  CLOVA OCR:
    - 단가: ~15원/건
    - 예상 사용: 1,000건
    - 월 비용: ~15,000원
    - 확인: [✓/✗]

  GPT-4o (Identity Discovery):
    - 단가: ~0.01$/요청
    - 예상: 300건
    - 월 비용: ~$3 (~4,000원)
    - 확인: [✓/✗]

  GPT-4o (설명 생성):
    - 단가: ~0.02$/요청
    - 예상: 300건
    - 월 비용: ~$6 (~8,000원)
    - 확인: [✓/✗]

  Papago:
    - 월 비용: 0원 (일 10,000자 무료)
    - 확인: [✓/✗]

  DB (PostgreSQL):
    - 월 비용: ~50,000원
    - 확인: [✓/✗]

  S3 스토리지:
    - 월 비용: ~230원
    - 확인: [✓/✗]

  총 월 비용: ~77,000원
  확인: [✓/✗]

[ ] AI 비용 트렌드

  시간이 지날수록:
  [✓/✗] DB 매칭률 증가 → AI 호출 감소
  [✓/✗] 예상: 3개월 후 월 비용 50% 감소
```

### 📊 산출 포맷

```markdown
# Performance Validation Report

## 1. 응답 시간
| API | 목표 | 실제 | 상태 |
|-----|------|------|------|
| /identify (정확) | 100ms | XXms | ✅/⚠️ |
| /identify (수식어) | 300ms | XXms | ✅/⚠️ |
| /identify (AI) | 1500ms | XXms | ✅/⚠️ |
| /recognize | 2500ms | XXms | ✅/⚠️ |
| /qr | 200ms | XXms | ✅/⚠️ |

## 2. DB 최적화
- 인덱스: 15개 ✅
- 성능 향상: 6배 이상 ✅
- 응답 시간 p95: ~XXms

## 3. 월간 비용 추정
- CLOVA OCR: ~15,000원
- GPT-4o: ~12,000원
- DB: ~50,000원
- 기타: ~230원
- **총합: ~77,000원/월** ✅

## 4. 비용 트렌드
- 3개월 후: ~50% 감소 예상

## 5. 최종 평가
- 성능 목표 달성: XX%
- 배포 준비도: GO/CONDITIONAL/NO-GO
```

---

## 🎯 최종 산출물

모든 팀원이 작업을 완료한 후:

```
C:\project\menu\VALIDATION_REPORTS\
├── 01_Architecture_Review.md        (Architecture-Reviewer)
├── 02_Feature_Validation.md         (Feature-Validator)
├── 03_Backend_QA.md                 (Backend-QA)
├── 04_Frontend_Testing.md           (Frontend-Tester)
├── 05_I18n_Validation.md            (I18n-Auditor)
├── 06_Performance_Report.md         (Performance-Lead)
└── FINAL_VALIDATION_REPORT.md       (종합 리포트)
```

