# Menu Knowledge Engine - Test Plan

> **Date**: 2026-02-13
> **Version**: v0.1 (MVP)
> **Scope**: 3-stage matching pipeline, API endpoints, seed data integrity

---

## 1. Overview

This test plan validates the Menu Knowledge Engine's core functionality:
- **3-stage matching pipeline**: Exact Match -> Modifier Decomposition -> AI Discovery
- **API endpoints**: `/api/v1/menu/identify`, `/api/v1/menu/recognize`, B2B endpoints
- **Seed data integrity**: concepts, modifiers, canonical_menus
- **Performance**: response time, cache behavior

### Success Criteria (from MVP Scope Definition)
| Metric | Target | Measurement |
|--------|--------|-------------|
| DB Match Rate | 70%+ | `ai_called=false` ratio in matching results |
| OCR Recognition | 80%+ | Menu name extraction success rate |
| Response Time (DB hit) | < 3 seconds | Server log p95 |
| AI Cost per Scan | < 50 KRW | AI call count tracking |

---

## 2. Test Cases - 10 Core Menu Decomposition

> **Critical Validation**: "Can the engine correctly decompose '왕얼큰순두부뼈해장국'?"
>
> Target: **7 out of 10 correct decompositions (70%+)**

### 2-1. P0 - Must Pass (Core Pipeline)

| # | Input | Expected Method | Expected Canonical | Expected Modifiers | Spice Effect | Priority |
|---|-------|----------------|-------------------|-------------------|-------------|----------|
| TC-01 | 김치찌개 | `exact` | 김치찌개 (Kimchi Stew) | (none) | N/A | **P0** |
| TC-02 | 할머니김치찌개 | `modifier_decomposition` | 김치찌개 | 할머니 (emotion/homestyle) | N/A | **P0** |
| TC-03 | 왕돈까스 | `modifier_decomposition` | 돈까스 | 왕 (size/x_large) | N/A | **P0** |
| TC-04 | 얼큰순두부찌개 | `modifier_decomposition` | 순두부찌개 | 얼큰 (taste/spicy_hearty, +1) | spice +1 | **P0** |
| TC-07 | 왕얼큰뼈해장국 | `modifier_decomposition` | 뼈해장국 | 왕 (size), 얼큰 (taste) | spice +1 | **P0** |

**TC-07 Deep Analysis (Multi-modifier decomposition)**:
```
Input: "왕얼큰뼈해장국"
Step 1: Exact match "왕얼큰뼈해장국" in canonical_menus -> MISS
Step 2: Modifier decomposition
  - Find modifier "왕" (size, priority=15) -> remove -> "얼큰뼈해장국"
  - Try canonical match "얼큰뼈해장국" -> MISS
  - Find modifier "얼큰" (taste, priority=10) -> remove -> "뼈해장국"
  - Try canonical match "뼈해장국" -> HIT!
Result: canonical="뼈해장국", modifiers=["왕", "얼큰"], confidence=0.85
```

### 2-2. P1 - Should Pass (Extended Scenarios)

| # | Input | Expected Method | Expected Canonical | Expected Modifiers | Priority |
|---|-------|----------------|-------------------|-------------------|----------|
| TC-05 | 숯불갈비 | `modifier_decomposition` | 갈비 or 소갈비 | 숯불 (cooking/charcoal) | **P1** |
| TC-06 | 한우불고기 | `modifier_decomposition` | 불고기 | 한우 (ingredient/korean_beef) | **P1** |
| TC-08 | 옛날통닭 | `modifier_decomposition` | 닭 or 치킨 | 옛날 (emotion), 통 (cooking) | **P1** |

**TC-06 Note**: `한우` is type `ingredient` (priority=99 in engine). Current engine skips `ingredient` type modifiers in Step 2. This test may need AI Discovery or engine update. Expected behavior: either `modifier_decomposition` with special ingredient handling OR `ai_discovery`.

**TC-08 Note**: "통닭" may not exist as a canonical menu. "닭" alone is not a canonical. This case tests the engine's limits with compound words that include a cooking modifier plus a basic ingredient.

