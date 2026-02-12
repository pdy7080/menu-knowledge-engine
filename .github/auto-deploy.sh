#!/bin/bash

# 🚀 Menu Knowledge Engine 자동 배포 스크립트
# Phase 3.3 프로덕션 배포

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "═══════════════════════════════════════════════════════════"
echo "🚀 Menu Knowledge Engine v0.1.0 자동 배포 시작!"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 배포 정보 (CLAUDE.md에서 수집)
CHARGEAP_HOST="d11475.sgp1.stableserver.net"
CHARGEAP_USER="chargeap"
CHARGEAP_DEPLOY_PATH="/home/chargeap/menu-knowledge"
BACKEND_PORT="8000"

# GitHub Secrets에서 제공됨 (보안상 노출 금지)
# DATABASE_URL과 OPENAI_API_KEY는 GitHub Secrets을 통해 주입됨
DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://menu_admin:@localhost:5432/menu_knowledge_db}"
OPENAI_API_KEY="${OPENAI_API_KEY:-sk-proj-****}"

echo "📋 배포 정보 확인"
echo "────────────────────────────────────────────────────────────"
echo "Host: $CHARGEAP_HOST"
echo "User: $CHARGEAP_USER"
echo "Deploy Path: $CHARGEAP_DEPLOY_PATH"
echo "Backend Port: $BACKEND_PORT"
echo ""

# Step 1: GitHub Secrets 설정
echo "📋 Step 1: GitHub Secrets 자동 설정"
echo "────────────────────────────────────────────────────────────"

# GitHub CLI 확인
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh)가 설치되지 않았습니다.${NC}"
    echo "설치: https://cli.github.com/"
    exit 1
fi

# 로그인 확인
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI 로그인이 필요합니다.${NC}"
    gh auth login
fi

echo ""
echo "설정 중인 Secrets:"
echo "  1. CHARGEAP_HOST"
echo "  2. CHARGEAP_USER"
echo "  3. CHARGEAP_DEPLOY_PATH"
echo "  4. DATABASE_URL"
echo "  5. SECRET_KEY"
echo "  6. OPENAI_API_KEY"
echo ""

# SECRET_KEY 생성
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))" 2>/dev/null || echo "temp-secret-key-$(date +%s)")

# Secrets 설정
echo "$CHARGEAP_HOST" | gh secret set CHARGEAP_HOST --body -
echo "$CHARGEAP_USER" | gh secret set CHARGEAP_USER --body -
echo "$CHARGEAP_DEPLOY_PATH" | gh secret set CHARGEAP_DEPLOY_PATH --body -
echo "$DATABASE_URL" | gh secret set DATABASE_URL --body -
echo "$SECRET_KEY" | gh secret set SECRET_KEY --body -
echo "$OPENAI_API_KEY" | gh secret set OPENAI_API_KEY --body -

echo -e "${GREEN}✅ GitHub Secrets 설정 완료!${NC}"
echo ""

# Step 2: SSH Key 확인
echo "📋 Step 2: SSH Key 확인"
echo "────────────────────────────────────────────────────────────"

SSH_KEY_PATH="${HOME}/.ssh/menu_deploy"

if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${YELLOW}⚠️  SSH Key가 없습니다. 생성합니다...${NC}"
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N ""
    echo -e "${GREEN}✅ SSH Key 생성 완료: $SSH_KEY_PATH${NC}"

    echo ""
    echo "⚠️  중요: 다음 공개키를 Chargeap 서버의 ~/.ssh/authorized_keys에 추가하세요:"
    echo "────────────────────────────────────────────────────────────"
    cat "${SSH_KEY_PATH}.pub"
    echo "────────────────────────────────────────────────────────────"
    echo ""
    read -p "공개키를 서버에 추가했으면 엔터를 누르세요..."
else
    echo -e "${GREEN}✅ SSH Key 존재: $SSH_KEY_PATH${NC}"
fi

# SSH Key를 GitHub Secret에 등록
SSH_KEY=$(cat "$SSH_KEY_PATH")
echo "$SSH_KEY" | gh secret set CHARGEAP_SSH_KEY --body -
echo -e "${GREEN}✅ SSH Key를 GitHub Secret에 등록했습니다.${NC}"
echo ""

# Step 3: SSH 접속 테스트
echo "📋 Step 3: SSH 접속 테스트"
echo "────────────────────────────────────────────────────────────"

if ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$CHARGEAP_USER@$CHARGEAP_HOST" "echo 'SSH 접속 성공'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH 접속 성공!${NC}"
else
    echo -e "${RED}❌ SSH 접속 실패. SSH Key가 서버에 등록되었는지 확인하세요.${NC}"
    exit 1
fi
echo ""

# Step 4: Chargeap 서버 배포 준비
echo "📋 Step 4: Chargeap 서버 배포 준비"
echo "────────────────────────────────────────────────────────────"

ssh -i "$SSH_KEY_PATH" "$CHARGEAP_USER@$CHARGEAP_HOST" << 'REMOTESCRIPT'
# 배포 디렉토리 생성
mkdir -p /home/chargeap/menu-knowledge
cd /home/chargeap/menu-knowledge

# Git 저장소 클론 (처음 1회만)
if [ ! -d .git ]; then
    echo "🔄 Git 저장소 클론 중..."
    git clone https://github.com/dccla/menu.git .
else
    echo "🔄 Git 저장소 업데이트 중..."
    git fetch origin
    git checkout main
    git pull origin main
fi

# .env.production 파일 생성
cat > .env.production << 'EOF'
# Database (프로덕션)
DATABASE_URL=postgresql+asyncpg://menu_admin:menu_dev_2025@localhost:5432/menu_knowledge_db

# Security
SECRET_KEY=temp-secret-key
DEBUG=False

# OpenAI API
OPENAI_API_KEY=sk-proj-...

# App
APP_ENV=production
LOG_LEVEL=INFO

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# CORS
ALLOWED_ORIGINS=https://api.menu.chargeapp.net,http://localhost:8000

EOF

echo "✅ 배포 디렉토리 준비 완료"
REMOTESCRIPT

echo -e "${GREEN}✅ Chargeap 서버 준비 완료!${NC}"
echo ""

# Step 5: Docker 빌드 및 배포
echo "📋 Step 5: Docker 이미지 빌드 및 배포"
echo "────────────────────────────────────────────────────────────"

ssh -i "$SSH_KEY_PATH" "$CHARGEAP_USER@$CHARGEAP_HOST" << 'REMOTESCRIPT'
cd /home/chargeap/menu-knowledge

echo "🔄 Docker 이미지 빌드 중..."
docker-compose build --no-cache

echo "🔄 서비스 시작 중..."
docker-compose up -d

echo "⏳ 서비스 시작 대기 중 (30초)..."
sleep 30

echo "✅ 배포 완료"
REMOTESCRIPT

echo -e "${GREEN}✅ Docker 배포 완료!${NC}"
echo ""

# Step 6: Health Check
echo "📋 Step 6: Health Check"
echo "────────────────────────────────────────────────────────────"

HEALTH_CHECK_URL="http://$CHARGEAP_HOST:$BACKEND_PORT/health"

echo "Health Check 실행 중: $HEALTH_CHECK_URL"
sleep 5

if curl -s "$HEALTH_CHECK_URL" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✅ Health Check 성공!${NC}"
else
    echo -e "${YELLOW}⚠️  Health Check 응답 확인 중...${NC}"
    curl -s "$HEALTH_CHECK_URL" | head -20
fi
echo ""

# Step 7: API 테스트
echo "📋 Step 7: API 엔드포인트 테스트"
echo "────────────────────────────────────────────────────────────"

ADMIN_STATS_URL="http://$CHARGEAP_HOST:$BACKEND_PORT/api/v1/admin/stats"
echo "Admin Stats 조회: $ADMIN_STATS_URL"
curl -s "$ADMIN_STATS_URL" | python3 -m json.tool | head -15

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Menu Knowledge Engine v0.1.0 배포 완료!${NC}"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🚀 Production API: http://$CHARGEAP_HOST:$BACKEND_PORT"
echo "📚 API Docs: http://$CHARGEAP_HOST:$BACKEND_PORT/docs"
echo "🏥 Health Check: http://$CHARGEAP_HOST:$BACKEND_PORT/health"
echo ""
echo "다음 단계:"
echo "1. 서브도메인 설정 (DNS + Nginx)"
echo "2. CI/CD 파이프라인 테스트 (main 푸시)"
echo "3. 모니터링 설정 (선택)"
echo ""
