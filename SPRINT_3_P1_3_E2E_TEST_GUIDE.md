# 🎯 Sprint 3 P1-3: End-to-End 통합 테스트 가이드

> **목표:** 실제 식당 메뉴판으로 전체 파이프라인 검증
> **기간:** 2일 (현장 테스트 + 리포트)
> **KPI 목표:**
> - OCR 인식률 >= 80%
> - DB 매칭률 >= 70%
> - 응답 시간 <= 3초 (p95)
> - 사장님 수정률 <= 20%

---

## 📋 **Phase 1: 현장 준비 (2시간)**

### 1.1 테스트 식당 섭외

**명동 추천 식당 3곳:**

| # | 식당명 | 특징 | 섭외 포인트 |
|---|--------|------|-----------|
| **1** | 명동 교자 | 간단함 (5-10개) | OCR 기본 정확도 |
| **2** | 신계순 순대국 | 복잡함 (20-30개) | 매칭률 검증 |
| **3** | 명동 할머니순대 | 손글씨 섞임 | OCR 한계 |

**섭외 스크립트:**

```
안녕하세요! 저는 한국 음식을 해외 관광객에게 설명해주는
"Menu Lens Korea" 서비스를 개발 중입니다.

귀 식당의 메뉴판 사진을 찍고 테스트하고 싶은데,
가능할까요? 비용은 없고, 결과 리포트를 공유해드리겠습니다.

테스트 시간: 30분 예상
필요한 것: 메뉴판 (그대로 두면 됨)
```

### 1.2 테스트 장비 준비

**필수:**
- 스마트폰 (iOS 또는 Android)
- USB-C 케이블 (데이터 전송용, 옵션)
- 노트북 (테스트 결과 기록)

**선택:**
- 삼각대 (안정적인 사진)
- 조명 (암부 조정)

### 1.3 사전 체크리스트

- [ ] 3개 식당 예약 확정
- [ ] 노트북 배터리 100% (4시간 이상)
- [ ] 스마트폰 배터리 100%
- [ ] 카메라 렌즈 청소
- [ ] 테스트 폴더 준비: `/app/data/e2e_test_20250218/`

---

## 🏪 **Phase 2: 현장 테스트 (2시간 30분)**

### 2.1 각 식당별 프로토콜

**시간 배분:**

```
식당 1 (교자): 45분
├─ 메뉴판 촬영: 10분 (30-50장)
├─ OCR 테스트: 15분
├─ 결과 검증: 15분
└─ 정리: 5분

식당 2 (순대국): 45분
└─ (동일)

식당 3 (할머니순대): 45분
└─ (동일)

이동 시간: 10분
```

### 2.2 메뉴판 촬영 체크리스트

**각 식당마다:**

- [ ] 메뉴판 전체 샷 (1장)
- [ ] 섹션별 샷 (국/밥/면 등)
- [ ] 다각도 촬영 (정면, 45도, 옆각)
- [ ] 조명 변화 (밝음, 어두움)
- [ ] 손글씨 부분 클로즈업 (있으면)
- [ ] 가격 명확 촬영 (OCR 검증용)

**촬영 팁:**
```
✅ 좋은 사진:
- 해상도 1920x1080 이상
- 각도 0도 (정면)
- 밝기 충분함
- 메뉴판 가득 (프레이밍)

❌ 피할 사진:
- 각도 45도 이상 (왜곡)
- 역광 (글씨 안 보임)
- 손/손가락 가림
- 흔들림 (ISO 높음)
```

### 2.3 현장 테스트 프로토콜

**각 메뉴판 테스트 순서:**

#### Step 1: OCR 테스트

```bash
# 1. 메뉴판 사진 1장 업로드
curl -X POST http://localhost:8000/api/v1/menu/recognize \
  -F "file=@/path/to/menu_photo.jpg"

# 2. 응답 분석
# {
#   "success": true,
#   "menu_items": [
#     {"name_ko": "순대국", "price_ko": "8,000"},
#     {"name_ko": "부속 한그릇", "price_ko": "13,000"},
#     ...
#   ],
#   "ocr_confidence": 0.92,
#   "count": 8,
#   "processing_time_ms": 1200
# }

# 3. 기록: ocr_confidence 값, menu_items 수
```

