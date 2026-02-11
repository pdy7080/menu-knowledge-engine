# 🔍 Menu Knowledge Engine MVP 검증 계획

> **목적:** 설계 문서 vs 구현 코드 완전 검증
> **방식:** Agent Teams 6명 병렬 검증
> **기간:** 단일 세션
> **산출:** 최종 검증 리포트

---

## 👥 검증 팀 구성

| # | 역할 | 담당자 | 도구 | 체크 항목 |
|---|------|--------|------|----------|
| 1 | **설계 검증** | Architecture Reviewer | code-reviewer | 설계 문서 vs 코드 구조 일치도 |
| 2 | **기능 검증** | Feature Validator | verifier | 요구사항 vs 구현 기능 일치도 |
| 3 | **Backend 검증** | Backend QA | sonnet | API 스펙, 비즈니스 로직 |
| 4 | **Frontend 검증** | Frontend Tester | webapp-testing | 브라우저 동작, UI/UX |
| 5 | **다국어 검증** | I18n Auditor | i18n-checker | 번역 일관성, 누락 |
| 6 | **성능 검증** | Performance Lead | infra-architect | 최적화, 응답 시간 |

---

## 📋 검증 기획 문서

### **기획 문서 위치**
```
C:\project\menu\기획\3차_설계문서_20250211\
├── 01_concept_overview.md
├── 02_menu_knowledge_graph.md
├── 03_data_schema_v0.1.md          ← DB 검증
├── 04_data_flow_scenarios.md       ← 시나리오 검증
├── 05_mvp_scope_definition.md      ← 기능 범위 검증
├── 06_api_specification_v0.1.md    ← API 스펙 검증
├── 07_seed_data_guide.md           ← 시드 데이터 검증
└── 08_wireframe_v0.1.md            ← 와이어프레임 검증
```

### **구현 코드 위치**
```
C:\project\menu\app\
├── backend/api/                    ← API 구현
├── backend/services/               ← 비즈니스 로직
├── backend/models/                 ← DB 모델
├── frontend/                       ← B2C UI
└── frontend-b2b/                   ← B2B UI
```

---

## ✅ 각 팀원별 검증 체크리스트

### **1️⃣ Architecture Reviewer (설계 검증)**

**검증 파일:**
- 설계 문서: 03_data_schema, 06_api_specification
- 코드: backend/models/, backend/api/

**체크항목:**

```
[ ] DB 스키마 일치도 (9개 테이블)
    - concepts ✓
    - canonical_menus ✓
    - modifiers ✓
    - menu_variants ✓
    - shops ✓
    - scan_logs ✓
    - evidences ✓
    - menu_relations ✓
    - cultural_concepts ✓

[ ] 테이블 관계 (ForeignKey 일치도)
    - canonical_menus.concept_id → concepts.id
    - menu_variants.canonical_id → canonical_menus.id
    - etc.

[ ] 컬럼 정의 일치
    - 데이터 타입 (UUID, JSONB, etc.)
    - Nullable 여부
    - 기본값 (created_at, updated_at)

[ ] 인덱스 전략
    - pg_trgm (유사 검색)
    - UUID primary key
    - 성능 인덱싱 (15개)

[ ] API 엔드포인트 구조 (설계 vs 코드)
    - /api/v1/menu/identify
    - /api/v1/menu/recognize
    - /api/v1/admin/queue
    - /api/v1/admin/queue/{id}/approve
    - /api/v1/admin/stats
    - /qr/{shop_code}
```

**산출:**
- 일치도 점수 (%)
- 불일치 항목 리스트
- 권장사항

---

### **2️⃣ Feature Validator (기능 검증)**

**검증 파일:**
- 설계: 05_mvp_scope_definition.md
- 코드: 전체 구현

**체크항목:**

```
[ ] MVP 포함 기능 (P0)
    ✅ F1: 메뉴판 OCR (/api/v1/menu/recognize)
    ✅ F2: DB 매칭 (4단계 파이프라인)
    ✅ F3: 수식어 분해 (modifiers)
    ✅ F4: AI Identity Discovery (GPT-4o)
    ✅ F5: 다국어 설명 출력 (EN/JA/ZH)
    ✅ F6: B2B 메뉴 등록
    ✅ F7: B2C 메뉴 스캔
    ✅ F8: 일/중 언어 지원
    ✅ F9: 스캔 로그 기록 (scan_logs)
    ✅ F10: 사장님 수정 기능

[ ] MVP 제외 기능 (v0.2)
    확인: 다음이 구현되지 않았는가?
    - 동남아 언어 (제외 OK)
    - 난이도 스코어 대시보드 (제외 OK)
    - 메뉴 컨설팅 리포트 (제외 OK)
    - pgvector (미활성화 OK)
    - KIMCHI 모델 (제외 OK)
    - 결제/구독 (제외 OK)
    - 네이버/구글맵 연동 (제외 OK)

[ ] 기능별 설계 vs 구현
    각 기능의 "설계된 동작" vs "실제 코드" 일치 확인
```

