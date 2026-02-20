# Menu Automation System

사무실 PC (Windows, 24시간 가동)를 활용한 **비용 $0** 자동 메뉴 DB 확충 시스템.

## 목표

| 시점 | 메뉴 수 | 월 비용 |
|------|---------|--------|
| 현재 | 260 | - |
| 1개월 | 800 | $0 |
| 3개월 | 1,900 | $0 |
| 6개월 | 3,500 | $0 |

> **참고**: Gemini 무료 tier RPD=20 기준 일일 최대 18메뉴.
> 다중 API 키 또는 Ollama 병행 시 처리량 증가 가능.

---

## 아키텍처

```
사무실 PC (Windows, 24시간 가동)
├── [Primary] Gemini 2.5 Flash-Lite ── 콘텐츠 생성 ......... $0 (RPD 20)
├── [Fallback] Ollama (Qwen2.5 7B) ── 대량 처리 ........... $0 (무제한)
├── Collectors ─────────────────────── 메뉴명 수집 ......... $0
├── Image Fetchers ─────────────────── 이미지 수집 ......... $0
├── APScheduler ────────────────────── 매일 자동 실행
└── DB Sync ────────────────────────── FastComet 프로덕션 동기화
```

### LLM 이중화 전략 (Gemini + Ollama)

이 시스템은 두 개의 LLM 클라이언트를 지원하며, **동일한 인터페이스**를 통해
교체 가능합니다.

| 항목 | Gemini 2.5 Flash-Lite | Ollama Qwen2.5 7B |
|------|----------------------|-------------------|
| **역할** | Primary (품질 우선) | Fallback (물량 우선) |
| **비용** | $0 (무료 tier) | $0 (로컬 GPU) |
| **품질** | 높음 (GPT-4o-mini급) | 중간 (할루시네이션 주의) |
| **RPD** | 20/일 (Google 제한) | 무제한 |
| **RPM** | 15/분 | GPU 성능 의존 (~3/분) |
| **요구사항** | API 키 + 인터넷 | GPU 8GB+ VRAM |
| **SDK** | `google-genai` | HTTP REST (localhost:11434) |
| **장점** | 사실 정확도 높음 | 한도 없음, 오프라인 가능 |
| **단점** | 일일 20건 한도 | 자장면=고추장 등 오류 가능 |

#### 운영 모드 3가지

```
Mode 1: Gemini Only (기본)
  - 일일 18건, 고품질
  - 인터넷 필요, GPU 불필요
  - .env: GOOGLE_API_KEY 설정

Mode 2: Ollama Only (오프라인)
  - 일일 무제한, 중간 품질
  - GPU 8GB+ 필요, 인터넷 불필요
  - Ollama 서버 실행 필요

Mode 3: Hybrid (권장, 최대 처리량)
  - Gemini로 18건 고품질 처리
  - RPD 소진 후 Ollama로 추가 처리
  - 또는: Ollama bulk → Gemini 검증
  - 양쪽 모두 설정 필요
```

### Gemini 무료 Tier 실측 한도 (2026-02-20)

> Google이 2025년 12월 7일에 무료 tier를 50-80% 축소했습니다.
> 공식 문서와 실제 한도가 크게 다릅니다.

| 모델 | RPM | RPD (공식) | RPD (실측) | 상태 |
|------|-----|-----------|-----------|------|
| gemini-2.5-flash-lite | 15 | 1,000 | **20** | 현재 사용 |
| gemini-2.5-flash | 10 | 250 | **20** | 같은 한도 |
| gemini-2.0-flash | 5 | - | **0** | 2026-03 퇴역 |

**RPD 리셋**: midnight UTC (한국시간 09:00)

#### RPD 예산 배분 (일일 20건)

| 용도 | RPD 사용 | 비고 |
|------|---------|------|
| is_available() | 0 | SDK 초기화만 (API 호출 안 함) |
| 메뉴 enrichment | 18 | 1건=1 RPD (JSON 파싱 성공 시) |
| 여유 (재시도) | 2 | JSON 파싱 실패 시 1회 재시도 |

---

### 일일 스케줄

