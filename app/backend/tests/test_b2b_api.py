"""
B2B API Tests - Restaurant Registration and Management

Tests Sprint 4 Task 1.1 endpoints:
- POST /api/v1/b2b/restaurants - Register restaurant
- GET /api/v1/b2b/restaurants/{id} - Get restaurant info
- POST /api/v1/b2b/restaurants/{id}/approve - Approve/reject restaurant
- GET /api/v1/b2b/restaurants - List restaurants with filters
"""

import asyncio
import httpx
import pytest
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

# Integration test requiring a live server on localhost:8000
pytestmark = pytest.mark.skip(
    reason="Integration test: requires live server on localhost:8000"
)

BASE_URL = "http://localhost:8000"


class TestResults:
    """Test results tracker"""

    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.restaurant_id: Optional[str] = None

    def add_pass(self, test_name: str):
        self.total += 1
        self.passed += 1
        print(f"  [PASS] {test_name}")

    def add_fail(self, test_name: str, reason: str):
        self.total += 1
        self.failed += 1
        print(f"  [FAIL] {test_name}")
        print(f"    Reason: {reason}")

    def summary(self):
        print(f"\n{'=' * 60}")
        print(f"Test Results: {self.passed}/{self.total} passed")
        if self.failed > 0:
            print(f"  [WARNING] {self.failed} tests failed")
        else:
            print("  [OK] All tests passed!")
        print(f"{'=' * 60}\n")


