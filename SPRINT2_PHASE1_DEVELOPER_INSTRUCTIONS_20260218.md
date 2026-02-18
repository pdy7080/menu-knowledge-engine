# Sprint 2 Phase 1 개발자 실행 지시서
## 한국 중심 이미지 수집 + 전문적 콘텐츠 (대체 전략)

**작성일**: 2026-02-18
**대상**: 터미널 개발자 (Backend + Frontend)
**상태**: 🚀 **즉시 실행 가능**
**예상 기간**: 3-4주 (56시간)

---

## ⚡ 빠른 요약

### 상황 변경
- ❌ 한국관광공사 API: 현재 오류 (직접 사용 불가)
- ✅ 대체 전략: 공공데이터포탈 + 크롤링 + 위키피디아

### 목표
100개 메뉴 × 3-5개 이미지 = **완전한 이미지 + 전문적 콘텐츠**

### 예상 결과
- 이미지: 300-600개 수집
- 메뉴: 100-200개 완전 정보
- 비용: $4.80 (DALL-E 3)

---

## 📋 **주차 1: 이미지 수집 (Days 1-4, 8시간)**

### **Day 1 (2시간): 공공데이터포탈 API 구축**

#### Step 1: 공공데이터포탈 가입 & API 키 발급 (30분)
```bash
# 1. 사이트 접속
https://www.data.go.kr/

# 2. 회원가입 → API 키 발급
# 3. API 키 복사 → 환경변수 설정

export ODCLOUD_API_KEY="YOUR_API_KEY"
```

#### Step 2: Python 스크립트 작성 (1.5시간)

**파일**: `app/backend/scripts/collect_public_data_images.py`

```python
#!/usr/bin/env python3
"""
공공데이터포탈에서 한국음식 정보 수집
- 데이터: 한국음식 영양정보, 전통음식, 음식점 정보
- 출처: 식약청, 문화재청, 소상공인진흥공단
"""

import os
import requests
import json
from typing import List, Dict

class PublicDataCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.odcloud.kr/api"

    def fetch_food_nutrition(self) -> List[Dict]:
        """한국음식 영양정보 수집"""
        print("🔄 공공데이터포탈: 한국음식 영양정보 수집 중...")

        # 데이터셋 ID (식약청 제공)
        dataset_id = "15000221"  # 예시 ID

        api_url = f"{self.base_url}/{dataset_id}/v1/uddi:certy:..."

        params = {
            "serviceKey": self.api_key,
            "limit": 1000,
            "offset": 0
        }

        try:
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            records = data.get('response', {}).get('body', {}).get('items', [])
            print(f"✅ 수집 완료: {len(records)}개 항목")

            return records
        except Exception as e:
            print(f"❌ 오류: {e}")
            return []

    def save_to_json(self, data: List[Dict], filename: str):
        """JSON으로 저장"""
        output_path = f"app/backend/data/{filename}"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"💾 저장 완료: {output_path}")

if __name__ == "__main__":
    api_key = os.getenv("ODCLOUD_API_KEY")
    if not api_key:
        print("❌ API 키 설정 필요: export ODCLOUD_API_KEY='YOUR_KEY'")
        exit(1)

    collector = PublicDataCollector(api_key)
    data = collector.fetch_food_nutrition()
    collector.save_to_json(data, "public_food_data.json")
```

#### Step 3: 스크립트 실행 & 검증 (30분)

```bash
# 1. 실행
cd app/backend
python scripts/collect_public_data_images.py

# 2. 결과 확인
ls -lh app/backend/data/public_food_data.json

# 3. 확인사항
# ✅ 50-100개 항목 수집 확인
# ✅ 메뉴명, 영양정보, 이미지 URL 포함 확인
# ✅ JSON 형식 검증
```

---

### **Day 1-2 (1.5시간): 위키피디아 한국어 크롤링**

#### Step 1: 스크립트 준비 (30분)

**파일**: `app/backend/scripts/collect_wikipedia_images.py`

