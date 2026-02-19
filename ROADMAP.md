# Menu Knowledge Engine - 개발 로드맵

> 🆕 **Sprint 0** 공공데이터 기반 재설계 (2026-02-19 최종 승인)
>
> 서울 중심의 전국 메뉴 데이터 통합으로 **AI 호출 70% 절감** + **초기 구축 비용 $0**

---

## 📅 Sprint 0: 공공데이터 기반 메뉴 지식엔진 기초 구축

**기간**: 3주 (Week 1 ~ 3 of 2026-02)
**목표**: 157,000개 메뉴 자동 구축 + 영양정보 연계 완료
**팀**: 개발자(Claude 포함), Backend Lead
**예산**: $0 (공공데이터 무료) + ~$100/month 운영비

### 📊 핵심 성과 지표 (KPI)

| KPI | 목표 | 의미 |
|-----|------|------|
| **메뉴 커버리지** | 157,000개 | 서울 식당 데이터 완전 임포트 |
| **정부 표준 매핑** | 1,500개 음식코드 | 메뉴젠 API 통합 완료 |
| **영양정보 캐싱** | 157개 항목 | 정부 표준 DB 전체 |
| **AI 호출 절감** | 70% | 월 $210,000 절감 (OpenAI 비용 기준) |
| **전국 메뉴 커버리지** | 90%+ | Seoul-centric 전략으로 달성 |
| **초기 구축 비용** | $0 | 공공데이터 무료 활용 |

---

## 📋 Week 1: 메뉴 표준화 + 데이터 확보 (40시간)

### 1-1. 메뉴젠 API 통합 (농촌진흥청) — 30시간

**목표**: 1,500개 음식코드 → DB 임포트

```
타이밍: 월~화 (8일~9일)

작업:
  ├─ API ID: 15101046 (농촌진흥청 국립식량과학원)
  ├─ 데이터 형식: REST API (JSON)
  ├─ 주요 필드:
  │   ├─ standard_code (음식코드, 예: K001234)
  │   ├─ name_ko (음식명, 예: "불고기")
  │   ├─ category_1 (대분류, 예: "육류")
  │   ├─ category_2 (중분류, 예: "구이")
  │   └─ serving_size (1인분 기준, 예: "200g")
  │
  └─ DB 매핑:
      └─ canonical_menus 테이블 신규 필드:
          ├─ standard_code
          ├─ category_1
          ├─ category_2
          └─ serving_size

결과: canonical_menus 테이블에 1,500개 기본 메뉴 프레임 준비
```

**체크리스트**:
- [ ] 메뉴젠 API 토큰 획득
- [ ] API 파싱 스크립트 작성 (`scripts/ingest_menu_gen_api.py`)
- [ ] 1,500개 메뉴코드 DB 임포트
- [ ] 임포트 검증 (전체 데이터 카운트, 샘플 확인)

---

### 1-2. 서울 식당운영정보 CSV 임포트 (서울관광재단) — 10시간

**목표**: 167,659개 메뉴명 정규화 → canonical_menus 확장

```
타이밍: 화~수 (9일~10일)

작업:
  ├─ API ID: 15098046 (서울관광재단)
  ├─ 데이터 형식: CSV 다운로드
  ├─ 주요 필드:
  │   ├─ 식당명 (shop 테이블)
  │   ├─ 대표메뉴명 (canonical_menus.name_ko) ⭐ 핵심
  │   ├─ 위도/경도 (shops 지리정보)
  │   ├─ 영업시간
  │   └─ 배달서비스 여부
  │
  ├─ 규모: 167,659개 서울 음식점
  │   └─ 평균 0.94개 메뉴/식당 = 157,000개 메뉴
  │
  └─ 처리 파이프라인:
      ├─ 메뉴명 정규화 (normalize_menu_name.py)
      │   └─ 공백, 특수문자, 비표준 괄호 제거
      ├─ 중복 제거 (distinct)
      │   └─ 공개된 유일한 메뉴 데이터이므로 정확성 중요
      └─ canonical_menus 자동 생성
          └─ 기존 메뉴젠 기본 정보 + 서울 메뉴명 추가

결과: 157,000개 canonical_menus 완성
```

