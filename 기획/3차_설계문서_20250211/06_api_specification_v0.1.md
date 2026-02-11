# 06. API Specification v0.1 — Menu Knowledge Engine 엔드포인트

> **이 문서는 03_data_schema에서 자동으로 도출된다.**  
> 스키마가 바뀌면 이 문서도 바뀐다.

---

## 0. 설계 원칙

- **RESTful** — 리소스 중심 URL, 표준 HTTP 메서드
- **버전닝** — `/api/v1/` 접두사
- **인증** — MVP는 API key 방식 (B2B: 식당별, B2C: 불필요 또는 익명 세션)
- **응답 형식** — JSON, UTF-8
- **에러** — 표준 HTTP 상태코드 + `{ "error": { "code": "...", "message": "..." } }`

---

## 1. 핵심 API — Menu Recognition Pipeline

### 1-1. `POST /api/v1/menu/recognize`

**목적:** 메뉴판 이미지 → OCR → 메뉴명 리스트 추출

> **클라이언트 카메라 방식:** 파일 업로드 기반 (`<input type="file" accept="image/*" capture="environment">`)
> getUserMedia 라이브뷰가 아닌, 폰 기본 카메라 앱이 열리는 방식. iOS Safari/Chrome 완전 호환.

```
Request:
  Content-Type: multipart/form-data
  Body:
    image: <file>              (필수) 메뉴판 사진 (JPEG/PNG, 최대 10MB)
    shop_id: UUID              (선택) 등록된 식당이면
    source: "b2b" | "b2c"      (필수)

Response 200:
{
  "request_id": "req_abc123",
  "ocr_raw_text": "할머니뼈해장국 9,000\n얼큰순두부찌개 8,000\n...",
  "extracted_items": [
    {
      "text_ko": "할머니뼈해장국",
      "price": 9000,
      "position": {"line": 1, "confidence": 0.92}
    },
    {
      "text_ko": "얼큰순두부찌개",
      "price": 8000,
      "position": {"line": 2, "confidence": 0.88}
    }
  ],
  "item_count": 2,
  "ocr_confidence_avg": 0.90
}
```

---

### 1-2. `POST /api/v1/menu/identify`

**목적:** 추출된 메뉴명 → DB 매칭 + 수식어 분해 + AI fallback → 구조화된 메뉴 정보

```
Request:
  Content-Type: application/json
  Body:
  {
    "items": [
      {"text_ko": "할머니뼈해장국", "price": 9000},
      {"text_ko": "얼큰순두부찌개", "price": 8000}
    ],
    "language": "en",           (필수) 출력 언어
    "include_details": true,    (선택) 상세 설명 포함 여부
    "shop_id": "uuid..."        (선택)
  }

Response 200:
{
  "request_id": "req_def456",
  "results": [
    {
      "input_text": "할머니뼈해장국",
      "match_method": "decomposition",     // "exact" | "similar" | "decomposition" | "ai_discovery"
      "confidence": 0.95,

      "canonical": {
        "id": "canon_042",
        "name_ko": "뼈해장국",
        "name_en": "Pork Bone Hangover Soup",
        "romanization": "Ppyeo-haejangguk",
        "explanation_short": "Slow-simmered pork bone soup, a popular Korean hangover cure",
        "spice_level": 2,
        "difficulty_score": 3,
        "allergens": ["pork"],
        "dietary_tags": ["contains_pork", "spicy_mild", "gluten_free"],
        "image_url": "https://cdn.example.com/images/canon_042.jpg"
      },

      "modifiers_applied": [
        {
          "text_ko": "할머니",
          "type": "emotion",
          "translation": "Homestyle",
          "effect": "감성 수식어 — 가정식 스타일을 강조"
        }
      ],

      "composed_name_en": "Homestyle Pork Bone Hangover Soup",
      "price": 9000,
      "ai_called": false
    },
    {
      "input_text": "얼큰순두부찌개",
      "match_method": "decomposition",
      "confidence": 0.93,

      "canonical": {
        "id": "canon_015",
        "name_ko": "순두부찌개",
        "name_en": "Soft Tofu Stew",
        "romanization": "Sundubu-jjigae",
        "explanation_short": "Spicy stew made with uncurdled soft tofu, often with seafood or pork",
        "spice_level": 3,
        "difficulty_score": 2,
        "allergens": ["soy", "seafood"],
        "dietary_tags": ["contains_soy", "spicy"],
        "image_url": "https://cdn.example.com/images/canon_015.jpg"
      },

      "modifiers_applied": [
        {
          "text_ko": "얼큰",
          "type": "taste",
          "translation": "Extra Spicy",
          "effect": "맵기 +1"
        }
      ],

      "composed_name_en": "Extra Spicy Soft Tofu Stew",
      "price": 8000,
      "ai_called": false
    }
  ],
  "stats": {
    "total_items": 2,
    "db_matched": 2,
    "ai_called": 0,
    "avg_confidence": 0.94
  }
}
```