```python
#!/usr/bin/env python3
"""
위키피디아 한국어에서 한국음식 정보 수집
- 라이선스: CC-BY-SA-4.0
- 출처: Korean Wikipedia
"""

from mediawiki import MediaWiki
import json
import os

class WikipediaCollector:
    def __init__(self):
        self.wiki_ko = MediaWiki(lang='ko')
        self.wiki_en = MediaWiki(lang='en')

    def collect_korean_foods(self) -> List[Dict]:
        """한국 음식 항목 수집"""
        print("🔄 위키피디아: 한국음식 정보 수집 중...")

        menus = [
            "비빔밥", "불고기", "갈비", "김치찌개", "떡볶이",
            "냉면", "돈까스", "한우", "낙지탕", "추어탕",
            # ... 100+ 항목
        ]

        results = []

        for menu in menus:
            try:
                ko_page = self.wiki_ko.page(menu)

                # 영문 정보도 가져오기
                en_menu = self._translate_korean_to_english(menu)
                en_page = self.wiki_en.page(en_menu)

                item = {
                    'menu_ko': menu,
                    'menu_en': en_menu,
                    'ko_content': ko_page.content[:500],  # 처음 500자
                    'en_content': en_page.content[:500],
                    'images': ko_page.images[:3],  # 처음 3개 이미지
                    'source': 'Wikipedia Korean',
                    'license': 'CC-BY-SA-4.0'
                }

                results.append(item)
                print(f"✅ {menu}: {len(ko_page.images)} 이미지")

            except Exception as e:
                print(f"⏭️  {menu}: 스킵 ({e})")

        return results

    def _translate_korean_to_english(self, menu: str) -> str:
        """한글을 영문으로 번역 (하드코딩)"""
        translation_map = {
            "비빔밥": "Bibimbap",
            "불고기": "Bulgogi",
            "갈비": "Galbi",
            # ... 더 많은 항목
        }
        return translation_map.get(menu, menu)

    def save_to_json(self, data: List[Dict], filename: str):
        output_path = f"app/backend/data/{filename}"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"💾 저장 완료: {output_path}")

if __name__ == "__main__":
    collector = WikipediaCollector()
    data = collector.collect_korean_foods()
    collector.save_to_json(data, "wikipedia_food_data.json")
    print(f"\n✅ 총 {len(data)}개 메뉴 수집")
```

#### Step 2: 스크립트 실행

```bash
python scripts/collect_wikipedia_images.py

# 예상 결과:
# ✅ 총 60-80개 메뉴 수집
# ✅ 각 메뉴별 이미지 3-5개
# ✅ CC-BY-SA-4.0 라이선스 명시
```

---

### **Day 2 (2시간): 네이버 지식백과 크롤링**

**⚠️ 중요: 저작권 명시 필수**

**파일**: `app/backend/scripts/collect_naver_images.py`

```python
#!/usr/bin/env python3
"""
네이버 지식백과에서 한국음식 정보 수집
⚠️  저작권: 항목별로 명시 필수
"""

from selenium import webdriver
from bs4 import BeautifulSoup
import time
import json

class NaverEncyclopediaCollector:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.base_url = "https://terms.naver.com/search.naver"

    def collect_foods(self, menus: List[str]) -> List[Dict]:
        """네이버 지식백과에서 음식 정보 수집"""
        print("🔄 네이버 지식백과: 한국음식 정보 수집 중...")

        results = []

        for menu in menus:
            try:
                # URL 구성
                url = f"{self.base_url}?query={menu}&searchtype=0"
                self.driver.get(url)
                time.sleep(0.5)

                soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                # 지식백과 항목 추출
                article = soup.find('div', class_='se_doc')
                if not article:
                    continue

                title = soup.find('h2', class_='title')
                description = soup.find('div', class_='dsc')
                image = soup.find('img', class_='img')

                item = {
                    'menu': menu,
                    'title': title.text if title else None,
                    'description': description.text if description else None,
                    'image_url': image['src'] if image else None,
                    'source': 'Naver Knowledge Encyclopedia',
                    'license': 'Check individual (Naver Terms)',
                    'copyright_notice': 'Content may be copyrighted - check Naver Terms of Use'
                }

                results.append(item)
                print(f"✅ {menu}: {item['title']}")

            except Exception as e:
                print(f"⏭️  {menu}: 스킵 ({e})")

            time.sleep(0.2)  # Rate limiting

        self.driver.quit()
        return results

    def save_to_json(self, data: List[Dict], filename: str):
        output_path = f"app/backend/data/{filename}"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 저장 완료: {output_path}")

if __name__ == "__main__":
    menus = [...]  # 100+ 메뉴 리스트

    collector = NaverEncyclopediaCollector()
    data = collector.collect_foods(menus)
    collector.save_to_json(data, "naver_food_data.json")
    print(f"\n✅ 총 {len(data)}개 메뉴 수집")
```