| 시간 | 작업 | 모듈 | LLM |
|------|------|------|-----|
| 02:00 | 새 메뉴 수집 | `menu_discovery.py` | 불필요 |
| 04:00 | 콘텐츠 생성 | `content_generator.py` | Gemini/Ollama |
| 06:00 | 이미지 수집 | `image_matcher.py` | 불필요 |
| 08:00 | 프로덕션 DB 동기화 | `db_sync.py` | 불필요 |

---

## 빠른 시작

### 1. 사전 요구사항

```powershell
# Python 의존성
pip install google-genai apscheduler beautifulsoup4 lxml pydantic-settings httpx

# (선택) Ollama 설치 — Fallback LLM
# https://ollama.com/download/windows
ollama pull qwen2.5:7b
```

### 2. 환경변수 설정

`app/backend/.env`에 추가:

```env
# Gemini (Primary — 무료, 권장)
GOOGLE_API_KEY=your_gemini_api_key   # https://aistudio.google.com/app/apikey
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_RPM_LIMIT=15
GEMINI_RPD_LIMIT=20

# Ollama (Fallback — 로컬, 선택)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT=120

# 이미지 (선택)
UNSPLASH_ACCESS_KEY=your_key         # https://unsplash.com/developers
PIXABAY_API_KEY=your_key             # https://pixabay.com/api/docs/

# 자동화
AUTOMATION_ENABLED=true
DAILY_MENU_TARGET=18
```

### 3. Gemini API 키 발급

1. https://aistudio.google.com/app/apikey 접속
2. "Create API key" 클릭
3. 프로젝트 선택 (또는 신규 생성)
4. 생성된 키를 `.env`에 `GOOGLE_API_KEY`로 저장

> **주의**: API 키가 Git에 노출되면 Google이 자동 감지하여 경고합니다.
> `.env`는 `.gitignore`에 포함되어 있어야 합니다.

### 4. 실행

```powershell
# 스케줄러 시작 (24시간 구동)
cd app\backend\scripts
python -m automation.run_scheduler

# 또는 수동 전체 파이프라인 실행
python -c "import asyncio; from automation.scheduler import run_all_jobs; asyncio.run(run_all_jobs())"
```

### 5. 상태 확인

```powershell
curl http://localhost:8099/health
```

---

## 모듈 구조

```
automation/
├── config_auto.py          # 설정 (Pydantic BaseSettings, .env 로드)
├── logging_config.py       # 로그 (일일 파일 + 콘솔)
├── state_manager.py        # 체크포인트/재개
├── metrics.py              # 일일 지표
│
├── gemini_client.py        # [Primary] Google Gemini API 클라이언트
├── ollama_client.py        # [Fallback] Ollama REST API 클라이언트
├── prompt_templates.py     # 카테고리별 프롬프트 + 사실 정확성 규칙
├── menu_name_filter.py     # 메뉴명 품질 필터 (브랜드/매장/레시피 제거)
├── content_generator.py    # 콘텐츠 생성 (10필드 JSON — name_en 포함)
│
├── collectors/
│   ├── base_collector.py         # 수집기 추상 클래스
│   ├── wikipedia_collector.py    # Wikipedia 한식 카테고리
│   ├── public_data_collector.py  # data.go.kr 공공데이터
│   └── recipe_collector.py       # 만개의레시피 (robots.txt 준수)
├── menu_discovery.py       # 수집 오케스트레이터
│
├── image_collectors/
│   ├── base_image_collector.py   # 이미지 수집기 추상 클래스
│   ├── wikimedia_collector.py    # Wikimedia (CC 라이선스)
│   ├── unsplash_collector.py     # Unsplash (무료 50/hr)
│   └── pixabay_collector.py      # Pixabay (CC0)
├── image_matcher.py        # 이미지 매칭 (enriched name_en 기반)
│
├── scheduler.py            # APScheduler 일일 작업 정의
├── run_scheduler.py        # 메인 진입점
├── health.py               # HTTP 상태 확인 (:8099)
└── db_sync.py              # 프로덕션 DB 동기화 (SQL export 포함)
```

### 데이터 디렉토리

```
app/backend/data/automation/
├── state/          # 체크포인트 JSON (재개 가능)
├── staging/
│   ├── new_menus/  # 수집된 신규 메뉴 (discovery_*.json)
│   ├── export/     # SQL export 파일 (sync_*.sql)
│   └── enrichment_batch_*.json  # Gemini/Ollama 생성 콘텐츠
├── logs/           # 일일 로그 파일
└── metrics/        # 일일 지표 JSON
```