---

### 1-3. `POST /api/v1/menu/translate`

**목적:** 이미 identify된 메뉴를 다른 언어로 번역 요청

```
Request:
{
  "canonical_ids": ["canon_042", "canon_015"],
  "languages": ["ja", "zh_cn"],
  "include_cultural_context": true
}

Response 200:
{
  "translations": {
    "canon_042": {
      "ja": {
        "name": "ピョヘジャングク（豚の背骨スープ）",
        "explanation_short": "豚の背骨を長時間煮込んだスープ。二日酔いの朝に人気の料理です。",
        "cultural_context": "韓国では飲み過ぎた翌朝にこのスープを食べる文化があります。"
      },
      "zh_cn": {
        "name": "骨头解酒汤",
        "explanation_short": "将猪脊骨长时间熬煮的汤，是韩国人解酒的热门选择。",
        "cultural_context": "在韩国，人们习惯在宿醉后的早晨喝这道汤来解酒。"
      }
    },
    "canon_015": {
      "ja": { "..." },
      "zh_cn": { "..." }
    }
  }
}
```

---

## 2. B2B API — 식당 관리

### 2-1. `POST /api/v1/shop/register`

```
Request:
{
  "name_ko": "할머니뼈해장국집",
  "name_en": "Grandma's Bone Soup",        // (선택)
  "address_ko": "서울 중구 명동길 14",
  "latitude": 37.5636,
  "longitude": 126.9835,
  "area_tag": "명동"
}

Response 201:
{
  "shop_id": "shop_uuid...",
  "api_key": "sk_live_abc123...",           // B2B 인증용
  "qr_page_url": null,                      // 메뉴 등록 후 생성
  "status": "active"
}
```

### 2-2. `POST /api/v1/shop/{shop_id}/menu/upload`

**목적:** 사장님이 메뉴판 사진을 올려 한 번에 처리 (recognize + identify + confirm)

```
Request:
  Content-Type: multipart/form-data
  Headers: X-API-Key: sk_live_abc123...
  Body:
    image: <file>
    languages: ["en", "ja", "zh_cn"]

Response 200:
{
  "shop_id": "shop_uuid...",
  "menu_items": [
    {
      "variant_id": "var_187",
      "display_name_ko": "할머니뼈해장국",
      "canonical_name_en": "Homestyle Pork Bone Hangover Soup",
      "price": 9000,
      "match_method": "decomposition",
      "confidence": 0.95,
      "needs_review": false
    },
    { "..." }
  ],
  "qr_page_url": null,          // confirm 전이라 아직 미생성
  "review_url": "https://app.example.com/shop/shop_uuid/review"
}
```

### 2-3. `POST /api/v1/shop/{shop_id}/menu/confirm`

**목적:** 사장님이 검토 완료 후 확정 → QR 페이지 생성

```
Request:
{
  "confirmed_items": [
    {"variant_id": "var_187", "approved": true},
    {"variant_id": "var_188", "approved": true, "correction": {"name_en": "수정된 이름"}},
    {"variant_id": "var_189", "approved": false}    // 삭제
  ]
}

Response 200:
{
  "shop_id": "shop_uuid...",
  "qr_page_url": "https://menu.example.com/s/abc123",
  "qr_image_url": "https://cdn.example.com/qr/shop_uuid.png",
  "confirmed_count": 2,
  "menu_count_total": 2
}
```

---

## 3. QR 메뉴 페이지

### 3-1. `GET /menu/{shop_code}`

**목적:** 외국인이 QR 코드 스캔 시 보는 웹 페이지 (HTML, 서버 사이드 렌더링)

```
URL: https://menu.example.com/s/{shop_code}
Query params:
  ?lang=en       (기본: en, 지원: en, ja, zh_cn, zh_tw)

Response: HTML 페이지
  - 식당명 (한국어 + 영어)
  - 메뉴 리스트
    - 이름 (한국어 + 선택 언어 + 로마자)
    - 설명 (짧은/긴 토글)
    - 가격
    - 알레르기 아이콘
    - 맵기 레벨 아이콘
    - 난이도 표시
    - 대표 이미지 (있으면)
  - 언어 전환 버튼
  - "Was this helpful?" 피드백 버튼
```

### 3-2. `GET /api/v1/qr/{shop_id}/generate`

```
Response 200:
{
  "qr_image_url": "https://cdn.example.com/qr/shop_uuid.png",
  "qr_page_url": "https://menu.example.com/s/abc123",
  "format": "png",
  "size": "300x300"
}
```