#### Step 2: 각 메뉴 매칭 테스트

```bash
# recognize 결과의 각 menu_name_ko에 대해

for menu in ${메뉴명_배열}; do
  curl -X POST http://localhost:8000/api/v1/menu/identify \
    -H "Content-Type: application/json" \
    -d "{\"menu_name_ko\": \"$menu\"}"
done

# 응답 분석:
# {
#   "match_type": "exact|modifier|ai_discovery",
#   "canonical": {
#     "name_ko": "...",
#     "name_en": "...",
#     "explanation_short": {"en": "..."},
#     ...
#   },
#   "confidence": 0.95,
#   "processing_time_ms": 450
# }

# 기록: match_type, confidence, processing_time
```

#### Step 3: B2B 워크플로우 테스트

```
1. B2B 관리자 UI: http://localhost:8081
   ├─ 메뉴판 사진 업로드 (같은 사진)
   ├─ OCR 결과 확인
   ├─ 매칭 결과 카드 검증
   └─ 신뢰도 배지 (✅ ⚠️ ❓) 확인

2. 검수 화면 (B2B-2)
   ├─ 각 메뉴 카드의 신뢰도 확인
   ├─ "수정 필요" 메뉴 수 기록
   └─ [전체 승인] 클릭

3. QR 생성 확인
   ├─ QR 코드 URL 확인
   └─ 스캔 (B2B-3 페이지 확인)
```

#### Step 4: B2C 결과 검증

```
1. QR 스캔 결과
   ├─ 다국어 표시 (영/일/중)
   ├─ 알레르기 정보 정확도
   ├─ 설명 텍스트 품질
   └─ 응답 속도 측정

2. 검색 UI (http://localhost:8080)
   ├─ 메뉴명 직접 입력 → 검색
   ├─ 결과 카드 표시 (영문 설명)
   ├─ 다중 검색 (쉼표 구분)
   └─ 응답 시간 측정
```

---

## 📊 **Phase 3: 데이터 기록 (현장에서 실시간)**

### 3.1 테스트 로그 템플릿

**파일:** `/app/data/e2e_test_20250218/{restaurant}/log.json`

```json
{
  "test_date": "2025-02-18",
  "restaurant": "명동 교자",
  "location": "서울시 중구 명동 1-가",
  "tester": "개발자명",

  "ocr_phase": {
    "total_photos": 45,
    "menu_items_found": 8,
    "ocr_confidence_avg": 0.92,
    "processing_time_ms": 1200,
    "success": true,
    "notes": "깔끔한 메뉴판, OCR 정확함"
  },

  "matching_phase": {
    "total_menus": 8,
    "exact_match": 7,
    "modifier_match": 1,
    "ai_discovery": 0,
    "failed_menus": [],
    "processing_time_avg_ms": 450,
    "db_hit_rate": 0.875
  },

  "b2b_phase": {
    "upload_success": true,
    "matching_display_correct": true,
    "confidence_badges": "✅ ✅ ✅ ✅ ✅ ⚠️ ✅ ✅",
    "user_corrections_needed": 1,
    "user_correction_rate": 0.125
  },

  "b2c_phase": {
    "qr_generation_success": true,
    "qr_scan_success": true,
    "language_tabs": ["en", "ja", "zh"],
    "description_quality": "excellent",
    "allergen_accuracy": 0.99,
    "response_time_ms": 2300
  },

  "kpi_measurements": {
    "ocr_recognition_rate": 1.0,
    "db_matching_rate": 0.875,
    "response_time_p95_ms": 2800,
    "user_correction_rate": 0.125
  },

  "issues_found": [
    {
      "type": "minor",
      "description": "손글씨 부분 OCR 미인식",
      "location": "메뉴판 하단",
      "severity": "low"
    }
  ],

  "screenshots": [
    "menu_photo_001.jpg",
    "ocr_result_001.json",
    "b2c_result_001.png",
    "admin_dashboard_001.png"
  ],

  "notes": "전반적으로 매우 좋은 결과. OCR 정확도 높음."
}
```

### 3.2 현장 기록 스크립트 (Python)

**파일:** `/app/scripts/e2e_test_logger.py`

