# 🚀 Menu Knowledge Engine v0.1.0 배포 가이드

**최종 수정**: 2026-02-12
**상태**: Phase 3.3 프로덕션 배포
**목표**: Menu Knowledge Engine을 Chargeap 서버에 배포하기

---

## 📋 배포 체크리스트

### Phase 1: 준비 단계 ✅
- [x] Docker 이미지 준비 (Dockerfile, docker-compose.yml)
- [x] CI/CD 파이프라인 구성 (.github/workflows/)
- [x] 환경변수 템플릿 작성 (.env.example)
- [ ] **GitHub Secrets 설정** ← 현재 단계

### Phase 2: 배포 전 검증 ⏳
- [ ] GitHub Secrets 등록 (7개)
- [ ] SSH 접속 테스트
- [ ] 배포 디렉토리 준비

### Phase 3: 실제 배포 ⏳
- [ ] 초기 배포 스크립트 실행
- [ ] Health Check 검증
- [ ] API 엔드포인트 테스트
- [ ] 서브도메인 설정

---

## 🔐 GitHub Secrets 설정 (필수 7개)

### Step 1: GitHub 저장소 접속
```
https://github.com/[username]/menu → Settings → Secrets and variables → Actions
```

### Step 2: 다음 7개 Secrets 등록

#### 1️⃣ CHARGEAP_HOST
```
값: d11475.sgp1.stableserver.net
설명: Chargeap 서버 호스트명
```

#### 2️⃣ CHARGEAP_USER
```
값: chargeap
설명: SSH 로그인 사용자명
```

#### 3️⃣ CHARGEAP_SSH_KEY
```
값: -----BEGIN RSA PRIVATE KEY-----
     [SSH Private Key 내용]
     -----END RSA PRIVATE KEY-----
설명: SSH Private Key (PEM 형식)
생성 방법: ssh-keygen -t rsa -b 4096 -f menu_deploy
```

#### 4️⃣ CHARGEAP_DEPLOY_PATH
```
값: /home/chargeap/menu-knowledge
설명: 배포 디렉토리 경로 (자동 생성)
```

#### 5️⃣ DATABASE_URL
```
값: postgresql+asyncpg://[user]:[password]@[host]:[port]/[database]
예: postgresql+asyncpg://menu_admin:menu_dev_2025@localhost:5432/menu_knowledge_db
설명: PostgreSQL 연결 문자열 (프로덕션 DB)
```

#### 6️⃣ SECRET_KEY
```
값: [64자 이상의 랜덤 문자열]
생성 방법: python -c "import secrets; print(secrets.token_urlsafe(64))"
설명: FastAPI SECRET_KEY (보안)
```

#### 7️⃣ OPENAI_API_KEY
```
값: sk-proj-[...]
설명: OpenAI API Key (메뉴 번역용)
```

### Step 3: 검증
```bash
# GitHub Actions 로그에서 Secrets 마스킹 확인
# ✅ 보이는 예: CHARGEAP_HOST=***
```

---

## 🔑 SSH Key 생성 (처음 설정 시)

```bash
# 1. SSH Key 쌍 생성
ssh-keygen -t rsa -b 4096 -f menu_deploy -N ""

# 2. Public Key를 Chargeap 서버에 추가
# ~/.ssh/authorized_keys 에 menu_deploy.pub 내용 추가

# 3. Private Key를 GitHub Secret으로 등록
cat menu_deploy | pbcopy  # macOS
cat menu_deploy | wl-copy # Linux
# Windows: Notepad menu_deploy → 복사

# 4. 로컬 테스트
ssh -i menu_deploy chargeap@d11475.sgp1.stableserver.net "echo 'SSH 접속 성공'"
```

---

## 📦 배포 구조

```
Chargeap Server (/home/chargeap/menu-knowledge/)
├── app/                    # 애플리케이션 소스
│   ├── backend/
│   ├── docker-compose.yml
│   └── Dockerfile
├── .env.production         # 프로덕션 환경변수
├── .git/                   # Git 저장소
└── docker-compose.logs     # 로그 파일
```

---

## 🚀 배포 플로우

### 자동 배포 (main 브랜치 머지 시)
```
1. GitHub Actions 트리거
2. CI 파이프라인 실행 (Lint → Test → Build)
3. SSH로 Chargeap 서버 접속
4. Git pull (최신 코드 다운로드)
5. docker-compose build --no-cache
6. docker-compose up -d
7. Health check 검증
```

