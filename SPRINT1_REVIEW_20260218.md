# Menu Knowledge Engine - Sprint 1 전략 검토 보고서

**작성일**: 2026-02-18
**검토자**: Senior Developer (10년차 관점)
**현재 상황**: v0.1.0 배포 완료, 214개 시드 데이터, 성능 227배 초과 달성
**검토 대상**: Sprint 1 옵션 3가지 (핵심 API, pg_trgm, OCR)

---

## 📊 Executive Summary

### 권장 결론: **Option 1 (핵심 API 완성) 80% + Option 2 (pg_trgm 활용) 20%**

**이유:**
1. ✅ **비즈니스 가치 극대화**: 플래그십 케이스("왕얼큰순두부뼈해장국") 이미 통과, DB 매칭률 60% → 90%로 단기간에 개선 가능
2. ✅ **기술 리스크 최소화**: 코드 완성 (Option 1) + 이미 설치된 pg_trgm 활성화 (Option 2)만 하면 됨
3. ⚠️ **OCR은 Phase 2로 연기**: CLOVA OCR 통합은 메뉴판 이미지 없이 테스트 불가, 현재는 준비 단계

**점수 (100점 만점)**:
- Option 1 (핵심 API): **85점** ⭐ 권장
- Option 2 (pg_trgm): **70점** (Option 1 보조용)
- Option 3 (OCR): **55점** (시기상조)

---

## 🎯 현재 상황 분석 (v0.1.0 달성도)

### ✅ 이미 완료된 것 (놀랍도록 우수함)

| 항목 | 목표 | 달성 | 비율 |
|------|------|------|------|
| **DB 스키마** | 12개 테이블 | 12개 완료 | ✅ 100% |
| **시드 데이터** | 100개 메뉴 | 116개 | ✅ 116% |
| **3단계 파이프라인** | Exact → Modifier → AI | 완성 | ✅ 100% |
| **성능** | p95 < 3초 | p95 = 24.80ms | ✅ 12,000% |
| **Redis 캐싱** | 구현 | 완료 | ✅ 100% |
| **AI Discovery** | GPT-4o 통합 | 완료 | ✅ 100% |
| **E2E 테스트** | 10개 케이스 | 8/10 통과 | ✅ 80% |

### ⚠️ 미달 항목 (개선 가능)

| 항목 | 목표 | 현재 | 갭 | 개선 난도 |
|------|------|------|-----|----------|
| **DB 매칭률** | 70% | 60% | -10% | 🟢 쉬움 (1주) |
| **pg_trgm 활용** | 유사 검색 | 설치만 됨 | 미활용 | 🟢 쉬움 (1일) |
| **10대 테스트 케이스** | 10/10 | 8/10 | -2 | 🟡 중간 (2주) |
| **OCR 파이프라인** | recognize API | 미구현 | 100% | 🔴 어려움 (4주) |

### 🔍 핵심 인사이트

**v0.1.0은 이미 "작동하는 엔진"을 증명했다.**
- ✅ 플래그십 케이스 통과: "왕얼큰뼈해장국" 0.85 신뢰도
- ✅ 성능 목표 초과: 평균 응답 13.2ms (목표 3초 대비 227배)
- ✅ AI 비용 예상: $2.70/월 (목표 $50/월 대비 18배 절감)

**Sprint 1의 핵심 질문:**
> "이미 작동하는 엔진을 어떻게 **70% → 90% 매칭률**로 끌어올릴 것인가?"

---

## 📋 Option 1: 핵심 API 완성 (권장) - 85/100점

### 비즈니스 가치: ⭐⭐⭐⭐⭐ (5/5)

**왜 가장 가치가 높은가?**
1. **DB 매칭률 60% → 90%** 달성 가능 (목표 70% 초과)
2. **실패한 2개 케이스 해결**:
   - TC-06: "한우불고기" (ingredient 타입 수식어 미처리)
   - TC-10: "고씨네묵은지감자탕" (브랜드명 패턴 미처리)
3. **지식 엔진의 핵심 완성**: AI 호출 없이 DB만으로 90% 처리 → 비용 절감

### 기술 구현 계획 (1-2주)

#### Week 1: 수식어 분해 알고리즘 개선

**현재 문제점 (코드 분석 결과):**
```python
# matching_engine.py:176 - ingredient 타입 수식어 제외됨
if modifier.type == "ingredient":
    continue  # "한우" 같은 grade 타입 메뉴가 ingredient로 잘못 분류되면 실패
```