```python
#!/usr/bin/env python3
"""
E2E 테스트 현장 기록 도구

사용법:
  python e2e_test_logger.py --restaurant "명동 교자" --start
  # ... 테스트 진행 ...
  python e2e_test_logger.py --restaurant "명동 교자" --log-ocr "45" "8" "0.92"
  python e2e_test_logger.py --restaurant "명동 교자" --log-matching "7" "1" "0" "450"
  python e2e_test_logger.py --restaurant "명동 교자" --finalize
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

class E2ETestLogger:
    def __init__(self, restaurant: str):
        self.restaurant = restaurant
        self.test_dir = Path(f"/app/data/e2e_test_{datetime.now():%Y%m%d}") / restaurant.replace(" ", "_")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.test_dir / "log.json"
        self.log_data = self._load_or_init()

    def _load_or_init(self) -> dict:
        if self.log_file.exists():
            with open(self.log_file) as f:
                return json.load(f)

        return {
            "test_date": datetime.now().isoformat(),
            "restaurant": self.restaurant,
            "ocr_phase": {},
            "matching_phase": {},
            "b2b_phase": {},
            "b2c_phase": {},
            "kpi_measurements": {},
            "issues_found": [],
            "screenshots": [],
            "notes": ""
        }

    def log_ocr(self, total_photos: int, menu_items: int, confidence: float, time_ms: int):
        """OCR 결과 기록"""
        self.log_data["ocr_phase"] = {
            "total_photos": total_photos,
            "menu_items_found": menu_items,
            "ocr_confidence_avg": confidence,
            "processing_time_ms": time_ms,
            "success": True
        }
        self._save()
        print(f"✅ OCR logged: {menu_items} items, confidence {confidence}")

    def log_matching(self, exact: int, modifier: int, ai: int, time_ms: int, failed: list = None):
        """매칭 결과 기록"""
        total = exact + modifier + ai
        self.log_data["matching_phase"] = {
            "total_menus": total,
            "exact_match": exact,
            "modifier_match": modifier,
            "ai_discovery": ai,
            "failed_menus": failed or [],
            "processing_time_avg_ms": time_ms,
            "db_hit_rate": exact / total if total > 0 else 0
        }
        self._save()
        print(f"✅ Matching logged: {exact}/{total} exact, DB hit rate {exact/total*100:.1f}%")

    def log_issue(self, issue_type: str, description: str, severity: str):
        """이슈 기록"""
        self.log_data["issues_found"].append({
            "type": issue_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
        self._save()
        print(f"⚠️ Issue logged: {issue_type} - {description}")

    def finalize(self):
        """테스트 완료 및 KPI 계산"""
        ocr = self.log_data["ocr_phase"]
        matching = self.log_data["matching_phase"]

        # KPI 계산
        self.log_data["kpi_measurements"] = {
            "ocr_recognition_rate": ocr.get("menu_items_found", 0) / ocr.get("total_photos", 1),
            "db_matching_rate": matching.get("db_hit_rate", 0),
            "issues_count": len(self.log_data["issues_found"])
        }
        self._save()

        print(f"\n🎯 Test Complete for {self.restaurant}")
        print(json.dumps(self.log_data["kpi_measurements"], indent=2))

    def _save(self):
        """디스크에 저장"""
        with open(self.log_file, 'w') as f:
            json.dump(self.log_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--restaurant", required=True)
    parser.add_argument("--log-ocr", nargs=4, type=int, help="total_photos menu_items confidence time_ms")
    parser.add_argument("--log-matching", nargs=4, type=int, help="exact modifier ai time_ms")
    parser.add_argument("--log-issue", nargs=3, help="type description severity")
    parser.add_argument("--finalize", action="store_true")

    args = parser.parse_args()
    logger = E2ETestLogger(args.restaurant)

    if args.log_ocr:
        logger.log_ocr(*args.log_ocr)
    if args.log_matching:
        logger.log_matching(*args.log_matching)
    if args.log_issue:
        logger.log_issue(*args.log_issue)
    if args.finalize:
        logger.finalize()
```

---

## 📈 **Phase 4: 데이터 분석 (사무실)**

### 4.1 결과 수집

**3개 식당의 로그 파일 수집:**