실행:
```bash
python scripts/collect_naver_images.py

# 예상 결과:
# ✅ 총 80-120개 메뉴 수집
# ⚠️  저작권 명시 확인: Copyright notice 필드 포함
```

---

### **Day 3 (1.5시간): 이미지 통합 & S3 업로드**

**파일**: `app/backend/scripts/merge_images_to_s3.py`

```python
#!/usr/bin/env python3
"""
수집한 이미지들을 통합하여 S3에 업로드
- 공공데이터포탈
- 위키피디아
- 네이버
- Google/Bing (나중)
"""

import json
import boto3
import requests
from typing import List, Dict

class ImageS3Uploader:
    def __init__(self, bucket_name: str, region: str):
        self.s3_client = boto3.client('s3', region_name=region)
        self.bucket_name = bucket_name

    def merge_image_sources(self) -> List[Dict]:
        """모든 출처의 이미지 통합"""
        print("🔄 이미지 통합 중...")

        merged = {}

        # 1. 공공데이터포탈 데이터
        with open('app/backend/data/public_food_data.json', 'r', encoding='utf-8') as f:
            public_data = json.load(f)

        for item in public_data:
            menu = item.get('menu_name')
            if menu not in merged:
                merged[menu] = {'images': [], 'metadata': {}}

            merged[menu]['images'].append({
                'url': item.get('image_url'),
                'source': 'Public Data Portal (Ministry of Food and Drug Safety)',
                'license': 'CC0'
            })

        # 2. 위키피디아 데이터
        with open('app/backend/data/wikipedia_food_data.json', 'r', encoding='utf-8') as f:
            wiki_data = json.load(f)

        for item in wiki_data:
            menu = item.get('menu_ko')
            if menu not in merged:
                merged[menu] = {'images': [], 'metadata': {}}

            for image_url in item.get('images', [])[:2]:
                merged[menu]['images'].append({
                    'url': image_url,
                    'source': 'Wikipedia Korean',
                    'license': 'CC-BY-SA-4.0'
                })

        # 3. 네이버 데이터
        with open('app/backend/data/naver_food_data.json', 'r', encoding='utf-8') as f:
            naver_data = json.load(f)

        for item in naver_data:
            menu = item.get('menu')
            if menu not in merged:
                merged[menu] = {'images': [], 'metadata': {}}

            merged[menu]['images'].append({
                'url': item.get('image_url'),
                'source': 'Naver Knowledge Encyclopedia',
                'license': 'Check individual',  # ⚠️  저작권 확인 필요
                'copyright_notice': item.get('copyright_notice')
            })

        return merged

    def upload_to_s3(self, merged_data: Dict):
        """S3에 이미지 및 메타데이터 업로드"""
        print(f"🔄 S3 업로드 중 ({len(merged_data)} 메뉴)...")

        for menu, data in merged_data.items():
            # 메타데이터 파일 생성
            metadata = {
                'menu_ko': menu,
                'images': data['images'],
                'collection_date': '2026-02-18'
            }

            # S3에 업로드
            key = f"canonical/metadata/{menu}.json"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(metadata, ensure_ascii=False),
                ContentType='application/json'
            )

            print(f"✅ {menu}: {len(data['images'])} 이미지")

        print("✅ S3 업로드 완료")

if __name__ == "__main__":
    uploader = ImageS3Uploader(
        bucket_name='menu-knowledge-images',
        region='us-east-1'
    )

    merged_data = uploader.merge_image_sources()
    uploader.upload_to_s3(merged_data)
```