### 수동 배포 (필요 시)
```bash
# GitHub Actions > CD - Deploy to Production > Run workflow
# 또는 CLI:
gh workflow run cd.yml --ref main -f environment=production
```

---

## 🧪 배포 후 검증

### 1️⃣ Health Check
```bash
curl http://localhost:8000/health

# 예상 응답:
# {
#   "status": "ok",
#   "service": "Menu Knowledge Engine",
#   "version": "0.1.0",
#   "environment": "production"
# }
```

### 2️⃣ Admin Stats API
```bash
curl http://localhost:8000/api/v1/admin/stats

# 캐싱 동작 확인 (Redis)
```

### 3️⃣ B2B 식당 등록 API
```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "테스트 식당",
    "owner_name": "김철수",
    "owner_phone": "010-1234-5678",
    "address": "서울시 강남구",
    "business_license": "1234567890"
  }'
```

---

## 🌐 서브도메인 설정

### 현재 상황
- Backend API: `http://localhost:8000` (로컬) / `http://[Chargeap]:8000` (프로덕션)
- 목표: `https://api.menu.chargeapp.net` (서브도메인)

### 설정 방법

#### Step 1: DNS 레코드 추가
```
호스트: api.menu
타입: A
값: [Chargeap 서버 IP]  또는 CNAME: d11475.sgp1.stableserver.net
```

#### Step 2: Nginx/Reverse Proxy 설정
```nginx
# /etc/nginx/sites-available/menu-api

server {
    listen 80;
    server_name api.menu.chargeapp.net;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Step 3: SSL/TLS 인증서 (Let's Encrypt)
```bash
sudo certbot certonly --standalone -d api.menu.chargeapp.net
sudo certbot renew --dry-run  # 자동 갱신 테스트
```

---

## 🚨 트러블슈팅

### 문제 1: SSH 접속 거부
```bash
# 원인: 공개키 미등록
# 해결:
ssh-copy-id -i menu_deploy.pub chargeap@d11475.sgp1.stableserver.net
```

### 문제 2: Docker 이미지 빌드 실패
```bash
# 원인: 의존성 누락
# 해결:
docker-compose build --no-cache --pull
```

### 문제 3: PostgreSQL 연결 실패
```bash
# 원인: DATABASE_URL 잘못됨
# 확인:
echo $DATABASE_URL
psql $DATABASE_URL -c "SELECT 1"
```

### 문제 4: Redis 캐싱 미작동
```bash
# 원인: Redis 서버 미실행
# 확인:
docker-compose ps
redis-cli ping  # PONG 응답 확인
```

---

## 📊 배포 후 모니터링

### Health Check URL
```
http://api.menu.chargeapp.net/health
```

### Admin 대시보드
```
http://api.menu.chargeapp.net/admin/stats
```

### API 문서 (Swagger)
```
http://api.menu.chargeapp.net/docs
```

### 로그 확인
```bash
docker-compose logs backend --follow
```

---

## 🎯 다음 단계

### Phase 4: 모니터링 & 최적화
- [ ] Sentry 에러 모니터링 설정
- [ ] New Relic APM 성능 모니터링
- [ ] CloudFlare CDN 설정
- [ ] 백업 전략 수립

### Phase 5: 프론트엔드 개발 (v0.2)
- [ ] Admin Dashboard UI
- [ ] B2B 포탈
- [ ] 메뉴 관리 UI

---

## 📞 필요한 정보

현재 배포를 진행하기 위해 다음 정보가 필요합니다:

```
[ ] Chargeap 서버 접속 권한
    - Host: d11475.sgp1.stableserver.net
    - User: chargeap
    - SSH Key: ?

[ ] 프로덕션 PostgreSQL
    - Host: ?
    - Port: ? (기본 5432)
    - Database: menu_knowledge_db
    - User: ?
    - Password: ?

[ ] OpenAI API Key
    - 이미 .env에 있음: sk-proj-...

[ ] 서브도메인 (선택)
    - api.menu.chargeapp.net
    - 또는 menu-api.chargeapp.net
```

---

## ✅ 배포 완료 확인

```
배포 완료 시:
✅ http://api.menu.chargeapp.net/health → 200 OK
✅ Redis 캐싱 동작
✅ PostgreSQL 연결 성공
✅ Docker 컨테이너 실행 중
✅ GitHub Actions CI/CD 자동 배포 활성화
```

---

**배포 준비 완료!** 🎉
