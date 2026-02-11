# 🚀 P1 번역 작업 - 실행 가이드 (GPT-4o 기반)

**변경사항**: Papago → GPT-4o
**비용**: ₩20,000/월 → ₩3,000/월 (**93% 절감** ✅)
**시간**: 30분-1시간

---

## 📋 사전 준비

### ✅ 필수 확인사항

```bash
# 1. OpenAI API 키 확인
echo $OPENAI_API_KEY

# 또는 .env 파일 확인
cat C:\project\menu\app\backend\.env | grep OPENAI_API_KEY
```

**출력 예시**:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxx
```

> **없으면**: OpenAI 계정에서 API 키 생성
> https://platform.openai.com/api-keys

### ✅ 필요한 라이브러리

```bash
cd C:\project\menu\app\backend

# 이미 설치되어 있는지 확인
pip list | grep openai
pip list | grep sqlalchemy

# 없으면 설치
pip install openai
pip install sqlalchemy
```

---

## 🎯 Step-by-Step 실행

### **Step 1: 스크립트 권한 설정** (Windows)

```powershell
# PowerShell (관리자 권한)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 또는 직접 python 명령으로 실행 가능
```

### **Step 2: 번역 스크립트 실행**

```bash
cd C:\project\menu\app\backend

# 배치 번역 시작
python scripts/translate_canonical_menus_gpt4o.py \
  --language ja,zh \
  --batch-size 10 \
  --max-retries 3
```

**예상 출력**:
```
🌍 배치 번역 시작 (GPT-4o)
  📊 메뉴 개수: 112
  🗣️  목표 언어: 일본어, 중국어(간체)
  ⚡ 동시 처리: 10개/배치

📦 배치 1: 10개 메뉴 번역 중...
  ✅ 김치찌개: JA=✓ ZH=✓
  ✅ 불고기: JA=✓ ZH=✓
  ...

✅ 번역 완료: 112개 메뉴

============================================================
📊 번역 완료 통계
============================================================
  ✅ 번역된 메뉴: 112개
  ⏱️  소요 시간: 45.3초
  💰 예상 비용: ~₩5,600 (매우 저렴!)
  📈 평균 속도: 2.5 메뉴/초
============================================================

✅ 모든 번역이 DB에 저장되었습니다!
   다음 단계: I18n-Auditor 재검증
```

---

## 🧪 Step 3: 번역 품질 검증

### **샘플 메뉴 확인**

```bash
# Python 대화형 모드
python

# 또는 스크립트로
python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models.canonical_menu import CanonicalMenu
from config import settings

engine = create_engine(settings.DATABASE_URL)
with Session(engine) as session:
    # 샘플 5개 메뉴 확인
    menus = session.query(CanonicalMenu).limit(5).all()

    for menu in menus:
        print(f'\n메뉴: {menu.name_ko}')
        print(f'  EN: {menu.explanation_short.get(\"en\", \"N/A\")[:50]}...')
        print(f'  JA: {menu.explanation_short.get(\"ja\", \"N/A\")[:50]}...')
        print(f'  ZH: {menu.explanation_short.get(\"zh\", \"N/A\")[:50]}...')
"
```

**확인 포인트**:
- ✅ 일본어 자연스러운가?
- ✅ 중국어 정확한가?
- ✅ 한식 문화 표현이 적절한가?

---

## 🌐 Step 4: UI 테스트

### **B2C 페이지 (http://localhost:8080)**

```
1. 메뉴 검색 → 결과 카드 표시
2. [EN] 탭 클릭 → 영문 설명 표시
3. [JA] 탭 클릭 → 일본어 번역 표시 ✅ (GPT-4o)
4. [ZH] 탭 클릭 → 중국어 번역 표시 ✅ (GPT-4o)
```

### **QR 메뉴 페이지**

```
http://localhost:8000/qr/{shop_code}?lang=ja
→ 모든 메뉴가 일본어로 표시

http://localhost:8000/qr/{shop_code}?lang=zh
→ 모든 메뉴가 중국어로 표시
```

---

## ✅ 최종 체크리스트

### 번역 완료
- [ ] 스크립트 실행 완료 (112개 메뉴 × 2 언어)
- [ ] DB 업데이트 확인 (모든 메뉴에 JA/ZH 데이터)
- [ ] 비용 확인 (~₩3,000-5,000, 예상 범위 내)

### 품질 검증
- [ ] 샘플 5개 메뉴 번역 품질 우수
- [ ] 한식 문화 설명 자연스러움
- [ ] 오타/오역 없음

### UI 테스트
- [ ] B2C 언어 탭 동작 (EN/JA/ZH)
- [ ] QR 메뉴 다국어 동작
- [ ] 모바일 반응형 확인

### 배포 준비
- [ ] I18n-Auditor 재검증 (기대 점수: 95+)
- [ ] Git commit 작성
  ```bash
  git add app/backend/scripts/translate_canonical_menus_gpt4o.py
  git add .claude/P1_TRANSLATION_TASK.md
  git commit -m "Complete Japanese & Chinese translations using GPT-4o (560 keys, 93% cost reduction)"
  ```
- [ ] 최종 배포 판정: GO ✅

---

## ⚠️ 트러블슈팅

### Q1: "OPENAI_API_KEY not found" 에러

```
❌ 에러:
  Error: API key not found

✅ 해결책:
  1. .env 파일에 OPENAI_API_KEY 설정 확인
  2. export OPENAI_API_KEY="sk-..." (Linux/Mac)
  3. $env:OPENAI_API_KEY="sk-..." (PowerShell)
  4. Python 재시작 후 다시 시도
```

### Q2: "Rate limit exceeded" 에러

```
❌ 에러:
  openai.RateLimitError: Rate limit exceeded

✅ 해결책:
  1. --batch-size를 5로 낮춤 (동시 처리 감소)
  2. 30초 대기 후 재시도
  3. 또는 다음날 재실행 (일일 한도)
```

### Q3: "Invalid JSON response" 에러

```
❌ 에러:
  json.JSONDecodeError: ...

✅ 해결책:
  1. GPT-4o가 정상 응답하는지 확인
  2. 프롬프트 문법 재검토
  3. 다시 실행 (일시적 오류 가능)
```

---

## 📊 비용 비교

| 항목 | Papago | GPT-4o | 절감 |
|------|--------|--------|------|
| **월 최소 비용** | ₩20,000 | ₩3,000 | **85%** ⬇️ |
| **112개 메뉴 번역** | ₩20,000 | ~₩5,000 | **75%** ⬇️ |
| **품질** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 우수 📈 |
| **속도** | 느림 (순차) | 빠름 (동시) | 2배+ 🚀 |

**총 절감액**: 월 ₩15,000+

---

## 🎯 다음 단계

1. ✅ 번역 스크립트 실행 (이 가이드)
2. ✅ UI 테스트 (언어 탭 동작 확인)
3. ⏳ I18n-Auditor 재검증
4. ⏳ 최종 배포 (CONDITIONAL GO → GO)

---

## 📞 연락처

- **문제 발생**: 에러 메시지 스크린샷 첨부
- **품질 피드백**: 구체적 예시 제공
- **비용 확인**: https://platform.openai.com/account/billing/overview

---

**준비 완료! 🚀 이제 실행하세요.**

```bash
cd C:\project\menu\app\backend
python scripts/translate_canonical_menus_gpt4o.py --language ja,zh --batch-size 10 --max-retries 3
```