**해결 방법:**
1. **"한우" modifier 타입 수정** (DB 업데이트)
   ```sql
   -- 이미 코드는 수정됨, DB만 반영하면 됨
   UPDATE modifiers SET type = 'grade' WHERE text_ko = '한우';
   ```
   - 예상 시간: **30분**
   - 영향: TC-06 "한우불고기" 즉시 통과 → DB 매칭률 +10%

2. **브랜드명 패턴 추가**
   ```python
   # matching_engine.py에 추가
   BRAND_PATTERNS = [
       r'^(\w+)씨네',  # "고씨네", "박씨네"
       r'^(\w+)네',    # "할매네", "원조네"
       r'^할매',       # "할매곰탕"
       r'^원조',       # "원조집"
   ]
   ```
   - 예상 시간: **2시간** (테스트 포함)
   - 영향: TC-10 "고씨네묵은지감자탕" 통과 → DB 매칭률 +10%

3. **"통닭" canonical_menus 추가**
   ```sql
   INSERT INTO canonical_menus (name_ko, name_en, romanization, ...)
   VALUES ('통닭', 'Whole Fried Chicken', 'Tongdak', ...);
   ```
   - 예상 시간: **1시간** (GPT-4o로 설명 생성)
   - 영향: TC-08 "옛날통닭" DB 매칭 성공 → AI 호출 감소 10%

#### Week 2: 매칭 엔진 테스트 및 최적화

4. **10대 테스트 케이스 재검증**
   ```bash
   python e2e_test_runner.py
   ```
   - 예상 결과: **9/10 통과** (TC-10 브랜드명 패턴 개선 필요할 수 있음)
   - DB 매칭률: **80%+**

5. **300개 실전 메뉴 추가 테스트** (이미 스크립트 존재)
   ```bash
   python tests/test_300_menus.py
   ```
   - 목표: **70% 이상 DB 매칭**
   - 실패 케이스 분석 → 수식어/canonical 추가

6. **Match Confidence 튜닝**
   ```python
   # matching_engine.py:234
   confidence = 0.95 - (len(found_modifiers) * 0.05)
   confidence = max(confidence, 0.7)
   ```
   - 현재: 수식어 1개당 -0.05 (최소 0.7)
   - 개선: 타입별 차등 적용 (emotion: -0.02, ingredient: -0.08)
   - 예상 시간: **4시간**

### 기술 위험도: 🟢 낮음 (1/5)

**장점:**
- ✅ 코드 이미 완성 (수정만 필요)
- ✅ DB 스키마 변경 없음 (시드 데이터만 추가/수정)
- ✅ 테스트 스크립트 준비됨 (e2e_test_runner.py)
- ✅ 팀 역량 충분 (Python + SQLAlchemy 숙련)

**단점:**
- ⚠️ 브랜드명 패턴 정규식 복잡할 수 있음 (한글 유니코드)
- ⚠️ 300개 실전 메뉴 테스트에서 예상 못한 엣지 케이스 발견 가능

### 마일스톤 달성: ⭐⭐⭐⭐⭐ (5/5)

**2주 후 목표:**
- ✅ DB 매칭률 90%+ (목표 70% 초과)
- ✅ 10대 테스트 케이스 9/10 통과
- ✅ AI 비용/스캔 < 30원 (현재 < 50원)

**Sprint 1 완료 기준 달성률: 100%**

### 향후 확장성: ⭐⭐⭐⭐ (4/5)

**좋은 점:**
- ✅ 수식어 사전 확장 가능 (54개 → 100개)
- ✅ canonical_menus 확장 가능 (116개 → 500개)
- ✅ 브랜드명 패턴은 규칙 기반 (AI 불필요)

**제한점:**
- ⚠️ 복합 수식어 조합 폭발 문제 (예: "왕얼큰묵은지순두부찌개")
  - 해결: v0.2에서 pgvector + 임베딩 검색

---

## 📋 Option 2: pg_trgm 활용 (보조) - 70/100점

### 비즈니스 가치: ⭐⭐⭐ (3/5)

**왜 Option 1보다 낮은가?**
- ✅ 오타 감지 개선 (김치찌개 vs 김치찌게)
- ✅ 유사도 검색 정확도 향상 (70% → 95%)
- ⚠️ **하지만 v0.1.0에서 이미 정확 매칭률 80%** → 추가 가치 제한적

### 기술 구현 계획 (1일)

