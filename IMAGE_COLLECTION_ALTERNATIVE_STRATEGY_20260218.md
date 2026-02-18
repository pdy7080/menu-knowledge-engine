# 이미지 수집 대체 전략 연구 (한국관광공사 API 대체)

**작성일**: 2026-02-18
**상황**: 한국관광공사 API 오류 → 대체 방안 필요
**목표**: 한국 중심 이미지 수집 루트 재설계

---

## 🔍 한국관광공사 API 문제 분석

### 현황
- ❌ API 오류 상태 (현재 작동 불가)
- ❌ 웹사이트에 우리가 원하는 음식 이미지 정보 부족
- ❌ 직접 활용 불가능

### 결론
**공식 API → 대체 크롤링/데이터 수집 방식으로 전환**

---

## ✅ 대체 방안 (우선순위순)

### **우선 1순위: 공공데이터포탈 (data.go.kr)**

#### 검색 가능한 데이터셋

```
1. "한국음식 영양정보" - 식약청
   ├── 메뉴명, 영양정보 (칼로리, 단백질 등)
   ├── 조리재료
   └── 이미지 있음 (일부)

2. "음식 알레르기 정보" - 식약청
   ├── 메뉴별 알레르기 정보
   └── 재료 정보

3. "전통음식 정보" - 문화재청
   ├── 한국 전통음식 설명
   ├── 역사 정보
   ├── 조리법
   └── 이미지

4. "지역 특산 음식" - 각 도청/시청
   ├── 지역별 음식 목록
   ├── 설명
   └── 이미지 (일부)

5. "음식점 정보" - 소상공인진흥공단
   ├── 식당 정보
   ├── 음식 카테고리
   └── 메뉴정보
```

**접근 방법**:
```python
# 공공데이터포탈 API (인증키 필수)
# https://www.data.go.kr/

import requests

api_url = "https://api.odcloud.kr/api/15000221/v1/uddi:certy:0a58c8f8-4e4d-4a2a-be0a-5e81f7e07bdc"
api_key = "YOUR_API_KEY"  # 공공데이터포탈에서 무료 발급

params = {
    "serviceKey": api_key,
    "limit": 1000
}

response = requests.get(api_url, params=params)
data = response.json()
```

**예상 수집 가능**: **50-100개 메뉴정보 + 이미지**

---

### **우선 2순위: 네이버 지식백과 크롤링**

#### 장점
- ✅ 한국 음식 정보 매우 상세
- ✅ 이미지 고품질
- ✅ 지역별 정보 풍부
- ✅ 접근 용이

#### 단점
- ⚠️ 저작권 확인 필요
- ⚠️ 네이버 약관 준수 필요
- ⚠️ Robots.txt 준수

#### 수집 방법

```python
# 네이버 지식백과 크롤링 (한국 음식 항목)
# 저작권: 일부 CC, 일부 저작권 있음 → 명시 필수

from selenium import webdriver
from bs4 import BeautifulSoup
import time

driver = webdriver.Chrome()

# 검색 항목들
menus = [
    "비빔밥", "불고기", "갈비", "김치찌개", "떡볶이",
    "냉면", "돈까스", "한우", "낙지탕", "추어탕"
]

results = []

for menu in menus:
    url = f"https://terms.naver.com/search.naver?query={menu}&searchtype=0"
    driver.get(url)
    time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # 지식백과 항목 추출
    article = soup.find('div', class_='se_doc')
    if article:
        title = soup.find('h2', class_='title').text
        description = soup.find('div', class_='dsc').text
        image = soup.find('img')

        results.append({
            'menu': menu,
            'title': title,
            'description': description,
            'image_url': image['src'] if image else None,
            'source': 'Naver Knowledge Encyclopedia'
        })

driver.quit()
```

**예상 수집 가능**: **80-120개 메뉴 + 이미지**

---

### **우선 3순위: 위키피디아 한국어 (이미 준비)**

#### 특징
- ✅ CC-BY-SA 라이선스 (명확한 저작권)
- ✅ 100+ 한국 음식 항목
- ✅ 영어 버전과 교차검증 가능

#### 수집 방법 (이미 검증됨)
```python
from mediawiki import MediaWiki

wiki = MediaWiki(lang='ko')

menus = ["비빔밥", "불고기", "갈비", ...]

for menu in menus:
    try:
        page = wiki.page(menu)
        content = page.content
        images = page.images
        # 데이터 저장
    except:
        pass  # 항목 없으면 스킵
```

**예상 수집 가능**: **60-80개 메뉴 + 이미지**

---

### **우선 4순위: 농촌진흥청 (Rural Development Administration)**

#### 특징
- ✅ 공개 데이터 (CC0)
- ✅ 음식 영양정보 풍부
- ✅ 조리법 상세

#### 접근 방법
```python
# 농촌진흥청 음식 정보 API
# https://www.rda.go.kr/

# 검색 가능한 정보:
# - 음식 영양정보
# - 조리법
# - 이미지
```

