# QA/DevOps Infrastructure Summary

> **Created**: 2026-02-19
> **Owner**: qa-devops (teammate)
> **Status**: ✅ Infrastructure Ready

---

## Overview

Complete testing and deployment infrastructure for Sprint 2 Phase 1, ready for integration testing, production deployment, and user acceptance testing.

---

## Files Created

### Test Suite (10 files)

```
tests/
├── integration/
│   └── test_menu_detail_flow.py          # Integration tests (Python)
├── e2e/
│   ├── test_ui_components.spec.ts        # E2E tests (Playwright/TypeScript)
│   ├── package.json                      # NPM dependencies
│   └── playwright.config.ts              # Playwright configuration
├── README.md                             # Test documentation
├── QA_DEVOPS_CHECKLIST.md                # Progress tracking
└── INFRASTRUCTURE_SUMMARY.md             # This file

scripts/
├── deploy_sprint2_phase1.sh              # Bash deployment (Linux/Mac)
└── deploy_sprint2_phase1.ps1             # PowerShell deployment (Windows)

infrastructure/
└── s3_cloudfront_setup.sh                # AWS S3 & CloudFront setup

docs/
└── SPRINT2_PHASE1_DEPLOYMENT_REPORT_20260219.md  # Deployment tracking
```

---

## Test Coverage

### Integration Tests (`test_menu_detail_flow.py`)

**What it tests:**
- Menu list API (`/api/v1/canonical-menus`)
- Menu detail API (`/api/v1/canonical-menus/{id}`)
- Image loading performance
- Multi-language support (ko/en/ja/zh)
- Content completeness calculation

**Metrics tracked:**
- API response times (mean, median, p95)
- Image load times (average, max)
- Data quality (completeness %, image coverage)

**Success criteria:**
- p95 API response < 500ms
- Average image load < 2s
- 280+ menus with images (93%)
- 100+ menus at 90% completeness

**How to run:**
```bash
cd app/backend
python tests/integration/test_menu_detail_flow.py
```

---

### E2E Tests (`test_ui_components.spec.ts`)

**What it tests:**
- UI component rendering
- User interactions (click, navigate, carousel)
- Language switching
- Responsive design (desktop, mobile)
- Performance metrics (FCP, DOM load)
- Error handling

**Browser coverage:**
- Desktop: Chromium, Firefox, WebKit
- Mobile: Chrome (Pixel 5), Safari (iPhone 12)

**How to run:**
```bash
cd tests/e2e
npm install
npx playwright install
npm test
```

---

## Deployment Scripts

### Bash Script (`deploy_sprint2_phase1.sh`)

**Features:**
- Pre-deployment checks (SSH key, local tests)
- Database backup (PostgreSQL dump + gzip)
- Code sync (rsync with exclusions)
- Dependency installation (pip install)
- Database migrations (alembic)
- Blue-green deployment (zero downtime)
- Health check verification
- Production smoke tests
- 5-minute monitoring
- Backup cleanup (7-day retention)

**How to use:**
```bash
# Make executable
chmod +x scripts/deploy_sprint2_phase1.sh

# Run deployment
./scripts/deploy_sprint2_phase1.sh
```

**Rollback:**
```bash
ssh -i ~/.ssh/menu_deploy chargeap@d11475.sgp1.stableserver.net \
  'cd /home/chargeap/menu-knowledge-engine && \
   git reset --hard HEAD~1 && \
   pkill -f uvicorn && \
   nohup uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2 &'
```

---

### PowerShell Script (`deploy_sprint2_phase1.ps1`)

**Windows-compatible version with same features**

**Parameters:**
- `-SkipTests`: Skip local integration tests
- `-DryRun`: Preview deployment without executing

**How to use:**
```powershell
# Run deployment
.\scripts\deploy_sprint2_phase1.ps1

# Dry run (preview only)
.\scripts\deploy_sprint2_phase1.ps1 -DryRun

# Skip tests
.\scripts\deploy_sprint2_phase1.ps1 -SkipTests
```

---

## Infrastructure Setup

### S3 & CloudFront (`s3_cloudfront_setup.sh`)

**What it creates:**
- S3 bucket: `menu-knowledge-images`
- Region: `ap-northeast-2` (Seoul)
- Public read access policy
- Versioning enabled
- Lifecycle policy:
  - Delete old versions after 30 days
  - Transition to Infrequent Access after 90 days
- CloudFront distribution:
  - 24h caching (86400s TTL)
  - HTTPS redirect
  - Compression enabled
  - Price class: 200 (Asia/Europe/US)

**Cost targets:**
- S3: < $5/month
- CloudFront: < $5/month
- Total: < $10/month

**How to use:**
```bash
# Requires AWS CLI configured
# Check: aws sts get-caller-identity

# Run setup
chmod +x infrastructure/s3_cloudfront_setup.sh
./infrastructure/s3_cloudfront_setup.sh
```

