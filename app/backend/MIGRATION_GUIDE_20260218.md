# Task #4: 브랜드명 패턴 50개 추가 - 마이그레이션 가이드

**작성일**: 2026-02-18
**상태**: 준비 완료 (실행 대기)
**목표**: TC-02, TC-10 등 브랜드명 포함 메뉴의 정확한 분해

---

## 📋 마이그레이션 내용

### 추가되는 브랜드명 패턴 (총 50개)

| 패턴 | 개수 | 예시 |
|------|------|------|
| **~씨네** (가족 레스토랑) | 15개 | 고씨네, 김씨네, 이씨네, ... |
| **~식당** (음식 카테고리) | 15개 | 고기식당, 우육식당, 닭식당, ... |
| **~집** (집 느낌) | 10개 | 엄마집, 할머니집, 이모집, ... |
| **~네** (축약형) | 5개 | 어머니네, 친구네, 동네네, ... |
| **~하우스** (영어 차용) | 5개 | 미트하우스, 스테이크하우스, ... |

**Total**: 50개 추가 (기존 54개 + 50개 = 104개)

### 수정되는 테이블

- **Table**: `modifiers`
- **Type**: `emotion` (감성/브랜드명)
- **Priority**: `5` (중간 우선순위)

---

## 🎯 영향받는 테스트 케이스

### TC-02: "할머니김치찌개"
```
입력: "할머니김치찌개"
분해:
  - 수식어: "할머니" (emotion, 이미 존재)
  - 캐노니컬: "김치찌개"
결과: ✅ 정확 분해 (이미 동작)
```

### TC-10: "고씨네묵은지감자탕"
```
입력: "고씨네묵은지감자탕"
분해:
  - 수식어 1: "고씨네" (emotion, 새로 추가)
  - 수식어 2: "묵은지" (ingredient, 이미 존재)
  - 캐노니컬: "감자탕"
결과: ✅ 정확 분해 (마이그레이션 후)
```

---

## 🚀 마이그레이션 실행 방법

### 옵션 1: FastComet 서버에서 직접 실행 (권장)

```bash
# 1. FastComet 서버 SSH 접속
ssh chargeap@d11475.sgp1.stableserver.net

# 2. 마이그레이션 파일로 이동
cd /home/chargeap/menu-knowledge/app/backend/migrations

# 3. 마이그레이션 스크립트 실행
bash apply_migration.sh
```

**예상 출력**:
```
==================================================
Task #4: 브랜드명 패턴 50개 추가
==================================================

🔍 마이그레이션 파일 확인: .../add_brand_names_20260218.sql
✅ 파일 존재 확인

🔗 데이터베이스 연결 테스트...
✅ 데이터베이스 연결 성공

⚙️  마이그레이션 실행 중...
✅ 마이그레이션 완료!

🔍 검증 중...
📊 현재 Modifier 총 개수:
 count
-------
   104

📊 emotion 타입 Modifier 개수:
 count
-------
    61

✅ '고씨네' 확인 (TC-10용):
 text_ko | type    | priority
---------+---------+----------
 고씨네  | emotion |        5

✅ '할머니' 확인 (TC-02용):
 text_ko | type    | priority
---------+---------+----------
 할머니  | emotion |        5

📋 최근 추가된 emotion 항목 (상위 10개):
 text_ko      | semantic_key
--------------+---------------------------
 삼겹살하우스  | brand_pork_belly_house
 갈비하우스    | brand_galbi_house
 ...

==================================================
🎉 마이그레이션 성공!
==================================================
```

### 옵션 2: 직접 psql 명령 실행

```bash
# FastComet 서버에서:
cd /home/chargeap/menu-knowledge/app/backend/migrations

PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -f add_brand_names_20260218.sql
```

### 옵션 3: 데이터베이스 클라이언트 사용 (GUI)

- **도구**: DBeaver, pgAdmin, psql
- **연결 정보**:
  - Host: `d11475.sgp1.stableserver.net` (또는 FastComet VPN)
  - Port: `5432`
  - Database: `chargeap_menu_knowledge`
  - User: `chargeap_dcclab2022`
  - Password: `eromlab!1228`
- **실행**: `add_brand_names_20260218.sql` 파일의 SQL 쿼리 전체 실행

---

## 📂 관련 파일

| 파일 | 경로 | 설명 |
|------|------|------|
| SQL 마이그레이션 | `add_brand_names_20260218.sql` | 50개 브랜드명 패턴 INSERT |
| 실행 스크립트 | `apply_migration.sh` | FastComet 서버용 bash 스크립트 |
| 시드 데이터 | `../seeds/seed_modifiers.py` | 기본 시드 업데이트 (재설치 시) |
| 마이그레이션 가이드 | 본 문서 | 실행 방법 및 검증 |