---

## 4. Knowledge Graph API (v0.2+ 외부 공개용)

> MVP에서는 내부 사용. v0.2에서 외부 API로 공개.

### 4-1. `GET /api/v1/graph/canonical/{id}`

```
Response 200:
{
  "canonical": { ... 전체 canonical_menus 데이터 ... },
  "relations": [
    {"type": "similar_to", "target": {"id": "canon_045", "name_ko": "감자탕", "name_en": "Pork Bone Potato Stew"}},
    {"type": "often_confused_with", "target": {"id": "canon_050", "name_ko": "해장국"}}
  ],
  "variants": [
    {"display_name_ko": "할머니뼈해장국", "shop_name": "명동할매국밥", "price": 9000},
    {"display_name_ko": "얼큰뼈해장국", "shop_name": "해장의신", "price": 10000}
  ],
  "concept": {"name_ko": "해장국", "name_en": "Hangover Soup"}
}
```

### 4-2. `GET /api/v1/graph/search`

```
Request:
  ?q=해장국&lang=en&limit=10

Response 200:
{
  "results": [
    {"type": "canonical", "id": "canon_042", "name_ko": "뼈해장국", "name_en": "Pork Bone Hangover Soup", "score": 0.95},
    {"type": "canonical", "id": "canon_050", "name_ko": "해장국", "name_en": "Hangover Soup", "score": 0.90},
    {"type": "concept", "id": "concept_001", "name_ko": "해장국", "name_en": "Hangover Soup Category", "score": 0.85}
  ]
}
```

### 4-3. `GET /api/v1/graph/difficulty/{id}`

```
Response 200:
{
  "canonical_id": "canon_042",
  "name_ko": "뼈해장국",
  "difficulty_score": 3,
  "difficulty_label": "⭐⭐⭐ Needs Explanation",
  "factors": {
    "name_trap": false,
    "compound_count": 0,
    "unknown_ingredients": ["들깨가루"],
    "global_awareness": "low"
  },
  "tip": "The name literally means 'bone hangover soup' — it's made from pork spine bones and is traditionally eaten the morning after drinking."
}
```

---

## 5. 데이터 수집 API (내부)

### 5-1. `GET /api/v1/stats/scan-summary`

```
Request:
  ?period=7d&group_by=area

Response 200:
{
  "period": "2025-02-04 ~ 2025-02-11",
  "total_scans": 342,
  "unique_sessions": 128,
  "db_hit_rate": 0.73,
  "ai_call_rate": 0.27,
  "by_area": [
    {"area": "명동", "scans": 156, "unique_sessions": 62},
    {"area": "홍대", "scans": 98, "unique_sessions": 38},
    {"area": "성수", "scans": 88, "unique_sessions": 28}
  ],
  "by_language": [
    {"lang": "en", "count": 145},
    {"lang": "ja", "count": 102},
    {"lang": "zh_cn", "count": 95}
  ],
  "top_unmatched": [
    {"text": "시래기국", "count": 12},
    {"text": "도가니탕", "count": 8}
  ]
}
```

### 5-2. `GET /api/v1/stats/engine-health`

```
Response 200:
{
  "canonical_count": 523,
  "modifier_count": 87,
  "variant_count": 1240,
  "relation_count": 892,
  "shop_count": 45,
  "db_hit_rate_7d": 0.73,
  "db_hit_rate_30d": 0.68,
  "ai_cost_7d_krw": 12400,
  "avg_response_time_ms": 1240,
  "pending_review_count": 14
}
```

---

## 6. 에러 코드

| HTTP | 코드 | 설명 |
|---|---|---|
| 400 | `invalid_image` | 이미지 형식 오류 또는 인식 불가 |
| 400 | `no_menu_detected` | OCR에서 메뉴 텍스트를 추출 못함 |
| 401 | `invalid_api_key` | B2B API 키 무효 |
| 404 | `shop_not_found` | 식당 ID 없음 |
| 404 | `canonical_not_found` | 메뉴 ID 없음 |
| 429 | `rate_limit_exceeded` | 요청 한도 초과 |
| 500 | `ocr_service_error` | CLOVA OCR 서비스 장애 |
| 500 | `ai_service_error` | GPT-4o API 장애 |
| 503 | `service_unavailable` | 서버 점검 중 |

---

## 7. Rate Limit (MVP)

| 구분 | 제한 | 비고 |
|---|---|---|
| B2B (API key 기준) | 100 req/hour | 식당당 |
| B2C (IP 기준) | 30 req/hour | 익명 사용자 |
| recognize (OCR) | 10 req/min | OCR 비용 관리 |
| AI Discovery | 50 req/day | 전체 시스템 |
