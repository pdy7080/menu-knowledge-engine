# Task 1.2 Manual Testing Guide

## 테스트 접근 변경

**Before**: 자동화된 pytest 통합 테스트
**After**: 수동 API 테스트 (실제 PostgreSQL 사용)

**이유**: SQLite는 JSONB를 지원하지 않아 통합 테스트 불가능. 실제 DB 환경에서 테스트 필요.

---

## Prerequisites

1. PostgreSQL 서버 실행 중
2. Database 생성 및 마이그레이션 완료
3. `.env` 파일 설정:
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost/menu_db
   OPENAI_API_KEY=your_key
   ```

---

## 1단계: 서버 시작

```bash
cd C:\project\menu\app\backend
python -m uvicorn main:app --reload --port 8000
```

**기대 결과**:
```
INFO:     Started server process
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 2단계: Health Check

```bash
curl http://localhost:8000/health
```

**기대 응답**:
```json
{
  "status": "ok",
  "service": "Menu Knowledge Engine",
  "version": "0.1.0"
}
```

---

## 3단계: Restaurant 생성

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

**기대 응답**:
```json
{
  "success": true,
  "restaurant_id": "uuid-here",
  "status": "pending_approval",
  "message": "Restaurant registered. Waiting for admin approval."
}
```

**Action**: `restaurant_id` 저장 → 다음 단계에서 사용

---

## 4단계: CSV 메뉴 업로드

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@tests/sample_menus.csv"
```

**기대 응답**:
```json
{
  "success": true,
  "upload_task_id": "uuid-here",
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

**검증**:
- ✅ status = "completed"
- ✅ total_menus = 8
- ✅ successful = 8
- ✅ failed = 0

---

## 5단계: Upload Status 확인

```bash
curl http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload/{upload_task_id}
```

**기대 응답**:
```json
{
  "upload_task": {
    "id": "uuid",
    "status": "completed",
    "total_menus": 8,
    "successful": 8,
    "failed": 0,
    "skipped": 0
  },
  "details": [
    {
      "id": "uuid",
      "name_ko": "김치찌개",
      "name_en": "Kimchi Stew",
      "price": 8000,
      "status": "success",
      "created_menu_id": "uuid",
      "row_number": 1
    },
    ...
  ]
}
```

**검증**:
- ✅ 8개 메뉴 details 존재
- ✅ 모든 status = "success"
- ✅ created_menu_id가 모두 있음

---

## 6단계: JSON 메뉴 업로드

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@tests/sample_menus.json"
```

**기대**: CSV와 동일한 응답 (file_type = "json")

---

## 7단계: 중복 감지 테스트

**동일한 CSV 파일을 다시 업로드**:

```bash
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@tests/sample_menus.csv"
```

**기대 응답**:
```json
{
  "success": true,
  "status": "completed",
  "total_menus": 8,
  "successful": 0,
  "failed": 0,
  "skipped": 8  ← 모두 중복으로 건너뜀
}
```

---

## 8단계: 잘못된 파일 형식 테스트

```bash
echo "test" > test.txt
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@test.txt"
```

**기대 응답**:
```json
{
  "detail": "Unsupported file type. Use CSV or JSON"
}
```

**Status Code**: 400

---

## 9단계: DB 검증

```sql
-- Upload Tasks 확인
SELECT id, file_name, status, total_menus, successful, failed, skipped
FROM menu_upload_tasks
ORDER BY created_at DESC
LIMIT 5;

-- Upload Details 확인
SELECT name_ko, status, error_message, created_menu_id
FROM menu_upload_details
WHERE upload_task_id = 'your_upload_task_id';

-- Canonical Menus 확인 (번역 포함)
SELECT id, name_ko, name_en, explanation_short
FROM canonical_menus
WHERE name_ko IN ('김치찌개', '불고기', '비빔밥')
LIMIT 5;
```

**검증**:
- ✅ explanation_short JSONB에 en, ja, zh 키 존재
- ✅ created_menu_id가 canonical_menus.id와 일치

---

## Checklist

- [ ] 서버 정상 시작
- [ ] Health check 성공
- [ ] Restaurant 생성 성공
- [ ] CSV 업로드 성공 (8개 메뉴)
- [ ] JSON 업로드 성공 (8개 메뉴)
- [ ] 중복 감지 성공 (8개 skipped)
- [ ] 잘못된 파일 형식 거부 (400 에러)
- [ ] DB에 데이터 정상 저장
- [ ] JSONB 번역 데이터 확인 (en, ja, zh)

---

## Troubleshooting

### 문제: Restaurant not found (404)
**해결**: restaurant_id가 올바른지 확인

### 문제: OpenAI API 에러
**해결**: `.env`에 `OPENAI_API_KEY` 설정 확인

### 문제: Database connection error
**해결**: PostgreSQL 서버 실행 및 `DATABASE_URL` 확인

### 문제: 번역 실패
**해결**: GPT-4o-mini API 할당량 확인

---

**테스트 완료 시**: 모든 체크리스트 통과 → Task 1.2 검증 완료