---

## ✅ 마이그레이션 후 검증

### 1. DB 상태 확인

```sql
-- 전체 modifier 개수 (104개 확인)
SELECT COUNT(*) FROM modifiers;

-- emotion 타입 개수 (61개 확인)
SELECT COUNT(*) FROM modifiers WHERE type = 'emotion';

-- 타입별 분포
SELECT type, COUNT(*) FROM modifiers GROUP BY type ORDER BY type;
```

### 2. 테스트 케이스 실행

#### API를 통한 검증

```bash
# TC-02: "할머니김치찌개"
curl -X POST https://menu-knowledge.chargeapp.net/api/v1/menu/identify \
  -H "Content-Type: application/json" \
  -d '{"menu_name_ko": "할머니김치찌개"}'

# 예상 응답:
{
  "input": "할머니김치찌개",
  "match_type": "modifier_decomposition",
  "canonical": {
    "name_ko": "김치찌개",
    "name_en": "Kimchi Jjigae",
    ...
  },
  "modifiers": [
    {
      "text_ko": "할머니",
      "type": "emotion",
      "translation_en": "Grandma's / Homestyle"
    }
  ],
  "confidence": 0.9
}

# TC-10: "고씨네묵은지감자탕"
curl -X POST https://menu-knowledge.chargeapp.net/api/v1/menu/identify \
  -H "Content-Type: application/json" \
  -d '{"menu_name_ko": "고씨네묵은지감자탕"}'

# 예상 응답:
{
  "input": "고씨네묵은지감자탕",
  "match_type": "modifier_decomposition",
  "canonical": {
    "name_ko": "감자탕",
    "name_en": "Potato & Spine Soup",
    ...
  },
  "modifiers": [
    {
      "text_ko": "고씨네",
      "type": "emotion",
      "translation_en": "Gho Family Restaurant"
    },
    {
      "text_ko": "묵은지",
      "type": "ingredient",
      "translation_en": "Aged Kimchi"
    }
  ],
  "confidence": 0.85
}
```

### 3. 예상 결과

| 테스트 케이스 | 이전 | 이후 | 변화 |
|--------------|------|------|------|
| TC-01 김치찌개 | ✅ | ✅ | 동일 |
| TC-02 할머니김치찌개 | ✅ | ✅ | 동일 |
| TC-03 왕돈까스 | ✅ | ✅ | 동일 |
| TC-04 얼큰순두부찌개 | ✅ | ✅ | 동일 |
| TC-05 숯불갈비 | ✅ | ✅ | 동일 |
| TC-06 한우불고기 | ✅ | ✅ | 동일 (Task #3 완료) |
| TC-07 왕얼큰뼈해장국 | ✅ | ✅ | 동일 |
| **TC-08 옛날통닭** | ❌ | ✅ | **개선** (Task #3 완료) |
| **TC-10 고씨네묵은지감자탕** | ❌ | ✅ | **개선** (Task #4 완료) |
| TC-09 시래기국 | ❌ | ❌ | AI Discovery 필요 (v0.2) |

**예상 성과**:
- 통과율: 7/10 (70%) → **9/10 (90%)** ✅

---

## 🔄 롤백 방법 (필요 시)

```sql
-- 추가된 브랜드명 50개 제거
DELETE FROM modifiers
WHERE semantic_key LIKE 'brand_%'
  AND type = 'emotion';

-- 검증
SELECT COUNT(*) FROM modifiers;  -- 54개 확인

-- 복구 확인
SELECT COUNT(*) FROM modifiers WHERE type = 'emotion';  -- 11개 확인
```

---

## 📊 예상 영향

| 지표 | 현재 | 마이그레이션 후 |
|------|------|-----------------|
| **Modifier 총 개수** | 54 | 104 |
| **emotion 타입** | 11 | 61 |
| **TC 통과율** | 70% (7/10) | 90% (9/10) |
| **DB 매칭률** | 60% | 75-80% |
| **AI 호출 비율** | 40% | 20-25% |

---

## 📝 다음 단계

1. ✅ SQL 마이그레이션 파일 생성 (`add_brand_names_20260218.sql`)
2. ✅ 마이그레이션 스크립트 작성 (`apply_migration.sh`, Python 버전)
3. ⏳ **마이그레이션 실행** (본 가이드에 따라 실행)
4. ⏳ TC-02, TC-10 검증
5. ⏳ 최종 성과 측정 및 보고서 작성

---

**작성자**: Claude Code
**최종 수정**: 2026-02-18
**상태**: 실행 준비 완료 ✅