**예상 수집 가능**: **30-50개 메뉴 + 영양정보**

---

### **우선 5순위: Google Images + Bing Images 크롤링**

#### 특징
- ✅ 가장 많은 이미지 확보 가능
- ✅ 다양한 스타일의 음식 사진
- ⚠️ 저작권 확인 필수

#### 수집 방법
```python
from bing_image_downloader import bing_image_downloader

menus = ["비빔밥", "불고기", "갈비", ...]

for menu in menus:
    bing_image_downloader.download(
        menu,
        limit=5,  # 메뉴당 5개 이미지
        output_dir="dataset",
        adult_filter_off=True,
        force_replace=False
    )
```

**예상 수집 가능**: **100-200개 이미지 (저작권 확인 필요)**

---

### **우선 6순위: 각 지역 도청/시청 관광정보**

#### 특징
- ✅ 지역별 특산 음식 정보
- ✅ 공개 데이터
- ⚠️ 사이트마다 다름

#### 예시
```
서울특별시: https://www.seoul.go.kr/
├── 서울음식 정보
├── 지역별 음식 리스트
└── 이미지

전주시: https://www.jeonju.go.kr/
├── 전주 비빔밥, 전주 한우
└── 지역 특화 음식

제주도: https://www.jeju.go.kr/
├── 제주 흑돼지
├── 제주 해산물
└── 지역 음식
```

**예상 수집 가능**: **30-50개 지역별 메뉴**

---

### **우선 7순위: 한국식문화재단 + 전통음식 관련 기관**

#### 기관 목록
```
1. 한국식문화재단 (Korean Food Foundation)
   - 공식 한국 전통음식 정보
   - 이미지 + 설명

2. 한국음식진흥원 (Korean Food Promotion Board)
   - 한국음식 홍보 자료
   - 영문 정보 풍부

3. 한식재단 (Korea Foundation for International Cultural Exchange)
   - 전통음식 문화 정보

4. 한국문화정보원 (Korean Culture Information Service)
   - 문화 자료 + 이미지
```

**접근 방법**: 각 사이트의 개방 API 또는 데이터 다운로드

**예상 수집 가능**: **40-60개 메뉴 + 고품질 이미지**

---

## 🎯 **최종 통합 전략 (수정된 Phase 1)**

### 이미지 수집 Tier 재설계

```
Tier 1: 공공데이터 + 공개 API (무료)
├─ 공공데이터포탈 → 50-100개
├─ 위키피디아 한국어 → 60-80개
├─ 농촌진흥청 → 30-50개
└─ 합계: 140-230개 ✅

Tier 2: 웹 크롤링 (저작권 확인)
├─ 네이버 지식백과 → 80-120개 (명시 필수)
├─ 각 지역 도청/시청 → 30-50개
└─ 한국식문화재단 → 40-60개
   합계: 150-230개

Tier 3: 이미지 검색 엔진 (저작권 필터링)
├─ Google Images → 50-100개 (CC라이선스만)
├─ Bing Images → 50-100개 (CC라이선스만)
└─ 합계: 100-200개

전체 예상: 390-660개 이미지 수집 가능 ✅
```

---

## 📋 **구체적 실행 계획 (수정된 Day 1-4)**

### **Day 1: 공공데이터포탈 API**

```python
# 1. 공공데이터포탈 회원가입 및 API 키 발급
# 사이트: https://www.data.go.kr/
# 시간: 30분

# 2. 한국음식 영양정보 API 연결
import requests

api_url = "https://api.odcloud.kr/api/15000221/v1/uddi:certy:..."
api_key = "YOUR_KEY"

def fetch_food_data():
    params = {
        "serviceKey": api_key,
        "limit": 1000,
        "offset": 0
    }
    response = requests.get(api_url, params=params)
    return response.json()

# 3. 결과: 50-100개 메뉴 정보 + 일부 이미지
# 시간: 2시간
```

---

### **Day 1-2: 위키피디아 크롤링**

```python
# 이미 준비된 코드
from mediawiki import MediaWiki

wiki_ko = MediaWiki(lang='ko')
wiki_en = MediaWiki(lang='en')

menus = [
    "비빔밥", "불고기", "갈비", "김치찌개", "떡볶이",
    "냉면", "돈까스", "한우", "낙지탕", "추어탕",
    # ... 100+ 항목
]

results = []
for menu in menus:
    try:
        ko_page = wiki_ko.page(menu)
        en_page = wiki_en.page(translate_korean_to_english(menu))

        results.append({
            'menu': menu,
            'ko_content': ko_page.content,
            'en_content': en_page.content,
            'images': ko_page.images,
            'source': 'Wikipedia Korean'
        })
    except:
        pass

# 결과: 60-80개 메뉴 + 이미지
# 시간: 1시간 (API 호출만)
```

---

### **Day 2: 네이버 지식백과 크롤링**

