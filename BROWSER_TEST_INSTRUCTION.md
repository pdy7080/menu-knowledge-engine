# 🌐 Terminal Developer 지시사항

## 📌 지시 요약
Menu Knowledge Engine 프로덕션 배포 최종 검증을 위해 **브라우저 기반 API 테스트**를 요청합니다.

---

## ✅ 테스트 환경
```
서버: d11475.sgp1.stableserver.net:8001
상태: ✅ Health Check 통과, ✅ DB 초기화 완료, ✅ 모든 P0 버그 수정
```

---

## 🎯 핵심 지시사항

### **1단계: Swagger UI 접속 (API 문서 확인)**
```
🔗 http://d11475.sgp1.stableserver.net:8001/docs
```

✅ **확인할 사항:**
- Swagger 페이지가 정상 로드되는가?
- 좌측에 `/api/v1/concepts`, `/api/v1/modifiers`, `/api/v1/menu/identify` 등이 보이는가?

---

### **2단계: 4가지 핵심 API 테스트 (Swagger UI에서 직접 테스트)**

#### **Test 1️⃣: Modifiers 조회 - 한우 타입 확인 (P0 버그)**
```
GET /api/v1/modifiers 클릭 → Try it out → Execute
```

**찾아야 할 것:**
```json
{
  "text_ko": "한우",
  "type": "grade"  ← ✅ 이 값이 "grade"여야 함
}
```

✅ **통과 조건:** type이 **"grade"**
❌ **실패 조건:** type이 **"ingredient"** 이면 버그 미수정

---

#### **Test 2️⃣: 메뉴 식별 - 정확 매칭 (김치찌개)**
```
POST /api/v1/menu/identify 클릭 → Try it out → 아래 입력
```

**요청 본문:**
```json
{
  "menu_name_ko": "김치찌개"
}
```

**Execute** 버튼 클릭

✅ **통과 조건:**
- HTTP 200
- `"match_type": "exact"`
- `"confidence": 1.0`

---

#### **Test 3️⃣: 빈 입력값 거부 (P0 버그 - Empty Input Validation)**
```
POST /api/v1/menu/identify 클릭 → Try it out → 아래 입력
```

**요청 본문:**
```json
{
  "menu_name_ko": ""
}
```

**Execute** 버튼 클릭

✅ **통과 조건:**
- HTTP **422** (Unprocessable Entity) 반환
- 에러 메시지 표시

❌ **실패 조건:**
- HTTP 200이 반환되면 → 빈 입력값 검증 미작동

---

#### **Test 4️⃣: 한우불고기 - 수식어 분해 테스트**
```
POST /api/v1/menu/identify 클릭 → Try it out → 아래 입력
```

**요청 본문:**
```json
{
  "menu_name_ko": "한우불고기"
}
```

**Execute** 버튼 클릭

✅ **통과 조건:**
- HTTP 200
- `"match_type": "modifier_decomposition"` (또는 "exact")
- modifiers 배열에 한우가 포함
- 한우의 `"type": "grade"` ✅

---

## 📊 최종 결과 보고 형식

**테스트 완료 후, 다음 형식으로 보고해주세요:**

```
🧪 Menu Knowledge Engine - 브라우저 테스트 결과

✅ Test 1: Modifiers - 한우 타입
   결과: type = [grade / ingredient]
   상태: [✅ PASS / ❌ FAIL]

✅ Test 2: 김치찌개 정확 매칭
   결과: match_type = [exact / other]
   상태: [✅ PASS / ❌ FAIL]

✅ Test 3: 빈 입력값 거부
   결과: HTTP [422 / 200]
   상태: [✅ PASS / ❌ FAIL]

✅ Test 4: 한우불고기 수식어 분해
   결과: match_type = [modifier_decomposition / exact / other]
   상태: [✅ PASS / ❌ FAIL]

📋 종합 평가: [모두 통과 / 일부 실패]
```

---

## 🆘 추가 정보 (필요시)

### 🔧 Curl 명령어로도 테스트 가능:
```bash
# Health Check
curl http://d11475.sgp1.stableserver.net:8001/health

# Modifiers 조회
curl http://d11475.sgp1.stableserver.net:8001/api/v1/modifiers | grep -A 2 "한우"

# 김치찌개 테스트
curl -X POST http://d11475.sgp1.stableserver.net:8001/api/v1/menu/identify \
  -H "Content-Type: application/json" \
  -d '{"menu_name_ko":"김치찌개"}'

# 빈 입력값 테스트
curl -X POST http://d11475.sgp1.stableserver.net:8001/api/v1/menu/identify \
  -H "Content-Type: application/json" \
  -d '{"menu_name_ko":""}'
```

### 📸 스크린샷 (권장)
다음 3개 항목의 스크린샷을 캡처해주세요:
1. Swagger UI 메인 화면
2. 한우 modifier 응답 (type: grade 확인)
3. 빈 입력값 HTTP 422 거부 응답

---

## ✨ 예상 결과
모든 테스트가 통과하면:
```
🎉 Menu Knowledge Engine v0.1.0 프로덕션 배포 완료!
   - 모든 P0 버그 수정 검증 완료
   - PostgreSQL 정상 통합
   - API 정상 작동
```

---

**테스트 완료 후 결과 보고 부탁드립니다! 🚀**