실행:
```bash
python scripts/merge_images_to_s3.py

# 예상 결과:
# ✅ 300-600개 이미지 수집
# ✅ S3에 메타데이터 업로드
# ✅ 저작권 정보 포함
```

---

### **Day 4 (1시간): 이미지 검증 & DB 준비**

```bash
# 1. S3 이미지 확인
aws s3 ls s3://menu-knowledge-images/canonical/metadata/ | wc -l

# 2. 샘플 메타데이터 확인
aws s3 cp s3://menu-knowledge-images/canonical/metadata/비빔밥.json - | jq .

# 3. 예상
# ✅ 100-150개 메뉴 메타데이터 저장
# ✅ 각 메뉴별 3-5개 이미지 링크
# ✅ 저작권 정보 포함
```

---

## 📋 **주차 2: 콘텐츠 강화 (Days 5-10, 15시간)**

### **Day 5-6 (4시간): 콘텐츠 자동 수집 & 번역**

**파일**: `app/backend/scripts/enrich_content.py`

```python
#!/usr/bin/env python3
"""
수집한 이미지 메타데이터를 바탕으로 콘텐츠 강화
- 공공데이터 → 영양정보
- 위키피디아 → 설명, 역사
- GPT-4 → 번역, 확장
"""

import json
import openai
from typing import Dict

class ContentEnricher:
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key

    def enrich_menu_content(self, menu: str, description: str) -> Dict:
        """GPT-4를 사용하여 콘텐츠 강화"""

        prompt = f"""
        한국 음식: {menu}
        기본 설명: {description}

        다음 정보를 JSON 형식으로 생성해주세요:
        {{
            "description_short": "1줄 짧은 설명",
            "description_long": "3-4 문장 긴 설명",
            "origin": "역사/유래",
            "flavor_profile": {{
                "spice_level": 1-5,
                "taste_notes": ["맛 특성들"]
            }},
            "visitor_tips": {{
                "ordering": "주문 방법",
                "eating": "먹는 방법"
            }}
        }}
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        return json.loads(response['choices'][0]['message']['content'])

    def process_all_menus(self, metadata_list: List[Dict]) -> List[Dict]:
        """모든 메뉴 콘텐츠 강화"""
        print("🔄 콘텐츠 강화 중...")

        enriched = []

        for meta in metadata_list:
            menu = meta.get('menu_ko')
            description = meta.get('description', '')

            try:
                enriched_content = self.enrich_menu_content(menu, description)

                merged = {**meta, **enriched_content}
                enriched.append(merged)

                print(f"✅ {menu}: 강화 완료")

            except Exception as e:
                print(f"⏭️  {menu}: 스킵 ({e})")

        return enriched

if __name__ == "__main__":
    # 메타데이터 로드
    with open('app/backend/data/merged_metadata.json', 'r', encoding='utf-8') as f:
        metadata_list = json.load(f)

    enricher = ContentEnricher(api_key=os.getenv('OPENAI_API_KEY'))
    enriched_data = enricher.process_all_menus(metadata_list)

    # 저장
    with open('app/backend/data/enriched_content.json', 'w', encoding='utf-8') as f:
        json.dump(enriched_data, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(enriched_data)}개 메뉴 강화 완료")
```

---

### **Day 7-9 (8시간): DB 마이그레이션 & 데이터 로드**

**파일**: `app/backend/migrations/phase1_images_content.sql`

```sql
-- 1. canonical_menus 테이블 확장
ALTER TABLE canonical_menus ADD COLUMN IF NOT EXISTS (
    primary_image JSONB,
    images JSONB[],
    description_long_en TEXT,
    description_long_ko TEXT,
    regional_variants JSONB,
    preparation_steps JSONB,
    nutrition_detail JSONB,
    flavor_profile JSONB,
    visitor_tips JSONB,
    similar_dishes JSONB[],
    content_completeness DECIMAL(5,2),
    verified_by TEXT,
    verified_date TIMESTAMP
);

-- 2. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_canonical_images ON canonical_menus USING GIN(images);
CREATE INDEX IF NOT EXISTS idx_canonical_completeness ON canonical_menus(content_completeness DESC);

-- 3. 샘플 데이터 삽입 (Python 스크립트에서 수행)
```