---

## LLM 클라이언트 사용법

### GeminiClient와 OllamaClient — 동일 인터페이스

두 클라이언트는 **동일한 메서드 시그니처**를 제공합니다.
`ContentGenerator`에 어떤 클라이언트든 주입 가능합니다.

```python
# 공통 인터페이스
async def is_available() -> bool
async def has_model(model_name: str = "") -> bool
async def generate(prompt: str, system: str = "", temperature: float = 0.3, max_tokens: int = 4096) -> Optional[str]
async def generate_json(prompt: str, system: str = "", temperature: float = 0.3, max_retries: int = 2) -> Optional[dict]
```

### Gemini 사용 (기본)

```python
from automation.gemini_client import GeminiClient
from automation.content_generator import ContentGenerator

client = GeminiClient()
generator = ContentGenerator(client)

# 연결 확인 (RPD 소모 없음)
if await generator.check_llm():
    result = await generator.enrich_menu({"name_ko": "김치찌개"})
    print(result)

# 일일 사용량 확인
print(client.get_daily_usage())
# → {"date": "2026-02-20", "used": 1, "limit": 20, "remaining": 19}
```

### Ollama 사용 (Fallback)

```python
from automation.ollama_client import OllamaClient
from automation.content_generator import ContentGenerator

client = OllamaClient()
generator = ContentGenerator(client)

if await generator.check_llm():
    result = await generator.enrich_menu({"name_ko": "김치찌개"})
    print(result)
```

> **OllamaClient 사전 요구**:
> 1. Ollama 서비스 실행: `ollama serve`
> 2. 모델 다운로드: `ollama pull qwen2.5:7b`
> 3. GPU 8GB+ VRAM 권장 (CPU도 가능하나 매우 느림)

### Hybrid 모드 구현 예시

```python
from automation.gemini_client import GeminiClient
from automation.ollama_client import OllamaClient
from automation.content_generator import ContentGenerator

async def hybrid_enrichment(menus: list):
    """Gemini 우선, RPD 소진 시 Ollama fallback"""
    gemini = GeminiClient()
    ollama = OllamaClient()

    results = []

    # Phase 1: Gemini로 고품질 처리 (최대 18건)
    if await gemini.is_available():
        gen_gemini = ContentGenerator(gemini)
        for menu in menus:
            if gemini.get_daily_usage()["remaining"] <= 0:
                break  # RPD 소진
            result = await gen_gemini.enrich_menu(menu)
            if result:
                results.append(result)

    # Phase 2: 남은 메뉴는 Ollama로 처리
    remaining = [m for m in menus if m["name_ko"] not in {r["name_ko"] for r in results}]
    if remaining and await ollama.is_available():
        gen_ollama = ContentGenerator(ollama)
        for menu in remaining:
            result = await gen_ollama.enrich_menu(menu)
            if result:
                results.append(result)

    return results
```

---

## 메뉴명 품질 필터

`menu_name_filter.py`가 수집된 메뉴명을 자동 정제합니다.

### 필터 규칙

| 규칙 | 예시 | 결과 |
|------|------|------|
| 브랜드 접두사 제거 | 농심어묵우동 | → 어묵우동 |
| 매장명 접두사 제거 | 교동짬뽕 | → 짬뽕 |
| 레시피 키워드 제거 | 감자전만들기 | → 감자전 |
| 특수문자 제거 | 라면EX라면 | → 라면 |
| 비음식 개념 필터 | 한국요리 | → None (제외) |
| 길이 제한 | 아 | → None (2자 미만) |

### 성능

- **유효율**: 100% (10/10, 2026-02-20 테스트)
- 개선 전 32% → 개선 후 100%

---

## 콘텐츠 생성 품질 보장

### 사실 정확성 규칙 (prompt_templates.py)

시스템 프롬프트에 **할루시네이션 방지 규칙**이 포함됩니다:

```
- 자장면/짜장면 → 반드시 춘장(검은콩 발효 소스). 절대 고추장 아님
- 짬뽕 → 매운 해물 국물 요리. 땅콩 소스 아님
- 제육 → 돼지고기. 소고기 아님
- 냉면 → 육수는 동치미/사골/겨자
```