```
/app/data/e2e_test_20250218/
├── 명동_교자/
│   ├── log.json
│   ├── menu_photos/ (45장)
│   └── ocr_results.json
├── 신계순_순대국/
│   └── (동일)
└── 명동_할머니순대/
    └── (동일)
```

### 4.2 리포트 생성 스크립트

**파일:** `/app/scripts/generate_e2e_report.py`

```python
#!/usr/bin/env python3
"""
E2E 테스트 결과 리포트 자동 생성

사용법:
  python generate_e2e_report.py --date 20250218 --output report.md
"""

import json
import os
from pathlib import Path
from datetime import datetime

def generate_report(test_date: str, output_file: str):
    """
    3개 식당의 로그를 수집하여 최종 리포트 생성
    """
    test_dir = Path(f"/app/data/e2e_test_{test_date}")
    restaurants = {}

    # 각 식당의 로그 수집
    for restaurant_dir in test_dir.iterdir():
        if restaurant_dir.is_dir():
            log_file = restaurant_dir / "log.json"
            if log_file.exists():
                with open(log_file) as f:
                    restaurants[restaurant_dir.name] = json.load(f)

    # 마크다운 리포트 생성
    report = f"""# End-to-End 통합 테스트 리포트

**테스트 일시:** {test_date}
**작성일:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 종합 결과

| 지표 | 목표 | 실제 | 평가 |
|------|------|------|------|
| OCR 인식률 | 80%+ | {calc_avg_ocr(restaurants):.1f}% | {'✅' if calc_avg_ocr(restaurants) >= 80 else '⚠️'} |
| DB 매칭률 | 70%+ | {calc_avg_matching(restaurants):.1f}% | {'✅' if calc_avg_matching(restaurants) >= 70 else '⚠️'} |
| 평균 응답 시간 | 3초 이내 | {calc_avg_response_time(restaurants):.2f}s | {'✅' if calc_avg_response_time(restaurants) <= 3 else '⚠️'} |
| 사용자 수정률 | 20% 이하 | {calc_avg_correction(restaurants):.1f}% | {'✅' if calc_avg_correction(restaurants) <= 20 else '⚠️'} |

"""

    # 각 식당별 상세
    for restaurant, data in restaurants.items():
        report += f"""
## {restaurant}

**메뉴 수:** {data['matching_phase'].get('total_menus', 0)}개
**OCR 정확도:** {data['ocr_phase'].get('ocr_confidence_avg', 0):.1%}
**DB 매칭률:** {data['matching_phase'].get('db_hit_rate', 0):.1%}
**평균 응답 시간:** {data['matching_phase'].get('processing_time_avg_ms', 0)/1000:.2f}s
**사용자 수정률:** {data['b2b_phase'].get('user_correction_rate', 0):.1%}

### 상세 분석

- 정확 매칭: {data['matching_phase'].get('exact_match', 0)}개
- 수식어 분해: {data['matching_phase'].get('modifier_match', 0)}개
- AI Discovery: {data['matching_phase'].get('ai_discovery', 0)}개
- 실패: {len(data['matching_phase'].get('failed_menus', []))}개

### 발견 사항

"""
        for issue in data.get('issues_found', []):
            report += f"- **{issue['severity'].upper()}**: {issue['description']}\n"

    # 권장사항
    report += f"""

---

## 💡 권장사항

1. **OCR 개선**: 손글씨 메뉴판은 사용자 안내 필요
2. **매칭 확대**: 미등록 메뉴 추가 → 매칭률 상향
3. **성능 최적화**: 응답 시간 2초대 달성 (P2-2에서)
4. **모니터링**: 실패 메뉴 자동 큐에 추가

---

**테스트 완료자:** 개발팀
**다음 단계:** Sprint 3 P2-1 (QR 메뉴) 진행
"""

    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ Report saved: {output_file}")


def calc_avg_ocr(restaurants):
    values = [r.get('ocr_phase', {}).get('ocr_confidence_avg', 0) * 100 for r in restaurants.values()]
    return sum(values) / len(values) if values else 0

def calc_avg_matching(restaurants):
    values = [r.get('matching_phase', {}).get('db_hit_rate', 0) * 100 for r in restaurants.values()]
    return sum(values) / len(values) if values else 0

def calc_avg_response_time(restaurants):
    times = []
    for r in restaurants.values():
        time_ms = r.get('matching_phase', {}).get('processing_time_avg_ms', 0)
        times.append(time_ms / 1000)
    return sum(times) / len(times) if times else 0

def calc_avg_correction(restaurants):
    rates = [r.get('b2b_phase', {}).get('user_correction_rate', 0) * 100 for r in restaurants.values()]
    return sum(rates) / len(rates) if rates else 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Test date (YYYYMMDD)")
    parser.add_argument("--output", default="E2E_TEST_REPORT.md")

    args = parser.parse_args()
    generate_report(args.date, args.output)
```

