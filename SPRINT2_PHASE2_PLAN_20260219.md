# Sprint 2 Phase 2 - 계획서

> **작성일**: 2026-02-19
> **작성자**: Menu Knowledge Engine 개발팀
> **목표**: S3/CDN 이미지 마이그레이션 + 콘텐츠 확장 + UI 개선
> **예상 기간**: 3-4주

---

## 📋 Phase 1 성과 요약

**완료 사항** (2026-02-19):
- ✅ 111개 메뉴 enriched content 완료 (42.7% coverage)
- ✅ Claude API 기반 콘텐츠 자동 생성 (28.7분, 99.1% 성공률)
- ✅ Multi-image support (primary_image, images[])
- ✅ Content completeness scoring (0-100)
- ✅ API 엔드포인트 추가 (GET /canonical-menus)
- ✅ 프로덕션 배포 완료 (테스트 100% 통과)

**알려진 제약**:
- ⚠️ 이미지 URL 404 (서버에 업로드되었으나 웹 접근 불가)
- ⚠️ 나머지 149개 메뉴 미강화 (260개 중 111개만 완료)
- ⚠️ UI 컴포넌트 미개발 (백엔드만 완료)

---

## 🎯 Phase 2 목표

### 핵심 목표
1. **P0: 이미지 인프라 개선** - S3/CloudFront로 마이그레이션하여 안정적 이미지 서빙
2. **P1: 콘텐츠 확장** - 나머지 149개 메뉴 강화 (전체 coverage 80%+ 목표)
3. **P1: UI 컴포넌트 개발** - 외국인 사용자를 위한 메뉴 상세 페이지

### 성공 지표
| 지표 | Phase 1 실적 | Phase 2 목표 | 측정 방법 |
|------|-------------|-------------|----------|
| **Enriched 메뉴 수** | 111개 (42.7%) | 210개+ (80%+) | SQL COUNT |
| **Content Completeness** | 100% (111/111) | 95%+ (210/210) | AVG(content_completeness) |
| **이미지 가용성** | 0% (404 오류) | 100% (CDN 서빙) | HTTP 200 비율 |
| **API 응답 시간** | p95 미측정 | p95 < 500ms | 모니터링 |
| **UI 개발** | 0% | 100% | 페이지 배포 완료 |

---

## 📅 Phase 2 일정

### Week 1-2: P0 이미지 인프라 (최우선)
**목표**: S3 + CloudFront 구축 및 기존 이미지 마이그레이션

| 작업 | 소요 시간 | 담당 | 우선순위 |
|------|----------|------|---------|
| AWS S3 버킷 생성 및 정책 설정 | 2시간 | DevOps | P0 |
| CloudFront 배포 생성 및 도메인 연결 | 3시간 | DevOps | P0 |
| 기존 8개 이미지 S3 업로드 | 1시간 | Backend | P0 |
| DB URL 업데이트 (CDN URL로 변경) | 2시간 | Backend | P0 |
| 이미지 업로드 스크립트 S3 대응 | 3시간 | Backend | P0 |
| 썸네일 자동 생성 람다 함수 | 4시간 | Backend | P1 |
| 검증 및 모니터링 설정 | 2시간 | DevOps | P0 |

**산출물**:
- S3 버킷: `menu-knowledge-images` (ap-northeast-2)
- CloudFront 배포: `d[랜덤].cloudfront.net` → `images.menu-knowledge.chargeapp.net`
- 스크립트: `scripts/upload_to_s3.py` (scp 대신 boto3 사용)

### Week 2-3: P1 콘텐츠 확장
**목표**: 나머지 149개 메뉴 enriched content 생성

| 작업 | 소요 시간 | 담당 | 우선순위 |
|------|----------|------|---------|
| 배치 처리 스크립트 개선 | 3시간 | Backend | P1 |
| Claude API 호출 (149개, 배치 50개씩) | 40분 | Backend | P1 |
| 데이터 검증 및 수동 보정 | 6시간 | Content | P1 |
| DB 로드 및 검증 | 2시간 | Backend | P1 |
| 완성도 점수 검증 | 1시간 | QA | P1 |

**비용 예상**:
- Claude API: 149개 × $0.02 = $2.98
- 총 처리 시간: 약 40분 (Phase 1 대비 동일 속도)

