# Task 1.2 Menu Upload API Testing Guide

## Overview

Task 1.2 implements B2B menu batch upload functionality with:
- CSV/JSON file parsing
- Automatic translation (GPT-4o-mini)
- Duplicate detection
- Retry logic with exponential backoff
- Comprehensive error handling

## Test Files

| File | Description |
|------|-------------|
| `test_b2b_menu_upload.py` | Comprehensive pytest test suite |
| `sample_menus.csv` | Sample CSV file for manual testing |
| `sample_menus.json` | Sample JSON file for manual testing |

## Running Automated Tests

### 1. Install Test Dependencies

```bash
pip install pytest pytest-asyncio httpx
```

### 2. Run All Tests

```bash
# Run all menu upload tests
pytest tests/test_b2b_menu_upload.py -v

# Run specific test
pytest tests/test_b2b_menu_upload.py::test_upload_menus_csv -v

# Run with coverage
pytest tests/test_b2b_menu_upload.py --cov=services.menu_upload_service --cov-report=html
```

### 3. Expected Test Coverage

Target: **>80% coverage**

| Test Case | Coverage Area |
|-----------|---------------|
| `test_upload_menus_csv` | CSV parsing, upload workflow |
| `test_upload_menus_json` | JSON parsing, upload workflow |
| `test_auto_translation` | GPT-4o translation, JSONB storage |
| `test_retry_on_failure` | Retry decorator, error handling |
| `test_duplicate_menu_detection` | Duplicate checking logic |
| `test_invalid_file_type` | File validation |
| `test_restaurant_not_found` | Restaurant validation |
| `test_malformed_csv` | CSV error handling |
| `test_malformed_json` | JSON error handling |

## Manual API Testing

### Prerequisites

1. **Start backend server**:
   ```bash
   cd C:\project\menu\app\backend
   uvicorn main:app --reload --port 8000
   ```

2. **Create a test restaurant** (if not exists):
   ```bash
   curl -X POST http://localhost:8000/api/v1/b2b/restaurants \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Restaurant",
       "owner_name": "Test Owner",
       "owner_phone": "010-1234-5678",
       "owner_email": "test@example.com",
       "address": "Seoul, Korea",
       "business_license": "123-45-67890",
       "business_type": "Korean"
     }'
   ```

   Save the returned `restaurant_id`.

### Test 1: Upload CSV File

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@tests/sample_menus.csv"
```

**Expected Response**:
```json
{
  "success": true,
  "upload_task_id": "uuid",
  "file_name": "sample_menus.csv",
  "file_type": "csv",
  "status": "completed",
  "total_menus": 8,
  "successful": 8,
  "failed": 0,
  "skipped": 0,
  "created_at": "2026-02-12T...",
  "started_at": "2026-02-12T...",
  "completed_at": "2026-02-12T..."
}
```

### Test 2: Upload JSON File

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@tests/sample_menus.json"
```

**Expected Response**: Same as CSV (with `"file_type": "json"`)

### Test 3: Check Upload Status

```bash
curl http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload/{upload_task_id}
```

**Expected Response**:
```json
{
  "upload_task": {
    "id": "uuid",
    "restaurant_id": "uuid",
    "file_name": "sample_menus.csv",
    "file_type": "csv",
    "status": "completed",
    "total_menus": 8,
    "successful": 8,
    "failed": 0,
    "skipped": 0,
    "error_log": null,
    "created_at": "...",
    "started_at": "...",
    "completed_at": "..."
  },
  "details": [
    {
      "id": "uuid",
      "name_ko": "김치찌개",
      "name_en": "Kimchi Stew",
      "category": "stew",
      "price": 8000,
      "status": "success",
      "error_message": null,
      "created_menu_id": "uuid",
      "row_number": 1
    },
    ...
  ]
}
```

### Test 4: Duplicate Detection

Upload the same file twice:

```bash
# First upload
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@tests/sample_menus.csv"

# Second upload (same file)
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@tests/sample_menus.csv"
```

**Expected**: Second upload should have `"skipped": 8` (all duplicates)

### Test 5: Invalid File Type

```bash
echo "test" > test.txt
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@test.txt"
```

**Expected Response**:
```json
{
  "detail": "Unsupported file type. Use CSV or JSON"
}
```

## Verification Checklist

After running all tests, verify:

- [ ] All pytest tests pass (9/9)
- [ ] Coverage >80%
- [ ] CSV upload creates menus in database
- [ ] JSON upload creates menus in database
- [ ] GPT-4o translation generates JA/ZH translations
- [ ] Duplicate menus are skipped (not created)
- [ ] Retry logic handles temporary API failures
- [ ] Invalid file types return 400 error
- [ ] Non-existent restaurant returns 404 error
- [ ] Malformed CSV/JSON returns 400 error

## Database Verification

Check created menus in database:

```sql
-- Check upload tasks
SELECT id, file_name, status, total_menus, successful, failed, skipped
FROM menu_upload_tasks
ORDER BY created_at DESC
LIMIT 10;

-- Check upload details
SELECT name_ko, status, error_message, created_menu_id
FROM menu_upload_details
WHERE upload_task_id = 'your_upload_task_id';

-- Check created canonical menus
SELECT id, name_ko, name_en, category, explanation_short
FROM canonical_menus
WHERE name_ko IN ('김치찌개', '불고기', '비빔밥')
LIMIT 5;
```

## Performance Testing

Test with larger files:

```bash
# Generate 1000-menu CSV
python -c "
import csv
with open('large_test.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['name_ko', 'name_en', 'description_en', 'category', 'price'])
    writer.writeheader()
    for i in range(1000):
        writer.writerow({
            'name_ko': f'메뉴{i}',
            'name_en': f'Menu {i}',
            'description_en': f'Description for menu {i}',
            'category': 'main',
            'price': 10000 + i
        })
"

# Upload and measure time
time curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@large_test.csv"
```

**Expected Performance**:
- 100 menus: ~10-15 seconds
- 1000 menus: ~2-3 minutes (with GPT-4o calls)

## Troubleshooting

### Test Failures

**Issue**: `ModuleNotFoundError: No module named 'pytest'`
**Solution**: `pip install pytest pytest-asyncio`

**Issue**: `Database connection error`
**Solution**: Ensure PostgreSQL is running and database exists

**Issue**: `OpenAI API key error`
**Solution**: Set `OPENAI_API_KEY` in `.env` file

### API Errors

**Issue**: 500 Internal Server Error
**Solution**: Check server logs for detailed error message

**Issue**: 404 Restaurant not found
**Solution**: Verify restaurant_id exists in database

**Issue**: Translation fails
**Solution**: Check GPT-4o API quota and network connection

## Next Steps

After completing Task 1.2 testing:

1. ✅ Commit changes: `git add . && git commit -m "feat: Task 1.2 - B2B Menu Upload API"`
2. ✅ Push branch: `git push origin feat/task-1.2-menu-upload`
3. ✅ Create PR for code review (2 approvals required)
4. 📋 Proceed to Task 1.3 (Menu Translation API)

## Support

For issues or questions:
- Check server logs: `tail -f logs/app.log`
- Review test output: `pytest -v --tb=short`
- Consult `CLAUDE.md` for project guidelines