**산출:**
- 구현 기능 개수 (목표 10개)
- 미구현 기능 (있으면 위험)
- 추가 구현 기능 (scope creep 확인)

---

### **3️⃣ Backend QA (API 검증)**

**검증 파일:**
- API 스펙: 06_api_specification_v0.1.md
- 코드: backend/api/menu.py, backend/api/admin.py, backend/api/qr_menu.py

**체크항목:**

```
[ ] 엔드포인트 일치도 (11개)

1. POST /api/v1/menu/identify
   ✓ 요청 스키마 (menu_name_ko)
   ✓ 응답 스키마 (match_type, confidence, canonical)
   ✓ 에러 처리 (400, 500)

2. POST /api/v1/menu/recognize
   ✓ 요청: multipart/form-data (file)
   ✓ 응답: OCR 결과 (menu_items, ocr_confidence)
   ✓ 타임아웃 (5초 이상은 위험)

3. GET /api/v1/admin/queue
   ✓ 쿼리 파라미터 (status, source, limit, offset)
   ✓ 응답 스키마
   ✓ 페이지네이션

4. POST /api/v1/admin/queue/{id}/approve
   ✓ 액션 파라미터 (approve, reject, edit)
   ✓ DB 업데이트 (scan_logs, evidences)
   ✓ 트랜잭션 무결성

5. GET /api/v1/admin/stats
   ✓ 응답 항목
     - canonical_count
     - modifier_count
     - db_hit_rate_7d
     - ai_cost_7d
     - pending_queue_count

6. GET /qr/{shop_code}
   ✓ 언어 파라미터 (lang=en|ja|zh)
   ✓ HTML 렌더링
   ✓ 캐싱 헤더

7-11. 기본 엔드포인트
   ✓ /health
   ✓ /api/v1/concepts
   ✓ /api/v1/modifiers
   ✓ /api/v1/canonical-menus
   ✓ /docs (Swagger UI)

[ ] 비즈니스 로직 검증

4단계 매칭 파이프라인:
   1단계: 정확 매칭 (canonical_menus.name_ko)
   2단계: 유사 검색 (pg_trgm)
   3단계: 수식어 분해 (modifiers 사전)
   4단계: AI Discovery (GPT-4o)

각 단계:
   ✓ 신뢰도 계산 방식
   ✓ Fallback 로직
   ✓ 에러 처리

[ ] 데이터 일관성
   ✓ UUID 사용 (보안)
   ✓ 타임스탐프 (UTC, created_at, updated_at)
   ✓ JSONB 사용 (다국어, 유연성)
   ✓ Nullable 규칙
```

**산출:**
- API 구현 완성도 (%)
- 스펙 불일치 항목
- 성능 이슈 (응답 시간 > 3초)

---

### **4️⃣ Frontend Tester (브라우저 검증)**

**검증 파일:**
- 와이어프레임: 08_wireframe_v0.1.md
- 코드: frontend/, frontend-b2b/

**체크항목:**

