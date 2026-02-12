"""
B2B Menu Upload API Tests
"""
import pytest
import pytest_asyncio
import io
import csv
import json
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from main import app
from database import get_db
from models.restaurant import Restaurant, RestaurantStatus
from models.canonical_menu import CanonicalMenu
from models.menu_upload import MenuUploadTask, MenuUploadDetail, UploadStatus, MenuItemStatus


# Test Database Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        from database import Base
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def test_restaurant(test_db: AsyncSession):
    """Create test restaurant"""
    restaurant = Restaurant(
        name="Test Restaurant",
        name_en="Test Restaurant EN",
        owner_name="Test Owner",
        owner_phone="010-1234-5678",
        owner_email="test@example.com",
        address="Test Address",
        business_license="123-45-67890",
        business_type="Korean",
        status=RestaurantStatus.active
    )
    test_db.add(restaurant)
    await test_db.commit()
    await test_db.refresh(restaurant)
    return restaurant


@pytest.fixture
def sample_csv_content():
    """Create sample CSV content (category field removed - not in model)"""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['name_ko', 'name_en', 'description_en', 'price'])
    writer.writeheader()
    writer.writerow({
        'name_ko': '김치찌개',
        'name_en': 'Kimchi Stew',
        'description_en': 'Spicy Korean stew with kimchi and pork',
        'price': '8000'
    })
    writer.writerow({
        'name_ko': '불고기',
        'name_en': 'Bulgogi',
        'description_en': 'Marinated grilled beef',
        'price': '12000'
    })
    return output.getvalue().encode('utf-8')


@pytest.fixture
def sample_json_content():
    """Create sample JSON content (category field removed - not in model)"""
    data = {
        "menus": [
            {
                "name_ko": "김치찌개",
                "name_en": "Kimchi Stew",
                "description_en": "Spicy Korean stew with kimchi and pork",
                "price": 8000
            },
            {
                "name_ko": "불고기",
                "name_en": "Bulgogi",
                "description_en": "Marinated grilled beef",
                "price": 12000
            }
        ]
    }
    return json.dumps(data).encode('utf-8')