**목표 Coverage**:
```
Phase 1: 111 / 260 = 42.7%
Phase 2: 210 / 260 = 80.8%
증가분: +99개 메뉴
```

### Week 3-4: P1 UI 컴포넌트 개발
**목표**: 외국인 사용자를 위한 메뉴 상세 페이지 구현

| 작업 | 소요 시간 | 담당 | 우선순위 |
|------|----------|------|---------|
| 메뉴 상세 페이지 설계 (Figma) | 4시간 | Designer | P1 |
| 이미지 캐러셀 컴포넌트 | 3시간 | Frontend | P1 |
| 지역 변종 탭 컴포넌트 | 2시간 | Frontend | P1 |
| 조리법 단계 표시 컴포넌트 | 2시간 | Frontend | P1 |
| 영양정보 차트 (Chart.js) | 3시간 | Frontend | P1 |
| 방문자 팁 섹션 | 2시간 | Frontend | P1 |
| 유사 메뉴 추천 컴포넌트 | 2시간 | Frontend | P1 |
| 다국어 전환 (next-intl) | 3시간 | Frontend | P1 |
| 반응형 스타일링 (모바일) | 4시간 | Frontend | P1 |
| API 통합 및 테스트 | 3시간 | Frontend | P1 |

**기술 스택**:
- **Frontend**: Next.js 14 App Router, React 18, TypeScript
- **UI 라이브러리**: Tailwind CSS, shadcn/ui
- **다국어**: next-intl (ko, en, ja, zh)
- **차트**: Chart.js 또는 Recharts
- **이미지**: next/image (CDN 연동)

**페이지 구조**:
```
/menu/[id]
├── Hero 섹션 (대표 이미지 + 기본 정보)
├── 탭 네비게이션
│   ├── 설명 (description_long)
│   ├── 지역 변종 (regional_variants)
│   ├── 조리법 (preparation_steps)
│   ├── 영양정보 (nutrition_detail)
│   └── 방문자 팁 (visitor_tips)
├── 맛 프로필 (flavor_profile) - 레이더 차트
├── 유사 메뉴 (similar_dishes) - 카드 리스트
└── 문화적 배경 (cultural_context)
```

---

## 🔧 상세 구현 계획

### P0: S3/CloudFront 이미지 마이그레이션

#### 1. S3 버킷 생성 (2시간)

**AWS CLI 명령어**:
```bash
# 1. S3 버킷 생성
aws s3api create-bucket \
  --bucket menu-knowledge-images \
  --region ap-northeast-2 \
  --create-bucket-configuration LocationConstraint=ap-northeast-2

# 2. 퍼블릭 액세스 정책 설정
aws s3api put-bucket-policy \
  --bucket menu-knowledge-images \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::menu-knowledge-images/*"
    }]
  }'

# 3. CORS 설정
aws s3api put-bucket-cors \
  --bucket menu-knowledge-images \
  --cors-configuration '{
    "CORSRules": [{
      "AllowedOrigins": ["https://menu-knowledge.chargeapp.net"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }]
  }'
```

**디렉토리 구조**:
```
s3://menu-knowledge-images/
├── canonical/              # 표준 메뉴 이미지
│   ├── {menu_id}/
│   │   ├── primary.jpg
│   │   ├── variant_1.jpg
│   │   └── ...
├── thumbnails/             # 자동 생성 썸네일 (300x300)
│   └── {menu_id}/
│       └── primary_thumb.jpg
└── user-uploads/           # B2B 사용자 업로드 (Phase 3)
```

#### 2. CloudFront 배포 (3시간)

**CloudFront 설정**:
```bash
# CloudFront 배포 생성
aws cloudfront create-distribution \
  --origin-domain-name menu-knowledge-images.s3.ap-northeast-2.amazonaws.com \
  --default-root-object index.html

# 캐시 정책
# - 이미지: max-age=86400 (24시간)
# - 썸네일: max-age=604800 (7일)
```

**도메인 연결**:
```
CNAME: images.menu-knowledge.chargeapp.net → d[랜덤].cloudfront.net
SSL: AWS Certificate Manager (무료)
```

#### 3. 이미지 업로드 스크립트 (3시간)

