# 🚀 P1 Issues 개선 - 개발팀 Action Plan

**대상**: Menu Knowledge Engine MVP
**기간**: 1주 (월-금)
**목표**: CONDITIONAL GO → ✅ DEPLOYMENT READY
**현황**: 81.8/100점 → 목표 95+/100점

---

## 📋 3개 팀별 작업 분배

```
┌─────────────────────────────────────┐
│  P1 Issues (CONDITIONAL GO 원인)    │
├─────────────────────────────────────┤
│ ✅ P0 (배포 차단): 모두 해결됨       │
│    - ScanLog 컬럼 누락 ✅ Fixed      │
│    - QR 404 에러 ✅ Fixed           │
│    - OCR 임시파일 누수 ✅ Fixed     │
│                                     │
│ ⚠️  P1 (1주 내 필수): 3가지 작업   │
│    1. 번역 데이터 (560개 키)        │
│    2. B2B Admin UI 프론트엔드       │
│    3. 백엔드 API 최적화 (4개 이슈)  │
└─────────────────────────────────────┘
```

---

## 👥 팀별 역할 & 일정

### 🌍 Team 1: Translation Team (i18n)
**담당**: 번역 데이터 완성 (P1 Issue #4)
**시간**: 2-3시간
**일정**: 월-화 (2일)
**결과**: I18n-Auditor 50점 → **95점**

**담당자**: 1명
**준비물**: Papago API 클라이언트 ID/시크릿

📄 **상세 지시서**: `C:\project\menu\.claude\P1_TRANSLATION_TASK.md`

```bash
# 실행 명령
python app/backend/scripts/translate_canonical_menus.py \
  --language ja,zh \
  --batch-size 100 \
  --max-retries 3
```

**체크리스트**:
- [ ] Papago API 설정 확인
- [ ] 112개 메뉴 × 2 언어 번역 실행
- [ ] DB 업데이트 확인 (5-10분 소요)
- [ ] UI 테스트 (언어 탭 동작)
- [ ] Git commit & 재검증 요청

**성공 기준**: 560/560 번역 완료, UI 100% 동작

---

### 🏢 Team 2: Frontend Team (B2B Admin)
**담당**: Admin Dashboard UI 개발 (P1 Issue #5)
**시간**: 4-6시간
**일정**: 월-수 (3일, 병렬 가능)
**결과**: Feature-Validator 80점 → **95점**

**담당자**: 1-2명
**준비물**: Bootstrap 5, HTML5, Vanilla JS

📄 **상세 지시서**: `C:\project\menu\.claude\P1_B2B_ADMIN_UI_TASK.md`

**개발 파일**:
```
app/frontend-b2b/
├── admin.html                 # 메인 페이지 (완전한 HTML)
├── css/
│   ├── admin-dashboard.css    # 스타일
│   └── admin-responsive.css   # 반응형 (768px)
└── js/
    ├── admin-api.js           # API 호출
    └── admin-dashboard.js     # 상태 관리 & 렌더링
```

**체크리스트**:
- [ ] admin.html 구조 완성 (헤더, 메인, 사이드바)
- [ ] CSS 반응형 테스트 (768px)
- [ ] JS API 호출 함수 완성
- [ ] 필터/액션 버튼 동작
- [ ] 실시간 통계 갱신 (5초)
- [ ] 콘솔 에러 0개
- [ ] Git commit & UI 테스트

**성공 기준**: Admin API 모든 엔드포인트 동작, 폐이지 로드 < 2초

---

### ⚙️ Team 3: Backend Team (API Optimization)
**담당**: API 성능 & 안정성 (P1 Issues #6-9)
**시간**: 2.5-3시간
**일정**: 월-화 (2일, 병렬 가능)
**결과**: Backend-QA 75점 → **95점**

**담당자**: 2명 (병렬 작업 추천)
**준비물**: Python, SQLAlchemy, Tenacity, Pillow

📄 **상세 지시서**: `C:\project\menu\.claude\P1_BACKEND_OPTIMIZATION_TASK.md`

**4개 이슈 분담**:

| 이슈 | 담당 | 시간 | 파일 |
|------|------|------|------|
| #6: Thread-Safety | 1명 | 45분 | `matching_engine.py` |
| #7: Stats 성능 | 1명 | 50분 | `scan_log.py`, `admin.py` |
| #8: 재시도 로직 | 1명 | 30분 | `translation_service.py` |
| #9: 이미지 포맷 | 1명 | 25분 | `ocr_service.py` |

**체크리스트**:
- [ ] asyncio.Lock 구현 (Issue #6)
- [ ] 마이그레이션 & 쿼리 최적화 (Issue #7)
- [ ] Tenacity @retry 데코레이터 (Issue #8)
- [ ] 이미지 포맷 자동 감지 (Issue #9)
- [ ] 단위 테스트 통과
- [ ] 성능 벤치마크 확인
- [ ] Git commit

**성공 기준**: 모든 API 응답 < 3초, 안정성 개선

---

## 📅 일정표 (1주)

```
월요일:
├─ Team 1 (번역): 시작 → 진행 중 (2시간)
├─ Team 2 (Frontend): HTML 구조 작성 (2시간)
└─ Team 3 (Backend): Issue #6 + #7 (1.5시간)

화요일:
├─ Team 1 (번역): 완료 + 재검증
├─ Team 2 (Frontend): CSS + JS (3시간)
└─ Team 3 (Backend): Issue #8 + #9 (1.5시간)

수요일:
├─ Team 1 (번역): 재검증 + 최종 확인
├─ Team 2 (Frontend): 버그 수정 + 테스트 (1시간)
└─ Team 3 (Backend): 테스트 + 성능 검증 (1시간)

목요일:
├─ 모든 팀: QA 재검증 + 빌드
├─ Git commit 및 코드 리뷰
└─ 최종 테스트

금요일:
├─ 배포 준비 완료
├─ CONDITIONAL GO → ✅ GO 판정
└─ 배포 대기
```

---

## 🎯 주요 마일스톤

### ✅ Day 1-2 (월-화)
- [ ] 번역 완료 (560개 키)
- [ ] B2B Admin UI 60% 진행
- [ ] 백엔드 최적화 80% 진행

### ✅ Day 2-3 (화-수)
- [ ] 번역 재검증 완료
- [ ] B2B Admin UI 완성 + 테스트
- [ ] 백엔드 최적화 완성 + 벤치마크

### ✅ Day 3-4 (수-목)
- [ ] 모든 팀 작업 완료
- [ ] 통합 테스트 (end-to-end)
- [ ] QA 재검증 시작

### ✅ Day 4-5 (목-금)
- [ ] 최종 버그 수정
- [ ] Git commit & 코드 리뷰
- [ ] 배포 준비 완료

---

## 🔍 검증 기준 (Go-No Go)

### Team 1: Translation
```
성공 기준:
✅ 560/560 번역 키 완성
✅ B2C UI 언어 탭 동작
✅ QR 메뉴 (?lang=ja|zh) 동작
✅ I18n-Auditor 재검증: 95+점

재검증 요청:
→ I18n-Auditor에게 재검증 지시
   (5-10분 소요)
```

### Team 2: Frontend
```
성공 기준:
✅ admin.html 완성
✅ 반응형 (768px) 테스트 통과
✅ 콘솔 에러 0개
✅ 페이지 로드 < 2초
✅ 모든 API 연동 동작
✅ Feature-Validator 재검증: 95+점

재검증 요청:
→ Frontend-Tester에게 재검증 지시
   (15-20분 소요)
```

### Team 3: Backend
```
성공 기준:
✅ Issue #6: Thread-safe 캐시
✅ Issue #7: /admin/stats < 500ms
✅ Issue #8: 3회 재시도 작동
✅ Issue #9: 5개 포맷 지원
✅ Backend-QA 재검증: 95+점

재검증 요청:
→ Backend-QA에게 재검증 지시
   (30-45분 소요)
```

---

## 📊 최종 배포 판정

### 현재 상태
```
점수: 81.8/100 (B+)
상태: ⚠️ CONDITIONAL GO (3개 P0 버그 고정됨)
```

### 목표 상태 (이번 주 완료 후)
```
점수: 95+/100 (A)
상태: ✅ DEPLOYMENT READY

상세:
├─ 프론트엔드 UI/UX: 95/100 (유지)
├─ DB 아키텍처: 91/100 (유지)
├─ 성능 최적화: 95/100 (↑ 90)
├─ 기능 구현: 95/100 (↑ 80)
├─ 백엔드 API: 95/100 (↑ 75)
└─ 다국어 I18n: 95/100 (↑ 50)

종합: 95/100 (A) → ✅ GO
```

---

## 🚀 실행 명령어

### Team 1: 번역
```bash
cd C:\project\menu
python app/backend/scripts/translate_canonical_menus.py \
  --language ja,zh \
  --batch-size 100 \
  --max-retries 3
```

### Team 2: Frontend
```bash
# 로컬 테스트
cd C:\project\menu\app\frontend-b2b
python -m http.server 8081

# http://localhost:8081/admin.html 접속
```

### Team 3: Backend
```bash
# 마이그레이션 실행 (Issue #7)
python -m alembic upgrade head

# 성능 테스트
python app/backend/scripts/benchmark.py --endpoints /admin/stats

# 각 이슈별 테스트
python -m pytest app/backend/tests/test_thread_safety.py
python -m pytest app/backend/tests/test_ocr_formats.py
```

---

## 📞 소통 방식

### 일일 회의
- **시간**: 오전 10시, 오후 3시
- **목표**: 진행도 공유, 블로킹 이슈 해결
- **참석**: 각 팀 리더 1명

### GitHub Issues
- 각 팀별 branch: `feature/translation`, `feature/admin-ui`, `feature/backend-optimization`
- PR 생성 시 관련 리포트 링크 포함
- 리뷰: 최소 1명 (다른 팀원)

### Slack / 메시지
- 긴급 이슈: 즉시 알림
- 일반 업데이트: 하루 1-2회

---

## ✅ 최종 체크리스트

### 준비 단계
- [ ] 각 팀 리더가 상세 지시서 읽음
- [ ] 필요한 도구/라이브러리 설치 확인
- [ ] API 키/시크릿 설정 확인 (번역팀)

### 개발 단계
- [ ] Team 1: P1_TRANSLATION_TASK.md 실행
- [ ] Team 2: P1_B2B_ADMIN_UI_TASK.md 실행
- [ ] Team 3: P1_BACKEND_OPTIMIZATION_TASK.md 실행

### 테스트 단계
- [ ] 각 팀 자체 테스트 완료
- [ ] 통합 테스트 (모든 팀 동시)
- [ ] QA 재검증 요청

### 배포 단계
- [ ] 모든 P1 이슈 해결 확인
- [ ] 최종 점수 95+/100 달성
- [ ] ✅ GO 판정 받음
- [ ] 배포 진행

---

## 📚 참고 문서

| 주제 | 문서 | 팀 |
|------|------|-----|
| 번역 | `P1_TRANSLATION_TASK.md` | Team 1 |
| B2B UI | `P1_B2B_ADMIN_UI_TASK.md` | Team 2 |
| 백엔드 | `P1_BACKEND_OPTIMIZATION_TASK.md` | Team 3 |
| 원본 검증 | `VALIDATION_FINAL_REPORT_20260211.md` | All |
| Playbook | `C:\project\dev-reference\playbooks\i18n-setup.md` | Team 1 |

---

## 💬 연락처 & 지원

- **리더**: [Project Lead Name]
- **기술 리뷰**: [Architect]
- **QA**: [QA Lead]
- **배포**: [DevOps Lead]

---

**목표**: 🎯 **월요일 시작 → 금요일 배포 완료**

**성공 판정**: 81.8/100 (CONDITIONAL GO) → 95+/100 (✅ GO)

---

**준비 완료! 🚀 각 팀이 지시서를 읽고 월요일부터 시작하세요.**