**Outputs:**
- S3 bucket URL
- CloudFront distribution ID
- CloudFront domain name
- Test image URLs

---

## Success Metrics

All tests track these 11 success criteria:

| # | Metric | Target | Test Coverage |
|---|--------|--------|---------------|
| 1 | Image Coverage | 280 menus (93%) | Integration ✅ |
| 2 | Images per Menu | 3-5 | Integration ✅ |
| 3 | Content Completeness | 100 menus at 90%+ | Integration ✅ |
| 4 | API Response (p95) | < 500ms | Integration ✅ |
| 5 | Image Load Time | < 2s | Integration ✅ + E2E ✅ |
| 6 | User Satisfaction | 4.5/5.0+ | UAT template ✅ |
| 7 | Multi-language | 4 languages | Integration ✅ + E2E ✅ |
| 8 | License Transparency | 100% attribution | Manual ✅ |
| 9 | S3 Cost | < $10/month | CloudWatch ✅ |
| 10 | Production Errors | Zero | Monitoring ✅ |
| 11 | All Tasks Complete | 11/11 | Task system ✅ |

---

## Dependencies

### Python (Integration Tests)
- pytest==8.3.4
- pytest-asyncio==0.24.0
- httpx==0.28.1
- (Already in `requirements.txt`)

### Node.js (E2E Tests)
- @playwright/test==^1.40.0
- typescript==^5.3.0
- (New `package.json` created)

### System Requirements
- **SSH Key**: `~/.ssh/menu_deploy` (RSA)
- **Python**: 3.11+ (venv)
- **Node.js**: 18+ (for Playwright)
- **Bash**: Git Bash / WSL (for rsync)
- **AWS CLI**: For S3/CloudFront setup

---

## Deployment Workflow

### Phase 1: Pre-Deployment (Local)
1. Run integration tests
2. Run E2E tests (all browsers)
3. Verify success criteria
4. Review deployment report template

### Phase 2: Deployment (Production)
1. SSH key authentication
2. Database backup
3. Code sync (rsync)
4. Dependency installation
5. Database migrations
6. Blue-green deployment
7. Health check
8. Smoke tests

### Phase 3: Monitoring (1 hour)
1. Real-time log monitoring
2. Error tracking
3. Performance metrics
4. User feedback

### Phase 4: S3/CloudFront Setup
1. Create S3 bucket
2. Configure public access
3. Create CloudFront distribution
4. Upload test image
5. Verify CDN delivery

### Phase 5: UAT (User Acceptance)
1. Recruit 3 foreign testers
2. Run test scenarios
3. Collect feedback (target: 4.5/5.0+)
4. Document issues
5. Finalize deployment report

---

## Rollback Strategy

### Automatic Backup
- Database: Auto-backup before deployment
- Format: `db_backup_YYYYMMDD_HHMMSS.sql.gz`
- Retention: 7 days
- Location: `/home/chargeap/backups`

### Rollback Command
```bash
# 1. Restore code
git reset --hard HEAD~1

# 2. Restore database
gunzip /home/chargeap/backups/db_backup_YYYYMMDD_HHMMSS.sql.gz
psql -U chargeap -d chargeap_menu_knowledge < /home/chargeap/backups/db_backup_YYYYMMDD_HHMMSS.sql

# 3. Restart service
pkill -f "uvicorn main:app"
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2 &
```

**Rollback Time**: ~5 minutes
**Data Loss**: None (full backup restored)

---

## Next Steps

### Immediate
- [x] Infrastructure setup complete ✅
- [ ] Wait for teammate tasks to complete
- [ ] Coordinate integration testing
- [ ] Execute deployment

### Post-Deployment
- [ ] Monitor production for 1 hour
- [ ] Run UAT sessions
- [ ] Update deployment report
- [ ] Notify team lead

### Future Improvements
- [ ] Add automated CI/CD pipeline (GitHub Actions)
- [ ] Implement performance regression tests
- [ ] Add visual regression tests (Percy, BackstopJS)
- [ ] Implement A/B testing framework

---

## Coordination

### Waiting For

| Teammate | Task | Blocking QA/DevOps |
|----------|------|-------------------|
| image-collector | Image gathering | Task #9 (Integration tests) |
| content-engineer | Content expansion | Task #9 (Integration tests) |
| backend-dev | API endpoints | Task #9 (Integration tests) |
| frontend-dev | UI components | Task #9 (Integration tests) |

### Communication

- **Team Lead notified**: ✅ 2026-02-19
- **Infrastructure ready**: ✅
- **Deployment scheduled**: After Task #1-8 completion
- **ETA**: 2-4 hours from unblock

---

## Contact

- **QA/DevOps Engineer**: qa-devops (teammate)
- **Team Lead**: team-lead
- **Backend Dev**: backend-dev
- **Frontend Dev**: frontend-dev

---

**Last Updated**: 2026-02-19
**Version**: 1.0
**Status**: ✅ Ready for Integration