**파일**: `app/backend/scripts/load_enriched_data.py`

```python
#!/usr/bin/env python3
"""
강화된 콘텐츠를 DB에 로드
"""

import json
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DataLoader:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def load_enriched_data(self, enriched_data: List[Dict]):
        """DB에 데이터 로드"""
        print("🔄 DB 로드 중...")

        session = self.Session()

        for data in enriched_data:
            menu_name = data.get('menu_ko')

            # 기존 메뉴 확인
            existing = session.query(CanonicalMenu).filter_by(
                name_ko=menu_name
            ).first()

            if existing:
                # 업데이트
                existing.primary_image = data.get('images')[0] if data.get('images') else None
                existing.images = data.get('images', [])
                existing.description_long_ko = data.get('description_long')
                existing.flavor_profile = data.get('flavor_profile')
                existing.visitor_tips = data.get('visitor_tips')
                existing.content_completeness = 85  # 예시
                existing.verified_by = "system"
                existing.verified_date = datetime.now()

                print(f"✅ {menu_name}: 업데이트")
            else:
                # 새 항목 추가
                new_menu = CanonicalMenu(
                    name_ko=menu_name,
                    name_en=data.get('menu_en'),
                    primary_image=data.get('images')[0] if data.get('images') else None,
                    images=data.get('images', []),
                    description_long_ko=data.get('description_long'),
                    # ... 다른 필드들
                )
                session.add(new_menu)

                print(f"✅ {menu_name}: 추가")

        session.commit()
        session.close()

        print("✅ DB 로드 완료")

if __name__ == "__main__":
    with open('app/backend/data/enriched_content.json', 'r', encoding='utf-8') as f:
        enriched_data = json.load(f)

    loader = DataLoader(db_url=os.getenv('DATABASE_URL'))
    loader.load_enriched_data(enriched_data)
```

실행:
```bash
# 1. 마이그레이션 실행
psql -U $DB_USER -d $DB_NAME -f app/backend/migrations/phase1_images_content.sql

# 2. 데이터 로드
python app/backend/scripts/load_enriched_data.py

# 3. 검증
psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM canonical_menus WHERE primary_image IS NOT NULL;"
```

---

### **Day 10 (3시간): AI 이미지 생성 (보충)**

**파일**: `app/backend/scripts/generate_ai_images.py`

```python
#!/usr/bin/env python3
"""
DALL-E 3로 부족한 이미지 생성
- 비용: $0.08/이미지 × 50개 = $4
"""

import openai
import boto3
import json
import os

class AIImageGenerator:
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
        self.s3_client = boto3.client('s3')

    def generate_image(self, menu: str) -> str:
        """DALL-E 3로 음식 이미지 생성"""

        prompt = f"""
        Create a professional food photography image of {menu},
        a traditional Korean dish.

        Requirements:
        - Studio lighting with warm, golden tones
        - Authentic Korean presentation
        - High resolution (4K quality)
        - Ultra-realistic and appetizing
        - No text or watermarks
        """

        response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1
        )

        return response['data'][0]['url']

    def process_missing_menus(self, menus: List[str]):
        """부족한 메뉴 이미지 생성"""
        print(f"🔄 AI 이미지 생성 중 ({len(menus)}개)...")

        results = []

        for menu in menus:
            try:
                image_url = self.generate_image(menu)

                results.append({
                    'menu': menu,
                    'image_url': image_url,
                    'source': 'AI Generated (DALL-E 3)',
                    'license': 'Commercial Use Permitted'
                })

                print(f"✅ {menu}: 생성 완료")

            except Exception as e:
                print(f"❌ {menu}: 실패 ({e})")

        return results

if __name__ == "__main__":
    # 부족한 메뉴 리스트 (예시)
    missing_menus = ["떡국", "배추김치", "팔보채"]  # 등등

    generator = AIImageGenerator(
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )

    ai_images = generator.process_missing_menus(missing_menus)

    # 결과 저장
    with open('app/backend/data/ai_generated_images.json', 'w', encoding='utf-8') as f:
        json.dump(ai_images, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(ai_images)}개 AI 이미지 생성 완료")
```

