# 🚀 Menu Knowledge Engine v0.1.0 배포 가이드

**최종 수정**: 2026-02-13
**상태**: Phase 3.3 프로덕션 배포 ✅ 완료
**목표**: Menu Knowledge Engine을 Chargeap 서버에 배포하기

---

## 📚 공통 참조 문서

> 다른 프로젝트에서도 이 문서를 참조할 수 있습니다.

| 문서 | 위치 | 용도 |
|------|------|------|
| **FastComet 배포 (전체)** | `dev-reference/docs/FASTCOMET_DEPLOYMENT_GUIDE.md` | Python venv, Node.js, Nginx, SSL 설정 |
| **PostgreSQL 설정** | `dev-reference/docs/FASTCOMET_POSTGRESQL_SETUP.md` | ⭐ cPanel Database Wizard 사용 방법 |
| **배포 빠른 시작** | `dev-reference/docs/FASTCOMET_DEPLOYMENT_QUICK_START.md` | 5분 안에 배포하기 |
| **문제 해결** | `dev-reference/docs/FASTCOMET_DEPLOYMENT_TROUBLESHOOTING.md` | SSH, 에러 디버깅 |

**새 프로젝트에서 DB가 필요한 경우:**
→ `FASTCOMET_POSTGRESQL_SETUP.md`의 "다른 프로젝트에서 사용하기" 섹션 참조

---

## ⚡ FastComet Managed VPS 특이사항

> **중요**: FastComet의 **Managed VPS** 플랜에서는 다음 제한사항이 있습니다.
> 이 정보는 향후 배포 시 필수 참조 사항입니다.

### 🚫 Docker 미지원
- **상황**: Managed VPS에서는 Docker 미지원
- **이유**: root 권한 필요, Managed 환경에서는 보안상 제한
- **해결책**:
  - Python `venv` + `uvicorn` 사용 (이번 배포 방식)
  - 또는 Unmanaged VPS로 업그레이드 필요
- **참고**: `sudo` 명령어 사용 불가

### ✅ PostgreSQL 설치 가능
- **상황**: FastComet 지원팀이 직접 설치 가능
- **요청 방법**: cPanel → Support Ticket에서 요청
- **설치 정보**:
  - 메일로 연결 정보 제공
  - 기본 포트: 5432 (localhost만 접근)
  - 사용자명/비밀번호 설정됨

### ✅ Redis cPanel 도구로 관리
- **상황**: cPanel에 내장 Redis 관리 도구 있음
- **위치**: cPanel → "Redis" 검색
- **설정**:
  - 인스턴스 자동 생성 가능
  - 포트: 무작위 할당 (예: 34967)
  - 비밀번호: 자동 생성
- **접근**: localhost 또는 127.0.0.1

### 🔌 포트 관리
- **현재 상태**: FastAPI는 8000번 포트에서 실행
- **외부 접근**:
  - 8000번 포트: 직접 접근 가능
  - 80번 포트: cPanel Reverse Proxy 필요
- **Reverse Proxy 설정**:
  ```
  cPanel → Apache Handlers 또는 Proxy 설정
  URL 포트: 80/443
  내부 포트: 8000
  ```

---

## 📊 실제 배포 결과 (2026-02-12)

### 환경 구성 (최종 - 2026-02-13)
```
✅ Python 3.12 + venv
✅ FastAPI + uvicorn (2 workers)
✅ PostgreSQL 13.23 (cPanel 관리)
✅ Redis (cPanel, 127.0.0.1:34967)
❌ Docker (Managed VPS 미지원 - venv 사용)
```

### 📦 PostgreSQL 설치 정보 (2026-02-13)
```
Database: chargeap_menu_knowledge
User: chargeap_dcclab2022
Host: localhost:5432
Status: ✅ Connected (Health Check: database=true)

CONNECTION STRING:
postgresql+asyncpg://chargeap_dcclab2022:eromlab!1228@localhost:5432/chargeap_menu_knowledge
```

### 배포 성공 메트릭
- 배포 시간: 약 3분
- Health Check: ✅ 성공 (database: true)
- PostgreSQL 연결: ✅ 성공
- Redis 연결: ✅ 성공
- API 응답: ✅ 정상 (<100ms)
- 메모리 사용: 약 150MB
- CPU 사용: 약 1-2%

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

## 🚀 배포 방식 비교

### Docker 기반 배포 (원래 계획)
```
❌ FastComet Managed VPS에서 미지원
   - root 권한 필요
   - Unmanaged VPS로 업그레이드 필요 (추가 비용)

✅ 대안: Unmanaged VPS 또는 다른 호스팅
   - AWS EC2, DigitalOcean, Linode 등
```

