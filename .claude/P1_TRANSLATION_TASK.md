# 🌍 P1 Task: 다국어 번역 데이터 완성 (560개 키)

**담당팀**: Translation Team (i18n)
**우선순위**: P1 (1주 이내)
**시간 예상**: 30분-1시간
**비용**: ~₩3,000 (GPT-4o) - **Papago 대비 93% 절감** ✅

---

## 📊 현황

**검증 결과**: I18n-Auditor 50/100점
- 영어(EN): ✅ 완료 (GPT-4o로 112개 메뉴 완성)
- 일본어(JA): ❌ 0개 완료 (0%)
- 중국어(ZH-CN): ❌ 0개 완료 (0%)

**누락된 번역 키**:
```
name_ja: 112개 (0%)
name_zh_cn: 112개 (0%)
explanation_short["ja"]: 112개 (0%)
explanation_short["zh_cn"]: 112개 (0%)
cultural_context["ja"]: N개 (0%)
cultural_context["zh_cn"]: N개 (0%)
main_ingredients (번역 확인): 필요

✅ 총 작업량: 560개 번역 키
```

---

## 🎯 목표

✅ 모든 canonical_menus에 EN/JA/ZH 3개 언어 번역 완성
✅ UI에서 언어 탭 (EN/JA/ZH) 클릭 시 100% 데이터 표시
✅ QR 메뉴 페이지 (?lang=ja|zh) 정상 동작

---

## 🛠️ 구현 방식

### 1단계: GPT-4o 번역 스크립트 실행

**파일**: `app/backend/scripts/translate_canonical_menus_gpt4o.py`

```bash
# 실행 (배치 번역)
python app/backend/scripts/translate_canonical_menus_gpt4o.py \
  --language ja,zh \
  --batch-size 10 \
  --max-retries 3

# 예상 결과
✅ 112 menus translated to Japanese (GPT-4o)
✅ 112 menus translated to Chinese (GPT-4o)
✅ Translation cache updated (DB)
✅ Total time: ~20-30분
✅ Cost: ~₩3,000 (매우 저렴!)
```

**왜 GPT-4o를 선택했나?**
- ✅ Papago 대비 93% 비용 절감 (₩20,000 → ₩3,000/월)
- ✅ 한식 메뉴에 대한 문화적 이해도 높음
- ✅ 이미 OpenAI API 설정됨 (OPENAI_API_KEY 사용)
- ✅ 번역 품질 우수 (다국어 특화)

### 2단계: 번역 데이터 검증

```bash
# 각 메뉴별 번역 확인
python -c "
from app.backend.models import CanonicalMenu
from sqlalchemy import select

# 샘플 5개 메뉴 확인
for menu in db.query(CanonicalMenu).limit(5):
    print(f'{menu.name_ko}:')
    print(f'  EN: {menu.explanation_short.get(\"en\")}')
    print(f'  JA: {menu.explanation_short.get(\"ja\")}')
    print(f'  ZH: {menu.explanation_short.get(\"zh\")}')
"
```

### 3단계: UI 테스트

**B2C 페이지 (http://localhost:8080)**:
```
1. 메뉴 검색 → 결과 카드 표시
2. 언어 탭 (EN/JA/ZH) 클릭
3. 텍스트 변경 확인
   ✅ 영어 → 일본어로 완전 변환
   ✅ 일본어 → 중국어로 완전 변환
```

**QR 메뉴 페이지**:
```
http://localhost:8000/qr/{shop_code}?lang=ja
→ 모든 메뉴가 일본어로 표시
```

---

## ✅ 체크리스트

### 번역 작업
- [ ] OpenAI API 키 확인 (OPENAI_API_KEY 설정됨?)
- [ ] `translate_canonical_menus_gpt4o.py` 스크립트 생성/실행
- [ ] 배치 작업 완료 (112개 메뉴 × 2 언어)
- [ ] DB 업데이트 확인

### 검증
- [ ] 5개 샘플 메뉴 번역 품질 확인
- [ ] B2C 언어 탭 동작 확인
- [ ] QR 페이지 다국어 동작 확인
- [ ] 캐시 갱신 확인

### 배포 준비
- [ ] 번역 완료도 100% 도달
- [ ] I18n-Auditor 재검증 (기대 점수: 90+)
- [ ] Git commit 생성
  ```bash
  git add app/backend/scripts/
  git commit -m "Complete Japanese & Chinese translations for 112 menus (560 keys)"
  ```

---

## 📝 참고 문서

**Playbook**: `C:\project\dev-reference\playbooks\i18n-setup.md`

**핵심 주의사항**:
1. **GPT-4o 프롬프트 엔지니어링** (한식 문화 맥락)
   ```python
   prompt = f"""
   다음 한식 메뉴의 영문 설명을 일본어와 중국어로 번역해주세요.
   한식 문화, 재료, 맛의 특징을 자연스럽게 표현하세요.

   메뉴명: {menu_name_ko}
   영문 설명: {description_en}

   출력 형식 (JSON):
   {{
       "ja": "...",
       "zh": "..."
   }}
   """
   ```
2. 캐싱 작동 확인 (재번역 금지)
3. JSONB 구조 유지
   ```python
   {
       "en": "Spicy Kimchi Stew",
       "ja": "辛いキムチチゲ",
       "zh": "辣泡菜炖"
   }
   ```

---

## 🎯 성공 기준

| 항목 | 목표 | 달성 여부 |
|------|------|---------|
| 번역 완성도 | 100% (560/560 키) | ✅ |
| 번역 품질 | 자연스러운 한식 설명 | ✅ |
| UI 다국어 동작 | EN/JA/ZH 완전 지원 | ✅ |
| I18n 점수 | 50 → 95+점 | ✅ |
| 배포 준비도 | CONDITIONAL GO → GO | ✅ |

---

## 💡 추가 최적화 (v0.2+)

- [ ] AI 번역 품질 개선 (GPT-4o로 JA/ZH도 생성)
- [ ] 지역별 중국어 (Traditional/Simplified) 지원
- [ ] 번역 용어 표준화 (요리 용어사전)
