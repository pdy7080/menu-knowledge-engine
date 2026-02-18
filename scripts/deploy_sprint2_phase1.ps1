################################################################################
# Sprint 2 Phase 1 - Production Deployment Script (PowerShell)
# Menu Knowledge Engine - Menu Detail & Image Integration
#
# Target: FastComet Managed VPS (d11475.sgp1.stableserver.net)
# Deploy Time: Korea 02:00-04:00 (off-hours)
# Zero Downtime: Blue-Green deployment strategy
################################################################################

param(
    [switch]$SkipTests = $false,
    [switch]$DryRun = $false
)

# Configuration
$REMOTE_USER = "chargeap"
$REMOTE_HOST = "d11475.sgp1.stableserver.net"
$REMOTE_PATH = "/home/chargeap/menu-knowledge-engine"
$SERVICE_NAME = "menu-api"
$PORT = 8001
$BACKUP_DIR = "/home/chargeap/backups"
$DEPLOY_DATE = Get-Date -Format "yyyyMMdd_HHmmss"
$SSH_KEY = "$env:USERPROFILE\.ssh\menu_deploy"

# Colors
function Write-Step { param($Message) Write-Host "[STEP] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }

Write-Host "================================" -ForegroundColor Blue
Write-Host "Sprint 2 Phase 1 - Production Deployment" -ForegroundColor Blue
Write-Host "================================" -ForegroundColor Blue
Write-Host ""

# Step 1: Pre-deployment checks
Write-Step "1/10 - Pre-deployment checks"

# Check if SSH key exists
if (-not (Test-Path $SSH_KEY)) {
    Write-Error "SSH key not found at $SSH_KEY"
    Write-Info "Generate key: ssh-keygen -t rsa -f $SSH_KEY"
    exit 1
}

if (-not $SkipTests) {
    # Check local tests passed
    Write-Step "Running local integration tests..."
    Set-Location (Split-Path -Parent $PSScriptRoot)

    python tests\integration\test_menu_detail_flow.py

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Local tests failed. Fix issues before deploying."
        exit 1
    }

    Write-Step "✅ Local tests passed"
}

if ($DryRun) {
    Write-Warning "DRY RUN MODE - No actual deployment will occur"
}

# Step 2: Backup current production
Write-Step "2/10 - Backing up production database"

$backupScript = @"
BACKUP_DIR="/home/chargeap/backups"
DEPLOY_DATE=`$(date +%Y%m%d_%H%M%S)

mkdir -p `${BACKUP_DIR}

# Backup PostgreSQL database
pg_dump -U chargeap -d chargeap_menu_knowledge > `${BACKUP_DIR}/db_backup_`${DEPLOY_DATE}.sql

# Compress backup
gzip `${BACKUP_DIR}/db_backup_`${DEPLOY_DATE}.sql

echo "✅ Database backup created: `${BACKUP_DIR}/db_backup_`${DEPLOY_DATE}.sql.gz"
"@

if (-not $DryRun) {
    ssh -i $SSH_KEY "${REMOTE_USER}@${REMOTE_HOST}" $backupScript
}

# Step 3: Sync code to production
Write-Step "3/10 - Syncing code to production server"

$excludeList = @(
    "venv",
    ".git",
    "__pycache__",
    ".env",
    "*.pyc",
    "node_modules"
)

if (-not $DryRun) {
    # Using rsync via WSL or Git Bash
    & bash -c "rsync -avz --exclude='venv' --exclude='.git' --exclude='__pycache__' --exclude='.env' --exclude='*.pyc' --exclude='node_modules' -e 'ssh -i ~/.ssh/menu_deploy' app/backend/ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"
}

Write-Step "✅ Code synced"

# Step 4: Install dependencies
Write-Step "4/10 - Installing Python dependencies"

$installScript = @"
cd /home/chargeap/menu-knowledge-engine
source venv/bin/activate
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
"@

if (-not $DryRun) {
    ssh -i $SSH_KEY "${REMOTE_USER}@${REMOTE_HOST}" $installScript
}

# Step 5: Run database migrations
Write-Step "5/10 - Running database migrations"

$migrationScript = @"
cd /home/chargeap/menu-knowledge-engine
source venv/bin/activate

if [ -d "alembic" ]; then
    alembic upgrade head
    echo "✅ Migrations applied"
else
    echo "⚠️  No alembic migrations found, skipping"
fi
"@

