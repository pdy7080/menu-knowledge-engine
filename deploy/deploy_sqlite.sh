#!/bin/bash
# Menu Knowledge Engine - SQLite 배포 스크립트
# FastComet Chargeap 서버용 (sudo 권한 불필요)

set -e

echo "🚀 Menu Knowledge Engine - SQLite 배포 시작..."

# 변수 설정
DEPLOY_DIR="$HOME/menu-knowledge"
BACKEND_DIR="$DEPLOY_DIR/app/backend"
VENV_DIR="$BACKEND_DIR/venv"
DB_PATH="$BACKEND_DIR/menu_knowledge.db"
PORT=8000

# 1. 디렉토리 이동
echo "📂 배포 디렉토리로 이동: $DEPLOY_DIR"
cd "$DEPLOY_DIR"

# 2. 최신 코드 pull
echo "📥 최신 코드 가져오기..."
git fetch origin
git checkout main
git pull origin main

# 3. Python 가상환경 생성 (없으면)
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Python 가상환경 생성..."
    cd "$BACKEND_DIR"
    python3 -m venv venv
else
    echo "✅ Python 가상환경 이미 존재"
fi

# 4. 의존성 설치
echo "📦 Python 패키지 설치..."
cd "$BACKEND_DIR"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. .env.production 파일 생성 (없으면)
if [ ! -f "$BACKEND_DIR/.env.production" ]; then
    echo "📝 .env.production 파일 생성..."
    cat > "$BACKEND_DIR/.env.production" <<EOF
# SQLite Database
DATABASE_URL=sqlite:///$DB_PATH

# Application
APP_ENV=production
DEBUG=false
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://menu-knowledge.chargeapp.net

# Redis Cache (비활성화)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_ENABLED=false

# API Keys (실제 키로 변경 필요)
OPENAI_API_KEY=
CLOVA_OCR_API_KEY=
CLOVA_OCR_SECRET=
PAPAGO_CLIENT_ID=
PAPAGO_CLIENT_SECRET=

# Storage
S3_ENDPOINT=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET_NAME=menu-knowledge-bucket

# Logging
LOG_LEVEL=INFO
EOF
    echo "⚠️  .env.production 파일이 생성되었습니다."
    echo "⚠️  OPENAI_API_KEY 등 실제 API 키를 입력하세요!"
else
    echo "✅ .env.production 파일 이미 존재"
fi

# 6. 데이터베이스 초기화 (테이블 생성)
echo "🗄️  데이터베이스 초기화..."
cd "$BACKEND_DIR"
source venv/bin/activate

# init_db.py 스크립트 실행
python3 << 'PYTHON_SCRIPT'
import asyncio
from database import init_db

async def main():
    print("Creating database tables...")
    await init_db()
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())
PYTHON_SCRIPT

# 7. 기존 프로세스 중지 (있으면)
echo "🛑 기존 프로세스 중지..."
pkill -f "uvicorn main:app" || true
sleep 2

# 8. 서버 시작 (백그라운드)
echo "🚀 서버 시작 (포트 $PORT)..."
cd "$BACKEND_DIR"
source venv/bin/activate

# nohup으로 백그라운드 실행
nohup uvicorn main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --env-file .env.production \
    --log-level info \
    > logs/server.log 2>&1 &

SERVER_PID=$!
echo "✅ 서버 시작됨 (PID: $SERVER_PID)"

# 9. 서버 헬스체크 (10초 대기)
echo "⏳ 서버 시작 대기 중..."
sleep 10

# 헬스체크
if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
    echo "✅ 배포 성공! 서버가 정상 동작 중입니다."
    echo "🔗 Health Check: http://localhost:$PORT/health"
    echo "🔗 API Docs: http://localhost:$PORT/docs"
    echo ""
    echo "📋 서버 정보:"
    echo "  - PID: $SERVER_PID"
    echo "  - Port: $PORT"
    echo "  - Database: SQLite ($DB_PATH)"
    echo "  - Logs: $BACKEND_DIR/logs/server.log"
    echo ""
    echo "📝 서버 중지: pkill -f 'uvicorn main:app'"
    echo "📝 로그 확인: tail -f $BACKEND_DIR/logs/server.log"
else
    echo "❌ 헬스체크 실패! 로그를 확인하세요."
    echo "📝 로그 확인: tail -f $BACKEND_DIR/logs/server.log"
    exit 1
fi
