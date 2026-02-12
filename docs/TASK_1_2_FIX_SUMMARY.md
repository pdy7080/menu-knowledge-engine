# Task 1.2 수정 완료 - 테스트 Fixture 및 모델 불일치 해결

## 🔧 수정 개요

**문제**: CanonicalMenu 모델과 코드 구현 간 필드 불일치
**해결**: 모델 스키마에 맞게 전체 코드베이스 수정

---

## 📋 발견된 문제점

### 1. category 필드 미존재
**문제**: 코드에서 `category` 필드를 사용했으나, `CanonicalMenu` 모델에 해당 컬럼 없음
**영향 범위**: Service, Model, Migration, API, Tests, Sample Data

### 2. price 필드명 불일치
**문제**: `price_range_start/end` 사용 → 실제 모델은 `typical_price_min/max`
**영향 범위**: Service

### 3. Async Fixture 설정 누락
**문제**: `@pytest.fixture` 사용 → `@pytest_asyncio.fixture` 필요
**영향 범위**: Tests

### 4. pytest-asyncio 의존성 누락
**문제**: requirements.txt에 테스트 라이브러리 없음
**영향 범위**: Testing Infrastructure

---

## ✅ 수정 내용

### 1. Service Layer 수정 (`menu_upload_service.py`)

**Before**:
```python
menu = CanonicalMenu(
    name_ko=menu_data['name_ko'],
    name_en=menu_data.get('name_en'),
    category=menu_data.get('category', 'main'),  # ❌ 존재하지 않는 필드
    price_range_start=menu_data.get('price'),    # ❌ 잘못된 필드명
    price_range_end=menu_data.get('price')
)
```

**After**:
```python
menu = CanonicalMenu(
    name_ko=menu_data['name_ko'],
    name_en=menu_data.get('name_en', menu_data['name_ko']),  # ✅ Default to KO
    typical_price_min=menu_data.get('price'),  # ✅ 올바른 필드명
    typical_price_max=menu_data.get('price')
)
```

**파싱 메서드 수정**:
- `_parse_csv()`: category 필드 제거
- `_parse_json()`: category 필드 제거
- `_process_menus()`: MenuUploadDetail 생성 시 category 제거

---

### 2. Model 수정 (`models/menu_upload.py`)

**Before**:
```python
class MenuUploadDetail(Base):
    name_ko = Column(String(200), nullable=False)
    name_en = Column(String(200))
    description_en = Column(Text)
    category = Column(String(50))  # ❌ 제거
    price = Column(Integer)
```

**After**:
```python
class MenuUploadDetail(Base):
    name_ko = Column(String(200), nullable=False)
    name_en = Column(String(200))
    description_en = Column(Text)
    price = Column(Integer)  # ✅ category 제거
```

---

### 3. Migration 수정 (`create_menu_upload_tables.sql`)

**Before**:
```sql
CREATE TABLE IF NOT EXISTS menu_upload_details (
    ...
    name_ko VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    description_en TEXT,
    category VARCHAR(50),  -- ❌ 제거
    price INTEGER,
    ...
);
```

**After**:
```sql
CREATE TABLE IF NOT EXISTS menu_upload_details (
    ...
    name_ko VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    description_en TEXT,
    price INTEGER,  -- ✅ category 제거
    ...
);
```

---

### 4. API 응답 수정 (`api/b2b.py`)

**Before**:
```python
"details": [
    {
        "id": str(d.id),
        "name_ko": d.name_ko,
        "name_en": d.name_en,
        "category": d.category,  # ❌ 제거
        "price": d.price,
        ...
    }
]
```

**After**:
```python
"details": [
    {
        "id": str(d.id),
        "name_ko": d.name_ko,
        "name_en": d.name_en,
        "price": d.price,  # ✅ category 제거
        ...
    }
]
```

---

### 5. Test 수정 (`tests/test_b2b_menu_upload.py`)

#### A. Async Fixture 설정

**Before**:
```python
import pytest

@pytest.fixture
async def test_db():
    """Create test database"""
    ...
```

**After**:
```python
import pytest
import pytest_asyncio

@pytest_asyncio.fixture
async def test_db():
    """Create test database"""
    ...
```

#### B. Sample Data 수정

**Before (CSV)**:
```csv
name_ko,name_en,description_en,category,price
김치찌개,Kimchi Stew,Spicy Korean stew...,stew,8000
```

**After (CSV)**:
```csv
name_ko,name_en,description_en,price
김치찌개,Kimchi Stew,Spicy Korean stew...,8000
```

**Before (JSON)**:
```json
{
  "name_ko": "김치찌개",
  "name_en": "Kimchi Stew",
  "description_en": "Spicy Korean stew...",
  "category": "stew",
  "price": 8000
}
```

**After (JSON)**:
```json
{
  "name_ko": "김치찌개",
  "name_en": "Kimchi Stew",
  "description_en": "Spicy Korean stew...",
  "price": 8000
}
```

#### C. CanonicalMenu 생성 수정

**Before**:
```python
existing_menu = CanonicalMenu(
    name_ko="김치찌개",
    name_en="Kimchi Stew",
    category="stew",              # ❌ 존재하지 않는 필드
    price_range_start=8000,       # ❌ 잘못된 필드명
    price_range_end=8000
)
```

**After**:
```python
existing_menu = CanonicalMenu(
    name_ko="김치찌개",
    name_en="Kimchi Stew",
    typical_price_min=8000,       # ✅ 올바른 필드명
    typical_price_max=8000,
    explanation_short={}          # ✅ Required JSONB field
)
```

---