**`scripts/upload_to_s3.py`** (scp 대신 boto3):
```python
import boto3
from pathlib import Path
from PIL import Image
from io import BytesIO
import os

s3_client = boto3.client('s3', region_name='ap-northeast-2')
BUCKET_NAME = "menu-knowledge-images"
CDN_BASE_URL = "https://images.menu-knowledge.chargeapp.net"

def upload_menu_image(
    menu_id: str,
    local_path: Path,
    image_type: str = "primary"
) -> str:
    """
    메뉴 이미지를 S3에 업로드하고 CDN URL 반환

    Args:
        menu_id: 메뉴 UUID
        local_path: 로컬 이미지 경로
        image_type: primary, variant_1, variant_2, ...

    Returns:
        CDN URL (https://images.menu-knowledge.chargeapp.net/canonical/{menu_id}/primary.jpg)
    """
    # 1. 이미지 로드 및 최적화
    img = Image.open(local_path)
    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

    # 2. JPEG로 변환 (품질 85%)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    buffer.seek(0)

    # 3. S3 업로드
    key = f"canonical/{menu_id}/{image_type}.jpg"
    s3_client.upload_fileobj(
        buffer,
        BUCKET_NAME,
        key,
        ExtraArgs={
            'ContentType': 'image/jpeg',
            'CacheControl': 'max-age=86400',  # 24시간
            'ACL': 'public-read'
        }
    )

    # 4. CDN URL 반환
    return f"{CDN_BASE_URL}/{key}"

def generate_thumbnail(menu_id: str, source_key: str) -> str:
    """
    썸네일 자동 생성 (300x300)
    """
    # S3에서 원본 이미지 다운로드
    obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=source_key)
    img = Image.open(obj['Body'])

    # 썸네일 생성
    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=80)
    buffer.seek(0)

    # 썸네일 업로드
    thumb_key = f"thumbnails/{menu_id}/primary_thumb.jpg"
    s3_client.upload_fileobj(
        buffer,
        BUCKET_NAME,
        thumb_key,
        ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'max-age=604800'}
    )

    return f"{CDN_BASE_URL}/{thumb_key}"
```

#### 4. DB URL 업데이트 (2시간)

**마이그레이션 SQL**:
```sql
-- migrations/sprint2_phase2_s3_migration.sql

BEGIN;

-- 1. primary_image URL을 CDN URL로 변경
UPDATE canonical_menus
SET primary_image = jsonb_set(
    primary_image,
    '{url}',
    to_jsonb(
        'https://images.menu-knowledge.chargeapp.net/canonical/' || id::text || '/primary.jpg'
    )
)
WHERE primary_image IS NOT NULL;

-- 2. images[] 배열의 URL도 변경
UPDATE canonical_menus
SET images = (
    SELECT jsonb_agg(
        jsonb_set(img, '{url}',
            to_jsonb('https://images.menu-knowledge.chargeapp.net' ||
                SUBSTRING(img->>'url' FROM '/canonical/.*'))
        )
    )
    FROM jsonb_array_elements(images) AS img
)
WHERE images IS NOT NULL;

-- 3. 검증
SELECT
    name_ko,
    primary_image->>'url' AS primary_url,
    jsonb_array_length(images) AS image_count
FROM canonical_menus
WHERE primary_image IS NOT NULL
LIMIT 5;

COMMIT;
```

---

### P1: 콘텐츠 확장 (나머지 149개 메뉴)

#### 1. 배치 처리 스크립트 개선 (3시간)

