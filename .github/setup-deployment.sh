#!/bin/bash

# 🚀 GitHub Secrets 자동 설정 스크립트
# 사용법: bash .github/setup-deployment.sh

set -e

echo "═══════════════════════════════════════════════════════════"
echo "🚀 Menu Knowledge Engine - GitHub Secrets 설정 스크립트"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. gh CLI 확인
echo "📋 Step 1: 환경 확인"
echo "────────────────────────────────────────────────────────────"

if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh)가 설치되지 않았습니다.${NC}"
    echo "설치: https://cli.github.com/"
    exit 1
fi

echo -e "${GREEN}✅ GitHub CLI 설치됨${NC}"

# 2. 리포지토리 확인
echo ""
echo "📋 Step 2: GitHub 리포지토리 확인"
echo "────────────────────────────────────────────────────────────"

REPO=$(gh repo view --json nameWithOwner -q)
if [ -z "$REPO" ]; then
    echo -e "${RED}❌ GitHub 리포지토리를 찾을 수 없습니다.${NC}"
    echo "gh auth login을 실행해주세요."
    exit 1
fi

echo -e "${GREEN}✅ 리포지토리: $REPO${NC}"

# 3. Secrets 설정
echo ""
echo "📋 Step 3: GitHub Secrets 설정"
echo "────────────────────────────────────────────────────────────"

# Function to set secret
set_secret() {
    local name=$1
    local value=$2
    local description=$3

    if [ -z "$value" ]; then
        echo -e "${YELLOW}⏭️  $name: 값이 없어 스킵됨${NC}"
        return
    fi

    echo "$value" | gh secret set "$name"
    echo -e "${GREEN}✅ $name 설정 완료${NC}"
}

# 3.1. CHARGEAP_HOST
echo ""
echo "1️⃣  CHARGEAP_HOST (배포 서버 호스트)"
echo "기본값: d11475.sgp1.stableserver.net"
read -p "값 입력 (엔터로 기본값): " CHARGEAP_HOST
CHARGEAP_HOST=${CHARGEAP_HOST:-d11475.sgp1.stableserver.net}
set_secret "CHARGEAP_HOST" "$CHARGEAP_HOST"

# 3.2. CHARGEAP_USER
echo ""
echo "2️⃣  CHARGEAP_USER (SSH 사용자명)"
echo "기본값: chargeap"
read -p "값 입력 (엔터로 기본값): " CHARGEAP_USER
CHARGEAP_USER=${CHARGEAP_USER:-chargeap}
set_secret "CHARGEAP_USER" "$CHARGEAP_USER"

# 3.3. CHARGEAP_SSH_KEY
echo ""
echo "3️⃣  CHARGEAP_SSH_KEY (SSH Private Key)"
echo "PEM 형식의 Private Key 파일 경로를 입력하세요"
echo "예: ~/.ssh/menu_deploy"
read -p "파일 경로 입력: " SSH_KEY_PATH

if [ -f "$SSH_KEY_PATH" ]; then
    SSH_KEY=$(cat "$SSH_KEY_PATH")
    set_secret "CHARGEAP_SSH_KEY" "$SSH_KEY"
else
    echo -e "${YELLOW}⏭️  SSH 키 파일을 찾을 수 없습니다. 스킵됨${NC}"
fi

# 3.4. CHARGEAP_DEPLOY_PATH
echo ""
echo "4️⃣  CHARGEAP_DEPLOY_PATH (배포 디렉토리)"
echo "기본값: /home/chargeap/menu-knowledge"
read -p "값 입력 (엔터로 기본값): " CHARGEAP_DEPLOY_PATH
CHARGEAP_DEPLOY_PATH=${CHARGEAP_DEPLOY_PATH:-/home/chargeap/menu-knowledge}
set_secret "CHARGEAP_DEPLOY_PATH" "$CHARGEAP_DEPLOY_PATH"

# 3.5. DATABASE_URL
echo ""
echo "5️⃣  DATABASE_URL (PostgreSQL 연결)"
echo "형식: postgresql+asyncpg://user:password@host:port/database"
read -p "DATABASE_URL 입력: " DATABASE_URL

if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⏭️  DATABASE_URL이 비어있습니다. 스킵됨${NC}"
else
    set_secret "DATABASE_URL" "$DATABASE_URL"
fi

# 3.6. SECRET_KEY (생성)
echo ""
echo "6️⃣  SECRET_KEY (자동 생성)"
if command -v python3 &> /dev/null; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    set_secret "SECRET_KEY" "$SECRET_KEY"
    echo -e "${GREEN}✅ SECRET_KEY 자동 생성됨${NC}"
else
    echo -e "${YELLOW}⏭️  Python3이 필요합니다. 수동으로 설정해주세요.${NC}"
fi

# 3.7. OPENAI_API_KEY
echo ""
echo "7️⃣  OPENAI_API_KEY"
echo "기본값: (환경에서 자동 감지)"
read -p "OpenAI API Key 입력 (선택): " OPENAI_API_KEY

if [ -n "$OPENAI_API_KEY" ]; then
    set_secret "OPENAI_API_KEY" "$OPENAI_API_KEY"
fi

# 4. 검증
echo ""
echo "📋 Step 4: Secrets 검증"
echo "────────────────────────────────────────────────────────────"

echo "GitHub 저장소에 설정된 Secrets:"
gh secret list

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ GitHub Secrets 설정 완료!${NC}"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "다음 단계:"
echo "1. GitHub Actions에서 CI/CD 파이프라인 확인"
echo "2. main 브랜치에 푸시 → 자동 배포 실행"
echo "3. https://github.com/$REPO/actions 에서 진행 상황 모니터링"
echo ""