@pytest.mark.asyncio
async def test_upload_menus_csv(test_db: AsyncSession, test_restaurant: Restaurant, sample_csv_content: bytes):
    """
    Test CSV 메뉴 업로드

    Verify:
    - CSV 파일 파싱 성공
    - 메뉴 생성 성공
    - Upload Task 생성 및 상태 업데이트
    """
    with patch('services.menu_upload_service.OpenAI') as mock_openai:
        # Mock GPT-4o response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "ja": "キムチチゲ",
            "zh": "泡菜汤"
        })
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        # Override get_db dependency
        async def override_get_db():
            yield test_db

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)

        # Upload CSV file
        response = client.post(
            f"/api/v1/b2b/restaurants/{test_restaurant.id}/menus/upload",
            files={"file": ("test_menus.csv", io.BytesIO(sample_csv_content), "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["file_name"] == "test_menus.csv"
        assert data["file_type"] == "csv"
        assert data["status"] == UploadStatus.completed.value
        assert data["total_menus"] == 2
        assert data["successful"] == 2
        assert data["failed"] == 0

        # Cleanup
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_menus_json(test_db: AsyncSession, test_restaurant: Restaurant, sample_json_content: bytes):
    """
    Test JSON 메뉴 업로드

    Verify:
    - JSON 파일 파싱 성공
    - 메뉴 생성 성공
    - Upload Task 생성 및 상태 업데이트
    """
    with patch('services.menu_upload_service.OpenAI') as mock_openai:
        # Mock GPT-4o response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "ja": "キムチチゲ",
            "zh": "泡菜汤"
        })
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        # Override get_db dependency
        async def override_get_db():
            yield test_db

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)

        # Upload JSON file
        response = client.post(
            f"/api/v1/b2b/restaurants/{test_restaurant.id}/menus/upload",
            files={"file": ("test_menus.json", io.BytesIO(sample_json_content), "application/json")}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["file_name"] == "test_menus.json"
        assert data["file_type"] == "json"
        assert data["status"] == UploadStatus.completed.value
        assert data["total_menus"] == 2
        assert data["successful"] == 2
        assert data["failed"] == 0

        # Cleanup
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_auto_translation(test_db: AsyncSession, test_restaurant: Restaurant, sample_csv_content: bytes):
    """
    Test 자동 번역 (GPT-4o)

    Verify:
    - GPT-4o API 호출 확인
    - JA, ZH 번역 생성
    - explanation_short JSONB에 저장
    """
    with patch('services.menu_upload_service.OpenAI') as mock_openai:
        # Mock GPT-4o response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "ja": "キムチチゲ - ピリ辛の韓国風鍋料理",
            "zh": "泡菜汤 - 辣韩式炖菜"
        })
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        # Override get_db dependency
        async def override_get_db():
            yield test_db

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)

        # Upload CSV file
        response = client.post(
            f"/api/v1/b2b/restaurants/{test_restaurant.id}/menus/upload",
            files={"file": ("test_menus.csv", io.BytesIO(sample_csv_content), "text/csv")}
        )

        assert response.status_code == 200

        # Verify GPT-4o was called
        assert mock_openai.return_value.chat.completions.create.called

        # Verify translation in database
        from sqlalchemy import select
        result = await test_db.execute(
            select(CanonicalMenu).where(CanonicalMenu.name_ko == '김치찌개')
        )
        menu = result.scalars().first()

        assert menu is not None
        assert menu.explanation_short is not None
        assert 'en' in menu.explanation_short
        assert 'ja' in menu.explanation_short
        assert 'zh' in menu.explanation_short

        # Cleanup
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_retry_on_failure(test_db: AsyncSession, test_restaurant: Restaurant, sample_csv_content: bytes):
    """
    Test GPT-4o 실패 시 재시도

    Verify:
    - 첫 2회 실패 → 재시도
    - 3회차 성공
    - 최대 3회 재시도 후 실패 처리
    """
    with patch('services.menu_upload_service.OpenAI') as mock_openai:
        # Mock: First 2 calls fail, 3rd succeeds
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("API temporary error")
            else:
                mock_response = MagicMock()
                mock_response.choices[0].message.content = json.dumps({
                    "ja": "キムチチゲ",
                    "zh": "泡菜汤"
                })
                return mock_response

        mock_openai.return_value.chat.completions.create.side_effect = side_effect

        # Override get_db dependency
        async def override_get_db():
            yield test_db

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)

        # Upload CSV file
        response = client.post(
            f"/api/v1/b2b/restaurants/{test_restaurant.id}/menus/upload",
            files={"file": ("test_menus.csv", io.BytesIO(sample_csv_content), "text/csv")}
        )

        # Should succeed on 3rd attempt
        assert response.status_code == 200
        assert call_count >= 3  # Verify retry happened

        # Cleanup
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_duplicate_menu_detection(test_db: AsyncSession, test_restaurant: Restaurant, sample_csv_content: bytes):
    """
    Test 중복 메뉴 감지

    Verify:
    - 기존 메뉴와 name_ko 중복 시 skipped
    - Upload Detail에 "Duplicate menu" 에러 메시지
    """
    # Pre-create existing menu
    existing_menu = CanonicalMenu(
        name_ko="김치찌개",
        name_en="Kimchi Stew",
        typical_price_min=8000,
        typical_price_max=8000,
        explanation_short={}  # Required field, default to empty dict
    )
    test_db.add(existing_menu)
    await test_db.commit()

    with patch('services.menu_upload_service.OpenAI') as mock_openai:
        # Mock GPT-4o response (for non-duplicate menu)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "ja": "プルコギ",
            "zh": "烤肉"
        })
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        # Override get_db dependency
        async def override_get_db():
            yield test_db

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)

        # Upload CSV file
        response = client.post(
            f"/api/v1/b2b/restaurants/{test_restaurant.id}/menus/upload",
            files={"file": ("test_menus.csv", io.BytesIO(sample_csv_content), "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify: 1 skipped (김치찌개), 1 successful (불고기)
        assert data["total_menus"] == 2
        assert data["successful"] == 1
        assert data["skipped"] == 1
        assert data["failed"] == 0

        # Verify upload details
        upload_task_id = data["upload_task_id"]
        details_response = client.get(
            f"/api/v1/b2b/restaurants/{test_restaurant.id}/menus/upload/{upload_task_id}"
        )

        details_data = details_response.json()
        skipped_detail = next(
            (d for d in details_data["details"] if d["status"] == MenuItemStatus.skipped.value),
            None
        )

        assert skipped_detail is not None
        assert skipped_detail["name_ko"] == "김치찌개"
        assert skipped_detail["error_message"] == "Duplicate menu"

        # Cleanup
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_invalid_file_type():
    """
    Test 지원하지 않는 파일 형식

    Verify:
    - .txt, .xlsx 등 → 400 Bad Request
    """
    client = TestClient(app)

    response = client.post(
        f"/api/v1/b2b/restaurants/{uuid.uuid4()}/menus/upload",
        files={"file": ("test.txt", b"invalid content", "text/plain")}
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_restaurant_not_found(sample_csv_content: bytes):
    """
    Test 존재하지 않는 식당 ID

    Verify:
    - 404 Not Found
    """
    client = TestClient(app)

    fake_restaurant_id = uuid.uuid4()
    response = client.post(
        f"/api/v1/b2b/restaurants/{fake_restaurant_id}/menus/upload",
        files={"file": ("test_menus.csv", io.BytesIO(sample_csv_content), "text/csv")}
    )

    assert response.status_code == 404
    assert "Restaurant" in response.json()["detail"]


@pytest.mark.asyncio
async def test_malformed_csv():
    """
    Test 잘못된 CSV 형식

    Verify:
    - 필수 컬럼 누락 → 400 Bad Request
    """
    client = TestClient(app)

    # CSV without required 'name_ko' column
    malformed_csv = b"name_en,price\nTest,5000"

    response = client.post(
        f"/api/v1/b2b/restaurants/{uuid.uuid4()}/menus/upload",
        files={"file": ("test.csv", io.BytesIO(malformed_csv), "text/csv")}
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_malformed_json():
    """
    Test 잘못된 JSON 형식

    Verify:
    - Invalid JSON → 400 Bad Request
    - Missing 'menus' array → 400 Bad Request
    """
    client = TestClient(app)

    # Invalid JSON
    response1 = client.post(
        f"/api/v1/b2b/restaurants/{uuid.uuid4()}/menus/upload",
        files={"file": ("test.json", b"{invalid json}", "application/json")}
    )

    assert response1.status_code == 400
    assert "Invalid JSON" in response1.json()["detail"]

    # Missing 'menus' array
    response2 = client.post(
        f"/api/v1/b2b/restaurants/{uuid.uuid4()}/menus/upload",
        files={"file": ("test.json", b'{"data": []}', "application/json")}
    )

    assert response2.status_code == 400
    assert "must have 'menus' array" in response2.json()["detail"]