**`scripts/enrich_content_batch.py`** (Phase 1 스크립트 개선):
```python
import asyncio
from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.database import get_db
from app.backend.models import CanonicalMenu
import json

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def enrich_menu_batch(
    menus: List[CanonicalMenu],
    batch_size: int = 50
) -> List[dict]:
    """
    배치 단위로 메뉴 강화 (50개씩)

    Args:
        menus: 강화할 메뉴 리스트
        batch_size: 배치 크기 (기본 50)

    Returns:
        강화된 데이터 리스트
    """
    results = []

    for i in range(0, len(menus), batch_size):
        batch = menus[i:i+batch_size]
        print(f"배치 {i//batch_size + 1}: {len(batch)}개 메뉴 처리 중...")

        # Claude API 병렬 호출 (asyncio.gather)
        tasks = [enrich_single_menu(menu) for menu in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 성공/실패 구분
        for menu, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                print(f"❌ 실패: {menu.name_ko} - {result}")
            else:
                print(f"✅ 성공: {menu.name_ko}")
                results.append(result)

        # Rate limit 고려 (1초 대기)
        await asyncio.sleep(1)

    return results

async def enrich_single_menu(menu: CanonicalMenu) -> dict:
    """
    단일 메뉴 강화 (Phase 1과 동일)
    """
    prompt = f"""
    한국 음식 '{menu.name_ko}'에 대해 다음 정보를 제공하세요:

    1. 상세 설명 (한국어/영어 각 150-200자)
    2. 지역별 변종 (3개 이상: 서울, 전라도, 경상도 등)
    3. 조리 단계 (5-7단계, 시간 포함)
    4. 영양정보 (칼로리, 단백질, 지방, 탄수화물)
    5. 맛 프로필 (sweet, salty, sour, bitter, umami 0-5 점수)
    6. 방문자 팁 (주문 방법, 먹는 법, 추천 사이드)
    7. 유사 메뉴 (3-5개, similarity_score 포함)
    8. 문화적 배경 (역사, 유래, 의미)

    JSON 형식으로 반환하세요.
    """

    response = await client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=4096,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )

    # JSON 파싱
    content = response.content[0].text
    data = json.loads(content)

    # 완성도 계산
    completeness = calculate_completeness(data)

    return {
        "menu_id": str(menu.id),
        "name_ko": menu.name_ko,
        **data,
        "content_completeness": completeness
    }

async def main():
    """
    메인 실행 함수
    """
    async with get_db() as db:
        # 1. enriched content가 없는 메뉴 조회
        result = await db.execute(
            select(CanonicalMenu)
            .where(CanonicalMenu.content_completeness == None)
            .order_by(CanonicalMenu.name_ko)
        )
        menus = result.scalars().all()

        print(f"총 {len(menus)}개 메뉴 강화 시작...")

        # 2. 배치 처리
        enriched_data = await enrich_menu_batch(menus)

        # 3. JSON 저장
        with open("data/enriched_menus_phase2.json", "w", encoding="utf-8") as f:
            json.dump(enriched_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 완료: {len(enriched_data)}개 메뉴 강화됨")
        print(f"저장 위치: data/enriched_menus_phase2.json")

if __name__ == "__main__":
    asyncio.run(main())
```

**실행 예상**:
```bash
$ python scripts/enrich_content_batch.py

총 149개 메뉴 강화 시작...
배치 1: 50개 메뉴 처리 중...
✅ 성공: 갈비탕
✅ 성공: 감자탕
✅ 성공: 곰탕
... (50개)

배치 2: 50개 메뉴 처리 중...
... (50개)

배치 3: 49개 메뉴 처리 중...
... (49개)

✅ 완료: 149개 메뉴 강화됨
저장 위치: data/enriched_menus_phase2.json

처리 시간: 약 40분
```

#### 2. 데이터 로드 (2시간)

**`scripts/load_enriched_data_phase2.py`** (Phase 1과 동일 방식):
```python
# Direct SQL UPDATE로 로드
# (Phase 1 스크립트 재사용)
```

---

### P1: UI 컴포넌트 개발

#### 1. 메뉴 상세 페이지 구조

