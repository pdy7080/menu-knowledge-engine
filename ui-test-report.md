# UI/UX Test Report - Menu Knowledge Engine

**Date**: 2026-02-13
**Tester**: browser-tester (automated)
**Backend Port**: 8001 (started for testing; default is 8000)
**Test Method**: Code review + API command-line testing (Chrome browser blocked by Windows Firewall on non-whitelisted ports)

---

## Executive Summary

| Category | Status | Score |
|----------|--------|-------|
| **B2C Frontend** (app/frontend/) | Functional (code review) | 7/10 |
| **B2B Frontend** (app/frontend-b2b/) | Functional (code review) | 6/10 |
| **Admin Dashboard** (app/backend/static/admin/) | Functional (code review) | 7/10 |
| **API Integration** | Verified (CLI) | 9/10 |

---

## 1. B2C Frontend (app/frontend/)

### 1.1 Page Structure
- **index.html**: Single-page app with landing and results sections
- **CSS**: Custom CSS with CSS variables, responsive design (480px mobile, 600px tablet+)
- **JS**: Vanilla JavaScript, no framework dependency

### 1.2 UI Elements Verified (Code Review)

| Element | Present | Functional | Notes |
|---------|---------|------------|-------|
| Logo & Tagline | YES | YES | "Menu Guide Korea" |
| Search Input | YES | YES | Korean placeholder text, autocomplete=off |
| Search Button | YES | YES | Click and Enter key handlers |
| Photo Upload Button | YES | DISABLED | "Coming Soon" badge, cursor: not-allowed |
| Language Selector | YES | PARTIAL | Only EN active; JA/ZH disabled |
| Popular Dishes Tags | YES | YES | 6 items: bibimbap, kimchi jjigae, samgyeopsal, tteokbokki, bulgogi, naengmyeon |
| Results Section | YES | YES | Hidden by default, shows on search |
| Back Button | YES | YES | Returns to landing |
| Loading Overlay | YES | YES | Spinner animation |
| Disclaimer Footer | YES | YES | Allergen + image attribution |

### 1.3 Bugs Found (Code Review)

#### BUG-1: API_BASE_URL Hardcoded to localhost:8000
- **File**: `app/frontend/js/app.js:10`
- **Issue**: `API_BASE_URL: 'http://localhost:8000'` is hardcoded. No environment variable or configuration system.
- **Impact**: Frontend will not work in production without code change.
- **Severity**: HIGH
- **Recommendation**: Use a config pattern or detect hostname at runtime.

#### BUG-2: escapeHtml() called on non-string values may crash
- **File**: `app/frontend/js/app.js:314-323`
- **Issue**: `escapeHtml(text)` calls `text.replace()` which will throw if `text` is null/undefined/number.
- **Affected locations**: Line 166 (`escapeHtml(input)` when input is undefined), Line 228-229 (canonical fields could be null)
- **Severity**: MEDIUM
- **Recommendation**: Add `String(text || '')` safety wrapper.

#### BUG-3: spice_level 0 produces empty emoji
- **File**: `app/frontend/js/app.js:126`
- **Issue**: `getSpiceEmoji(0)` returns `'🟢'.repeat(Math.max(1, 0))` = empty string since `Math.max(1, 0)` = 1 but `emojis[0]` is '🟢' and `repeat(1)` is correct. Actually this is fine on re-inspection.
- **Status**: FALSE POSITIVE - works correctly.

#### BUG-4: No input sanitization for XSS in menu cards
- **File**: `app/frontend/js/app.js:214-223`
- **Issue**: `image_url` is inserted into `src` attribute via `escapeHtml()` but `escapeHtml` only escapes HTML entities, not URL schemes. A malicious `javascript:` URL could be injected via API response.
- **Severity**: LOW (API is trusted source, but defense-in-depth recommended)
- **Recommendation**: Validate `image_url` starts with `http://` or `https://`.

#### BUG-5: Multiple menus searched sequentially, not in parallel
- **File**: `app/frontend/js/app.js:75-98`
- **Issue**: `searchMultipleMenus()` uses a `for` loop with `await`, making sequential API calls. For 5 menus, this takes 5x the time.
- **Severity**: LOW (UX performance)
- **Recommendation**: Use `Promise.allSettled()` for parallel requests.

### 1.4 UX Observations

