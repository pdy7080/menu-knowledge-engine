# Translation Service - P1-2

## 개요

Papago API를 사용한 다국어 번역 서비스입니다.

## 사용법

```python
from services.translation_service import translation_service

# 단일 번역
description_en = "Spicy stew made with kimchi and pork"
ja_text = translation_service.translate(description_en, "en", "ja")
zh_text = translation_service.translate(description_en, "en", "zh-CN")

# 메뉴 설명 자동 번역 (영문 → 일/중)
multi_lang = translation_service.translate_menu_description(description_en)
# Returns: {"en": "...", "ja": "...", "zh": "..."}
```

## 환경 변수

`.env` 파일에 Papago API 키 설정:

```
PAPAGO_CLIENT_ID=your_client_id
PAPAGO_CLIENT_SECRET=your_client_secret
```

## Canonical 메뉴 생성 시 자동 번역

새로운 canonical 메뉴를 생성할 때 자동으로 일/중 번역을 추가합니다:

```python
# Before (영문만)
canonical.explanation_short = {
    "en": "Spicy stew made with kimchi and pork"
}

# After (일/중 자동 추가)
canonical.explanation_short = {
    "en": "Spicy stew made with kimchi and pork",
    "ja": "キムチと豚肉で作った辛いシチュー",
    "zh": "用泡菜和猪肉做的辣汤"
}
```

## B2C 프론트엔드 연동 (예정)

향후 B2C 프론트엔드에 언어 전환 탭 추가:

```javascript
// 언어 선택
const currentLang = 'en';  // 'en', 'ja', 'zh'

// API 응답의 explanation_short[currentLang] 표시
const description = menuData.explanation_short[currentLang];
```

## 지원 언어

- **한국어** (ko)
- **English** (en)
- **日本語** (ja)
- **中文(简体)** (zh-CN)
- **中文(繁體)** (zh-TW)