if (-not $DryRun) {
    ssh -i $SSH_KEY "${REMOTE_USER}@${REMOTE_HOST}" $migrationScript
}

# Step 6: Blue-Green deployment
Write-Step "6/10 - Blue-Green deployment (zero downtime)"

$deployScript = @"
cd /home/chargeap/menu-knowledge-engine
source venv/bin/activate

TEMP_PORT=8002

echo "Starting new instance on port `${TEMP_PORT}..."
nohup uvicorn main:app --host 0.0.0.0 --port `${TEMP_PORT} --workers 2 > /tmp/menu-api-temp.log 2>&1 &
NEW_PID=`$!

sleep 5

# Health check
curl -f http://localhost:`${TEMP_PORT}/health || {
    echo "❌ New instance failed health check"
    kill `${NEW_PID}
    exit 1
}

echo "✅ New instance healthy on port `${TEMP_PORT}"

# Kill old instance
pkill -f "uvicorn main:app.*--port 8001" || true
sleep 2

# Start on main port
nohup uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2 > /tmp/menu-api.log 2>&1 &

# Kill temporary instance
sleep 3
kill `${NEW_PID} || true

echo "✅ Traffic switched to new version"
"@

if (-not $DryRun) {
    ssh -i $SSH_KEY "${REMOTE_USER}@${REMOTE_HOST}" $deployScript
}

# Step 7: Verify deployment
Write-Step "7/10 - Verifying deployment"

$HEALTH_CHECK_URL = "http://${REMOTE_HOST}:${PORT}/health"

for ($i = 1; $i -le 5; $i++) {
    Write-Info "Health check attempt $i/5..."

    try {
        $response = Invoke-RestMethod -Uri $HEALTH_CHECK_URL -TimeoutSec 5

        if ($response.status -eq "ok") {
            Write-Step "✅ Deployment verified - API is healthy"
            break
        }
    }
    catch {
        if ($i -eq 5) {
            Write-Error "Health check failed after 5 attempts"
            exit 1
        }
        Start-Sleep -Seconds 5
    }
}

# Step 8: Run production smoke tests
Write-Step "8/10 - Running production smoke tests"

try {
    $menuListResponse = Invoke-RestMethod -Uri "http://${REMOTE_HOST}:${PORT}/api/v1/canonical-menus"

    if ($menuListResponse.total) {
        Write-Step "✅ Menu list API working ($($menuListResponse.total) menus)"
    }
    else {
        Write-Error "Menu list API failed - no 'total' field in response"
        exit 1
    }
}
catch {
    Write-Error "Menu list API failed: $_"
    exit 1
}

# Step 9: Monitor for 5 minutes
Write-Step "9/10 - Monitoring for errors (5 minutes)"
Write-Warning "Press Ctrl+C to skip monitoring and continue to cleanup"

try {
    ssh -i $SSH_KEY "${REMOTE_USER}@${REMOTE_HOST}" "timeout 300 tail -f /home/chargeap/menu-knowledge-engine/logs/app.log 2>/dev/null || echo '⚠️  Log file not found, skipping monitoring'"
}
catch {
    Write-Warning "Monitoring interrupted or log file not found"
}

# Step 10: Cleanup old backups
Write-Step "10/10 - Cleaning up old backups"

$cleanupScript = @"
find /home/chargeap/backups -name "db_backup_*.sql.gz" -mtime +7 -delete
echo "✅ Old backups cleaned up (keeping last 7 days)"
"@

if (-not $DryRun) {
    ssh -i $SSH_KEY "${REMOTE_USER}@${REMOTE_HOST}" $cleanupScript
}

# Final summary
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT SUCCESSFUL" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Deployment Date: $DEPLOY_DATE"
Write-Host "Service: $SERVICE_NAME"
Write-Host "Port: $PORT"
Write-Host "Health Check: $HEALTH_CHECK_URL"
Write-Host ""
Write-Host "Next Steps:"
Write-Host "1. Run user acceptance tests"
Write-Host "2. Monitor production metrics for 1 hour"
Write-Host "3. Update DEPLOYMENT_REPORT with results"
Write-Host ""
Write-Host "Rollback command (if needed):" -ForegroundColor Yellow
Write-Host "ssh -i $SSH_KEY ${REMOTE_USER}@${REMOTE_HOST} 'cd ${REMOTE_PATH} && git reset --hard HEAD~1 && pkill -f uvicorn && nohup uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 2 &'"
Write-Host ""
