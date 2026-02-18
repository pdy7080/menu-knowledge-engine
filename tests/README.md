# Menu Knowledge Engine - Test Suite

> Sprint 2 Phase 1 - QA/DevOps Testing Documentation

---

## Test Structure

```
tests/
├── integration/
│   └── test_menu_detail_flow.py     # Menu list → Detail → Images → Multi-language
├── e2e/
│   ├── test_ui_components.spec.ts   # Playwright E2E tests
│   ├── package.json
│   └── playwright.config.ts
└── README.md (this file)
```

---

## Integration Tests (Python)

### Setup

```bash
# Navigate to backend directory
cd app/backend

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

### Running Tests

```bash
# Run integration tests
python tests/integration/test_menu_detail_flow.py

# Or using pytest
pytest tests/integration/test_menu_detail_flow.py -v
```

### What It Tests

1. **Menu List API** (`GET /api/v1/canonical-menus`)
   - Response format validation
   - Image coverage (target: 280 menus = 93%)
   - Content completeness (target: 100 menus at 90%+)

2. **Menu Detail API** (`GET /api/v1/canonical-menus/{id}`)
   - Individual menu data retrieval
   - API response time (target: p95 < 500ms)

3. **Multi-language Support**
   - Korean (ko)
   - English (en)
   - Japanese (ja)
   - Chinese (zh)

4. **Image Loading Performance**
   - Average load time (target: < 2s)
   - Image accessibility

### Success Criteria

| Metric | Target | Check |
|--------|--------|-------|
| Image Coverage | 280 menus (93%) | ✅/❌ |
| Content Completeness | 100 menus at 90%+ | ✅/❌ |
| API Response (p95) | < 500ms | ✅/❌ |
| Image Load Time | < 2s | ✅/❌ |
| Multi-language | 4 languages | ✅/❌ |

---

## E2E Tests (Playwright)

### Setup

```bash
# Navigate to E2E test directory
cd tests/e2e

# Install dependencies
npm install

# Install Playwright browsers
npx playwright install
```

### Running Tests

```bash
# Run all E2E tests
npm test

# Run with UI mode (interactive)
npm run test:ui

# Run in headed mode (see browser)
npm run test:headed

# Debug mode
npm run test:debug

# View test report
npm run report
```

### What It Tests

1. **UI Component Rendering**
   - Menu list page
   - Menu detail page
   - Image carousel
   - Language switcher

2. **User Interactions**
   - Click menu card → Navigate to detail
   - Carousel navigation (prev/next)
   - Language switching
   - Search and filter

3. **Responsive Design**
   - Desktop layout
   - Mobile layout (375x667)

4. **Performance**
   - DOM Content Loaded < 2s
   - First Contentful Paint < 1.5s

5. **Error Handling**
   - API error responses
   - Network failures

### Browser Coverage

- Chromium (Desktop)
- Firefox (Desktop)
- WebKit (Safari)
- Mobile Chrome (Pixel 5)
- Mobile Safari (iPhone 12)

---

## Deployment Tests

### Pre-Deployment Checklist

Run these tests before deploying to production:

```bash
# 1. Backend unit tests
cd app/backend
pytest tests/ -v

# 2. Integration tests
python tests/integration/test_menu_detail_flow.py

# 3. E2E tests (all browsers)
cd tests/e2e
npm test

# 4. Type checking (if TypeScript)
npx tsc --noEmit

# 5. Linting
cd app/backend
ruff check .
black --check .
```

### Production Smoke Tests

After deployment, run these quick checks:

```bash
# Health check
curl http://d11475.sgp1.stableserver.net:8001/health

# Menu list API
curl http://d11475.sgp1.stableserver.net:8001/api/v1/canonical-menus

# Menu detail API (replace {id} with actual menu ID)
curl http://d11475.sgp1.stableserver.net:8001/api/v1/canonical-menus/{id}
```

---

## Performance Monitoring

### API Response Times

```bash
# Using Apache Bench (ab)
ab -n 100 -c 10 http://localhost:8000/api/v1/canonical-menus

# Using wrk (more advanced)
wrk -t4 -c100 -d30s http://localhost:8000/api/v1/canonical-menus
```

### Image Load Times

```bash
# Using curl to measure image download
curl -w "@curl-format.txt" -o /dev/null -s https://cloudfront-domain/image.jpg

# curl-format.txt:
# time_namelookup:  %{time_namelookup}
# time_connect:     %{time_connect}
# time_starttransfer: %{time_starttransfer}
# time_total:       %{time_total}
```

---

## Continuous Integration

### GitHub Actions Workflow (Example)

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r app/backend/requirements.txt
      - name: Run integration tests
        run: |
          python tests/integration/test_menu_detail_flow.py

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install Playwright
        run: |
          cd tests/e2e
          npm install
          npx playwright install --with-deps
      - name: Run E2E tests
        run: |
          cd tests/e2e
          npm test
      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
```

---

## Troubleshooting

### Integration Tests Failing

**Problem**: Connection refused to localhost:8000

**Solution**:
```bash
# Make sure backend server is running
cd app/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### E2E Tests Failing

**Problem**: Browser not found

**Solution**:
```bash
# Reinstall Playwright browsers
cd tests/e2e
npx playwright install --force
```

**Problem**: Test timeout

**Solution**:
- Increase timeout in `playwright.config.ts`
- Check if server is running (`webServer.url`)

### Performance Tests Failing

**Problem**: p95 > 500ms

**Solution**:
- Check database indexes
- Review API query optimization
- Consider caching strategy

**Problem**: Image load > 2s

**Solution**:
- Verify CloudFront distribution
- Check image sizes (compress if > 200KB)
- Implement lazy loading

---

## Reporting

### Test Reports Location

```
tests/
├── integration/
│   └── test-results.log
├── e2e/
│   ├── playwright-report/    # HTML report
│   └── test-results.json     # JSON results
└── docs/
    └── SPRINT2_PHASE1_DEPLOYMENT_REPORT_20260219.md
```

### Generating Reports

```bash
# Integration tests (manual logging)
python tests/integration/test_menu_detail_flow.py > test-results.log 2>&1

# E2E tests (Playwright HTML report)
cd tests/e2e
npm test
npm run report  # Opens browser with interactive report
```

---

## Contact

For issues or questions:
- **QA/DevOps Engineer**: qa-devops (teammate)
- **Backend Developer**: backend-dev (teammate)
- **Frontend Developer**: frontend-dev (teammate)
- **Team Lead**: team-lead

---

**Last Updated**: 2026-02-19
**Version**: 1.0
**Sprint**: Sprint 2 Phase 1