**`app/frontend/pages/menu/[id].tsx`**:
```typescript
import { useRouter } from 'next/router';
import { useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import MenuImageCarousel from '@/components/MenuImageCarousel';
import RegionalVariants from '@/components/RegionalVariants';
import PreparationSteps from '@/components/PreparationSteps';
import NutritionChart from '@/components/NutritionChart';
import FlavorProfile from '@/components/FlavorProfile';
import VisitorTips from '@/components/VisitorTips';
import SimilarDishes from '@/components/SimilarDishes';

export default function MenuDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const t = useTranslations('menu');

  const { data: menu, isLoading } = useQuery({
    queryKey: ['menu', id],
    queryFn: async () => {
      const res = await fetch(`https://menu-knowledge.chargeapp.net/api/v1/canonical-menus/${id}`);
      return res.json();
    }
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero 섹션 */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">{menu.name_ko}</h1>
        <h2 className="text-2xl text-gray-600 mb-4">{menu.name_en}</h2>
        <p className="text-lg">{menu.explanation_short_en}</p>
      </div>

      {/* 이미지 캐러셀 */}
      <MenuImageCarousel images={[menu.primary_image, ...menu.images]} />

      {/* 탭 네비게이션 */}
      <Tabs defaultValue="description">
        <TabsList>
          <TabsTrigger value="description">{t('tabs.description')}</TabsTrigger>
          <TabsTrigger value="variants">{t('tabs.regional_variants')}</TabsTrigger>
          <TabsTrigger value="recipe">{t('tabs.preparation')}</TabsTrigger>
          <TabsTrigger value="nutrition">{t('tabs.nutrition')}</TabsTrigger>
          <TabsTrigger value="tips">{t('tabs.tips')}</TabsTrigger>
        </TabsList>

        <TabsContent value="description">
          <p className="text-lg">{menu.description_long_en}</p>
          <p className="text-gray-600 mt-4">{menu.description_long_ko}</p>
        </TabsContent>

        <TabsContent value="variants">
          <RegionalVariants variants={menu.regional_variants} />
        </TabsContent>

        <TabsContent value="recipe">
          <PreparationSteps steps={menu.preparation_steps} />
        </TabsContent>

        <TabsContent value="nutrition">
          <NutritionChart nutrition={menu.nutrition_detail} />
        </TabsContent>

        <TabsContent value="tips">
          <VisitorTips tips={menu.visitor_tips} />
        </TabsContent>
      </Tabs>

      {/* 맛 프로필 */}
      <div className="mt-8">
        <h3 className="text-2xl font-bold mb-4">{t('flavor_profile')}</h3>
        <FlavorProfile profile={menu.flavor_profile} />
      </div>

      {/* 유사 메뉴 */}
      <div className="mt-8">
        <h3 className="text-2xl font-bold mb-4">{t('similar_dishes')}</h3>
        <SimilarDishes dishes={menu.similar_dishes} />
      </div>
    </div>
  );
}
```

#### 2. 주요 컴포넌트

**`components/FlavorProfile.tsx`** (레이더 차트):
```typescript
import { Radar } from 'react-chartjs-2';

export default function FlavorProfile({ profile }) {
  const data = {
    labels: ['Sweet', 'Salty', 'Sour', 'Bitter', 'Umami', 'Spicy'],
    datasets: [{
      label: 'Flavor Profile',
      data: [
        profile.balance.sweet,
        profile.balance.salty,
        profile.balance.sour,
        profile.balance.bitter,
        profile.balance.umami,
        profile.balance.spicy
      ],
      backgroundColor: 'rgba(255, 99, 132, 0.2)',
      borderColor: 'rgba(255, 99, 132, 1)',
      borderWidth: 2
    }]
  };

  return <Radar data={data} options={{ scale: { min: 0, max: 5 } }} />;
}
```

**`components/PreparationSteps.tsx`** (조리법):
```typescript
export default function PreparationSteps({ steps }) {
  return (
    <div className="space-y-4">
      {steps.steps.map((step, idx) => (
        <div key={idx} className="flex gap-4">
          <div className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center">
            {step.step}
          </div>
          <div className="flex-1">
            <p className="font-semibold">{step.instruction_en}</p>
            <p className="text-gray-600 text-sm">{step.instruction_ko}</p>
            <p className="text-xs text-gray-500 mt-1">⏱️ {step.time_minutes} min</p>
          </div>
        </div>
      ))}
      <div className="mt-6 p-4 bg-gray-100 rounded">
        <p className="font-bold">Total Time: {steps.total_time_minutes} minutes</p>
        <p className="text-sm text-gray-600">Difficulty: {steps.difficulty}</p>
      </div>
    </div>
  );
}
```

---

## 🧪 검증 계획

### Phase 2 완료 기준

#### 1. P0: 이미지 인프라
```bash
# 1. S3 업로드 성공
aws s3 ls s3://menu-knowledge-images/canonical/
# 기대: 111개 폴더 (각 메뉴마다)