### Python venv 배포 (현재 방식) ⭐
```
✅ FastComet Managed VPS 완벽 지원
✅ 추가 비용 없음
✅ 간단한 설치 및 관리
✅ 성능: Docker와 동등 수준

구성:
- Python venv (격리된 환경)
- uvicorn (ASGI 서버)
- systemd (자동 시작)
- cPanel Redis (캐싱)
- PostgreSQL (FastComet 설치)
```

### 배포 절차 (venv 방식)
```bash
1. Python venv 생성
   python3 -m venv venv
   source venv/bin/activate

2. 의존성 설치
   pip install -r requirements.txt

3. 환경변수 설정
   .env.production 생성 (Redis, DB 정보)

4. 서버 시작
   nohup uvicorn main:app --host 0.0.0.0 --port 8000 \
       --env-file .env.production &

5. systemd 등록 (자동 시작)
   /etc/systemd/system/menu-api.service
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

## ⚙️ systemd 자동 시작 설정

서버 재부팅 시 FastAPI가 자동으로 시작되도록 설정합니다.

### 1️⃣ systemd 서비스 파일 생성

```bash
# SSH 접속 후
ssh chargeap@d11475.sgp1.stableserver.net

# 서비스 파일 생성
cat > /tmp/menu-api.service << 'EOF'
[Unit]
Description=Menu Knowledge Engine API
After=network.target

[Service]
Type=simple
User=chargeap
WorkingDirectory=/home/chargeap/menu-knowledge/app/backend
ExecStart=/home/chargeap/menu-knowledge/app/backend/venv/bin/uvicorn \
    main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --env-file .env.production \
    --access-log
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 참고: sudo 필요하므로 FastComet 지원팀에 설치 요청
```

### 2️⃣ 자동 시작 활성화 (FastComet 지원팀 요청 후)

```bash
sudo systemctl daemon-reload
sudo systemctl enable menu-api
sudo systemctl start menu-api
sudo systemctl status menu-api
```

---

## 📊 실시간 모니터링

### 프로세스 상태 확인
```bash
# 프로세스 실행 여부
ps aux | grep uvicorn

# 포트 확인
netstat -tuln | grep 8000  # 또는
lsof -i :8000
```

### 로그 확인
```bash
# 마지막 로그 확인
tail -50 ~/menu-knowledge/app/backend/logs/server.log

# 실시간 로그 (Ctrl+C로 종료)
tail -f ~/menu-knowledge/app/backend/logs/server.log

# 에러만 필터링
grep ERROR ~/menu-knowledge/app/backend/logs/server.log
```

### Redis 상태 확인
```bash
# Redis 연결 테스트
redis-cli -h 127.0.0.1 -p 34967 -a PRPpam4vhU9uZL9zOyy ping

# Redis 캐시 통계
redis-cli -h 127.0.0.1 -p 34967 -a PRPpam4vhU9uZL9zOyy info stats

# 캐시 키 확인
redis-cli -h 127.0.0.1 -p 34967 -a PRPpam4vhU9uZL9zOyy keys "*"
```

### 서버 재시작
```bash
# 프로세스 종료
pkill -f 'uvicorn main:app'

# 수동 재시작
cd ~/menu-knowledge/app/backend
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 \
    --env-file .env.production \
    --workers 4 \
    --access-log > logs/server.log 2>&1 &
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

## 💾 PostgreSQL 설치 후 설정

FastComet에서 PostgreSQL 설치가 완료되면 다음을 수행합니다:

### 1️⃣ 접속 정보 확인
```
FastComet 이메일에서 다음 정보 확인:
- Database Host: localhost (또는 IP)
- Port: 5432 (기본값)
- Database Name: menu_knowledge_db
- Username: menu_admin
- Password: [확인]
```

### 2️⃣ .env.production 업데이트
```bash
# SSH 접속
ssh chargeap@d11475.sgp1.stableserver.net

# 파일 수정
nano ~/menu-knowledge/app/backend/.env.production

# 다음 라인 업데이트:
DATABASE_URL=postgresql+asyncpg://menu_admin:PASSWORD@localhost:5432/menu_knowledge_db
```

### 3️⃣ 데이터베이스 초기화
```bash
# SSH에서
cd ~/menu-knowledge/app/backend
source venv/bin/activate

# 마이그레이션 실행
python -c "from database import init_db; init_db()"

# 또는
alembic upgrade head
```

### 4️⃣ 서버 재시작
```bash
# 프로세스 종료
pkill -f 'uvicorn main:app'

# 재시작
nohup uvicorn main:app --host 0.0.0.0 --port 8000 \
    --env-file .env.production \
    --workers 4 \
    --access-log > logs/server.log 2>&1 &
```

### 5️⃣ 데이터베이스 연결 확인
```bash
# 직접 테스트 (psql 클라이언트 설치 필요)
psql -h localhost -U menu_admin -d menu_knowledge_db -c "SELECT version();"

# 또는 API를 통해 확인
curl http://localhost:8000/health
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