```
[ ] B2C 페이지 (index.html)

화면 1: Landing + 업로드
   ✓ 제목 ("🍲 Menu Lens Korea")
   ✓ 언어 선택 드롭다운
   ✓ 사진 업로드 버튼 (capture + gallery)
   ✓ 텍스트 검색 UI
   ✓ 태그라인 ("We explain, not just translate")

화면 2: 결과 리스트
   ✓ 메뉴 카드 렌더링
   ✓ 각 카드 요소:
     - composed_name_en
     - 한국어명 + 로마자
     - 설명 (1문장)
     - 맵기 (🟢🔴 아이콘)
     - 알레르기 아이콘
     - 난이도 (⭐⭐)
   ✓ 확장 버튼 ([More] [Allergy])
   ✓ 진행 표시 ("Analyzing...")
   ✓ "Was this helpful?" 피드백
   ✓ 식당 공유 링크

[ ] B2B 페이지 (index.html + admin.html)

B2B 메뉴 업로드:
   ✓ 사진 업로드 입력
   ✓ "2분 내 완성" 문구
   ✓ 또는 직접 추가 옵션

B2B 검수 화면 (B2B-2):
   ✓ 인식된 메뉴 카운트
   ✓ 신뢰도 배지 (✅ ⚠️ ❓)
   ✓ 각 메뉴의:
     - 인식된 이름
     - 매칭된 canonical
     - 수식어 분해
     - 영어 번역
     - 일/중 번역
     - 난이도, 알레르기
   ✓ 수정 모달
   ✓ [전체 승인] 버튼

Admin 대시보드:
   ✓ 신규 메뉴 큐 (리스트)
   ✓ 필터 ([전체] [확인필요] [자동등록])
   ✓ 각 항목:
     - 메뉴명, 소스, 분해 결과
     - 매칭 신뢰도
   ✓ 액션 ([승인] [수정] [신규])
   ✓ 우측 통계 패널
     - Canonical 수
     - Modifier 수
     - DB 히트율
     - AI 비용
     - 미검토 큐 수

[ ] QR 메뉴 페이지 (동적 생성)
   ✓ 헤더: 식당명 (한/영)
   ✓ 언어 탭 (EN/JA/ZH)
   ✓ 카테고리별 메뉴
   ✓ 각 메뉴카드:
     - 이미지 (있으면)
     - 영어명
     - 한국어명 + 로마자
     - 설명 (3-5문장)
     - 맵기, 알레르기, 난이도
     - 가격
   ✓ 문화 팁 (반찬, 호출벨, 등)
   ✓ 풋터 (Powered by...)

[ ] 모바일 반응형
   ✓ 480px 최적화 (스마트폰)
   ✓ 터치 친화적 (버튼 크기)
   ✓ 모바일 폰트 (가독성)
   ✓ 이미지 최적화 (로딩 속도)

[ ] 상호작용
   ✓ 언어 선택 (변경 즉시 반영)
   ✓ 필터 (전환 후 리스트 갱신)
   ✓ 버튼 클릭 (피드백 있는가?)
   ✓ 폼 제출 (오류 메시지)
```

**검증 방식:**

```bash
# 로컬에서 브라우저 테스트
# 1. 3개 서버 실행
python -m http.server 8080  # B2C
python -m http.server 8081  # B2B

# 2. 브라우저에서 테스트
http://localhost:8080/
http://localhost:8081/admin.html

# 3. 스크린샷 캡처 (증거 수집)
```

**산출:**
- 동작 확인도 (%)
- UI 불일치 항목
- 성능 이슈 (로딩 시간, 레이아웃 시프트)

---

### **5️⃣ I18n Auditor (다국어 검증)**

**검증 파일:**
- 기획: 05_mvp_scope, 07_seed_data_guide
- 코드: services/translation_service.py, frontend/

**체크항목:**

```
[ ] 언어 지원 범위
   ✓ 영어 (필수)
   ✓ 일본어 (필수)
   ✓ 중국어 (필수)
   ✗ 기타 (제외 확인)

[ ] 번역 데이터 완성도
   각 canonical_menu에 대해:
   ✓ explanation_short
     - en (존재하는가?)
     - ja (Papago 번역됨?)
     - zh (Papago 번역됨?)
   ✓ main_ingredients 번역
   ✓ cultural_context

[ ] Papago 번역 검증
   ✓ API 연동 (클라이언트 ID/시크릿)
   ✓ 캐싱 작동 (DB에 저장됨?)
   ✓ 배치 번역 (모든 메뉴 번역됨?)
   ✓ 번역 품질 샘플 (3-5개 메뉴)

[ ] 프론트엔드 표시
   B2C 결과:
   ✓ 언어 탭 (EN/JA/ZH)
   ✓ 클릭 시 텍스트 변경
   ✓ 번역 누락 없음

   QR 메뉴:
   ✓ ?lang=en|ja|zh 작동
   ✓ 전체 메뉴 번역됨
   ✓ 언어별 HTML 렌더링

[ ] 이모지 / 문화 표현
   ✓ 맵기 아이콘 (🟢 🟡 🔴)
   ✓ 알레르기 아이콘 (🐷 🐄 🦐 등)
   ✓ 난이도 (⭐~⭐⭐⭐⭐⭐)
   ✓ 언어별 일관성
```