### 2-3. P2 - Edge Cases (AI Discovery / Complex)

| # | Input | Expected Method | Expected Canonical | Notes | Priority |
|---|-------|----------------|-------------------|-------|----------|
| TC-09 | 시래기국 | `ai_discovery` or `exact` | 시래기국 (if seeded) | May not be in canonical_menus. Tests AI fallback. | **P2** |
| TC-10 | 고씨네묵은지감자탕 | `modifier_decomposition` or `ai_discovery` | 감자탕 | "고씨네" = brand (not in modifier dict). Tests brand name handling. | **P2** |

**TC-10 Deep Analysis (Brand + Modifier + Canonical)**:
```
Input: "고씨네묵은지감자탕"
Challenge: "고씨네" is a brand/shop name NOT in modifiers table
Step 1: Exact match -> MISS
Step 2: Modifier decomposition
  - "묵은지" (ingredient, priority=18) -> but ingredient type is SKIPPED
  - No other modifiers found -> FAIL
Step 3: AI Discovery
  - AI should identify base menu as "감자탕" (Pork Bone Stew with Potatoes)
  - AI should extract "고씨네" as brand, "묵은지" as ingredient modifier
Expected: ai_discovery with canonical-like result for 감자탕
```

---

## 3. Extended Test Cases - API Validation

### 3-1. Exact Match Verification (P0)

| # | Input | Expected Canonical | Confidence | Notes |
|---|-------|--------------------|------------|-------|
| TC-11 | 떡볶이 | 떡볶이 | 1.0 | Common street food |
| TC-12 | 제육볶음 | 제육볶음 | 1.0 | Common dish |
| TC-13 | 부대찌개 | 부대찌개 | 1.0 | Army stew |
| TC-14 | 삼겹살 | 삼겹살 | 1.0 | Korean BBQ staple |
| TC-15 | 비빔밥 | 비빔밥 | 1.0 | Iconic Korean dish |
| TC-16 | 삼계탕 | 삼계탕 | 1.0 | Ginseng chicken soup |
| TC-17 | 물냉면 | 물냉면 | 1.0 | Cold noodles |
| TC-18 | 잔치국수 | 잔치국수 | 1.0 | Banquet noodles |

### 3-2. Similarity Match / Typo Correction (P1)

| # | Input | Expected Canonical | Expected Method | Min Confidence |
|---|-------|--------------------|-----------------|----------------|
| TC-19 | 김치찌게 (typo: 개->게) | 김치찌개 | `similarity` | 0.4 |
| TC-20 | 된장찌게 (typo: 개->게) | 된장찌개 | `similarity` | 0.4 |
| TC-21 | 떡볶기 (typo: 이->기) | 떡볶이 | `similarity` | 0.4 |
| TC-22 | 삼겹쌀 (typo: 살->쌀) | 삼겹살 | `similarity` | 0.4 |

**Important constraint**: Current engine requires identical length for similarity match (`max_length_diff = 0`). All typo test cases above maintain the same character count.

### 3-3. Multi-Modifier Decomposition (P0)

| # | Input | Expected Canonical | Expected Modifiers | Modifier Count |
|---|-------|--------------------|-------------------|----------------|
| TC-23 | 왕갈비탕 | 갈비탕 | 왕 | 1 |
| TC-24 | 얼큰김치찌개 | 김치찌개 | 얼큰 | 1 |
| TC-25 | 원조할매순대국밥 | 순대국밥 | 원조, 할매 | 2 |
| TC-26 | 숯불돼지갈비 | 돼지갈비 | 숯불 | 1 |
| TC-27 | 매운갈비찜 | 갈비찜 | 매운 | 1 |

### 3-4. Negative / Edge Cases (P2)

