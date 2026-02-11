# P1 Issue: Translation Data Completion Guide

**Status**: 🟡 Papago API Required
**Priority**: P1 (High)
**Estimated Time**: 2-3 hours
**Target**: I18n Score 50% → 95%

---

## 📋 Current Status

| Language | Keys | Completion |
|----------|------|------------|
| Korean (KO) | 560 | 100% ✅ |
| English (EN) | 560 | 100% ✅ |
| Japanese (JA) | 0 | 0% ❌ |
| Chinese (ZH) | 0 | 0% ❌ |

**Problem**: 560 menu explanation keys missing JA/ZH translations

---

## 🎯 Solution: Papago Batch Translation

### Step 1: Get Papago API Credentials

1. Go to [Naver Cloud Platform](https://www.ncloud.com/)
2. Sign up / Log in
3. Navigate to **AI·NAVER API** → **Papago NMT**
4. Create application and get credentials:
   - Client ID
   - Client Secret

### Step 2: Configure Environment

Add to `.env` file:

```bash
# Papago Translation API
PAPAGO_CLIENT_ID=your_client_id_here
PAPAGO_CLIENT_SECRET=your_client_secret_here
```

### Step 3: Fix SQLAlchemy Model Issue

**Problem**: MenuVariant has ambiguous foreign keys to CanonicalMenu

**File**: `app/backend/models/menu_variant.py`

**Fix**: Specify `foreign_keys` in relationship

```python
# BEFORE (line 54)
canonical_menu = relationship("CanonicalMenu", backref="variants")

# AFTER
canonical_menu = relationship(
    "CanonicalMenu",
    foreign_keys=[canonical_menu_id],  # Specify which FK to use
    backref="variants"
)
```

### Step 4: Run Batch Translation

**Option A: Using Papago API (Production)**

```bash
python -X utf8 scripts/batch_translate_papago.py
```

Expected output:
```
🌍 Papago Batch Translation - Menu Knowledge Engine
✅ Papago API credentials found

📊 Found 560 canonical menus to translate

[1/560] 김치찌개 (Kimchi Stew)
  🇯🇵 Translating to Japanese... ✅ キムチチゲ
  🇨🇳 Translating to Chinese... ✅ 泡菜汤

...

✅ Completion: 1120/1120 (100.0%)
```

**Option B: Mock Translation (Development Only)**

For testing data structure without API:

```bash
python -X utf8 scripts/batch_translate_mock.py
```

⚠️ This creates `[JA] ...` and `[ZH] ...` prefixed translations for development.

---

## 🔍 Verification

### Check translation completeness:

```sql
-- Count translations per language
SELECT
  COUNT(*) FILTER (WHERE explanation_short->>'en' IS NOT NULL) as en_count,
  COUNT(*) FILTER (WHERE explanation_short->>'ja' IS NOT NULL) as ja_count,
  COUNT(*) FILTER (WHERE explanation_short->>'zh' IS NOT NULL) as zh_count
FROM canonical_menus;
```

Expected result:
```
en_count | ja_count | zh_count
---------|----------|---------
   560   |   560    |   560
```

### Sample translated record:

```sql
SELECT
  name_ko,
  name_en,
  explanation_short
FROM canonical_menus
WHERE name_ko = '김치찌개';
```

Expected result:
```json
{
  "en": "A spicy Korean stew made with kimchi, tofu, and pork",
  "ja": "キムチ、豆腐、豚肉で作る韓国の辛い鍋料理",
  "zh": "用泡菜、豆腐和猪肉制作的韩国辣汤"
}
```

---

## 🚀 Alternative: Direct SQL Update (Manual)

If Papago API is not available, you can update translations manually:

```sql
-- Example: Update single menu
UPDATE canonical_menus
SET explanation_short = jsonb_set(
  jsonb_set(
    explanation_short,
    '{ja}',
    '"キムチ、豆腐、豚肉で作る韓国の辛い鍋料理"'
  ),
  '{zh}',
  '"用泡菜、豆腐和猪肉制作的韩国辣汤"'
)
WHERE name_ko = '김치찌개';
```

⚠️ Not recommended for 560 keys - use Papago API instead.

---

## 📊 Cost Estimate (Papago API)

- **Papago NMT Pricing**: ₩10 per 1,000 characters (approximate)
- **Average explanation**: 50-100 characters
- **Total characters**: 560 keys × 75 chars avg × 2 languages = 84,000 chars
- **Estimated cost**: ₩840 (less than $1 USD)

**One-time cost, permanent benefit**

---

## ✅ Acceptance Criteria

- [ ] Papago API credentials configured
- [ ] SQLAlchemy model ambiguity fixed
- [ ] Batch translation script executed successfully
- [ ] All 560 menus have JA translations
- [ ] All 560 menus have ZH translations
- [ ] SQL verification query shows 100% completion
- [ ] QR Menu page JA/ZH buttons work correctly
- [ ] I18n score: 50% → 95%

---

## 🔧 Troubleshooting

### Issue: "Papago API credentials not configured"

**Solution**: Check `.env` file has correct credentials

```bash
grep PAPAGO .env
```

### Issue: "AmbiguousForeignKeysError"

**Solution**: Apply fix in Step 3 (menu_variant.py relationship)

### Issue: "Rate limit exceeded"

**Solution**: Add delay between API calls

```python
# In batch_translate_papago.py, add:
import time
time.sleep(0.1)  # 100ms delay between calls
```

---

## 📁 Related Files

- `scripts/batch_translate_papago.py` - Production translation script
- `scripts/batch_translate_mock.py` - Development mock script
- `app/backend/services/translation_service.py` - Papago API wrapper
- `app/backend/models/menu_variant.py` - Model needing fix
- `.env` - Environment variables

---

**Created**: 2026-02-12
**Status**: Ready for execution (Papago API required)
**Next Step**: Get Papago API credentials or use mock for development