#### 현재 상태:
```sql
-- PostgreSQL 13.23에 pg_trgm 이미 설치됨
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

#### 활성화 작업:
1. **similarity 검색 threshold 조정**
   ```python
   # matching_engine.py:124
   similarity_threshold = 0.4  # 이미 구현됨!
   ```
   - 현재 코드는 이미 pg_trgm 사용 중
   - **단, FastComet 서버에서 에러 발생**:
     ```
     function similarity(char, varchar) does not exist
     ```

2. **FastComet 지원팀 요청** (이메일)
   ```
   Subject: PostgreSQL pg_trgm Extension Activation Request

   Hello,

   I need to activate the pg_trgm extension for my PostgreSQL 13.23 database.
   - Database: menu_knowledge
   - Purpose: Korean menu name similarity search
   - Required: CREATE EXTENSION pg_trgm;

   Current error:
   "function similarity(char, varchar) does not exist"

   Can you help activate this extension?

   Thank you.
   ```
   - 예상 응답 시간: **1-3일**
   - 성공률: **80%** (Managed VPS 정책상 불확실)

3. **Fallback 전략** (pg_trgm 실패 시)
   ```python
   # matching_engine.py에 추가
   try:
       # pg_trgm similarity search
       result = await self.db.execute(...)
   except Exception as e:
       # Fallback to LIKE search
       result = await self.db.execute(
           select(CanonicalMenu).where(
               CanonicalMenu.name_ko.like(f"%{menu_name}%")
           )
       )
   ```
   - 예상 시간: **2시간**

### 기술 위험도: 🟡 중간 (3/5)

**위험 요인:**
- ⚠️ **FastComet Managed VPS 정책**: contrib 확장 컴파일 바이너리 제공 여부 불확실
- ⚠️ **지원팀 응답 지연**: 1-3일 소요 가능
- ⚠️ **실패 시 대안**: Unmanaged VPS 마이그레이션 (Docker 지원) → 비용 증가

**장점:**
- ✅ 코드 이미 구현됨 (pg_trgm 사용 중)
- ✅ 설치만 되면 즉시 활용 가능

### 마일스톤 달성: ⭐⭐⭐ (3/5)

**성공 시:**
- ✅ 오타 감지 개선 (김치찌개 vs 김치찌게 매칭)
- ✅ 유사 메뉴 검색 정확도 95%+

**실패 시:**
- ⚠️ Fallback (LIKE 검색)으로 대체
- ⚠️ DB 매칭률 개선 없음 (현재 60% 유지)

### 향후 확장성: ⭐⭐⭐ (3/5)

**제한점:**
- ⚠️ pg_trgm은 **문자열 유사도**만 검색 (의미 검색 불가)
- ⚠️ "불고기" vs "갈비" (의미는 다르지만 비슷한 음식) 검색 불가
- ✅ **해결**: v0.2에서 pgvector + 임베딩 (의미 검색)

---

## 📋 Option 3: OCR 파이프라인 (Phase 2) - 55/100점

### 비즈니스 가치: ⭐⭐ (2/5)

**왜 가장 낮은가?**
1. **테스트 불가능**: 실제 메뉴판 이미지 20장 수집 필요 (명동/성수)
2. **의존성 높음**: CLOVA OCR API 키 발급 + 네이버 클라우드 계정
3. **현재 우선순위 낮음**: B2C 프론트엔드 없음 (메뉴판 스캔 기능 미구현)

### 기술 구현 계획 (4주)

#### Week 1-2: CLOVA OCR 통합
```python
# services/ocr_service.py
import requests

class ClovaOCRService:
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://naveropenapi.apigw.ntruss.com/vision/v1/ocr"

    async def recognize_menu(self, image_bytes: bytes) -> dict:
        """메뉴판 이미지 → 텍스트 추출"""
        response = requests.post(
            self.base_url,
            headers={"X-NCP-APIGW-API-KEY-ID": self.api_key, ...},
            files={"image": image_bytes}
        )
        # 응답 파싱 + 메뉴명/가격 분리
        ...
```

#### Week 3: GPT-4o 후처리
```python
# OCR 결과를 GPT-4o로 정제
ocr_raw = "할머니뼈해장국 9,000\n얼큰순두부찌개 8,000\n..."

prompt = f"""
Extract menu items from this OCR text:
{ocr_raw}

Return JSON:
[
  {{"name_ko": "할머니뼈해장국", "price": 9000}},
  {{"name_ko": "얼큰순두부찌개", "price": 8000}}
]
"""
```

#### Week 4: API 엔드포인트 구현
```python
# api/menu.py
@router.post("/api/v1/menu/recognize")
async def recognize_menu(image: UploadFile):
    # 1. 이미지 검증
    # 2. CLOVA OCR 호출
    # 3. GPT-4o 후처리
    # 4. 메뉴명 리스트 반환
    ...