---

## 📋 **주차 3: API + UI + 배포 (Days 11-20, 28시간)**

### **Day 11-12 (4시간): API 엔드포인트 확장**

**파일**: `app/backend/main.py` (확장)

```python
# GET /api/v1/canonical-menus/{id}
@router.get("/canonical-menus/{menu_id}")
async def get_canonical_menu(menu_id: UUID):
    """메뉴 상세 정보 (이미지 + 콘텐츠 포함)"""

    menu = await db.query(CanonicalMenu).filter_by(id=menu_id).first()

    return {
        "id": menu.id,
        "name_ko": menu.name_ko,
        "name_en": menu.name_en,

        # 🆕 이미지
        "primary_image": menu.primary_image,
        "images": menu.images,

        # 🆕 콘텐츠
        "description": {
            "short": menu.description_short,
            "long": menu.description_long_ko,
            "origin": menu.origin_story,
            "cultural_significance": menu.cultural_significance
        },

        # 🆕 지역별
        "regional_variants": menu.regional_variants,

        # 🆕 조리법
        "preparation": {
            "ingredients": menu.main_ingredients,
            "steps": menu.preparation_steps,
            "tips": menu.cooking_tips
        },

        # 🆕 영양/맛
        "nutrition": menu.nutrition_detail,
        "flavor_profile": menu.flavor_profile,

        # 기존 필드들
        "allergens": menu.allergens,
        "spice_level": menu.spice_level,
        "difficulty_score": menu.difficulty_score
    }
```

---

### **Day 13-17 (10시간): UI 컴포넌트 개발**

**파일**: `app/frontend/components/MenuImage.tsx`

```tsx
import React, { useState } from 'react';
import Image from 'next/image';

interface MenuImageProps {
  images: Array<{
    url: string;
    source: string;
    license: string;
  }>;
  menu_name: string;
}

export function MenuImage({ images, menu_name }: MenuImageProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  const current = images[currentIndex];

  return (
    <div className="menu-image-container">
      {/* 메인 이미지 */}
      <div className="image-wrapper">
        <Image
          src={current.url}
          alt={menu_name}
          width={400}
          height={400}
          className="menu-image"
          priority
          loading="lazy"
        />

        {/* 출처 표시 */}
        <span className="image-credit">
          Source: {current.source}
        </span>
      </div>

      {/* 이미지 캐러셀 */}
      {images.length > 1 && (
        <div className="image-carousel">
          <button
            onClick={() => setCurrentIndex((i) => (i - 1 + images.length) % images.length)}
            className="carousel-btn prev"
          >
            ‹
          </button>

          <div className="carousel-dots">
            {images.map((_, i) => (
              <button
                key={i}
                className={`dot ${i === currentIndex ? 'active' : ''}`}
                onClick={() => setCurrentIndex(i)}
              />
            ))}
          </div>

          <button
            onClick={() => setCurrentIndex((i) => (i + 1) % images.length)}
            className="carousel-btn next"
          >
            ›
          </button>
        </div>
      )}
    </div>
  );
}
```

**파일**: `app/frontend/components/MenuContent.tsx`

