# 🎯 Task 1.3: B2B 메뉴 확정 승인 API

**작업 코드**: P1-1.3
**담당**: Backend-2
**소요시간**: 1일
**우선순위**: 🔴 HIGH
**일정**: Day 3 (2026-02-12)

---

## 📋 작업 개요

식당에서 업로드한 메뉴를 최종 검증 후 확정하는 API

**플로우:**
```
식당 메뉴 선택
    ↓
POST /api/v1/b2b/restaurants/{id}/approve
    ↓
최종 데이터 검증 (모든 메뉴 번역 완료?)
    ↓
QR 코드 생성 (Shop QR 코드)
    ↓
식당 상태 변경: pending_approval → active
    ↓
응답: {"status": "active", "menu_count": 42, "qr_code": "..."}
```

---

## 🔧 구현 요구사항

### 1️⃣ API 엔드포인트

**Route**: `POST /api/v1/b2b/restaurants/{restaurant_id}/approve`

**Request:**
```json
{
  "admin_user_id": "admin-123",
  "selected_menu_ids": ["uuid1", "uuid2", ...]  // 승인할 메뉴 선택
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "restaurant_id": "uuid",
  "restaurant_name": "강남 한정식",
  "status": "active",
  "menu_count": 42,
  "menu_language_coverage": {
    "ko": 42,
    "en": 42,
    "ja": 42,
    "zh": 42
  },
  "qr_code": {
    "url": "https://cdn.example.com/qr/uuid.png",
    "shop_code": "SHOP-001",
    "activation_date": "2026-02-12T10:00:00Z"
  },
  "approval_details": {
    "approved_at": "2026-02-12T10:00:00Z",
    "approved_by": "admin-123",
    "total_menus_approved": 42
  }
}
```

**Response (Error - 400/404/409):**
```json
{
  "success": false,
  "error": "Incomplete translations or validation failed",
  "details": {
    "incomplete_languages": ["ja", "zh"],
    "menu_validation_errors": ["menu-uuid: missing description"]
  }
}
```

---

### 2️⃣ 검증 로직

**승인 전 필수 체크:**

```python
class MenuApprovalValidator:
    async def validate_approval(
        self,
        restaurant_id: UUID,
        selected_menu_ids: List[UUID],
        db: AsyncSession
    ) -> ValidationResult:
        """
        1. 식당 존재 확인
        2. 식당 상태 확인 (pending_approval만 가능)
        3. 선택된 메뉴 존재 확인
        4. 번역 완료 확인 (KO, EN, JA, ZH 모두 필수)
        5. 메뉴 설명 및 가격 검증
        6. 중복 메뉴 확인
        """
```

**체크리스트:**
- [ ] Restaurant 상태: pending_approval인가?
- [ ] 최소 1개 이상의 메뉴 선택됨?
- [ ] 모든 선택된 메뉴의 번역 완료?
  - KO: ✅
  - EN: ✅
  - JA: ✅
  - ZH: ✅
- [ ] 모든 메뉴의 필수 필드 존재?
  - name_ko
  - name_en
  - explanation_short (모든 언어)
  - category
- [ ] price > 0?
- [ ] 메뉴 이름 중복 없음?

---

### 3️⃣ QR 코드 생성

**QR 코드 포함 정보:**
```python
qr_data = {
    "restaurant_id": str(restaurant_id),
    "shop_code": "SHOP-{restaurant_id[:6]}",
    "activation_date": datetime.now().isoformat(),
    "menu_count": len(selected_menus),
    "languages": ["ko", "en", "ja", "zh"],
    "qr_url": f"https://example.com/qr/{restaurant_id}"
}

# QR 코드 생성 (python-qrcode)
import qrcode
qr = qrcode.QRCode()
qr.add_data(json.dumps(qr_data))
qr.make()
img = qr.make_image()
# → AWS S3 또는 CDN에 저장
```

**생성 파일:**
- `app/backend/services/qr_code_service.py`

---

### 4️⃣ DB 업데이트

**Restaurant 모델 업데이트:**
```python
restaurant.status = RestaurantStatus.active
restaurant.approved_at = datetime.now(timezone.utc)
restaurant.approved_by = admin_user_id
db.commit()
```

**MenuUploadTask 업데이트:**
```python
upload_task.status = "approved"
upload_task.completed_at = datetime.now(timezone.utc)
db.commit()
```

---

## 📁 생성할 파일

| 파일 | 설명 |
|------|------|
| `services/qr_code_service.py` | QR 코드 생성 서비스 |
| `services/menu_approval_service.py` | 메뉴 승인 검증 로직 |
| `tests/test_b2b_menu_approval.py` | 단위 테스트 (10개 케이스) |

---

## 🧪 테스트 케이스

```python
# tests/test_b2b_menu_approval.py

async def test_approve_menus_success():
    """모든 조건 충족 - 승인 성공"""

async def test_approve_incomplete_translations():
    """번역 미완료 - 거부"""

async def test_approve_missing_menus():
    """메뉴 누락 - 거부"""

async def test_approve_invalid_restaurant_status():
    """식당 상태 오류 - 거부"""

async def test_qr_code_generation():
    """QR 코드 생성 검증"""

async def test_restaurant_status_change():
    """식당 상태 변경 확인"""

async def test_duplicate_approval_prevention():
    """중복 승인 방지"""

async def test_partial_menu_selection():
    """일부 메뉴만 선택 승인"""

async def test_approval_audit_log():
    """승인 이력 기록"""

async def test_error_handling():
    """다양한 오류 처리"""
```

---

## ✅ 완료 기준

```
필수:
☐ MenuApprovalValidator 구현
☐ QR 코드 서비스 구현
☐ POST /api/v1/b2b/restaurants/{id}/approve 엔드포인트
☐ 전체 검증 로직 완료
☐ DB 상태 변경 확인

테스트:
☐ 10개 테스트 케이스 작성
☐ 모든 테스트 통과
☐ 커버리지 > 80%

성능:
☐ API 응답 < 500ms
☐ QR 코드 생성 < 2초

품질:
☐ 코드 리뷰 통과 (2명 승인)
☐ 오류 처리 완벽
☐ 문서 작성 완료
```

---

## 🎯 Git 명령

```bash
# 1. 새 브랜치 생성
cd c:\project\menu
git checkout -b feature/task-1.3-menu-approval

# 2. 작업 후 커밋
git add app/backend/
git commit -m "feat: Task 1.3 - B2B Menu Approval API (QR generation + validation)"

# 3. 푸시
git push -u origin feature/task-1.3-menu-approval
```

---

## 📞 의존성

- ✅ Task 1.1: Restaurant 모델 (완료)
- ✅ Task 1.2: 메뉴 업로드 (완료)
- 🔄 QR 코드 라이브러리: `python-qrcode`

```bash
pip install python-qrcode[pil]
```

---

## 💡 팁

1. **QR 코드 저장 위치**: AWS S3 또는 로컬 static 폴더
2. **오류 처리**: 검증 실패 시 명확한 오류 메시지
3. **감사 로그**: 승인 이력 기록 (누가, 언제, 뭘 승인?)
4. **멱등성**: 중복 요청 처리

---

**시작할 준비가 되셨나요? 🚀**

