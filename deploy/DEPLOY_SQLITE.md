# SQLite 배포 가이드 (sudo 권한 불필요)

FastComet Chargeap 서버에서 **PostgreSQL/Redis/Docker 없이** Menu Knowledge Engine을 배포하는 방법입니다.

## ✅ 장점

- sudo 권한 불필요
- 외부 서비스 불필요 (DB, Redis)
- 15분 내 배포 완료
- Python만 설치되어 있으면 가능

## ⚠️ 제약 사항

- SQLite 동시성 제한 (단일 사용자 환경 권장)
- Redis 캐싱 비활성화 (성능 영향)
- 프로덕션 환경으로는 부족 (임시/테스트용 권장)

---

## 📋 사전 요구사항

Chargeap 서버에 다음이 설치되어 있어야 합니다:

- [x] Python 3.11+ (`python3 --version`)
- [x] pip (`pip3 --version`)
- [x] Git (`git --version`)
- [x] curl (`curl --version`)

---

## 🚀 배포 방법

### Step 1: 서버에 SSH 접속

```bash
ssh chargeap@d11475.sgp1.stableserver.net
```

### Step 2: 배포 스크립트 실행

```bash
cd ~/menu-knowledge
bash deploy/deploy_sqlite.sh
```

**스크립트가 자동으로 수행하는 작업**:
1. 최신 코드 pull (`git pull origin main`)
2. Python 가상환경 생성 (`python3 -m venv venv`)
3. 의존성 설치 (`pip install -r requirements.txt`)
4. `.env.production` 파일 생성 (SQLite 설정)
5. 데이터베이스 초기화 (테이블 생성)
6. 기존 프로세스 중지
7. 서버 시작 (`uvicorn` 백그라운드 실행)
8. 헬스체크 검증

**예상 소요 시간**: 5-10분

---

## 🔐 API 키 설정

배포 후 `.env.production` 파일에 실제 API 키를 입력해야 합니다.

### 편집 방법

```bash
cd ~/menu-knowledge/app/backend
nano .env.production
```

### 수정할 항목

```bash
# OpenAI API Key (필수)
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_HERE

# Naver CLOVA OCR (선택)
CLOVA_OCR_API_KEY=your_key_here
CLOVA_OCR_SECRET=your_secret_here

# Naver Papago (선택)
PAPAGO_CLIENT_ID=your_client_id
PAPAGO_CLIENT_SECRET=your_client_secret
```

**저장**: `Ctrl+O`, Enter, `Ctrl+X`

### 서버 재시작

```bash
# 서버 중지
pkill -f "uvicorn main:app"

# 서버 시작
cd ~/menu-knowledge/app/backend
source venv/bin/activate
nohup uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --env-file .env.production \
    --log-level info \
    > logs/server.log 2>&1 &
```

---

## ✅ 배포 검증

### 1. 헬스체크

```bash
curl http://localhost:8000/health
```

**기대 결과**:
```json
{
  "status": "ok",
  "service": "Menu Knowledge Engine",
  "version": "0.1.0",
  "environment": "production"
}
```

### 2. API 문서 확인

브라우저에서 다음 URL 접속:
- **Swagger UI**: http://YOUR_SERVER_IP:8000/docs
- **ReDoc**: http://YOUR_SERVER_IP:8000/redoc

### 3. 서버 로그 확인

```bash
tail -f ~/menu-knowledge/app/backend/logs/server.log
```

---

## 🔄 서버 관리 명령어

### 서버 상태 확인

```bash
# 프로세스 확인
ps aux | grep uvicorn

# 포트 확인
netstat -tuln | grep 8000
```

### 서버 중지

```bash
pkill -f "uvicorn main:app"
```

### 서버 재시작

```bash
cd ~/menu-knowledge/app/backend
source venv/bin/activate
nohup uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --env-file .env.production \
    --log-level info \
    > logs/server.log 2>&1 &
```

### 로그 확인

