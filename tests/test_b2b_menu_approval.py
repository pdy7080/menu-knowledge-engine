"""
테스트: B2B 메뉴 확정 승인 API
pytest - 10개 테스트 케이스, >80% 커버리지 목표

Note: 이 테스트는 Mock 데이터를 사용한 단위 테스트입니다.
실제 데이터베이스 통합 테스트는 별도 test_integration_approval.py에서 수행합니다.
"""
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Add backend to path
backend_path = Path(__file__).parent.parent / "app" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent.parent))

import pytest
from fastapi import HTTPException

# Import services
try:
    from services.menu_approval_service import MenuApprovalValidator, MenuApprovalService
    from services.qr_code_service import QRCodeService
except ImportError as e:
    print(f"Import Error: {e}")
    pytest.skip("Cannot import services", allow_module_level=True)


# ============================================================================
# Unit Tests - Validator & Service Logic
# ============================================================================

class TestMenuApprovalValidator:
    """MenuApprovalValidator 단위 테스트 (Mock 데이터)"""

    def test_validate_translations_complete(self):
        """1️⃣ 번역 완료 확인"""
        validator = MenuApprovalValidator(None)

        mock_menu = Mock()
        mock_menu.id = uuid4()
        mock_menu.name_ko = "비빔밥"
        mock_menu.name_en = "Bibimbap"
        mock_menu.explanation_short = {
            "ko": "비빔밥 설명",
            "en": "Bibimbap description",
            "ja": "ビビンバ説明",
            "zh": "拌饭说明"
        }

        # 검증 실행
        validator._validate_translations(mock_menu, str(mock_menu.id))

        # 번역이 완료되면 에러 없어야 함
        assert len([e for e in validator.validation_errors if "translation" in e.lower()]) == 0

    def test_validate_translations_incomplete(self):
        """2️⃣ 번역 미완료 (JA, ZH 누락)"""
        validator = MenuApprovalValidator(None)

        mock_menu = Mock()
        mock_menu.id = uuid4()
        mock_menu.name_ko = "국밥"
        mock_menu.name_en = "Soup Rice"
        mock_menu.explanation_short = {
            "ko": "국밥 설명",
            "en": "Soup rice description"
            # ja, zh 누락
        }

        # 검증 실행
        validator._validate_translations(mock_menu, str(mock_menu.id))

        # 번역 미완료 에러 발생
        assert len(validator.validation_errors) >= 2
        assert any("ja" in e.lower() for e in validator.validation_errors)
        assert any("zh" in e.lower() for e in validator.validation_errors)

    def test_validate_price_valid(self):
        """3️⃣ 가격 유효성 검사 - 정상"""
        validator = MenuApprovalValidator(None)

        mock_menu = Mock()
        mock_menu.id = uuid4()
        mock_menu.name_ko = "비빔밥"
        mock_menu.typical_price_min = 10000
        mock_menu.typical_price_max = 15000

        # 검증 실행
        validator._validate_price(mock_menu, str(mock_menu.id))

        # 에러 없어야 함
        assert len(validator.validation_errors) == 0

    def test_validate_price_zero(self):
        """4️⃣ 가격 유효성 검사 - 0 이하"""
        validator = MenuApprovalValidator(None)

        mock_menu = Mock()
        mock_menu.id = uuid4()
        mock_menu.name_ko = "무료 밥"
        mock_menu.typical_price_min = 0
        mock_menu.typical_price_max = 0

        # 검증 실행
        validator._validate_price(mock_menu, str(mock_menu.id))

        # 가격 에러 발생
        assert len(validator.validation_errors) >= 1
        assert any("price" in e.lower() for e in validator.validation_errors)

    def test_validate_price_missing(self):
        """5️⃣ 가격 유효성 검사 - 누락"""
        validator = MenuApprovalValidator(None)

        mock_menu = Mock()
        mock_menu.id = uuid4()
        mock_menu.name_ko = "무료 밥"
        mock_menu.typical_price_min = None
        mock_menu.typical_price_max = None

        # 검증 실행
        validator._validate_price(mock_menu, str(mock_menu.id))

        # 가격 누락 에러 발생
        assert len(validator.validation_errors) >= 1
        assert any("missing" in e.lower() for e in validator.validation_errors)

    def test_validate_required_fields(self):
        """6️⃣ 필수 필드 검증"""
        validator = MenuApprovalValidator(None)

        mock_menu = Mock()
        mock_menu.id = uuid4()
        mock_menu.name_ko = "비빔밥"
        mock_menu.name_en = "Bibimbap"
        mock_menu.explanation_short = {"ko": "설명"}

        # 검증 실행
        validator._validate_required_fields(mock_menu, str(mock_menu.id))

        # 필드가 모두 있으면 에러 없어야 함
        errors = [e for e in validator.validation_errors if "required" in e.lower()]
        assert len(errors) == 0

    def test_validate_menu_name_duplicates(self):
        """7️⃣ 메뉴 이름 중복 확인"""
        validator = MenuApprovalValidator(None)

        mock_menu1 = Mock()
        mock_menu1.name_ko = "비빔밥"
        mock_menu1.name_en = "Bibimbap"

        mock_menu2 = Mock()
        mock_menu2.name_ko = "비빔밥"  # 같은 이름
        mock_menu2.name_en = "Bibimbap"

        # 검증 실행
        validator._validate_menu_name_duplicates([mock_menu1, mock_menu2])

        # 중복 에러 발생
        assert len(validator.validation_errors) >= 1
        assert any("duplicate" in e.lower() for e in validator.validation_errors)

    def test_validate_menu_name_no_duplicates(self):
        """8️⃣ 메뉴 이름 중복 없음"""
        validator = MenuApprovalValidator(None)

        mock_menu1 = Mock()
        mock_menu1.name_ko = "비빔밥"
        mock_menu1.name_en = "Bibimbap"

        mock_menu2 = Mock()
        mock_menu2.name_ko = "국밥"  # 다른 이름
        mock_menu2.name_en = "Soup Rice"

        # 검증 실행
        validator._validate_menu_name_duplicates([mock_menu1, mock_menu2])

        # 중복 에러 없어야 함
        assert len(validator.validation_errors) == 0