| # | Input | Expected Behavior | Notes |
|---|-------|-------------------|-------|
| TC-28 | "" (empty string) | Error 400 or empty result | Input validation |
| TC-29 | "abc123" | `ai_discovery_needed` | Non-Korean text |
| TC-30 | "아주매우엄청나게긴메뉴이름테스트" | `ai_discovery_needed` | Very long nonsense |
| TC-31 | "스테이크" | `ai_discovery` or `exact` | Western food in Korean |

---

## 4. API Endpoint Tests

### 4-1. `POST /api/v1/menu/identify` (P0)

**Request Schema**:
```json
{
  "menu_name_ko": "string (required)"
}
```

**Test Cases**:

| # | Test | Method | Expected Status | Validation |
|---|------|--------|----------------|------------|
| API-01 | Valid menu name | POST | 200 | Response has `match_type`, `canonical`, `confidence` |
| API-02 | Empty body | POST | 422 | Validation error |
| API-03 | Missing field | POST `{}` | 422 | Validation error for required field |
| API-04 | Exact match response format | POST | 200 | `canonical.name_ko`, `canonical.name_en`, `canonical.explanation_short` present |
| API-05 | Modifier decomposition format | POST | 200 | `modifiers[]` has `text_ko`, `type`, `translation_en` |
| API-06 | AI discovery format | POST | 200 | `ai_called=true`, canonical has AI-generated fields |
| API-07 | Cache hit (2nd request same menu) | POST x2 | 200 | 2nd response faster, `ai_called=false` |

### 4-2. `POST /api/v1/menu/recognize` (P1)

**Request**: `multipart/form-data` with `file` field

| # | Test | Expected Status | Validation |
|---|------|----------------|------------|
| API-08 | Valid menu image (JPEG) | 200 | `success=true`, `menu_items[]` populated |
| API-09 | Valid menu image (PNG) | 200 | `success=true` |
| API-10 | Invalid file (text file) | 400 | `Invalid image` error |
| API-11 | Oversized image (>10MB) | 400 | Size limit error |
| API-12 | No file uploaded | 422 | Missing required field |

### 4-3. `GET /api/v1/concepts` (P1)

| # | Test | Expected Status | Validation |
|---|------|----------------|------------|
| API-13 | List all concepts | 200 | `total >= 47`, has `name_ko`, `name_en`, `parent_id` |
| API-14 | Concept tree structure | 200 | Top-level concepts (parent_id=null) = 12 categories |

### 4-4. `GET /api/v1/modifiers` (P1)

| # | Test | Expected Status | Validation |
|---|------|----------------|------------|
| API-15 | List all modifiers | 200 | `total >= 50`, has `text_ko`, `type`, `translation_en` |
| API-16 | Modifier types coverage | 200 | All 7 types present: taste, size, emotion, ingredient, cooking, grade, origin |

### 4-5. `GET /api/v1/canonical-menus` (P1)

| # | Test | Expected Status | Validation |
|---|------|----------------|------------|
| API-17 | List all canonical menus | 200 | `total >= 100` |
| API-18 | Data completeness | 200 | Each menu has `name_ko`, `name_en`, `explanation_short` non-null |

### 4-6. B2B API Endpoints (P1)

| # | Test | Endpoint | Expected Status | Validation |
|---|------|----------|----------------|------------|
| API-19 | Register restaurant | POST `/api/v1/b2b/restaurants` | 201 | Returns `restaurant_id`, `status=pending_approval` |
| API-20 | Duplicate business license | POST `/api/v1/b2b/restaurants` | 409 or error | Duplicate check |
| API-21 | Upload menu image | POST `/api/v1/b2b/restaurants/{id}/menu-upload` | 200 | Returns parsed menu items |
| API-22 | Approve menu items | POST `/api/v1/b2b/restaurants/{id}/menu-approve` | 200 | QR code generated |

---

## 5. Seed Data Integrity Tests

### 5-1. Concepts Table (P0)