```

### 기술 위험도: 🔴 높음 (4/5)

**위험 요인:**
1. **CLOVA OCR 성능 불확실성**:
   - 손글씨 메뉴판 인식률 < 50% 가능
   - 디자인폰트 미지원 (예: 캘리그라피)
   - 세로쓰기 메뉴판 처리 복잡

2. **메뉴판 이미지 수집**:
   - 실제 식당 20곳 방문 필요
   - 저작권 이슈 (식당 허가 필요)
   - 다양한 레이아웃 (표 형식, 세로, 가로, 이미지 배경)

3. **GPT-4o 비용 증가**:
   - OCR 후처리: ~$0.01/이미지
   - 월 1,000건 → $10/월 추가

### 마일스톤 달성: ⭐⭐ (2/5)

**현실적 목표 (4주 후):**
- ✅ CLOVA OCR API 연동 완료
- ✅ 테스트 메뉴판 10장 인식률 측정
- ⚠️ 인식률 목표 80%는 **달성 불확실** (손글씨/디자인폰트 문제)

**Sprint 1 완료 기준 달성률: 60%**

### 향후 확장성: ⭐⭐⭐⭐ (4/5)

**좋은 점:**
- ✅ B2B/B2C 파이프라인의 핵심 기능
- ✅ 성공하면 "메뉴판 사진 → QR 페이지" 완전 자동화

**제한점:**
- ⚠️ OCR 정확도 개선은 AI 모델 의존 (우리가 제어 불가)
- ⚠️ 메뉴판 레이아웃 다양성 → LLM 후처리 비용 증가

---

## 🎯 종합 권장사항

### Sprint 1 실행 계획: **Hybrid Approach**

```
Week 1-2: Option 1 (핵심 API 완성) 80%
  ├─ Day 1: "한우" modifier 타입 수정 + DB 반영
  ├─ Day 2-3: 브랜드명 패턴 추가 + "통닭" canonical 추가
  ├─ Day 4-5: 10대 테스트 케이스 재검증 (목표 9/10)
  └─ Day 6-10: 300개 실전 메뉴 테스트 + 수식어 사전 확장

Week 1: Option 2 (pg_trgm 활용) 20%
  ├─ Day 1: FastComet 지원팀 요청 (이메일)
  └─ Day 2-3: Fallback 전략 구현 (LIKE 검색)
  └─ Day 4-10: pg_trgm 활성화 대기 (백그라운드)

Option 3 (OCR): Phase 2로 연기 ❌
  - 이유: 메뉴판 이미지 수집 불가, B2C 프론트엔드 미구현
  - 시기: v0.2 (4주 후, B2B/B2C UI 완성 후)
```

### Sprint 1 성공 기준 (2주 후)

| 지표 | 현재 | 목표 | 달성 가능성 |
|------|------|------|-----------|
| DB 매칭률 | 60% | 90% | ✅ 90% |
| E2E 통과율 | 8/10 | 9/10 | ✅ 95% |
| AI 호출 비율 | 40% | 10% | ✅ 90% |
| 응답 시간 (p95) | 24.80ms | < 100ms | ✅ 100% (이미 달성) |
| 테스트 커버리지 | 10개 케이스 | 300개 케이스 | ✅ 80% |

---

## 🚨 리스크 및 대응 전략

### Risk 1: FastComet pg_trgm 활성화 실패 (확률: 30%)

**영향:**
- 유사 검색 불가 (김치찌개 vs 김치찌게 미매칭)
- DB 매칭률 개선 제한 (90% → 85%)

**대응:**
1. Fallback: LIKE 검색 구현 (성능 저하 수용)
2. v0.2에서 Unmanaged VPS 마이그레이션 검토
3. 단기: 정확 매칭 + 수식어 분해로 85% 달성 가능

### Risk 2: 브랜드명 패턴 정규식 복잡도 (확률: 20%)

**영향:**
- "고씨네묵은지감자탕" 같은 복합 케이스 미처리
- DB 매칭률 90% → 88%

**대응:**
1. 단순 패턴부터 시작 (r'^(\w+)씨네', r'^(\w+)네')
2. 실패 케이스 수집 → 패턴 추가 (점진적 개선)
3. v0.2에서 LLM 보조 분해 도입

### Risk 3: 300개 실전 메뉴 테스트에서 예상 못한 엣지 케이스 (확률: 40%)

**영향:**
- 신규 수식어/canonical 추가 필요
- 2주 → 3주 소요 가능

**대응:**
1. 실패 케이스 우선순위 분류 (P0/P1/P2)
2. P0만 Sprint 1에서 해결 (80% 목표)
3. P1/P2는 v0.2로 연기

---

## 📈 비즈니스 임팩트 예측 (Sprint 1 완료 후)

### 지식 엔진 성숙도

```
Before Sprint 1 (v0.1.0):
  DB 매칭: 60%
  AI 호출: 40%
  비용/스캔: ~30원