```python
# 저작권 명시 크롤링
from selenium import webdriver
import time

driver = webdriver.Chrome()
results = []

menus = [...]  # 100+ 메뉴

for menu in menus:
    url = f"https://terms.naver.com/search.naver?query={menu}"
    driver.get(url)
    time.sleep(0.3)

    # 지식백과 항목 추출
    # (상세 코드 생략)

    # 주의: 저작권 명시
    results.append({
        'menu': menu,
        'source': 'Naver Knowledge Encyclopedia',
        'license': 'Check individual copyright',
        'image': image_url
    })

# 결과: 80-120개 메뉴 + 이미지
# 시간: 2시간
# 주의: 저작권 명시 필수 ⚠️
```

---

### **Day 3: 지역별 도청/시청 + 농촌진흥청**

```python
# 지역별 데이터 수집
regional_sources = {
    "서울": "https://www.seoul.go.kr/",
    "전주": "https://www.jeonju.go.kr/",
    "제주": "https://www.jeju.go.kr/",
    # ... 16개 시도
}

# 농촌진흥청 API
rda_api = "https://api.rda.go.kr/..."

# 결과: 60-100개 메뉴 + 이미지
# 시간: 2시간 (자동화)
```

---

### **Day 4: Google/Bing Images (CC 라이선스만)**

```python
from bing_image_downloader import bing_image_downloader
import requests

menus = [...]

for menu in menus:
    # CC0/CC-BY 라이선스만 필터링
    download_images_with_license_filter(
        menu,
        licenses=['cc0', 'cc-by', 'cc-by-sa'],
        limit=5
    )

# 결과: 50-100개 이미지 (저작권 필터링)
# 시간: 1시간 (자동화)
```

---

## 📊 **수정된 예상 결과**

```
이미지 수집 결과 (Day 1-4)
├─ 공공데이터포탈: 50-100개
├─ 위키피디아: 60-80개
├─ 네이버 지식백과: 80-120개 (명시 필수)
├─ 지역/농촌진흥청: 60-100개
├─ Google/Bing: 50-100개 (CC라이선스)
└─ 총합: 300-600개 이미지 ✅

메뉴 커버리지
├─ 정확한 이미지: 100-150개 메뉴
├─ 부분 정보: 50-100개 메뉴
└─ AI 생성으로 보충: 30-50개 메뉴
   총합: 100-200개 메뉴 완성 ✅
```

---

## 🎯 **핵심 원칙**

### 저작권 관리
```
✅ 필수 명시:
1. 공공데이터포탈 → "출처: 공공데이터포탈 (식약청/문화재청)"
2. 위키피디아 → "CC-BY-SA-4.0 라이선스"
3. 네이버 → "출처: 네이버 지식백과 [작가명]"
4. Google/Bing → "CC0/CC-BY 라이선스"

❌ 피할 것:
- 저작권 불명확한 이미지
- 상업용 저작권 이미지
- 개인 블로그 무단 수집
```

---

## 📝 **수정된 Phase 1 일정**

```
주차 1: 데이터 수집 (공공 API + 크롤링)
├─ Day 1: 공공데이터포탈 (50-100개)
├─ Day 1-2: 위키피디아 (60-80개)
├─ Day 2: 네이버 지식백과 (80-120개) ⚠️ 저작권 명시
├─ Day 3: 지역/농촌진흥청 (60-100개)
├─ Day 4: Google/Bing CC이미지 (50-100개)
└─ 합계: 300-600개 이미지 수집 ✅

주차 2: AI 이미지 보충 (6시간)
├─ DALL-E 3로 부족한 부분 생성
├─ 지역별 변종 생성
└─ 예산: $4.80

주차 3-4: 콘텐츠 + API + UI + 배포
└─ (기존 계획과 동일)
```

---

## ✅ **즉시 시작할 작업**

### **Day 1 (지금 바로)**

1. **공공데이터포탈 가입**
   - 사이트: https://www.data.go.kr/
   - 회원가입 → API 키 발급
   - 예상: 30분

2. **검색할 데이터셋 확인**
   - "한국음식 영양정보" (식약청)
   - "전통음식 정보" (문화재청)
   - "음식점 정보" (소상공인진흥공단)

3. **위키피디아 스크립트 준비** (이미 준비됨)
   - 100+ 한국 음식 항목 리스트 작성

4. **네이버 크롤링 준비** ⚠️ 저작권 명시
   - Selenium/BeautifulSoup 스크립트
   - 저작권 명시 규칙 설정

---

## 🎯 **결론**

**한국관광공사 API 오류 → 다중 출처 전략으로 전환**

- ✅ 공공데이터 + API (무료, 신뢰도 높음)
- ✅ 웹 크롤링 (저작권 명시)
- ✅ 이미지 검색 (CC라이선스만)
- ✅ AI 생성 (DALL-E로 보충)

**예상 결과**: 300-600개 이미지 + 100-200개 메뉴 완전 정보

---

**제안**: 이 전략으로 **Day 1부터 즉시 시작**하겠습니다!

작성: Claude Code
날짜: 2026-02-18
우선순위: **P0 (Critical)**