| # | Check | Expected | Query |
|---|-------|----------|-------|
| SEED-01 | Total concept count | >= 47 | `SELECT COUNT(*) FROM concepts` |
| SEED-02 | Top-level categories | 12 | `SELECT COUNT(*) FROM concepts WHERE parent_id IS NULL` |
| SEED-03 | All top-level have name_en | 12/12 | `WHERE parent_id IS NULL AND name_en IS NOT NULL` |
| SEED-04 | Sub-categories exist | >= 35 | `WHERE parent_id IS NOT NULL` |
| SEED-05 | No orphan children | 0 orphans | `WHERE parent_id NOT IN (SELECT id FROM concepts)` |

**Expected 12 top-level categories**:
- 국물요리, 밥류, 면류, 구이류, 찜/조림류, 볶음류
- 전/부침류, 반찬류, 분식류, 안주류, 음료류, 디저트류

### 5-2. Modifiers Table (P0)

| # | Check | Expected | Query |
|---|-------|----------|-------|
| SEED-06 | Total modifier count | >= 50 | `SELECT COUNT(*) FROM modifiers` |
| SEED-07 | Type distribution | 7 types | `SELECT DISTINCT type FROM modifiers` |
| SEED-08 | taste count | >= 12 | `WHERE type='taste'` |
| SEED-09 | size count | >= 7 | `WHERE type='size'` |
| SEED-10 | emotion count | >= 10 | `WHERE type='emotion'` |
| SEED-11 | ingredient count | >= 10 | `WHERE type='ingredient'` |
| SEED-12 | cooking count | >= 6 | `WHERE type='cooking'` |
| SEED-13 | grade count | >= 3 | `WHERE type='grade'` |
| SEED-14 | origin count | >= 2 | `WHERE type='origin'` |
| SEED-15 | No duplicate text_ko | 0 dups | `GROUP BY text_ko HAVING COUNT(*) > 1` |

### 5-3. Canonical Menus Table (P0)

| # | Check | Expected | Query |
|---|-------|----------|-------|
| SEED-16 | Total canonical count | >= 100 | `SELECT COUNT(*) FROM canonical_menus` |
| SEED-17 | All have name_en | 100% | `WHERE name_en IS NOT NULL` |
| SEED-18 | All have explanation_short | 100% | `WHERE explanation_short IS NOT NULL AND explanation_short != '{}'` |
| SEED-19 | Spice level range | 0-5 | `WHERE spice_level BETWEEN 0 AND 5` |
| SEED-20 | Difficulty score range | 1-5 | `WHERE difficulty_score BETWEEN 1 AND 5` |
| SEED-21 | No duplicate name_ko | 0 dups | `GROUP BY name_ko HAVING COUNT(*) > 1` |
| SEED-22 | concept_id references valid | 0 orphans | FK integrity check |
| SEED-23 | Key menus exist | all present | Check: 김치찌개, 비빔밥, 삼겹살, 뼈해장국, 순두부찌개, 불고기 |

---

## 6. Performance Tests

### 6-1. Response Time (P1)

| # | Scenario | Target | Method |
|---|----------|--------|--------|
| PERF-01 | Exact match latency | < 200ms | Single identify request for seeded menu |
| PERF-02 | Modifier decomposition latency | < 500ms | Single identify with 1 modifier |
| PERF-03 | Multi-modifier decomposition | < 800ms | Identify with 2-3 modifiers |
| PERF-04 | AI Discovery latency | < 5000ms | Identify unknown menu (API key required) |
| PERF-05 | Cache hit latency | < 50ms | 2nd request for same menu |

### 6-2. Throughput (P2)

| # | Scenario | Target |
|---|----------|--------|
| PERF-06 | Sequential 100 requests | < 30 seconds total |
| PERF-07 | Concurrent 10 requests | All succeed, no errors |

---

## 7. Critical Validation: "왕얼큰순두부뼈해장국" Full Decomposition

This is the ultimate test case from CLAUDE.md. If this passes, the engine fundamentally works.

