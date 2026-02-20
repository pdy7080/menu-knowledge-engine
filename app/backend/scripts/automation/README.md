# Menu Automation System

사무실 PC (Windows, GPU 8-12GB, RAM 16GB, 24시간 가동)를 활용한
**비용 $0** 자동 메뉴 DB 확충 시스템.

## 목표

| 시점 | 메뉴 수 | 월 비용 |
|------|---------|--------|
| 현재 | 260 | - |
| 1개월 | 1,760 | $0 |
| 3개월 | 4,760 | $0 |
| 6개월 | 9,260 | $0 |

## 아키텍처

```
사무실 PC (Windows, 24시간 가동)
├── Ollama (Qwen2.5 7B) ─── 콘텐츠 생성 .............. $0
├── Collectors ───────────── 메뉴명 수집 .............. $0
├── Image Fetchers ──────── 이미지 수집 .............. $0
├── APScheduler ─────────── 매일 자동 실행
└── DB Sync ─────────────── FastComet 프로덕션 동기화
```

### 일일 스케줄

| 시간 | 작업 | 모듈 |
|------|------|------|
| 02:00 | 새 메뉴 수집 | `menu_discovery.py` |
| 04:00 | 콘텐츠 생성 (Ollama) | `content_generator.py` |
| 06:00 | 이미지 수집 | `image_matcher.py` |
| 08:00 | 프로덕션 DB 동기화 | `db_sync.py` |

## 빠른 시작

### 1. 사전 요구사항

```powershell
# Ollama 설치 (https://ollama.com/download/windows)
ollama pull qwen2.5:7b

# Python 의존성
pip install apscheduler beautifulsoup4 lxml sshtunnel
```

### 2. 환경변수 설정

`app/backend/.env`에 추가:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
UNSPLASH_ACCESS_KEY=your_key      # https://unsplash.com/developers
PIXABAY_API_KEY=your_key          # https://pixabay.com/api/docs/
AUTOMATION_ENABLED=true
DAILY_MENU_TARGET=50
```

### 3. 실행

```powershell
# 스케줄러 시작 (24시간 구동)
cd app\backend\scripts
python -m automation.run_scheduler

# 또는 수동 전체 파이프라인 실행
python -c "import asyncio; from automation.scheduler import run_all_jobs; asyncio.run(run_all_jobs())"
```

### 4. 상태 확인

```powershell
curl http://localhost:8099/health
```

## 모듈 구조

```
automation/
├── config_auto.py          # 설정 (Pydantic BaseSettings)
├── logging_config.py       # 로그 (일일 파일 + 콘솔)
├── state_manager.py        # 체크포인트/재개
├── metrics.py              # 일일 지표
│
├── ollama_client.py        # Ollama REST API 클라이언트
├── prompt_templates.py     # 카테고리별 프롬프트
├── content_generator.py    # 콘텐츠 생성 (9필드 JSON)
│
├── collectors/
│   ├── base_collector.py         # 수집기 추상 클래스
│   ├── wikipedia_collector.py    # Wikipedia 한식 카테고리
│   ├── public_data_collector.py  # data.go.kr 후보 데이터
│   └── recipe_collector.py       # 만개의레시피 (robots.txt 준수)
├── menu_discovery.py       # 수집 오케스트레이터
│
├── image_collectors/
│   ├── base_image_collector.py   # 이미지 수집기 추상 클래스
│   ├── wikimedia_collector.py    # Wikimedia (CC 라이선스)
│   ├── unsplash_collector.py     # Unsplash (무료 50/hr)
│   └── pixabay_collector.py      # Pixabay (CC0)
├── image_matcher.py        # 이미지 매칭 오케스트레이터
│
├── scheduler.py            # APScheduler 일일 작업 정의
├── run_scheduler.py        # 메인 진입점
├── health.py               # HTTP 상태 확인 (:8099)
└── db_sync.py              # 프로덕션 DB 동기화
```

## 데이터 디렉토리

```
app/backend/data/automation/
├── state/          # 체크포인트 JSON (재개 가능)
├── staging/
│   ├── new_menus/  # 수집된 신규 메뉴
│   ├── enriched/   # Ollama 생성 콘텐츠
│   ├── images/     # 다운로드된 이미지
│   └── export/     # SQL export 파일
├── logs/           # 일일 로그 파일
└── metrics/        # 일일 지표 JSON
```

## 개별 모듈 테스트

### Ollama 연결 확인

```python
import asyncio
from automation.ollama_client import OllamaClient

async def test():
    client = OllamaClient()
    print(f"Available: {await client.is_available()}")
    print(f"Has model: {await client.has_model()}")
    result = await client.generate("김치찌개를 설명해줘")
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
    result = await discovery.discover_daily()
    print(f"New menus: {result['total_new']}")

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

## Windows 서비스 등록 (선택)

### NSSM 사용

```powershell
# NSSM 설치 (https://nssm.cc/download)
nssm install MenuAutomation python.exe -m automation.run_scheduler
nssm set MenuAutomation AppDirectory C:\project\menu\app\backend\scripts
nssm start MenuAutomation
```

### Windows Task Scheduler 사용

```powershell
# 부팅 시 자동 시작
schtasks /create /tn "MenuAutomation" /tr "python -m automation.run_scheduler" /sc onstart /ru SYSTEM
```

## 무료 API 키 등록

| 서비스 | 등록 URL | 무료 한도 |
|--------|---------|----------|
| Unsplash | https://unsplash.com/developers | 50 req/hr |
| Pixabay | https://pixabay.com/api/docs/ | 100 req/min |
| Wikimedia | 등록 불필요 | 무제한 (User-Agent만) |

## 트러블슈팅

### Ollama 연결 실패
```powershell
# Ollama 서비스 상태 확인
ollama list
# 모델 없으면 다시 다운로드
ollama pull qwen2.5:7b
```

### APScheduler 미설치
스케줄러가 자동으로 simple_loop 모드로 전환됩니다 (1분 간격 체크).

### 프로덕션 DB 연결 실패
자동으로 SQL export 모드로 전환되어 `staging/export/` 디렉토리에 SQL 파일을 생성합니다.
서버에서 수동으로 실행하면 됩니다.