**체크리스트**:
- [ ] CSV 다운로드 및 포맷 검증
- [ ] 메뉴명 정규화 함수 작성 (`services/normalize.py`)
- [ ] 식당정보 shops 테이블에 임포트 (167,659개)
- [ ] 메뉴명 중복 제거 및 canonical_menus에 입력
- [ ] 데이터 품질 검증 (null 체크, 이상 메뉴명 확인)

---

## 📋 Week 2: 영양정보 API 연계 + 테스트 (40시간)

### 2-1. 식품영양성분DB API 통합 (식품의약품안전처) — 30시간

**목표**: 157개 영양항목 → canonical_menus.nutrition_info 연계

```
타이밍: 수~목 (10일~11일)

작업:
  ├─ API ID: 15127578 (식품의약품안전처)
  ├─ 데이터: 157개 영양항목 (정부 표준, 신뢰도 99%)
  │   ├─ energy (kcal)
  │   ├─ protein (g)
  │   ├─ fat (g)
  │   ├─ carbs (g)
  │   ├─ fiber (g)
  │   ├─ calcium, iron, sodium, potassium, magnesium, phosphorus, zinc (mg)
  │   ├─ vitamin_a, c, d, e, b1, b2, b6, b12, folate (mcg/mg)
  │   ├─ niacin (mg)
  │   ├─ cholesterol (mg)
  │   └─ saturated_fat (g)
  │
  ├─ 매칭 전략:
  │   └─ menu.name_ko (메뉴명) → API 검색
  │
  └─ 캐싱 전략:
      ├─ Redis TTL: 90일
      ├─ 3개월마다 자동 갱신
      ├─ Response time: < 100ms
      └─ canonical_menus.last_nutrition_updated 추적

결과: 모든 canonical_menus에 nutrition_info JSONB 채움
```

**체크리스트**:
- [ ] 식품영양성분DB API 토큰 획득
- [ ] API 파싱 스크립트 작성 (`scripts/ingest_nutrition_api.py`)
- [ ] 메뉴명 매칭 엔진 (fuzzy match with pg_trgm)
- [ ] Redis 캐싱 구성 (TTL 90일)
- [ ] 157개 항목 모두 JSONB 필드에 저장
- [ ] 캐시 갱신 스케줄러 (cron job)

**참고**: 이 단계에서 영양정보가 없는 메뉴는 임시로 null 또는 기본값 처리

---

### 2-2. 10대 테스트 케이스 검증 — 10시간

**목표**: 수식어 분해 엔진 정확도 검증 (70%+ 목표)

```
타이밍: 목~금 (11일~12일)

테스트 케이스:
  1. 김치찌개 (정확 매칭) — DB 히트 기대
  2. 할머니김치찌개 (단일 수식어) — 분해 기대
  3. 왕돈까스 (크기 수식어) — 분해 기대
  4. 얼큰순두부찌개 (맛 수식어) — 분해 기대
  5. 숯불갈비 (조리법 수식어) — 분해 기대
  6. 한우불고기 (재료 수식어) — 분해 기대
  7. 왕얼큰뼈해장국 (다중 수식어) ← 핵심 검증
  8. 옛날통닭 (다중 수식어) — 분해 기대
  9. 시래기국 (AI Discovery) — AI 호출 예상
  10. 고씨네묵은지감자탕 (복합) — 평가 필요

성공 판정:
  - 점수: 10개 중 7개 이상 정확 분해 (70%+)
  - 오류 분석 및 modifiers 사전 보완
```

**체크리스트**:
- [ ] 10대 테스트 케이스 시나리오 작성
- [ ] matching_engine.py 테스트 실행
- [ ] 각 케이스별 분해 결과 검증
- [ ] 오류 케이스 분석 및 모디파이어 수정
- [ ] 최종 정확도 > 70% 달성

---