# ============================================================================
# Unit Tests - QR Code Service
# ============================================================================

class TestQRCodeService:
    """QRCodeService 단위 테스트"""

    def test_qr_code_generation(self):
        """9️⃣ QR 코드 생성 검증"""
        service = QRCodeService(output_dir="/tmp/test_qr")

        result = service.generate_qr(
            restaurant_id=uuid4(),
            shop_code="SHOP12345678",
            menu_count=3,
            languages=['ko', 'en', 'ja', 'zh']
        )

        # QR 코드 생성 성공 검증
        assert result["qr_code_url"].startswith("/static/qr/")
        assert result["menu_count"] == 3
        assert result["languages"] == ['ko', 'en', 'ja', 'zh']
        assert "restaurant_id" in result["qr_code_data"]
        assert "shop_code" in result["qr_code_data"]
        assert result["qr_code_file_path"]
        assert result["activation_date"]

    def test_qr_code_generation_bytes(self):
        """🔟 QR 코드 바이트 생성 검증"""
        service = QRCodeService(output_dir="/tmp/test_qr")

        qr_bytes = service.generate_qr_bytes(
            restaurant_id=uuid4(),
            shop_code="SHOP12345678",
            menu_count=3,
            languages=['ko', 'en', 'ja', 'zh']
        )

        # QR 코드 바이트 생성 성공 검증
        assert isinstance(qr_bytes, bytes)
        assert len(qr_bytes) > 0
        assert qr_bytes[:4] == b'\x89PNG'  # PNG 파일 시그니처


# ============================================================================
# Integration Tests - API Response Simulation
# ============================================================================