### 검증 (validate_enrichment)

생성된 JSON은 자동으로 검증됩니다:

| 항목 | 최소 요구 |
|------|----------|
| description_ko | 존재 |
| description_en | 존재 |
| regional_variants | 2개 이상 |
| preparation_steps | 3개 이상 |
| similar_dishes | 2개 이상 |
| nutrition | 존재 |
| flavor_profile | 존재 |
| visitor_tips | 존재 |
| cultural_background | 존재 |

검증 실패 시 로그에 상세 원인이 기록됩니다:
```
Content validation failed for 자장면 | missing_keys=none | too_few=['regional_variants=1']
```

---

## 이미지 검색 전략

`image_matcher.py`는 enriched content의 **name_en**을 사용합니다.

```
검색 쿼리: "{name_en} Korean food"
예: "Kimchi-jjigae Korean food"
```

- name_en이 없는 메뉴는 이미지 검색 건너뜀
- 최소 크기: 300x300px
- 소스: Wikimedia Commons (CC) > Unsplash > Pixabay

---

## DB 동기화

### Export 모드 (기본)

`PRODUCTION_DATABASE_URL`이 없으면 SQL 파일을 생성합니다:

```sql
-- staging/export/sync_20260220_1332.sql
BEGIN;
INSERT INTO canonical_menus (id, name_ko, name_en, status, category_1)
VALUES (gen_random_uuid(), '된장국', 'Doenjang-guk', 'active', 'soups and stews')
ON CONFLICT (name_ko) DO NOTHING;
-- ...
COMMIT;
```

### Direct 모드

```env
PRODUCTION_DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

설정 시 asyncpg로 직접 INSERT/UPDATE합니다.

### None 값 방지

`_sanitize_value()` 함수가 자동으로 처리합니다:
- `None` → `""`
- `'None'` → `""`
- `'null'` → `""`
- `'N/A'` → `""`

---

## 개별 모듈 테스트

### Gemini 연결 확인

```python
import asyncio
from automation.gemini_client import GeminiClient

async def test():
    client = GeminiClient()
    print(f"Available: {await client.is_available()}")
    print(f"Usage: {client.get_daily_usage()}")
    result = await client.generate("김치찌개를 한 문장으로 설명해줘")
    print(result)

asyncio.run(test())
```

### Ollama 연결 확인

```python
import asyncio
from automation.ollama_client import OllamaClient

async def test():
    client = OllamaClient()
    print(f"Available: {await client.is_available()}")
    print(f"Has model: {await client.has_model()}")
    result = await client.generate("김치찌개를 한 문장으로 설명해줘")
    print(result)

asyncio.run(test())
```

### 메뉴 수집 테스트

```python
import asyncio
from automation.menu_discovery import MenuDiscovery

async def test():
    discovery = MenuDiscovery()
    await discovery.load_existing_names_from_file()
    result = await discovery.discover_daily(target=10)
    print(f"New menus: {result['total_new']}")
    for m in result['menus']:
        print(f"  {m['name_ko']} ({m['source']})")

asyncio.run(test())
```

### 이미지 수집 테스트

```python
import asyncio
from automation.image_matcher import ImageMatcher

async def test():
    matcher = ImageMatcher()
    images = await matcher.find_images_for_menu("김치찌개", "kimchi jjigae")
    for img in images:
        print(f"{img.source}: {img.url}")

asyncio.run(test())
```

### 메뉴명 필터 테스트

```python
from automation.menu_name_filter import filter_menu_name

tests = [
    ("농심어묵우동", "어묵우동"),     # 브랜드 제거
    ("교동짬뽕", "짬뽕"),             # 매장 제거
    ("감자전만들기", "감자전"),        # 레시피 제거
    ("한국요리", None),               # 비음식 개념
    ("김치찌개", "김치찌개"),          # 정상 통과
]

for input_name, expected in tests:
    result = filter_menu_name(input_name)
    status = "✓" if result == expected else "✗"
    print(f"  [{status}] {input_name} → {result} (expected: {expected})")