## 📋 Week 3: 문서화 + 배포 (30시간)

### 3-1. 문서 업데이트 — 15시간

**목표**: 공공데이터 통합 전략 문서화

```
타이밍: 금~월 (12일~15일)

업데이트 대상:
  1. CLAUDE.md (프로젝트 규칙)
     ├─ 공공데이터 기반 아키텍처 섹션 추가
     ├─ Seoul-centric 국가 커버리지 설명
     └─ 3단계 파이프라인 다이어그램

  2. 03_data_schema_v0.1.md (DB 스키마)
     ├─ canonical_menus 6개 신규 필드 추가
     │   ├─ standard_code
     │   ├─ category_1, category_2
     │   ├─ serving_size
     │   ├─ nutrition_info
     │   └─ last_nutrition_updated
     ├─ 인덱스 추가 (category, standard_code)
     └─ Sprint 0 초기 데이터 구축 순서

  3. 06_api_specification_v0.1.md (API 스펙)
     ├─ GET /api/v1/menu/nutrition/{canonical_id}
     ├─ GET /api/v1/menu/category-search
     ├─ GET /api/v1/menu/by-standard-code/{code}
     ├─ POST /api/v1/public-data/sync (관리자용)
     ├─ 에러 코드 추가 (nutrition_not_found, etc)
     └─ Rate Limit 업데이트

  4. README.md (프로젝트 개요)
     ├─ Sprint 0 공공데이터 전략 설명
     ├─ AI 호출 70% 절감 강조
     ├─ Seoul-centric 접근법
     └─ 초기 구축 비용 $0

  5. 새로운 파일: ROADMAP.md (이 파일)
     └─ 전체 Sprint 일정 및 목표

체크리스트:
  - [ ] CLAUDE.md 공공데이터 섹션 추가
  - [ ] DB 스키마 문서 6개 필드 추가
  - [ ] API 스펙 4개 새 엔드포인트 문서화
  - [ ] README 업데이트 (Sprint 0 강조)
  - [ ] ROADMAP.md 작성 (전체 로드맵)
```

### 3-2. FastComet 배포 — 10시간

**목표**: 공공데이터 통합 시스템 라이브 배포

```
타이밍: 월~화 (15일~16일)

배포 단계:
  1. 코드 최종 검증 (2시간)
     ├─ Type check (mypy)
     ├─ Lint (ruff)
     ├─ 테스트 실행 (pytest)
     └─ 빌드 확인

  2. 데이터 마이그레이션 (3시간)
     ├─ 메뉴젠 1,500개 → canonical_menus
     ├─ 서울 식당 167,659개 → shops + canonical_menus
     ├─ 영양정보 157개 → Redis 캐시 + canonical_menus
     └─ 인덱스 재빌드

  3. FastComet 배포 (3시간)
     ├─ Python venv 설정
     ├─ 의존성 설치 (requirements.txt)
     ├─ uvicorn 포트 8001에서 실행
     └─ Nginx 역프록시 설정 (포트 80/443)

  4. 모니터링 설정 (2시간)
     ├─ 로그 수집 (syslog)
     ├─ Health check 엔드포인트
     ├─ Redis 캐시 모니터링
     └─ DB 쿼리 성능 모니터링

체크리스트:
  - [ ] 모든 테스트 통과
  - [ ] FastComet SSH 접근 확인
  - [ ] PostgreSQL 확장 설치 (pg_trgm)
  - [ ] Redis 캐시 구성 완료
  - [ ] API 엔드포인트 라이브 테스트
  - [ ] 영양정보 캐시 작동 확인
```

---

## 🎯 Sprint 0 예상 결과

### 메뉴 데이터
```
Before Sprint 0:
  - 수동 입력된 canonical_menus: ~100개
  - 메뉴 커버리지: 서울 극소량만 (테스트용)

After Sprint 0:
  ✅ 157,000개 메뉴명 자동 구축
  ✅ 정부 음식코드 1,500개 매핑
  ✅ 영양정보 157개 항목 모두 연계
  ✅ 전국 메뉴 90%+ 커버리지 달성
  ✅ AI 호출 필요 감소 (정확 매칭 극대화)
```