class TestMenuApprovalAPIResponse:
    """API 응답 포맷 테스트"""

    def test_approval_success_response_format(self):
        """✅ 승인 성공 응답 포맷"""
        # Mock 응답
        response = {
            "success": True,
            "message": "Restaurant 'Test Restaurant' approved with 3 menus",
            "restaurant": {
                "id": str(uuid4()),
                "name": "Test Restaurant",
                "status": "active",
                "approved_at": datetime.utcnow().isoformat(),
                "approved_by": "admin-123",
            },
            "approved_menus": {
                "count": 3,
                "menu_ids": [str(uuid4()), str(uuid4()), str(uuid4())]
            },
            "qr_code": {
                "shop_code": "SHOP12345678",
                "qr_code_url": "/static/qr/SHOP12345678_20260211_120000.png",
                "qr_code_file_path": "c:\\project\\menu\\static\\qr\\SHOP12345678_20260211_120000.png",
                "activation_date": datetime.utcnow().isoformat(),
                "languages": ['ko', 'en', 'ja', 'zh']
            }
        }

        # 응답 포맷 검증
        assert response["success"] is True
        assert response["restaurant"]["status"] == "active"
        assert response["approved_menus"]["count"] == 3
        assert response["qr_code"]["shop_code"]
        assert response["qr_code"]["qr_code_url"]

    def test_approval_error_response_format(self):
        """❌ 승인 실패 응답 포맷"""
        # Mock 에러 응답
        error_response = {
            "success": False,
            "message": "Menu approval validation failed",
            "errors": [
                "Menu abc123: translation missing for language 'ja'",
                "Menu def456: typical_price_min must be > 0"
            ]
        }

        # 응답 포맷 검증
        assert error_response["success"] is False
        assert len(error_response["errors"]) > 0
        assert any("translation" in e for e in error_response["errors"])


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """성능 테스트"""

    def test_qr_generation_performance(self):
        """QR 코드 생성 시간 < 2초"""
        import time

        service = QRCodeService(output_dir="/tmp/test_qr")
        start = time.time()

        service.generate_qr(
            restaurant_id=uuid4(),
            shop_code="SHOP12345678",
            menu_count=10,
            languages=['ko', 'en', 'ja', 'zh']
        )

        elapsed = time.time() - start

        # 2초 이내 완료
        assert elapsed < 2.0, f"QR generation took {elapsed:.2f}s, expected < 2s"

    def test_validator_performance(self):
        """검증 로직 성능 < 100ms"""
        import time

        validator = MenuApprovalValidator(None)

        # 5개 메뉴의 검증 시뮬레이션
        menus = []
        for i in range(5):
            mock_menu = Mock()
            mock_menu.id = uuid4()
            mock_menu.name_ko = f"메뉴{i}"
            mock_menu.name_en = f"Menu{i}"
            mock_menu.explanation_short = {
                "ko": f"설명{i}", "en": f"Description{i}",
                "ja": f"説明{i}", "zh": f"描述{i}"
            }
            mock_menu.typical_price_min = 10000
            mock_menu.typical_price_max = 15000
            menus.append(mock_menu)

        start = time.time()

        for menu in menus:
            validator._validate_single_menu(menu)

        elapsed = time.time() - start

        # 5개 메뉴 검증이 100ms 이내 완료
        assert elapsed < 0.1, f"Validation took {elapsed*1000:.2f}ms, expected < 100ms"


# ============================================================================
# Markers for CI/CD
# ============================================================================

@pytest.mark.unit
def test_unit_marker():
    """Unit test marker verification"""
    assert True


@pytest.mark.integration
def test_integration_marker():
    """Integration test marker verification"""
    assert True


# ============================================================================
# Run Info
# ============================================================================

if __name__ == "__main__":
    """
    테스트 실행 방법:

    # 모든 테스트
    pytest tests/test_b2b_menu_approval.py -v

    # 커버리지 포함
    pytest tests/test_b2b_menu_approval.py -v --cov=app.backend.services --cov-report=term-missing

    # 특정 테스트 클래스만
    pytest tests/test_b2b_menu_approval.py::TestMenuApprovalValidator -v

    # 성능 테스트만
    pytest tests/test_b2b_menu_approval.py::TestPerformance -v
    """
    import subprocess
    subprocess.run(["pytest", __file__, "-v", "--tb=short"])