---

## 🧪 **Phase 5: 현장 테스트 체크리스트**

### Day 1: 메뉴판 촬영 + OCR 테스트

#### 식당 1 (명동 교자)
- [ ] 섭외 확인
- [ ] 메뉴판 30-50장 촬영
- [ ] OCR API 호출 (1장)
- [ ] 결과 기록: menu_items, ocr_confidence
- [ ] 각 메뉴 /identify API 테스트
- [ ] 결과 json 파일 저장

#### 식당 2 (신계순 순대국)
- [ ] (동일 프로세스)

#### 식당 3 (명동 할머니순대)
- [ ] (동일 프로세스)

### Day 2: B2B/B2C 워크플로우 + 리포트

#### B2B 흐름
- [ ] 각 식당 메뉴판 B2B 업로드
- [ ] OCR 결과 확인
- [ ] 신뢰도 배지 검증 (✅ ⚠️ ❓)
- [ ] [전체 승인] 클릭
- [ ] QR 생성 URL 확인

#### B2C 흐름
- [ ] QR 스캔 → B2B-3 페이지 표시
- [ ] 다국어 탭 (영/일/중) 테스트
- [ ] 직접 검색 UI 테스트
- [ ] 응답 시간 측정

#### 데이터 수집
- [ ] 3개 restaurants/ 폴더에 로그 저장
- [ ] generate_e2e_report.py 실행
- [ ] E2E_TEST_REPORT_20250218.md 생성

---

## 📝 **현장에서 사용할 커맨드**

### 빠른 OCR 테스트

```bash
# 1. 메뉴판 사진 업로드
curl -X POST http://localhost:8000/api/v1/menu/recognize \
  -F "file=@menu_photo.jpg" \
  -s | jq '.menu_items | length'

# 2. 첫 메뉴 매칭 테스트
MENU="$(curl -X POST http://localhost:8000/api/v1/menu/recognize \
  -F 'file=@menu_photo.jpg' -s | jq -r '.menu_items[0].name_ko')"

curl -X POST http://localhost:8000/api/v1/menu/identify \
  -H "Content-Type: application/json" \
  -d "{\"menu_name_ko\": \"$MENU\"}" \
  -s | jq '.confidence'
```

### 현장 로깅 (간단 버전)

```bash
# E2E 로그 기록 (간단 JSON)
cat > /app/data/e2e_test_20250218/restaurant_log.json << EOF
{
  "restaurant": "명동 교자",
  "ocr_items": 8,
  "ocr_confidence": 0.92,
  "exact_matches": 7,
  "modifier_matches": 1,
  "ai_discoveries": 0,
  "response_time_ms": 450,
  "user_corrections": 0
}
EOF
```

---

## 📊 **KPI 계산 공식**

```
OCR 인식률 (%) = (인식된 메뉴명 수) / (실제 메뉴 수) × 100
                목표: >= 80%

DB 매칭률 (%) = (AI 호출 없이 처리된 메뉴) / (전체 메뉴) × 100
                목표: >= 70%

응답 시간 (p95) = 95% 요청이 이 시간 이내 완료
                목표: <= 3초

사용자 수정률 (%) = (사용자가 수정한 메뉴) / (전체 메뉴) × 100
                  목표: <= 20%
```

---

## 🎯 **성공 기준**

**전체 통과 (Green):**
- OCR >= 80%
- 매칭 >= 70%
- 응답 <= 3초
- 수정 <= 20%

**부분 통과 (Yellow):**
- 2-3개 지표 목표 달성
- P2-2에서 개선 가능

**미달 (Red):**
- 1개 이하 지표 달성
- 아키텍처 재검토 필요

---

**다음 단계:** 현장 테스트 후 P2-1 (QR) 진행