- **Positive**: Clean mobile-first design, warm color palette (#E85D3A accent), Korean food theme
- **Positive**: Good use of emoji for visual cues (spice levels, allergens)
- **Positive**: Allergen disclaimer is prominent and well-styled
- **Negative**: No error toast/notification system - uses `alert()` for errors (lines 332, 340, 350)
- **Negative**: No loading state for individual popular dish clicks (entire overlay shows)
- **Negative**: Results view has no way to search again without going back first

---

## 2. B2B Frontend (app/frontend-b2b/)

### 2.1 Page Structure
- **index.html**: 3-step wizard (Upload -> Review -> Success)
- **admin.html**: Admin panel with queue management and stats
- **CSS**: Custom CSS with admin-specific styles

### 2.2 UI Elements Verified (Code Review)

| Element | Present | Functional | Notes |
|---------|---------|------------|-------|
| Upload Area | YES | ASSUMED | Drag & drop + file input |
| Image Preview | YES | ASSUMED | Hidden by default |
| OCR Results Display | YES | ASSUMED | Shows recognized text |
| Menu Items Container | YES | ASSUMED | Dynamic insertion |
| Confirm All Button | YES | ASSUMED | "전체 승인 및 등록" |
| Admin Queue Tab | YES | ASSUMED | Filter by status/source |
| Admin Stats Tab | YES | ASSUMED | Real-time stats |
| Admin Sidebar | YES | ASSUMED | Live statistics |

### 2.3 Bugs Found (Code Review)

#### BUG-6: admin.html uses separate JS that references localhost:8000
- **File**: `app/frontend-b2b/admin.html:132`
- **Impact**: Same hardcoded URL issue as B2C frontend
- **Severity**: HIGH

---

## 3. Admin Dashboard (app/backend/static/admin/)

### 3.1 Page Structure
- **index.html**: Dashboard with stats cards + quick actions
- **queue.html**: Menu queue table with filtering, pagination, approve/reject modals
- **stats.html**: Engine statistics with Chart.js integration

### 3.2 UI Elements Verified (Code Review)

| Element | Present | Notes |
|---------|---------|-------|
| Navigation Bar | YES | 3 tabs: Dashboard, Menu Queue, Statistics |
| Stats Cards (4) | YES | Total Menus, Pending Review, Hit Rate, AI Cost |
| Quick Actions (3) | YES | Review Queue, Engine Statistics, Browse All |
| System Status | YES | Hardcoded "Running" (not dynamic) |
| Queue Table | YES | 7 columns with sorting |
| Queue Filters | YES | Status + Source dropdowns |
| Pagination | YES | Previous/Next with disabled states |
| Approve/Reject Modal | YES | With notes textarea |
| Stats Charts | YES | Chart.js loaded, hit rate + performance metrics |
| Refresh Button | YES | Manual refresh + last updated timestamp |

### 3.3 Bugs Found (Code Review)

#### BUG-7: All admin pages hardcode API_BASE to localhost:8000
- **Files**: `admin/index.html:206`, `admin/queue.html:144`, `admin/stats.html:163`
- **Severity**: HIGH (same issue across all pages)

#### BUG-8: System Status is hardcoded, not dynamic
- **File**: `admin/index.html:174-195`
- **Issue**: API Server, Database, and AI Services all show green/Running regardless of actual status.
- **Severity**: MEDIUM
- **Recommendation**: Fetch from `/health` endpoint on page load.

#### BUG-9: XSS vulnerability in queue.html menu name rendering
- **File**: `admin/queue.html:209`
- **Issue**: `${item.menu_name_ko}` is inserted directly into HTML template literal without escaping.
- **Severity**: HIGH (if menu names come from user input via B2C/B2B)
- **Recommendation**: Use a proper HTML escaping function.

#### BUG-10: queue.html approve/reject uses same endpoint for both actions
- **File**: `admin/queue.html:276`
- **Issue**: Both approve and reject call `/api/v1/admin/queue/${id}/approve` endpoint. The action type is sent in the body but the URL says "approve" even for rejections.
- **Severity**: LOW (functional but semantically confusing)

#### BUG-11: Tailwind CSS loaded from CDN (security concern)
- **Files**: All admin pages
- **Issue**: `<script src="https://cdn.tailwindcss.com"></script>` is CDN-loaded, not suitable for production. Tailwind CDN also adds a console warning in production.
- **Severity**: LOW (development only acceptable)

#### BUG-12: stats.html uses `alert()` for error handling
- **File**: `admin/stats.html:183`
- **Issue**: `alert()` blocks the UI thread and provides poor UX.
- **Severity**: LOW

---

## 4. API Integration Test Results (Command Line)

Since Chrome browser was blocked by Windows Firewall from connecting to the backend port, API tests were performed via command line.

### 4.1 Menu Identify Endpoint

| Test Input | match_type | confidence | modifiers | Result |
|-----------|------------|------------|-----------|--------|
| 김치찌개 | exact | 1.0 | 0 | PASS |
| 비빔밥 | exact | 1.0 | 0 | PASS |
| 삼겹살 | exact | 1.0 | 0 | PASS |
| 왕얼큰뼈해장국 | modifier_decomposition | 0.85 | 2 | PASS |
| 할머니김치찌개 | modifier_decomposition | 0.90 | 1 | PASS |
| 시래기국 | ai_discovery_needed | 0.0 | 0 | PASS (expected) |

### 4.2 Admin Stats Endpoint

```json
{
  "canonical_count": 116,
  "modifier_count": 54,
  "pending_queue_count": 0,
  "scans_7d": 0,
  "db_hit_rate_7d": 0.0,
  "avg_confidence_7d": 0.0,
  "ai_cost_7d": 0.0
}
```
Status: PASS - All fields present and correctly typed.

### 4.3 Health Endpoint

```json
{
  "status": "ok",
  "service": "Menu Knowledge Engine",
  "version": "0.1.0",
  "environment": "development"
}
```
Status: PASS

---

## 5. Environment Issues

### ISSUE-1: Windows Firewall blocks Chrome from localhost ports
- **Problem**: Chrome cannot connect to `localhost:5500`, `localhost:8001`, or any non-whitelisted port
- **Evidence**: PowerShell `Invoke-WebRequest` works; Chrome shows "사이트에 연결할 수 없음"
- **Workaround**: Port 8000 works (already whitelisted by sungsuya project)
- **Impact**: Could not perform live browser testing
- **Recommendation**: Add Windows Firewall inbound rule for development ports (5500, 8001, etc.)

### ISSUE-2: Port 8000 occupied by sungsuya project
- **Problem**: Default port for Menu Knowledge Engine is 8000, but already in use
- **Workaround**: Started backend on port 8001
- **Impact**: Frontend hardcoded to 8000 will not connect to 8001

---

## 6. Summary of All Bugs

| ID | Severity | Category | Description |
|----|----------|----------|-------------|
| BUG-1 | HIGH | Config | API_BASE_URL hardcoded in B2C frontend |
| BUG-2 | MEDIUM | JS Error | escapeHtml() may crash on non-string input |
| BUG-4 | LOW | Security | image_url not validated for javascript: scheme |
| BUG-5 | LOW | UX/Perf | Sequential API calls for multiple menus |
| BUG-6 | HIGH | Config | API_BASE_URL hardcoded in B2B frontend |
| BUG-7 | HIGH | Config | API_BASE_URL hardcoded in all admin pages |
| BUG-8 | MEDIUM | UX | System status hardcoded, not dynamic |
| BUG-9 | HIGH | Security | XSS vulnerability in queue.html |
| BUG-10 | LOW | API Design | Approve endpoint used for both approve/reject |
| BUG-11 | LOW | DevOps | Tailwind CDN not production-ready |
| BUG-12 | LOW | UX | alert() used for error messages |

### Priority Actions
1. **Fix BUG-9 (XSS)**: Highest priority security issue
2. **Fix BUG-1/6/7 (Hardcoded URLs)**: Use environment-aware configuration
3. **Fix BUG-2 (escapeHtml crash)**: Add null/undefined guard
4. **Fix BUG-8 (System status)**: Make dynamic from /health endpoint

---

## 7. Positive Observations

1. **Well-structured codebase**: Clear separation of B2C, B2B, and Admin frontends
2. **Good CSS architecture**: CSS variables for theming, responsive design
3. **Proper error handling in API calls**: try/catch with user feedback
4. **Accessibility**: aria-label on search button, semantic HTML
5. **Korean food theme**: Warm colors, emoji usage, culturally appropriate design
6. **Allergen system**: Comprehensive allergen display with emoji mapping
7. **API response quality**: Rich data with multilingual support (EN/JA/ZH/KO)
8. **Modifier decomposition works**: "왕얼큰뼈해장국" correctly decomposed with 2 modifiers