### 6. Testing Infrastructure (`requirements.txt`, `pytest.ini`)

#### requirements.txt 추가

**Before**: pytest 의존성 없음

**After**:
```txt
# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
aiosqlite==0.20.0
```

#### pytest.ini 생성

**New File**:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
addopts = -v --tb=short --strict-markers
```

---

### 7. Sample Data 파일 수정

**Before (sample_menus.csv)**:
- Header: `name_ko,name_en,description_en,category,price`
- 8 rows with category field

**After (sample_menus.csv)**:
- Header: `name_ko,name_en,description_en,price`
- 8 rows without category field

**Before (sample_menus.json)**:
- Each menu has `category` field

**After (sample_menus.json)**:
- `category` field removed from all menus

---

## 📊 수정 파일 목록

| 파일 | 변경 내용 | 변경 수 |
|------|----------|---------|
| `services/menu_upload_service.py` | category 제거, price 필드명 수정 | 5개 메서드 |
| `models/menu_upload.py` | category 컬럼 제거 | 1개 컬럼 |
| `migrations/create_menu_upload_tables.sql` | category 컬럼 제거 | 1개 컬럼 |
| `api/b2b.py` | category 응답 필드 제거 | 1개 엔드포인트 |
| `tests/test_b2b_menu_upload.py` | Async fixture, category 제거 | 3개 fixture, 1개 테스트 |
| `tests/sample_menus.csv` | category 컬럼 제거 | 헤더 + 8행 |
| `tests/sample_menus.json` | category 필드 제거 | 8개 메뉴 |
| `requirements.txt` | 테스트 의존성 추가 | 3개 라이브러리 |
| `pytest.ini` | pytest 설정 파일 생성 | 새 파일 |

**총 9개 파일 수정/생성**

---

## 🧪 검증 단계

### 1. 의존성 설치

```bash
cd C:\project\menu\app\backend
pip install -r requirements.txt
```

### 2. 데이터베이스 마이그레이션 재실행 (필요 시)

```bash
# 기존 테이블 삭제 (개발 환경에서만!)
psql -U postgres -d menu_db -c "DROP TABLE IF EXISTS menu_upload_details CASCADE;"
psql -U postgres -d menu_db -c "DROP TABLE IF EXISTS menu_upload_tasks CASCADE;"

# 마이그레이션 재실행
psql -U postgres -d menu_db -f migrations/create_menu_upload_tables.sql
```

### 3. 테스트 실행

```bash
# 전체 테스트 실행
pytest tests/test_b2b_menu_upload.py -v

# 개별 테스트 실행
pytest tests/test_b2b_menu_upload.py::test_upload_menus_csv -v

# 커버리지 확인
pytest tests/test_b2b_menu_upload.py --cov=services.menu_upload_service
```

### 4. 수동 API 테스트

```bash
# 1. 서버 시작
uvicorn main:app --reload --port 8000

# 2. CSV 업로드 테스트
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@tests/sample_menus.csv"

# 3. JSON 업로드 테스트
curl -X POST http://localhost:8000/api/v1/b2b/restaurants/{restaurant_id}/menus/upload \
  -F "file=@tests/sample_menus.json"
```

---

## ✅ 검증 체크리스트

- [x] Service: category 필드 제거
- [x] Service: price 필드명 수정 (typical_price_min/max)
- [x] Model: category 컬럼 제거
- [x] Migration: category 컬럼 제거
- [x] API: category 응답 필드 제거
- [x] Tests: Async fixture 설정 (@pytest_asyncio.fixture)
- [x] Tests: CanonicalMenu 생성 시 올바른 필드 사용
- [x] Sample Data: category 필드 제거 (CSV, JSON)
- [x] Dependencies: pytest, pytest-asyncio, aiosqlite 추가
- [x] Configuration: pytest.ini 생성

---

## 🎯 다음 단계

### A. 테스트 검증 (필수)

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 테스트 실행
pytest tests/test_b2b_menu_upload.py -v

# 3. 커버리지 확인
pytest tests/test_b2b_menu_upload.py --cov=services.menu_upload_service --cov-report=html
```

### B. Git Commit

```bash
git add .
git commit -m "fix: Task 1.2 - Remove category field, fix price fields, add async fixtures

- Remove category field from models, service, API, tests, sample data
- Fix price field names (price_range_start/end → typical_price_min/max)
- Add pytest-asyncio fixtures for async database tests
- Add pytest, pytest-asyncio, aiosqlite dependencies
- Create pytest.ini configuration

Breaking Changes:
- MenuUploadDetail.category column removed
- API response no longer includes category field
- CSV/JSON upload format no longer accepts category field"
```

### C. Task 1.3 진행

모든 테스트 통과 후 Task 1.3 (Menu Translation API)로 진행

---

## 💡 교훈

### 1. 모델 우선 설계
**문제**: 코드 작성 시 실제 모델 스키마 미확인
**해결**: 코드 작성 전 항상 모델 정의 먼저 확인

### 2. 필드명 일관성
**문제**: `price_range_start` vs `typical_price_min` 혼동
**해결**: DB 스키마와 모델 필드명 100% 일치 원칙

### 3. Async 테스트 설정
**문제**: pytest-asyncio 설정 누락으로 fixture 오류
**해결**: pytest.ini에 `asyncio_mode = auto` 설정

### 4. 의존성 명시
**문제**: 테스트 라이브러리 requirements.txt 누락
**해결**: 개발/테스트 의존성 모두 문서화

---

**수정 완료 일시**: 2026-02-12
**수정자**: Claude Code Development Team
**검증 상태**: ⏳ 테스트 실행 대기