```tsx
import React, { useState } from 'react';

interface MenuContentProps {
  description: {
    short: string;
    long: string;
    origin: string;
    cultural_significance: string;
  };
  preparation: any;
  nutrition: any;
  flavor_profile: any;
  visitor_tips: any;
}

export function MenuContent({ description, preparation, nutrition, flavor_profile, visitor_tips }: MenuContentProps) {
  const [activeTab, setActiveTab] = useState('description');

  return (
    <div className="menu-content">
      {/* 탭 네비게이션 */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'description' ? 'active' : ''}`}
          onClick={() => setActiveTab('description')}
        >
          설명
        </button>
        <button
          className={`tab ${activeTab === 'preparation' ? 'active' : ''}`}
          onClick={() => setActiveTab('preparation')}
        >
          조리법
        </button>
        <button
          className={`tab ${activeTab === 'nutrition' ? 'active' : ''}`}
          onClick={() => setActiveTab('nutrition')}
        >
          영양정보
        </button>
        <button
          className={`tab ${activeTab === 'flavor' ? 'active' : ''}`}
          onClick={() => setActiveTab('flavor')}
        >
          맛
        </button>
        <button
          className={`tab ${activeTab === 'tips' ? 'active' : ''}`}
          onClick={() => setActiveTab('tips')}
        >
          팁
        </button>
      </div>

      {/* 탭 콘텐츠 */}
      <div className="tab-content">
        {activeTab === 'description' && (
          <div className="description-section">
            <h3>설명</h3>
            <p className="short">{description.short}</p>
            <p className="long">{description.long}</p>
            <h4>역사</h4>
            <p>{description.origin}</p>
            <h4>문화적 의미</h4>
            <p>{description.cultural_significance}</p>
          </div>
        )}

        {/* 다른 탭들 ... */}
      </div>
    </div>
  );
}
```

---

### **Day 18-19 (6시간): 스타일링 & 반응형**

**파일**: `app/frontend/styles/MenuResult.module.css`

```css
.menuImageContainer {
  position: relative;
  width: 100%;
  max-width: 400px;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f5f5, #e9e9e9);
}

.menuImage {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.imageCredit {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  z-index: 10;
}

/* 모바일 반응형 */
@media (max-width: 768px) {
  .menuImageContainer {
    max-width: 100%;
  }

  .menuImage {
    aspect-ratio: 16 / 9;
  }
}
```

---

### **Day 20 (8시간): 배포 & 테스트**

```bash
# 1. 마이그레이션 실행
ssh chargeap@d11475.sgp1.stableserver.net << EOF
cd ~/menu.chargeapp.net/backend
source venv/bin/activate

# DB 마이그레이션
psql -U $DB_USER -d $DB_NAME -f migrations/phase1_images_content.sql

# 데이터 로드
python scripts/load_enriched_data.py

# API 재시작
sudo systemctl restart menu-api
EOF

# 2. 배포 검증
curl -X GET "https://menu.chargeapp.net/api/v1/canonical-menus/[uuid]" | jq .

# 3. 예상 결과
# ✅ primary_image 필드 포함
# ✅ images 배열 (3-5개)
# ✅ description, preparation, nutrition 등 모든 필드

# 4. UI 테스트 (모바일)
# - 이미지 캐러셀 동작 ✅
# - 탭 네비게이션 동작 ✅
# - 반응형 표시 ✅
```

---

## ✅ **완료 체크리스트**

### 주차 1 (이미지 수집)
- [ ] 공공데이터포탈 API 키 발급 & 수집
- [ ] 위키피디아 크롤링 완료
- [ ] 네이버 지식백과 크롤링 완료 (저작권 명시)
- [ ] S3에 300-600개 이미지 업로드
- [ ] 메타데이터 JSON 생성

### 주차 2 (콘텐츠 강화)
- [ ] GPT-4 콘텐츠 확장
- [ ] DB 마이그레이션 성공
- [ ] 100+ 메뉴 데이터 로드
- [ ] AI 이미지 50-70개 생성

### 주차 3 (API + UI + 배포)
- [ ] API 엔드포인트 확장
- [ ] UI 컴포넌트 개발
- [ ] 모바일 반응형 테스트
- [ ] FastComet 배포 완료
- [ ] 프로덕션 검증

---

## 📞 **문제 발생 시**

| 문제 | 해결 |
|------|------|
| API 키 발급 안 됨 | data.go.kr 고객센터 문의 |
| 크롤링 차단됨 | User-Agent 변경, 지연 추가 |
| S3 업로드 실패 | AWS 자격증명 확인 |
| GPT-4 비용 초과 | 샘플 메뉴만 테스트 후 스케일 |

---

**예상 완료**: 2026-03-18 (4주)
**상태**: 🚀 **지금 바로 시작 가능**

작성: Claude Code
날짜: 2026-02-18
