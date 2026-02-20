# Gemini Multi-Key Auto-Translation Guide

> 260개 메뉴 자동 번역 시스템 (일본어/중국어)
> 3개 API 키 라운드 로빈으로 4.5일 완료

**작성일**: 2026-02-20
**완료 예정**: 2026-02-25 (4.5일)
**비용**: $0 (Gemini 무료 tier)

---

## 📊 시스템 개요

### 문제 상황
- **Ollama (Qwen2.5 7B)**: 할루시네이션 발견 (삼치→연어, 80% 오류율)
- **Gemini 단일 키**: 20 RPD → 260메뉴 = 13일 소요
- **OpenAI**: Billing limit 도달

### 해결책: Gemini Multi-Key Round Robin
```
3개 프로젝트 × 20 RPD = 60 RPD/day
260 menus ÷ 58 menus/day = 4.5 days
```

**핵심 전략**: API 키 자동 전환으로 RPD 한도 3배 확장

---

## 🔑 API 키 구성

### 현재 설정 (.env)
```env
GOOGLE_API_KEY_1=your-api-key-1-here
GOOGLE_API_KEY_2=your-api-key-2-here
GOOGLE_API_KEY_3=your-api-key-3-here
```

### RPD 리셋 시간
- **UTC 00:00** = **KST 09:00**
- 매일 09시부터 60 RPD 사용 가능

---

## 🤖 자동화 시스템

### 일일 번역 스크립트
**위치**: `app/backend/scripts/daily_translation.py`

**실행**:
```bash
cd ~/menu-knowledge/app/backend
source venv/bin/activate
python scripts/daily_translation.py --limit 58
```

**기능**:
1. 미번역 메뉴 조회 (name_ja IS NULL)
2. 58개 메뉴 자동 번역 (RPD 60 - 2 버퍼)
3. DB 자동 업데이트
4. 진행 상황 로그 기록

### 스케줄러 설정 (서버)

#### Cron 설정
```bash
# 매일 09:00 KST 자동 실행
0 9 * * * cd ~/menu-knowledge/app/backend && source venv/bin/activate && python scripts/daily_translation.py --limit 58 >> ~/translation.log 2>&1
```

#### 설치 방법
```bash
crontab -e
# 위 내용 추가
```

---

## 📈 진행 상황 모니터링

### 실시간 확인
```bash
# 번역 완료 개수
psql -U chargeap_dcclab2022 -d chargeap_menu_knowledge -c "
SELECT COUNT(*) FROM canonical_menus WHERE name_ja IS NOT NULL;
"

# 남은 개수
psql -U chargeap_dcclab2022 -d chargeap_menu_knowledge -c "
SELECT COUNT(*) FROM canonical_menus WHERE name_ja IS NULL;
"
```

### 로그 확인
```bash
tail -f ~/translation.log
```

---

## 🔧 트러블슈팅

### 1. 429 Quota Exceeded
**증상**: "You exceeded your current quota"

**원인**: 특정 키의 일일 20 RPD 소진

**해결**: 자동으로 다음 키로 전환 (코드에 구현됨)

```python
# auto_translate_service.py에서 자동 처리
if "429" in error_msg or "quota" in error_msg.lower():
    logger.warning(f"Key {self.current_key_index + 1} quota exhausted, switching to next key")
    self.daily_usage[self.current_key_index] = self.max_rpd  # 강제 소진
    # Retry 시 자동으로 다음 키 사용
```

### 2. 모든 키 소진
**증상**: "All API keys exhausted (60 RPD limit reached)"

**해결**: 다음 날 09:00 KST 대기 (자동 리셋)

### 3. 번역 품질 문제
**확인**:
```sql
SELECT name_ko, name_ja, name_zh_cn
FROM canonical_menus
WHERE name_ja IS NOT NULL
LIMIT 10;
```

**Gemini 품질 보장**: 이전 테스트에서 춘장/돼지고기 등 정확도 검증 완료

---

## 📊 예상 일정

| 날짜 | 번역 개수 | 누적 | 남은 개수 |
|------|----------|------|----------|
| Day 1 | 58 | 58 | 202 |
| Day 2 | 58 | 116 | 144 |
| Day 3 | 58 | 174 | 86 |
| Day 4 | 58 | 232 | 28 |
| Day 5 | 28 | 260 | 0 ✅ |

**완료 예정**: 2026-02-25

---

## 🎯 수동 실행 (테스트용)

### 단일 메뉴 번역 테스트
```python
from services.auto_translate_service import auto_translate_service
import asyncio

async def test():
    result = await auto_translate_service.auto_translate_new_menu(
        menu_id="<UUID>",
        menu_name_ko="김치찌개",
        description_en="Spicy stew with kimchi and pork",
        db=db_session
    )
    print(result)

asyncio.run(test())
```

### 10개 배치 번역
```bash
python scripts/daily_translation.py --limit 10
```

---

## 🔐 보안 주의사항

### API 키 보호
- ✅ .env 파일 절대 Git 커밋 금지
- ✅ .gitignore에 포함 확인
- ✅ GitHub에 노출 시 즉시 재발급

### 키 로테이션
- Gemini 무료 tier는 영구 유효
- 보안상 3개월마다 재발급 권장

---

## 📚 관련 문서

| 문서 | 경로 | 용도 |
|------|------|------|
| 프로젝트 규칙 | `CLAUDE.md` | 전체 개발 규칙 |
| 자동화 README | `app/backend/scripts/automation/README.md` | Ollama vs Gemini 비교 |
| Sprint 2 계획 | `SPRINT2_PHASE2_PLAN_20260219.md` | 다국어 번역 기획 |
| 품질 테스트 | `ollama_quality_test_20260220_140022.json` | Ollama 할루시네이션 증거 |

---

## 🚀 Quick Start

### 즉시 시작 (로컬)
```bash
cd ~/menu-knowledge/app/backend
source venv/bin/activate
python scripts/daily_translation.py --limit 58
```

### 서버 자동화 (권장)
```bash
# 1. Cron 설정
crontab -e

# 2. 다음 줄 추가
0 9 * * * cd ~/menu-knowledge/app/backend && source venv/bin/activate && python scripts/daily_translation.py --limit 58 >> ~/translation.log 2>&1

# 3. 저장 후 확인
crontab -l
```

---

**최종 수정**: 2026-02-20
**작성자**: terminal-developer
**검증 완료**: ✅ 서버 배포 완료, 3개 키 로드 확인
