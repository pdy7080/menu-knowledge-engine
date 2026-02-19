#!/bin/bash

# Sprint 4 OCR Abstraction - FastComet Deployment Script
# Usage: ./scripts/deploy_fastcomet_sprint4.sh

set -e  # Exit on error

FASTCOMET_HOST="d11475.sgp1.stableserver.net"
FASTCOMET_USER="chargeap"
DEPLOY_PATH="~/menu-knowledge/app/backend"

echo "=================================================="
echo "Sprint 4 OCR Deployment to FastComet"
echo "=================================================="
echo ""

# Phase 1: Pre-deployment checks
echo "[Phase 1] Pre-deployment Checks"
echo "  - Host: $FASTCOMET_HOST"
echo "  - User: $FASTCOMET_USER"
echo "  - Deploy path: $DEPLOY_PATH"
echo ""

# Phase 2: SSH connection test
echo "[Phase 2] Testing SSH Connection..."
ssh -o ConnectTimeout=5 "$FASTCOMET_USER@$FASTCOMET_HOST" "echo 'SSH connection OK'" || {
    echo "FAIL: Cannot connect to FastComet server"
    echo "Run: ssh-keygen -t ed25519 -f ~/.ssh/fastcomet_key"
    echo "Then add public key to FastComet authorized_keys"
    exit 1
}
echo "  PASS: SSH connection established"
echo ""

# Phase 3: Remote environment check
echo "[Phase 3] Remote Environment Check..."
ssh "$FASTCOMET_USER@$FASTCOMET_HOST" << 'REMOTE_SCRIPT'
    echo "  Checking Python..."
    python3 --version

    echo "  Checking venv..."
    if [ -d "$HOME/menu-knowledge/app/backend/venv" ]; then
        echo "  OK: venv directory exists"
    else
        echo "  ERROR: venv not found"
        exit 1
    fi

    echo "  Checking git..."
    cd ~/menu-knowledge
    git status --porcelain

    echo "  Checking .env..."
    if [ -f "app/backend/.env" ]; then
        echo "  OK: .env exists"
    else
        echo "  ERROR: .env not found"
        exit 1
    fi
REMOTE_SCRIPT

echo "  PASS: Remote environment OK"
echo ""

# Phase 4: Pull latest code
echo "[Phase 4] Pulling Latest Code..."
ssh "$FASTCOMET_USER@$FASTCOMET_HOST" << 'REMOTE_SCRIPT'
    cd ~/menu-knowledge
    echo "  Current branch: $(git rev-parse --abbrev-ref HEAD)"
    echo "  Current commit: $(git rev-parse --short HEAD)"

    git fetch origin
    git pull origin master

    echo "  Updated to: $(git rev-parse --short HEAD)"

    # Show recent commits
    echo ""
    echo "  Recent commits:"
    git log --oneline -3
REMOTE_SCRIPT

echo "  PASS: Code pulled successfully"
echo ""

# Phase 5: Install dependencies
echo "[Phase 5] Installing Dependencies..."
ssh "$FASTCOMET_USER@$FASTCOMET_HOST" << 'REMOTE_SCRIPT'
    cd ~/menu-knowledge/app/backend
    source venv/bin/activate

    echo "  Installing packages..."
    pip install -r requirements.txt --upgrade 2>&1 | tail -5

    echo "  Verifying critical packages..."
    python -c "import openai, redis, fastapi; print('  OK: All critical packages available')"
REMOTE_SCRIPT

echo "  PASS: Dependencies installed"
echo ""

# Phase 6: Health check before restart
echo "[Phase 6] Pre-restart Health Check..."
ssh "$FASTCOMET_USER@$FASTCOMET_HOST" << 'REMOTE_SCRIPT'
    echo "  Checking systemd service status..."
    systemctl status menu-api --no-pager | head -5

    echo ""
    echo "  Testing current API endpoint..."
    curl -s http://localhost:8001/api/v1/health | head -20 || echo "  (Current service may be down)"
REMOTE_SCRIPT

echo "  PASS: Pre-restart checks completed"
echo ""

# Phase 7: Restart service
echo "[Phase 7] Restarting Menu API Service..."
ssh "$FASTCOMET_USER@$FASTCOMET_HOST" << 'REMOTE_SCRIPT'
    echo "  Restarting service..."
    sudo systemctl restart menu-api

    echo "  Waiting for service to start..."
    sleep 3

    # Check status
    if systemctl is-active --quiet menu-api; then
        echo "  OK: Service is running"
    else
        echo "  ERROR: Service failed to start"
        echo "  Last 20 lines of log:"
        journalctl -u menu-api -n 20 --no-pager
        exit 1
    fi
REMOTE_SCRIPT

echo "  PASS: Service restarted successfully"
echo ""

# Phase 8: Post-deployment verification
echo "[Phase 8] Post-deployment Verification..."
sleep 2

echo "  Testing health endpoint..."
curl -s https://menu.chargeapp.net/api/v1/health | head -20 || {
    echo "  WARNING: Cannot reach health endpoint via HTTPS"
    echo "  Trying local connection..."
    ssh "$FASTCOMET_USER@$FASTCOMET_HOST" "curl -s http://localhost:8001/api/v1/health" | head -20
}

echo ""
echo "  Checking OCR metrics..."
ssh "$FASTCOMET_USER@$FASTCOMET_HOST" << 'REMOTE_SCRIPT'
    curl -s http://localhost:8001/api/v1/admin/ocr/metrics 2>/dev/null | python -m json.tool || echo "  (Metrics not yet available)"
REMOTE_SCRIPT

echo ""
echo "  PASS: Post-deployment verification completed"
echo ""

# Phase 9: Show deployment summary
echo "[Phase 9] Deployment Summary"
echo "=================================================="
ssh "$FASTCOMET_USER@$FASTCOMET_HOST" << 'REMOTE_SCRIPT'
    cd ~/menu-knowledge/app/backend

    echo "Deployment Status: SUCCESS"
    echo ""
    echo "Service Information:"
    echo "  - Service: menu-api"
    echo "  - Status: $(systemctl is-active menu-api)"
    echo "  - PID: $(systemctl status menu-api --no-pager | grep PID | head -1)"
    echo ""

    echo "Code Version:"
    echo "  - Branch: $(git rev-parse --abbrev-ref HEAD)"
    echo "  - Commit: $(git rev-parse --short HEAD)"
    echo "  - Message: $(git log -1 --pretty=%B | head -1)"
    echo ""

    echo "Python Environment:"
    source venv/bin/activate
    echo "  - Python: $(python --version 2>&1 | cut -d' ' -f2)"
    echo "  - venv: $(which python | cut -d'/' -f5-)"
    echo ""

    echo "Critical Packages:"
    python -c "
import openai, redis, fastapi
print(f'  - openai: {openai.__version__}')
print(f'  - redis: {redis.__version__}')
print(f'  - fastapi: {fastapi.__version__}')
"
REMOTE_SCRIPT

echo "=================================================="
echo ""
echo "DEPLOYMENT COMPLETE!"
echo ""
echo "Next Steps:"
echo "  1. Monitor logs: ssh $FASTCOMET_USER@$FASTCOMET_HOST 'tail -f ~/menu-api.log'"
echo "  2. Check metrics: curl https://menu.chargeapp.net/api/v1/admin/ocr/metrics | jq ."
echo "  3. Test B2B API: See deployment checklist for test commands"
echo ""
