# Task 1.3 Menu Approval API - Manual Testing Guide

## Prerequisites

1. PostgreSQL running with menu_db
2. Server running: `uvicorn main:app --reload --port 8000`
3. Restaurant with pending_approval status
4. Menus uploaded and ready for approval

---

## Test Scenario 1: Successful Approval

### Step 1: Create Restaurant (if not exists)

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Restaurant",
    "owner_name": "Test Owner",
    "owner_phone": "010-1234-5678",
    "owner_email": "test@example.com",
    "address": "Seoul, Korea",
    "business_license": "TEST-APPROVAL-001"
  }'
```

**Save**: `restaurant_id`

### Step 2: Upload Menus with Translations

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@tests/new_menus.csv"
```

**Expected**: Menus created with GPT-4o translations (en, ja, zh)

### Step 3: Get Menu IDs

Query database or check upload task details to get `created_menu_id` values.

```sql
SELECT id, name_ko, name_en, explanation_short
FROM canonical_menus
WHERE name_ko LIKE '%테스트%'
ORDER BY created_at DESC
LIMIT 5;
```

**Save**: List of `menu_id` values

### Step 4: Approve Menus

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/approve \
  -H "Content-Type: application/json" \
  -d '{
    "admin_user_id": "admin001",
    "selected_menu_ids": ["menu_id_1", "menu_id_2", "menu_id_3"]
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Restaurant 'Test Restaurant' approved with 3 menus",
  "restaurant": {
    "id": "uuid",
    "name": "Test Restaurant",
    "status": "active",
    "approved_at": "2026-02-12T...",
    "approved_by": "admin001"
  },
  "approved_menus": {
    "count": 3,
    "menu_ids": ["uuid1", "uuid2", "uuid3"]
  },
  "qr_code": {
    "shop_code": "SHOPXXXX",
    "qr_code_url": "/static/qr/SHOPXXXX_20260212_HHMMSS.png",
    "qr_code_file_path": "static/qr/SHOPXXXX_20260212_HHMMSS.png",
    "activation_date": "2026-02-12T...",
    "languages": ["ko", "en", "ja", "zh"]
  }
}
```

### Step 5: Verify QR Code File

```bash
ls -lh static/qr/
```

**Expected**: QR code PNG file exists

### Step 6: Verify DB Changes

```sql
-- Restaurant status changed
SELECT id, name, status, approved_at, approved_by
FROM restaurants
WHERE id = 'your_restaurant_id';

-- Expected: status = 'active', approved_at and approved_by set

-- Upload task status changed
SELECT id, status, completed_at
FROM menu_upload_tasks
WHERE restaurant_id = 'your_restaurant_id'
ORDER BY created_at DESC
LIMIT 1;

-- Expected: status = 'approved'
```

---

## Test Scenario 2: Validation Failures

### 2-1: Incomplete Translations

Create a menu without full translations:

```sql
INSERT INTO canonical_menus (name_ko, name_en, explanation_short)
VALUES ('불완전메뉴', 'Incomplete Menu', '{"en": "English only"}');
```

Try to approve:

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/approve \
  -H "Content-Type: application/json" \
  -d '{
    "admin_user_id": "admin001",
    "selected_menu_ids": ["incomplete_menu_id"]
  }'
```

**Expected Response** (400 Bad Request):
```json
{
  "detail": {
    "message": "Menu approval validation failed",
    "errors": [
      "Menu uuid (...): translation missing for language 'ja'",
      "Menu uuid (...): translation missing for language 'zh'"
    ]
  }
}
```

### 2-2: No Menus Selected

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/approve \
  -H "Content-Type: application/json" \
  -d '{
    "admin_user_id": "admin001",
    "selected_menu_ids": []
  }'
```

**Expected Error**:
```
"At least one menu must be selected for approval"
```

### 2-3: Wrong Restaurant Status

Try to approve an already-active restaurant:

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{active_restaurant_id}/menus/approve \
  -H "Content-Type: application/json" \
  -d '{
    "admin_user_id": "admin001",
    "selected_menu_ids": ["menu_id"]
  }'
```

**Expected Error**:
```
"Restaurant status must be 'pending_approval', current: 'active'"
```

### 2-4: Invalid Price

Create menu with price = 0:

```sql
UPDATE canonical_menus
SET typical_price_min = 0
WHERE id = 'test_menu_id';
```

**Expected Error**:
```
"Menu uuid (...): typical_price_min must be > 0"
```

### 2-5: Duplicate Menu Names

Try to approve menus with duplicate names:

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/approve \
  -H "Content-Type: application/json" \
  -d '{
    "admin_user_id": "admin001",
    "selected_menu_ids": ["menu1_id", "menu2_id_with_same_name"]
  }'
```

**Expected Error**:
```
"Duplicate menu name (KO): '김치찌개'"
```

---

## Test Scenario 3: Duplicate Approval Prevention

### Step 1: Approve menus first (Scenario 1)

### Step 2: Try to approve again

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/approve \
  -H "Content-Type: application/json" \
  -d '{
    "admin_user_id": "admin002",
    "selected_menu_ids": ["menu_id"]
  }'
```

**Expected Error**:
```
"Restaurant status must be 'pending_approval', current: 'active'"
```

---

## Validation Checklist

- [ ] Successful approval with valid data
- [ ] QR code file generated in static/qr/
- [ ] Restaurant status changed to 'active'
- [ ] approved_at and approved_by fields set
- [ ] MenuUploadTask status changed to 'approved'
- [ ] Incomplete translations rejected
- [ ] Empty menu selection rejected
- [ ] Wrong restaurant status rejected
- [ ] Invalid price (≤ 0) rejected
- [ ] Duplicate menu names rejected
- [ ] Duplicate approval prevented
- [ ] Non-existent restaurant rejected (404)
- [ ] Non-existent menu IDs rejected

---

## Performance Metrics

| Operation | Expected Time |
|-----------|---------------|
| Validation (7 checks) | < 500ms |
| QR generation | < 200ms |
| Total approval | < 1 second |

---

## Troubleshooting

### Issue: QR code file not created
**Solution**: Check static/qr/ directory permissions

### Issue: Validation passes but DB not updated
**Solution**: Check transaction commit

### Issue: Translation check fails incorrectly
**Solution**: Verify explanation_short JSONB structure

---

**Test Completion**: All checkboxes checked → Task 1.3 verified ✅
