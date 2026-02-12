# 🚀 Sprint 4 개발 계획

**기간**: 2026-02-11 ~ 2026-02-25 (2주)
**목표**: B2B API 완성 및 프로덕션 배포 준비
**팀**: Backend (2), DevOps (1), QA (1)

---

## 📊 우선순위 순서

### Phase 1: B2B API 기초 (1주) ⭐ START HERE

#### Task 1.1: B2B 식당 등록 API
**소요시간**: 1일
**담당**: Backend-1

```
POST /api/v1/b2b/restaurants
Request:
{
  "name": "강남 한정식",
  "owner_name": "김철수",
  "owner_phone": "010-1234-5678",
  "address": "서울시 강남구...",
  "business_license": "1234567890"
}
Response:
{
  "restaurant_id": "uuid",
  "status": "pending_approval",
  "approval_url": "http://localhost:8000/admin/restaurants/uuid"
}
```

**체크리스트**
- [ ] Restaurant 모델 생성 (name, owner, address, license, status)
- [ ] SQLAlchemy migration
- [ ] API 엔드포인트 작성
- [ ] Admin UI에 "식당 승인" 페이지 추가
- [ ] 단위 테스트 작성

---

#### Task 1.2: B2B 메뉴 일괄 업로드 API
**소요시간**: 1.5일
**담당**: Backend-1

```
POST /api/v1/b2b/restaurants/{restaurant_id}/menus/upload
Request:
{
  "menus": [
    {
      "name_ko": "비빔밥",
      "description_en": "Rice with mixed vegetables",
      "category": "main"
    }
  ]
}
```

**체크리스트**
- [ ] CSV/JSON 파일 업로드 지원
- [ ] 메뉴 데이터 검증
- [ ] 자동 번역 (GPT-4o)
- [ ] 배치 저장
- [ ] 오류 처리 및 재시도

---

#### Task 1.3: B2B 메뉴 확정 승인 API
**소요시간**: 1일
**담당**: Backend-2

```
POST /api/v1/b2b/restaurants/{restaurant_id}/approve
Response:
{
  "status": "active",
  "menu_count": 42,
  "activation_date": "2026-02-12"
}
```

**체크리스트**
- [ ] 최종 데이터 검증
- [ ] QR 코드 생성
- [ ] 배포 전 체크리스트
- [ ] 식당 상태 변경

---

### Phase 2: 성능 & 캐싱 (3일)

#### Task 2.1: Redis 캐싱 구현
**소요시간**: 1.5일
**담당**: Backend-2

**캐싱 대상**
```python
# Admin Stats (5분 TTL)
cache_key = "admin:stats"
ttl = 300

# 메뉴 번역 (24시간 TTL)
cache_key = f"menu:translation:{menu_id}"
ttl = 86400

# 식당 정보 (1시간 TTL)
cache_key = f"restaurant:{restaurant_id}"
ttl = 3600
```

**체크리스트**
- [ ] Redis 연결 설정
- [ ] 캐시 데코레이터 생성
- [ ] TTL 정책 수립
- [ ] 무효화 전략 구현

---

#### Task 2.2: 로드 테스트 및 최적화
**소요시간**: 1.5일
**담당**: DevOps

```bash
# 테스트 항목
- API 동시 요청: 1000 RPS
- Admin Stats 응답: <100ms
- 메뉴 검색: <50ms
- 자동 번역: <3초
```

**체크리스트**
- [ ] K6 또는 Locust로 로드 테스트
- [ ] 병목 지점 식별
- [ ] 데이터베이스 쿼리 최적화
- [ ] 성능 리포트 작성

---

### Phase 3: DevOps & 배포 (3일)

#### Task 3.1: Docker 이미지 빌드
**소요시간**: 1일
**담당**: DevOps

```dockerfile
# app/backend/Dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**체크리스트**
- [ ] Dockerfile 작성
- [ ] docker-compose.yml (PostgreSQL, Redis 포함)
- [ ] 이미지 빌드 및 테스트
- [ ] 레지스트리 푸시

---

#### Task 3.2: CI/CD 파이프라인 구성
**소요시간**: 1day
**담당**: DevOps

**파이프라인 단계**
```
Push to main
  ↓
1. Lint & Type Check (tsc, pylint)
  ↓
2. Unit Tests (pytest)
  ↓
3. Build Docker Image
  ↓
4. Push to Registry
  ↓
5. Deploy to Staging
  ↓
6. Run E2E Tests
  ↓
7. Manual Approval
  ↓
8. Deploy to Production
```

**체크리스트**
- [ ] GitHub Actions 워크플로우 작성
- [ ] 자동 테스트 통합
- [ ] 이미지 빌드 및 푸시
- [ ] Staging 배포 자동화
- [ ] 수동 승인 단계 (Production)

---

#### Task 3.3: 프로덕션 배포
**소요시간**: 1day
**담당**: DevOps

**배포 대상**
```
Backend: Chargeap Server (포트 8766)
Database: RDS PostgreSQL
Cache: ElastiCache Redis
CDN: CloudFront (static files)
```

**체크리스트**
- [ ] 환경변수 설정 (.env.production)
- [ ] 데이터베이스 마이그레이션
- [ ] 백업 전략 수립
- [ ] 모니터링 대시보드 설정
- [ ] 장애 대응 계획

---

## 📈 성공 기준

| 지표 | 목표 | 검증 방법 |
|------|------|---------|
| **API Response Time** | <100ms (p95) | K6 로드 테스트 |
| **Uptime** | 99.9% | Monitoring |
| **Cache Hit Rate** | >80% | Redis stats |
| **Test Coverage** | >80% | pytest coverage |
| **Deployment Time** | <5분 | CI/CD 로그 |

---

## 🎯 일정 (데이 단위)

```
Day 1: Task 1.1 (식당 등록)
Day 2: Task 1.2 (메뉴 업로드)
Day 3: Task 1.3 (메뉴 확정)
Day 4-5: Task 2.1 (Redis 캐싱)
Day 5-6: Task 2.2 (로드 테스트)
Day 7: Task 3.1 (Docker)
Day 8: Task 3.2 (CI/CD)
Day 9: Task 3.3 (배포)
Day 10: 통합 테스트 & QA
```

---

## 🔧 개발자 체크리스트

### 개발팀 온보딩
- [ ] 코드리뷰 가이드 숙지 (CLAUDE.md)
- [ ] Git 워크플로우 확인
- [ ] 로컬 환경 설정 (Docker Compose)
- [ ] 테스트 데이터 준비

### Daily Standup
- 09:00 - 일일 미팅 (15분)
- 진행 상황, 블로커 공유
- 우선순위 조정

### Code Review
- 모든 PR은 2명 승인 필수
- Linting & Type Check 통과 필수
- 테스트 커버리지 >80% 필수

---

## 📞 비상 연락망

| 역할 | 이름 | 연락처 |
|------|------|--------|
| Tech Lead | - | - |
| DevOps | - | - |
| QA Lead | - | - |

---

## 🚀 시작 명령

```bash
# Sprint 4 시작
cd c:\project\menu

# 1. 새 브랜치 생성
git checkout -b feature/sprint4-b2b-api

# 2. 개발 시작
git pull origin master

# 3. Task 1.1 시작
# → Backend-1: 식당 등록 API 구현
```

---

**Ready to start? Let's go! 🚀**
