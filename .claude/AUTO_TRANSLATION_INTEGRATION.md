# 🔄 자동 번역 통합 가이드

**목적**: 새로운 메뉴 추가 시 **자동으로 일본어/중국어 번역** 생성
**기술**: GPT-4o (AsyncIO 기반 백그라운드 작업)
**비용**: 메뉴당 ~₩50 (매우 저렴)

---

## 🎯 동작 흐름

```
사용자가 새 메뉴 등록
    ↓
Admin API (POST /api/v1/canonical-menus)
    ↓
CanonicalMenu DB 저장 (영문)
    ↓
자동 번역 트리거 (백그라운드)
    ↓
GPT-4o 호출 (JA/ZH 생성)
    ↓
DB 업데이트 (JSONB)
    ↓
완료 (사용자에게 즉시 응답, 번역은 2-3초 후)
```

---

## 📝 Step 1: Admin API 수정

**파일**: `app/backend/api/admin.py`

### 현재 코드 (수정 전)

```python
@router.post("/api/v1/admin/canonical-menus")
async def create_canonical_menu(
    menu_data: CanonicalMenuCreate,
    db: Session = Depends(get_db)
):
    # 메뉴 생성만 함
    menu = CanonicalMenu(...)
    db.add(menu)
    db.commit()
    return {"id": menu.id}
```

### 수정된 코드 (자동 번역 추가)

```python
import asyncio
from services.auto_translate_service import auto_translate_service

@router.post("/api/v1/admin/canonical-menus")
async def create_canonical_menu(
    menu_data: CanonicalMenuCreate,
    db: Session = Depends(get_db)
):
    """
    새 canonical 메뉴 생성 + 자동 번역

    요청:
    {
        "name_ko": "김치찌개",
        "name_en": "Kimchi Stew",
        "explanation_short_en": "Spicy fermented cabbage stew..."
    }

    응답:
    {
        "id": "uuid",
        "message": "메뉴 생성 완료. 자동 번역 진행 중..."
    }
    """

    # 1️⃣ 메뉴 생성
    menu = CanonicalMenu(
        name_ko=menu_data.name_ko,
        name_en=menu_data.name_en,
        explanation_short={
            "en": menu_data.explanation_short_en
        }
    )
    db.add(menu)
    db.commit()

    # 2️⃣ 자동 번역 트리거 (백그라운드)
    # 사용자는 즉시 응답받음, 번역은 2-3초 후 완료
    asyncio.create_task(
        auto_translate_service.auto_translate_new_menu(
            menu_id=menu.id,
            menu_name_ko=menu.name_ko,
            description_en=menu_data.explanation_short_en,
            db=db
        )
    )

    return {
        "id": str(menu.id),
        "message": "메뉴 생성 완료. 일본어/중국어 자동 번역 진행 중...",
        "status": "auto_translating"
    }
```

---

## 🛠️ Step 2: 스크립트에서 사용

**초기 배치 번역** (기존 메뉴)

```bash
# 한 번만 실행
python scripts/translate_canonical_menus_gpt4o.py --language ja,zh
```

**향후 자동 번역** (새 메뉴)

```
Admin Dashboard에서 새 메뉴 등록
→ 자동으로 JA/ZH 생성
→ 2-3초 후 DB 업데이트
→ 완료!
```

---

## ✅ 통합 체크리스트

### 구현 (개발팀)
- [ ] `auto_translate_service.py` 복사
  ```bash
  cp services/auto_translate_service.py app/backend/services/
  ```

- [ ] Admin API 수정 (위 코드 참고)
  ```python
  # app/backend/api/admin.py 수정
  import asyncio
  from services.auto_translate_service import auto_translate_service
  ```

- [ ] 테스트
  ```bash
  # Admin Dashboard에서 새 메뉴 추가
  # DB에서 JA/ZH 생성 확인
  ```

### 검증
- [ ] 새 메뉴 추가 API 호출 (POSTman/UI)
- [ ] 응답 확인 ("auto_translating" 상태)
- [ ] 2-3초 대기
- [ ] DB에서 JA/ZH 데이터 확인
- [ ] UI에서 언어 탭 동작 확인

---

## 📊 비용 분석

| 상황 | 비용 | 설명 |
|------|------|------|
| **초기 배치** (112개) | ~₩5,600 | 일회성 |
| **월 신규 (10개)** | ~₩500 | 자동 |
| **연간** | ~₩11,000 | 매우 저렴 |

---

## 🎯 성공 기준

✅ **배치 번역 완료**
- 112개 메뉴 × 2언어 번역 완료
- B2C/QR 페이지에서 EN/JA/ZH 모두 동작

✅ **자동 번역 통합**
- Admin에서 새 메뉴 추가 가능
- 자동으로 JA/ZH 생성
- 2-3초 이내 완료

✅ **프로덕션 준비**
- 비용 최적화 (Papago 대비 93% 절감)
- 운영 효율성 (수동 작업 제거)

---

## 🚀 다음 단계

1. ✅ API 키 등록 (완료)
2. ⏳ **배치 번역 실행**
3. ⏳ 자동 번역 통합 (Admin API 수정)
4. ⏳ 최종 배포

---

**준비 완료! Step 3로 진행하세요.** 🎯