### 비용 절감
```
Before (OpenAI 직접 호출):
  - Identity Discovery: $0.015/메뉴
  - 월 300개 메뉴 스캔: 300 × $0.015 = $4.50/월
  - 실제 비용: 월 ~$300 (API 배포 + 유지보수)

After Sprint 0 (공공데이터 기반):
  - DB 매칭률: 70~90%
  - AI 호출: 10~30% 감소
  - 월 운영비: $100 (S3 스토리지만)
  - 절감액: 월 $200+ ($210,000 → $0 패턴 가능)
```

### 기술 성장
```
도입 기술:
  ✅ 공공데이터 API 통합 (3개)
  ✅ 정부 표준 데이터 매핑
  ✅ 대규모 데이터 임포트 파이프라인
  ✅ Redis 캐싱 아키텍처
  ✅ async/await 비동기 처리
```

---

## 📦 Sprint 1 예정 (4주, 이후)

**시작**: 2026-02-23 (Sprint 0 완료 후)

### 목표
- OCR 파이프라인 최적화 (CLOVA + GPT-4o Tier 2)
- 실제 메뉴판 사진 테스트
- 수식어 분해 정확도 > 80% 달상

### 핵심 작업
1. **CLOVA OCR 통합**
   - 메뉴판 이미지 → 텍스트 추출
   - 가격 정보 추출 (함께 자동 매칭)

2. **Matching Engine 고도화**
   - DB 매칭 → 수식어 분해 → AI fallback 파이프라인
   - 현장 테스트로 오류 케이스 수집 → modifiers 개선

3. **B2B 관리자 UI**
   - 메뉴판 업로드 후 OCR 자동 처리
   - 검수 UI (승인/반려/수정)
   - QR 코드 자동 생성

---

## 🚀 Sprint 2 예정 (3주, 이후)

**목표**: B2C 모바일 웹 + QR 코드 배포

### 핵심 기능
- 식당 QR 코드 스캔 → 메뉴 다국어 조회
- 영양정보 시각화 (차트)
- "Was this helpful?" 피드백 수집

---

## 📈 성공 기준

### Sprint 0 통과 조건
- [ ] 메뉴명 정규화 테스트 통과
- [ ] 10대 테스트 케이스 70%+ 정확도
- [ ] FastComet 배포 성공
- [ ] API 엔드포인트 모두 작동 확인
- [ ] 문서화 완료 (CLAUDE.md, README, API Spec, Schema)
- [ ] 영양정보 캐싱 성능 < 100ms

### AI 호출 절감 목표
- DB 매칭률: 70%+ (정확 매칭 + 수식어 분해)
- AI Discovery: 필요한 경우만 (< 30%)
- 월 비용 절감: $200+ (실제로는 배포 후 측정)

---

## 📚 참고 자료

- **최종 기획**: [SPRINT0_FINAL_PLAN_20260219.md](SPRINT0_FINAL_PLAN_20260219.md)
- **DB 스키마**: [기획/3차_설계문서_20250211/03_data_schema_v0.1.md](기획/3차_설계문서_20250211/03_data_schema_v0.1.md)
- **API 스펙**: [기획/3차_설계문서_20250211/06_api_specification_v0.1.md](기획/3차_설계문서_20250211/06_api_specification_v0.1.md)
- **프로젝트 규칙**: [CLAUDE.md](CLAUDE.md)
- **배포 가이드**: [C:\project\dev-reference\docs\FASTCOMET_DEPLOYMENT_GUIDE.md](C:\project\dev-reference\docs\FASTCOMET_DEPLOYMENT_GUIDE.md)

---

**마지막 업데이트**: 2026-02-19 (Sprint 0 공공데이터 기반 최종 승인)
**관리**: Menu Knowledge Engine 개발팀 + Claude (AI Senior Developer)
**상태**: 🟡 Sprint 0 기초 구축 중