**산출:**
- 번역 완성도 (%)
- 누락된 번역 목록
- 번역 품질 샘플 (good/bad examples)

---

### **6️⃣ Performance Lead (성능 검증)**

**검증 파일:**
- 기획: 05_mvp_scope (비용 추정)
- 코드: app/backend/migrations/performance_optimization.sql

**체크항목:**

```
[ ] 응답 시간 (목표: ≤3초)

API 응답 시간:
   ✓ POST /api/v1/menu/identify
     - Exact match: ~100ms
     - Modifier decomposition: ~300ms
     - AI Discovery: ~1.5s
     - 평균: ~500ms

   ✓ POST /api/v1/menu/recognize
     - OCR 처리: ~2s (CLOVA)
     - LLM 파싱: ~0.5s (GPT-4o)
     - 합계: ~2.5s

   ✓ GET /qr/{shop_code}
     - 캐시 히트: ~50ms
     - DB 조회: ~200ms

[ ] DB 최적화

인덱싱:
   ✓ canonical_menus.name_ko (정확 매칭)
   ✓ pg_trgm (유사 검색)
   ✓ concept_id (카테고리 조회)
   ✓ created_at (최신순 정렬)
   총 15개 인덱스

성능 향상:
   ✓ 최적화 전: 3.2s
   ✓ 최적화 후: ~500ms
   ✓ 향상도: 10배 이상

[ ] 캐싱 전략

Redis (준비 단계):
   ✓ canonical 메뉴 캐시 (TTL: 24h)
   ✓ translation 캐시 (TTL: 7d)
   ✓ QR 페이지 캐시 (TTL: 1h)

[ ] 비용 추정 (월간)

CLOVA OCR: ~15,000원 (1,000건)
GPT-4o (Discovery): ~4,000원 (300건)
GPT-4o (설명): ~8,000원 (300건)
Papago: 0원 (일 10,000자 무료)
DB: ~50,000원 (최소 사양)
스토리지: ~230원 (10GB)
합계: ~77,000원/월

시간이 지날수록 AI 비용 감소 예상
```

**벤치마크 방식:**

```bash
# 성능 측정 스크립트 실행
python app/backend/scripts/benchmark.py

# 출력: 응답 시간, p95/p99 값
```

**산출:**
- 실제 응답 시간 (목표치 달성 여부)
- 병목 지점 분석
- 최적화 효과 검증

---

## 📝 최종 검증 리포트 포맷

```markdown
# Menu Knowledge Engine MVP 최종 검증 리포트

## 1️⃣ 설계 검증 (Architecture Reviewer)
- 일치도: XX%
- 불일치 항목: N개
- 상세: [링크]

## 2️⃣ 기능 검증 (Feature Validator)
- 구현 기능: 10/10 ✅
- 미구현 기능: 0개
- 상세: [링크]

## 3️⃣ Backend 검증 (Backend QA)
- API 완성도: XX%
- 비즈니스 로직: ✅
- 상세: [링크]

## 4️⃣ Frontend 검증 (Frontend Tester)
- UI 일치도: XX%
- 모바일 반응형: ✅
- 스크린샷: [이미지]

## 5️⃣ 다국어 검증 (I18n Auditor)
- 번역 완성도: XX%
- 누락: N개
- 상세: [링크]

## 6️⃣ 성능 검증 (Performance Lead)
- 응답 시간: ~XXms ✅/❌
- DB 최적화: 10배 향상 ✅
- 비용: ~77,000원/월 ✅

## 📊 종합 평가
- 총 점수: XX/100
- 상태: PASS/FAIL
- 주요 이슈: N개
- 배포 준비도: XX%

## ✅ 최종 판정
🟢 **배포 가능** / 🟡 **조건부 가능** / 🔴 **재검토 필요**
```

---

## 🎯 실행 순서

1. **병렬 검증 시작** (6명 동시 진행)
   - 각 팀원이 자신의 체크리스트 수행
   - 약 1-2시간 소요

2. **이슈 수집**
   - 각 팀원이 발견한 문제점 기록
   - 우선순위 분류 (P0/P1/P2)

3. **이슈 해결** (필요시)
   - P0 (배포 불가): 즉시 수정
   - P1 (권장): 시간 허락 시 수정
   - P2 (개선 사항): v0.2에서

4. **최종 리포트 생성**
   - 모든 팀원의 결과 종합
   - 배포 GO/NOGO 판정