# 2. CloudFront 배포 활성화
curl -I https://images.menu-knowledge.chargeapp.net/canonical/{menu_id}/primary.jpg
# 기대: HTTP 200 + x-cache: Hit from cloudfront

# 3. DB URL 업데이트 확인
psql -h localhost -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -c "SELECT primary_image->>'url' FROM canonical_menus WHERE primary_image IS NOT NULL LIMIT 5;"
# 기대: https://images.menu-knowledge.chargeapp.net/... 형식
```

#### 2. P1: 콘텐츠 확장
```sql
-- 1. 강화된 메뉴 개수 확인
SELECT COUNT(*) FROM canonical_menus WHERE content_completeness > 0;
-- 기대: 210개 이상 (Phase 1 111 + Phase 2 99+)

-- 2. Coverage 비율
SELECT
    COUNT(*) FILTER (WHERE content_completeness > 0) AS enriched,
    COUNT(*) AS total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE content_completeness > 0) / COUNT(*), 1) AS coverage_pct
FROM canonical_menus;
-- 기대: 80%+ coverage

-- 3. 완성도 분포
SELECT
    FLOOR(content_completeness / 10) * 10 AS completeness_range,
    COUNT(*) AS count
FROM canonical_menus
WHERE content_completeness IS NOT NULL
GROUP BY FLOOR(content_completeness / 10)
ORDER BY completeness_range DESC;
-- 기대: 대부분 90-100% 범위
```

#### 3. P1: UI 컴포넌트
```bash
# 1. 로컬 개발 서버
cd app/frontend
npm run dev
# http://localhost:3000/menu/{id} 접속

# 2. 빌드 성공
npm run build
# 기대: 에러 없이 빌드 완료

# 3. 프로덕션 배포
npm run build-standalone
rsync -avz frontend/standalone/ chargeap@d11475.sgp1.stableserver.net:~/menu-knowledge.chargeapp.net/frontend/standalone/
ssh chargeap@d11475.sgp1.stableserver.net
cd ~/menu-knowledge.chargeapp.net/frontend/standalone
pm2 restart menu-knowledge-frontend
```

---

## 📊 비용 예상

| 항목 | Phase 1 실적 | Phase 2 예상 | 비고 |
|------|-------------|-------------|------|
| **Claude API** | $2.22 (111개) | $2.98 (149개) | $0.02/메뉴 |
| **DALL-E 3** | $0 (기존 사용) | $20 (250개) | $0.08/이미지 (선택) |
| **S3 스토리지** | $0 | $5/월 | 500MB 예상 |
| **CloudFront** | $0 | $2-5/월 | 10GB 트래픽 예상 |
| **합계** | $2.22 | **$30-33** (초기) + $7-10/월 (운영) | |

**비용 절감 전략**:
- DALL-E 이미지는 필요시에만 생성 (기존 Wikimedia Commons 우선 활용)
- CloudFront 캐싱 적극 활용 (24시간 TTL)
- 썸네일 자동 생성으로 트래픽 감소

---

## 🚀 배포 전략

### 1단계: Staging 환경 검증
```bash
# 로컬 테스트 완료 후
# FastComet 서버에 staging 디렉토리 생성
ssh chargeap@d11475.sgp1.stableserver.net
mkdir -p ~/menu-knowledge-staging
```

### 2단계: Blue-Green 배포
```bash
# 기존 프로덕션 유지하면서 새 버전 배포
# Nginx에서 트래픽 전환
```

### 3단계: 모니터링
- CloudWatch (S3/CloudFront)
- API 응답 시간 (p95 < 500ms)
- 에러율 (< 1%)

---

## 📝 다음 단계 (Sprint 3)

Phase 2 완료 후:

1. **B2B 관리자 대시보드** - 식당 주인이 메뉴 업로드 및 관리
2. **AI 이미지 분석** - 업로드된 이미지로 메뉴 자동 인식
3. **OCR 파이프라인 최적화** - CLOVA OCR 정확도 개선
4. **성능 최적화** - Redis 캐싱, API 응답 시간 개선

---

**최종 수정**: 2026-02-19
**승인 대기**: 사용자 확인 필요
**예상 착수**: 2026-02-20 (승인 시)