```bash
# 실시간 로그
tail -f ~/menu-knowledge/app/backend/logs/server.log

# 최근 100줄
tail -100 ~/menu-knowledge/app/backend/logs/server.log

# 에러 로그만
grep ERROR ~/menu-knowledge/app/backend/logs/server.log
```

---

## 🔧 트러블슈팅

### 문제 1: 포트 8000 이미 사용 중

**에러**: `Address already in use`

**해결**:
```bash
# 8000 포트 사용 중인 프로세스 찾기
lsof -i :8000

# 프로세스 종료
kill -9 <PID>
```

---

### 문제 2: Python 패키지 설치 실패

**에러**: `ModuleNotFoundError: No module named 'xxx'`

**해결**:
```bash
cd ~/menu-knowledge/app/backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 문제 3: 데이터베이스 초기화 실패

**에러**: `Table already exists`

**해결**:
```bash
# 기존 DB 삭제 (데이터 손실 주의!)
rm ~/menu-knowledge/app/backend/menu_knowledge.db

# 재배포
bash deploy/deploy_sqlite.sh
```

---

### 문제 4: 헬스체크 실패

**해결**:
```bash
# 로그 확인
tail -50 ~/menu-knowledge/app/backend/logs/server.log

# 서버 재시작
pkill -f "uvicorn main:app"
cd ~/menu-knowledge/app/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --env-file .env.production
```

---

## 🌐 외부 접속 설정 (선택)

### Apache 리버스 프록시 (cPanel)

cPanel에서 Apache를 리버스 프록시로 설정하면 도메인으로 접속 가능합니다.

**cPanel → Apache Configuration → Proxy**:
```apache
ProxyPass / http://localhost:8000/
ProxyPassReverse / http://localhost:8000/
```

**결과**: https://menu-knowledge.chargeapp.net → http://localhost:8000

---

## 📊 성능 모니터링

### CPU/메모리 사용량

```bash
# 프로세스 리소스 확인
ps aux | grep uvicorn

# 서버 전체 리소스
top
```

### 데이터베이스 크기

```bash
ls -lh ~/menu-knowledge/app/backend/menu_knowledge.db
```

### 로그 파일 크기

```bash
du -sh ~/menu-knowledge/app/backend/logs/
```

---

## 🔄 업데이트 방법

### 코드 업데이트

```bash
cd ~/menu-knowledge
git pull origin main
bash deploy/deploy_sqlite.sh
```

### Python 패키지 업데이트

```bash
cd ~/menu-knowledge/app/backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

---

## 📝 백업 방법

### 데이터베이스 백업

```bash
# 백업 디렉토리 생성
mkdir -p ~/menu-knowledge/backups

# DB 파일 복사
cp ~/menu-knowledge/app/backend/menu_knowledge.db \
   ~/menu-knowledge/backups/menu_knowledge_$(date +%Y%m%d_%H%M%S).db
```

### 자동 백업 (cron)

```bash
# crontab 편집
crontab -e

# 매일 새벽 3시 백업
0 3 * * * cp ~/menu-knowledge/app/backend/menu_knowledge.db ~/menu-knowledge/backups/menu_knowledge_$(date +\%Y\%m\%d).db
```

---

## 🚀 향후 업그레이드 경로

SQLite 배포는 **임시/테스트용**이므로, 실제 프로덕션에서는 다음을 권장합니다:

### Option 1: FastComet 지원팀에 요청
- PostgreSQL 설치
- Redis 설치
- Docker 설치
- **예상 소요 시간**: 1-2시간

### Option 2: 외부 서비스 사용
- **PostgreSQL**: ElephantSQL (무료 20MB)
- **Redis**: Redis Labs (무료 30MB)
- `.env.production`에서 DATABASE_URL, REDIS_HOST만 변경

### Option 3: 다른 서버로 이전
- AWS, DigitalOcean, Linode 등
- Docker Compose로 전체 스택 배포

---

**Last Updated**: 2026-02-12
**Version**: v1.0
