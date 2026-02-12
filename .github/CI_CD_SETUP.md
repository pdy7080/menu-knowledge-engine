# CI/CD Pipeline 설정 완료

Menu Knowledge Engine의 자동 빌드/배포 파이프라인이 구성되었습니다.

## 📋 구성 요소

### 1. CI Workflow (`.github/workflows/ci.yml`)

**트리거**:
- `push`: main, develop, feature/** 브랜치
- `pull_request`: main, develop 브랜치

**Jobs**:
1. **Lint**: pylint으로 코드 품질 검사
2. **Test**: pytest로 자동화 테스트 실행 (PostgreSQL, Redis 서비스 포함)
3. **Build**: Docker 이미지 빌드 및 테스트
4. **Summary**: CI 결과 요약

**특징**:
- GitHub Actions Cache 활용 (pip, Docker Buildx)
- PostgreSQL/Redis 서비스 컨테이너 자동 구성
- 실패 시에도 다음 단계 진행 (continue-on-error)

---

### 2. CD Workflow (`.github/workflows/cd.yml`)

**트리거**:
- `push`: main 브랜치 (자동 배포)
- `workflow_dispatch`: 수동 배포 (production/staging 선택 가능)

**Jobs**:
1. **Deploy to Chargeap Server**
   - SSH로 서버 접속
   - Git pull (최신 코드)
   - Docker 이미지 재빌드
   - docker-compose up -d (서비스 재시작)
   - Health check 검증

**특징**:
- 무중단 배포 (docker-compose down → build → up)
- 배포 후 헬스체크 자동 실행
- 실패 시 알림 (GitHub Actions 로그)

---

## 🚀 사용 방법

### 1. Pull Request 생성 시 (자동 CI)

```bash
# 새 브랜치 생성
git checkout -b feature/new-feature

# 코드 작성
# ...

# 커밋 및 푸시
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

**결과**: GitHub에서 PR 생성 → CI 워크플로우 자동 실행 → Lint/Test/Build 결과 확인

---

### 2. main 브랜치 머지 시 (자동 배포)

```bash
# main 브랜치로 머지
git checkout main
git merge feature/new-feature
git push origin main
```

**결과**: CD 워크플로우 자동 실행 → Chargeap 서버에 배포

---

### 3. 수동 배포

**GitHub 웹에서**:
1. **Actions** 탭 클릭
2. **CD - Deploy to Production** 선택
3. **Run workflow** 클릭
4. Environment 선택 (production/staging)
5. **Run workflow** 실행

---

## 🔐 필수 GitHub Secrets

다음 Secrets을 GitHub 저장소에 등록해야 합니다:

| Secret Name | 설명 |
|------------|------|
| `CHARGEAP_HOST` | 서버 호스트명 |
| `CHARGEAP_USER` | SSH 사용자명 |
| `CHARGEAP_SSH_KEY` | SSH Private Key |
| `CHARGEAP_DEPLOY_PATH` | 배포 경로 |
| `DATABASE_URL` | PostgreSQL 연결 문자열 |
| `SECRET_KEY` | FastAPI SECRET_KEY |
| `OPENAI_API_KEY` | OpenAI API Key |

**설정 방법**: [SECRETS_SETUP.md](SECRETS_SETUP.md) 참조

---

## 📊 워크플로우 실행 확인

### GitHub Actions 페이지

1. GitHub 저장소 → **Actions** 탭
2. 왼쪽 메뉴에서 워크플로우 선택:
   - **CI - Lint, Test, Build**
   - **CD - Deploy to Production**
3. 최근 실행 목록 확인

### 배포 상태 확인

```bash
# 서버에서 컨테이너 상태 확인
ssh chargeap@d11475.sgp1.stableserver.net
cd /home/chargeap/menu-knowledge/app
docker-compose ps

# 로그 확인
docker-compose logs backend --tail 50

# 헬스체크
curl http://localhost:8000/health
```

---

## 🎯 배포 플로우

```
코드 작성 → 브랜치 푸시 → PR 생성 → CI 실행 (Lint/Test/Build)
                                            ↓ (통과)
                                         리뷰 승인
                                            ↓
                                      main 브랜치 머지
                                            ↓
                                      CD 실행 (자동 배포)
                                            ↓
                                    프로덕션 서버 업데이트
                                            ↓
                                       헬스체크 검증
                                            ↓
                                         배포 완료 ✅
```

---

## 🐛 트러블슈팅

### CI 실패

**문제**: Lint/Test 실패

**해결**:
1. GitHub Actions 로그 확인
2. 로컬에서 동일 명령 실행:
   ```bash
   cd app/backend
   pylint --disable=all --enable=E,F api/ services/ models/
   pytest tests/ -v
   ```
3. 수정 후 재푸시

---

### CD 실패

**문제**: 배포 중 에러

**해결**:
1. GitHub Actions 로그 확인
2. SSH로 서버 접속하여 수동 확인:
   ```bash
   ssh chargeap@d11475.sgp1.stableserver.net
   cd /home/chargeap/menu-knowledge/app
   docker-compose logs backend
   ```
3. 필요 시 수동 롤백:
   ```bash
   git checkout <이전_커밋>
   docker-compose down
   docker-compose build backend
   docker-compose up -d
   ```

---

## 📈 모니터링

### GitHub Actions Insights

**Settings → Actions → General**:
- Workflow 실행 통계
- 평균 실행 시간
- 실패율

### 서버 모니터링

```bash
# CPU/메모리 사용량
docker stats

# 디스크 사용량
df -h

# 네트워크 상태
docker-compose logs backend | grep "INFO"
```

---

## 🔄 향후 개선 사항

- [ ] Docker Hub/GitHub Container Registry로 이미지 푸시
- [ ] 롤백 자동화 (배포 실패 시 자동 롤백)
- [ ] Slack/Discord 알림 통합
- [ ] 성능 테스트 자동화 (Locust/K6)
- [ ] Blue-Green 배포 전략
- [ ] 카나리 배포 (점진적 배포)

---

**Last Updated**: 2026-02-12
**Version**: v1.0