```

---

## 처리량 증대 전략

### 옵션 1: 다중 Gemini API 키 (가장 간단)

Google Cloud 프로젝트를 여러 개 만들면 각각 별도 RPD를 받습니다.

```
프로젝트 A → API 키 A → 20 RPD
프로젝트 B → API 키 B → 20 RPD
프로젝트 C → API 키 C → 20 RPD
합계: 60 RPD/일 → 58 메뉴/일
```

구현: `GeminiClient`를 키별로 인스턴스화하여 라운드 로빈.

### 옵션 2: Ollama Hybrid (GPU 있을 때)

```
Gemini: 18건/일 (고품질, 핵심 메뉴)
Ollama: 100+건/일 (중간 품질, 보조 메뉴)
합계: 118+ 메뉴/일
```

### 옵션 3: Gemini 유료 전환

Pay-as-you-go ($0.15/1M input tokens) 시 RPD 제한 해제.

| 일일 | 월 비용 | 메뉴/월 |
|------|---------|---------|
| 50 | ~$2 | 1,500 |
| 200 | ~$8 | 6,000 |

---

## Windows 서비스 등록 (선택)

### NSSM 사용

```powershell
nssm install MenuAutomation python.exe -m automation.run_scheduler
nssm set MenuAutomation AppDirectory C:\project\menu\app\backend\scripts
nssm start MenuAutomation
```

### Windows Task Scheduler 사용

```powershell
schtasks /create /tn "MenuAutomation" /tr "python -m automation.run_scheduler" /sc onstart /ru SYSTEM
```

---

## 무료 API 키 등록

| 서비스 | 등록 URL | 무료 한도 | 필수 |
|--------|---------|----------|------|
| **Google Gemini** | https://aistudio.google.com/app/apikey | 20 RPD | ✅ |
| Unsplash | https://unsplash.com/developers | 50 req/hr | 선택 |
| Pixabay | https://pixabay.com/api/docs/ | 100 req/min | 선택 |
| Wikimedia | 등록 불필요 | 무제한 | 선택 |

---

## 트러블슈팅

### Gemini 429 RESOURCE_EXHAUSTED

```
원인: 일일 RPD (20) 소진
해결: midnight UTC (09:00 KST) 이후 자동 리셋
확인: client.get_daily_usage() 호출
방지: GeminiClient가 429 수신 시 자동으로 당일 추가 호출 차단
```

### Gemini API 키 노출 경고

```
원인: API 키가 Git 등에 노출
해결:
1. https://aistudio.google.com/app/apikey 접속
2. 노출된 키 삭제
3. 새 키 생성
4. .env 파일 업데이트
주의: .env는 .gitignore에 포함되어 있어야 함
```

### Ollama 연결 실패

```powershell
# Ollama 서비스 상태 확인
ollama list
# 모델 없으면 다시 다운로드
ollama pull qwen2.5:7b
# 서비스 시작
ollama serve
```

### Ollama 품질 문제 (할루시네이션)

```
증상: 자장면을 고추장 요리로 설명, 짬뽕을 땅콩 소스로 설명
원인: Qwen2.5 7B의 한식 지식 한계
해결:
1. prompt_templates.py의 SYSTEM_PROMPT에 사실 정확성 규칙 추가
2. validate_enrichment()로 자동 검증
3. 검증 실패 시 Gemini로 재시도 (Hybrid 모드)
```

### APScheduler 미설치

스케줄러가 자동으로 simple_loop 모드로 전환됩니다 (1분 간격 체크).

### 프로덕션 DB 연결 실패

자동으로 SQL export 모드로 전환되어 `staging/export/` 디렉토리에 SQL 파일을 생성합니다.
서버에서 수동으로 실행하면 됩니다.

---

## 관련 문서

| 문서 | 경로 |
|------|------|
| 프로젝트 규칙 | `CLAUDE.md` |
| 공공데이터 API 가이드 | `docs/PUBLIC_DATA_API_GUIDE.md` |
| 개발 로드맵 | `ROADMAP.md` |
| Sprint 0 기획 | `SPRINT0_FINAL_PLAN_20260219.md` |
| FastComet 배포 가이드 | `C:\project\dev-reference\docs\FASTCOMET_DEPLOYMENT_GUIDE.md` |

---

**최종 수정**: 2026-02-20
**작성자**: terminal-developer
**비용**: $0 (Gemini 무료 + Ollama 로컬 + 공공데이터)