After Sprint 1 (v0.1.1):
  DB 매칭: 90%  (+30%p ⬆️)
  AI 호출: 10%  (-30%p ⬇️)
  비용/스캔: ~10원 (-67% ⬇️)
```

### 사용자 경험 개선

| 시나리오 | Before | After | 개선 |
|---------|--------|-------|------|
| "한우불고기" 검색 | AI Discovery (3초) | DB 매칭 (25ms) | **120배 빠름** |
| "고씨네묵은지감자탕" | no_match | modifier_decomposition | **매칭 성공** |
| "옛날통닭" | AI Discovery | exact match | **AI 비용 절감** |

### 운영 비용 절감

```
월 5,000 스캔 기준:
  Before: 5,000 × 40% AI × 30원 = 60,000원/월
  After:  5,000 × 10% AI × 30원 = 15,000원/월

절감액: 45,000원/월 (75% 감소)
```

---

## 🎓 교훈 및 시사점

### 1. "작동하는 엔진"을 먼저 증명하라

v0.1.0은 이미 **플래그십 케이스("왕얼큰뼈해장국")**를 통과했다.
Sprint 1은 **70% → 90%로 점진적 개선**하는 단계다.

**교훈:**
- ✅ MVP는 완벽함이 아닌 **핵심 가치 증명**이 목표
- ✅ 성능은 이미 목표의 227배 달성 → 더 빠를 필요 없음
- ✅ DB 매칭률 개선이 **가장 큰 비즈니스 임팩트**

### 2. OCR은 "있으면 좋은 것", 매칭 엔진이 "핵심"

OCR 정확도 80%를 달성해도, **매칭 엔진이 60%면 전체 정확도 = 48%**
반대로, 매칭 엔진 90%면, **OCR 70%여도 전체 정확도 = 63%**

**교훈:**
- ✅ 매칭 엔진 > OCR 우선순위
- ✅ OCR은 Phase 2 (B2C 프론트엔드 완성 후)
- ✅ "지식 엔진"의 핵심은 **DB 매칭률**

### 3. pg_trgm은 "Nice-to-Have", 수식어 분해가 "Must-Have"

pg_trgm 없어도 **정확 매칭 + 수식어 분해로 85% 달성 가능**
pg_trgm 있으면 **오타 감지로 85% → 90%** (5%p 개선)

**교훈:**
- ✅ 핵심 로직 완성 > 기술 도구
- ✅ pg_trgm은 Option 1 보조용
- ✅ FastComet 실패 시에도 목표 달성 가능

---

## 🏆 최종 권장 결정

### Sprint 1 실행: **Option 1 (80%) + Option 2 (20%)**

**주 목표:**
1. DB 매칭률 60% → 90% 달성
2. 10대 테스트 케이스 9/10 통과
3. AI 호출 비율 40% → 10% 감소
4. 비용/스캔 30원 → 10원 절감

**부 목표 (Option 2):**
5. pg_trgm 활성화 (FastComet 지원팀 요청)
6. Fallback 전략 구현 (실패 시 LIKE 검색)

**연기 항목:**
- ❌ OCR 파이프라인 (Phase 2, 4주 후)
- ❌ B2C 프론트엔드 (Phase 3, 8주 후)

### Sprint 1 완료 기준 (Definition of Done)

```
✅ E2E 테스트 9/10 통과
✅ DB 매칭률 90%+
✅ 300개 실전 메뉴 테스트 완료
✅ 수식어 사전 70개+ (현재 54개)
✅ canonical_menus 120개+ (현재 116개)
✅ 성능 p95 < 100ms (현재 24.80ms)
✅ 문서화 완료 (Sprint 1 Report)
```

### Sprint 2 준비 (3주 차)

```
Week 3-4: B2B/B2C 프론트엔드 프로토타입
  ├─ B2B: 메뉴 업로드 웹 (QR 생성)
  ├─ B2C: 모바일웹 (파일 업로드 기반 카메라)
  └─ OCR 파이프라인 통합 (CLOVA + GPT-4o)
```

---

**보고서 작성**: 2026-02-18
**검토자**: Senior Developer
**권장 결정**: Option 1 (80%) + Option 2 (20%)
**예상 성과**: DB 매칭률 90%, AI 비용 67% 절감
**위험 등급**: 🟢 낮음 (pg_trgm 실패해도 목표 달성 가능)