```
Input: "왕얼큰순두부뼈해장국"

Expected decomposition:
  Modifier 1: "왕" (type=size, semantic_key=x_large, affects_size=x_large)
  Modifier 2: "얼큰" (type=taste, semantic_key=spicy_hearty, affects_spice=+1)
  Modifier 3: "순두부" (type=ingredient, semantic_key=soft_tofu)
  Base Menu: "뼈해장국" (canonical)

Expected result:
  match_type: "modifier_decomposition"
  canonical.name_ko: "뼈해장국"
  canonical.name_en: "Pork Bone Hangover Soup"
  modifiers: [왕, 얼큰, 순두부]  (3 modifiers)
  confidence: >= 0.7
  ai_called: false
```

**Current Engine Limitation**: The matching engine skips `ingredient` type modifiers in Step 2 (`modifier.type == "ingredient": continue`). This means "순두부" (soft_tofu, type=ingredient) will NOT be extracted as a modifier by the current engine.

**Actual Expected Behavior with Current Code**:
```
Step 2 Modifier Decomposition:
  1. "왕" found (type=size, not skipped) -> remove -> "얼큰순두부뼈해장국"
  2. "얼큰" found (type=taste, not skipped) -> remove -> "순두부뼈해장국"
  3. "순두부" found (type=ingredient, SKIPPED by engine)
  4. Try canonical match "순두부뼈해장국" -> MISS (not in canonical_menus)

  Result: Step 2 FAILS, falls through to Step 3 (AI Discovery)
```

**Known Gap**: To fully pass the "왕얼큰순두부뼈해장국" test, the engine needs either:
1. Allow ingredient-type modifiers in decomposition (with safeguards), OR
2. Try all combinations including ingredient modifiers, OR
3. Accept a partial match: "왕얼큰" extracted, "순두부뼈해장국" falls to AI

**Recommendation**: This gap should be tracked as a P0 improvement for the matching engine.

---

## 8. Test Execution Plan

### Phase 1: Seed Data Validation (Immediate)
- Run SEED-01 through SEED-23
- Verify concept tree, modifier dictionary, canonical menus
- Expected: All checks pass

### Phase 2: Core Matching Pipeline (P0)
- Run TC-01 through TC-07 (10 core cases)
- Target: 7/10 pass (70%)
- Focus on exact match and single-modifier decomposition

### Phase 3: API Endpoint Validation (P1)
- Run API-01 through API-22
- Verify request/response schemas
- Test error handling

### Phase 4: Extended & Performance (P2)
- Run TC-11 through TC-31 (extended cases)
- Run PERF-01 through PERF-07
- Document edge case failures for v0.2

### Test Environment
- **Server**: `http://localhost:8002`
- **Database**: PostgreSQL with pg_trgm extension
- **API Key**: OPENAI_API_KEY required for AI Discovery tests
- **Test Runner**: `pytest` or `httpx` async client

---

## 9. Known Limitations & Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ingredient modifiers skipped in Step 2 | "순두부" in compound names won't decompose | Engine improvement needed (P0) |
| Brand names not in modifier dict | "고씨네", "할매" variants may fail | Expand modifier dictionary or add brand detection |
| Similarity match requires same length | Typos that change char count won't match | Consider relaxing `max_length_diff` |
| AI Discovery needs API key | Tests skip without OPENAI_API_KEY | Provide mock or test key |
| "할매" vs "할머니" variant | "할매" may not be in modifiers table | Verify and add common variants |

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| **canonical_menu** | Standard/base menu entry in DB (e.g., "뼈해장국") |
| **modifier** | Prefix/suffix that modifies a canonical menu (e.g., "왕", "얼큰") |
| **exact match** | Direct DB lookup by `name_ko` |
| **similarity match** | pg_trgm trigram similarity search (for typo correction) |
| **modifier_decomposition** | Strip modifiers from input to find canonical base |
| **ai_discovery** | GPT-4o fallback for unknown menus |
| **confidence** | 0.0-1.0 score indicating match reliability |

---

**Document prepared by**: spec-analyzer agent
**Based on**: 01_concept_overview.md, 03_data_schema_v0.1.md, 05_mvp_scope_definition.md, 06_api_specification_v0.1.md, 07_seed_data_guide.md, matching_engine.py