async def test_b2b_api():
    """Test B2B Restaurant API endpoints"""
    results = TestResults()
    async with httpx.AsyncClient(timeout=30.0) as client:
        # ===========================
        # Test 1: Register Restaurant
        # ===========================
        print("\n[Test 1] POST /api/v1/b2b/restaurants - Register restaurant")
        try:
            payload = {
                "name": "강남 한정식",
                "name_en": "Gangnam Korean Cuisine",
                "owner_name": "김철수",
                "owner_phone": "010-1234-5678",
                "owner_email": "test@example.com",
                "address": "서울시 강남구 테헤란로 123",
                "address_detail": "101호",
                "postal_code": "06234",
                "business_license": "TEST-2026-001",
                "business_type": "Korean",
            }

            response = await client.post(
                f"{BASE_URL}/api/v1/b2b/restaurants", json=payload
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("restaurant_id"):
                    results.restaurant_id = data["restaurant_id"]
                    results.add_pass("Restaurant registration successful")

                    if data.get("status") == "pending_approval":
                        results.add_pass("Default status is pending_approval")
                    else:
                        results.add_fail(
                            "Default status check",
                            f"Expected pending_approval, got {data.get('status')}",
                        )

                    if "approval_url" in data:
                        results.add_pass("Approval URL provided")
                    else:
                        results.add_fail(
                            "Approval URL check", "approval_url not in response"
                        )
                else:
                    results.add_fail(
                        "Registration response format",
                        f"Missing success or restaurant_id: {data}",
                    )
            else:
                results.add_fail(
                    "Restaurant registration",
                    f"Status code: {response.status_code}, Body: {response.text}",
                )

        except Exception as e:
            results.add_fail("Restaurant registration", f"Exception: {str(e)}")

        # ===========================
        # Test 2: Duplicate Business License
        # ===========================
        print(
            "\n[Test 2] POST /api/v1/b2b/restaurants - Duplicate business license should fail"
        )
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/b2b/restaurants", json=payload
            )

            if response.status_code == 400:
                results.add_pass("Duplicate business license rejected (400)")
            else:
                results.add_fail(
                    "Duplicate check", f"Expected 400, got {response.status_code}"
                )

        except Exception as e:
            results.add_fail("Duplicate check", f"Exception: {str(e)}")

        # ===========================
        # Test 3: Get Restaurant Info
        # ===========================
        if results.restaurant_id:
            print(
                f"\n[Test 3] GET /api/v1/b2b/restaurants/{results.restaurant_id} - Get restaurant info"
            )
            try:
                response = await client.get(
                    f"{BASE_URL}/api/v1/b2b/restaurants/{results.restaurant_id}"
                )

                if response.status_code == 200:
                    data = response.json()

                    if data.get("id") == results.restaurant_id:
                        results.add_pass("Restaurant ID matches")
                    else:
                        results.add_fail(
                            "Restaurant ID check",
                            f"Expected {results.restaurant_id}, got {data.get('id')}",
                        )

                    if data.get("name") == payload["name"]:
                        results.add_pass("Restaurant name matches")
                    else:
                        results.add_fail(
                            "Restaurant name check",
                            f"Expected {payload['name']}, got {data.get('name')}",
                        )

                    if data.get("business_license") == payload["business_license"]:
                        results.add_pass("Business license matches")
                    else:
                        results.add_fail(
                            "Business license check",
                            f"Expected {payload['business_license']}, got {data.get('business_license')}",
                        )

                else:
                    results.add_fail(
                        "Get restaurant info", f"Status code: {response.status_code}"
                    )

            except Exception as e:
                results.add_fail("Get restaurant info", f"Exception: {str(e)}")

        # ===========================
        # Test 4: List Restaurants
        # ===========================
        print("\n[Test 4] GET /api/v1/b2b/restaurants - List all restaurants")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/b2b/restaurants")

            if response.status_code == 200:
                data = response.json()

                if "total" in data and "data" in data:
                    results.add_pass("List response format valid")

                    if data["total"] > 0:
                        results.add_pass(f"Found {data['total']} restaurants")
                    else:
                        results.add_fail(
                            "Restaurant count", "Expected at least 1 restaurant"
                        )

                else:
                    results.add_fail(
                        "List response format", f"Missing total or data: {data}"
                    )

            else:
                results.add_fail(
                    "List restaurants", f"Status code: {response.status_code}"
                )

        except Exception as e:
            results.add_fail("List restaurants", f"Exception: {str(e)}")

        # ===========================
        # Test 5: Filter by Status
        # ===========================
        print(
            "\n[Test 5] GET /api/v1/b2b/restaurants?status=pending_approval - Filter by status"
        )
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/b2b/restaurants?status=pending_approval"
            )

            if response.status_code == 200:
                data = response.json()

                all_pending = all(
                    r["status"] == "pending_approval" for r in data.get("data", [])
                )
                if all_pending:
                    results.add_pass("Status filter works correctly")
                else:
                    results.add_fail(
                        "Status filter", "Some restaurants have different status"
                    )

            else:
                results.add_fail(
                    "Filter by status", f"Status code: {response.status_code}"
                )

        except Exception as e:
            results.add_fail("Filter by status", f"Exception: {str(e)}")

        # ===========================
        # Test 6: Approve Restaurant
        # ===========================
        if results.restaurant_id:
            print(
                f"\n[Test 6] POST /api/v1/b2b/restaurants/{results.restaurant_id}/approve - Approve restaurant"
            )
            try:
                approve_payload = {
                    "action": "approve",
                    "admin_user_id": "test_admin_001",
                }

                response = await client.post(
                    f"{BASE_URL}/api/v1/b2b/restaurants/{results.restaurant_id}/approve",
                    json=approve_payload,
                )

                if response.status_code == 200:
                    data = response.json()

                    if data.get("success"):
                        results.add_pass("Approval request successful")

                        if data.get("status") == "active":
                            results.add_pass("Status changed to active")
                        else:
                            results.add_fail(
                                "Status after approval",
                                f"Expected active, got {data.get('status')}",
                            )

                    else:
                        results.add_fail("Approval response", f"success=False: {data}")

                else:
                    results.add_fail(
                        "Approve restaurant", f"Status code: {response.status_code}"
                    )

            except Exception as e:
                results.add_fail("Approve restaurant", f"Exception: {str(e)}")

        # ===========================
        # Test 7: Verify Status Change
        # ===========================
        if results.restaurant_id:
            print("\n[Test 7] Verify status changed to active")
            try:
                response = await client.get(
                    f"{BASE_URL}/api/v1/b2b/restaurants/{results.restaurant_id}"
                )

                if response.status_code == 200:
                    data = response.json()

                    if data.get("status") == "active":
                        results.add_pass("Status is active after approval")
                    else:
                        results.add_fail(
                            "Status verification",
                            f"Expected active, got {data.get('status')}",
                        )

                    if data.get("approved_at"):
                        results.add_pass("approved_at timestamp set")
                    else:
                        results.add_fail("approved_at check", "approved_at is null")

                    if data.get("approved_by") == "test_admin_001":
                        results.add_pass("approved_by set correctly")
                    else:
                        results.add_fail(
                            "approved_by check",
                            f"Expected test_admin_001, got {data.get('approved_by')}",
                        )

            except Exception as e:
                results.add_fail("Verify status change", f"Exception: {str(e)}")

        # ===========================
        # Test 8: Reject Restaurant
        # ===========================
        print("\n[Test 8] POST /api/v1/b2b/restaurants - Register and reject")
        try:
            # Register new restaurant
            reject_payload = {
                "name": "테스트 음식점",
                "owner_name": "홍길동",
                "owner_phone": "010-9999-8888",
                "address": "서울시 종로구 종로 1",
                "business_license": "TEST-2026-002",
                "business_type": "Korean",
            }

            response = await client.post(
                f"{BASE_URL}/api/v1/b2b/restaurants", json=reject_payload
            )

            if response.status_code == 200:
                reject_id = response.json().get("restaurant_id")

                # Reject it
                reject_request = {
                    "action": "reject",
                    "admin_user_id": "test_admin_002",
                    "rejection_reason": "사업자 등록증 불일치",
                }

                response = await client.post(
                    f"{BASE_URL}/api/v1/b2b/restaurants/{reject_id}/approve",
                    json=reject_request,
                )

                if response.status_code == 200:
                    data = response.json()

                    if data.get("status") == "rejected":
                        results.add_pass("Restaurant rejected successfully")
                    else:
                        results.add_fail(
                            "Rejection status",
                            f"Expected rejected, got {data.get('status')}",
                        )

                    # Verify rejection
                    response = await client.get(
                        f"{BASE_URL}/api/v1/b2b/restaurants/{reject_id}"
                    )
                    data = response.json()

                    if (
                        data.get("rejection_reason")
                        == reject_request["rejection_reason"]
                    ):
                        results.add_pass("Rejection reason saved correctly")
                    else:
                        results.add_fail(
                            "Rejection reason",
                            f"Expected '{reject_request['rejection_reason']}', got '{data.get('rejection_reason')}'",
                        )

                else:
                    results.add_fail(
                        "Reject restaurant", f"Status code: {response.status_code}"
                    )

        except Exception as e:
            results.add_fail("Reject restaurant", f"Exception: {str(e)}")

        # ===========================
        # Test 9: Invalid Action
        # ===========================
        if results.restaurant_id:
            print(
                f"\n[Test 9] POST /api/v1/b2b/restaurants/{results.restaurant_id}/approve - Invalid action should fail"
            )
            try:
                invalid_payload = {
                    "action": "invalid_action",
                    "admin_user_id": "test_admin",
                }

                response = await client.post(
                    f"{BASE_URL}/api/v1/b2b/restaurants/{results.restaurant_id}/approve",
                    json=invalid_payload,
                )

                if response.status_code == 400:
                    results.add_pass("Invalid action rejected (400)")
                else:
                    results.add_fail(
                        "Invalid action check",
                        f"Expected 400, got {response.status_code}",
                    )

            except Exception as e:
                results.add_fail("Invalid action check", f"Exception: {str(e)}")

        # ===========================
        # Test 10: Pagination
        # ===========================
        print("\n[Test 10] GET /api/v1/b2b/restaurants?limit=1&offset=0 - Pagination")
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/b2b/restaurants?limit=1&offset=0"
            )

            if response.status_code == 200:
                data = response.json()

                if len(data.get("data", [])) <= 1:
                    results.add_pass("Pagination limit works")

                    if data.get("limit") == 1 and data.get("offset") == 0:
                        results.add_pass("Pagination metadata correct")
                    else:
                        results.add_fail(
                            "Pagination metadata",
                            f"limit={data.get('limit')}, offset={data.get('offset')}",
                        )

                else:
                    results.add_fail(
                        "Pagination limit",
                        f"Expected 1 item, got {len(data.get('data', []))}",
                    )

            else:
                results.add_fail("Pagination", f"Status code: {response.status_code}")

        except Exception as e:
            results.add_fail("Pagination", f"Exception: {str(e)}")

    # Print summary
    results.summary()
    return results.passed == results.total


if __name__ == "__main__":
    print("=" * 60)
    print("B2B API Test Suite - Sprint 4 Task 1.1")
    print("=" * 60)
    print("\nStarting tests...")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("")

    success = asyncio.run(test_b2b_api())

    if success:
        print("[DONE] All B2B API tests passed!")
        sys.exit(0)
    else:
        print("[WARNING] Some tests failed. Check logs above.")
        sys.exit(1)
