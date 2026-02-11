#!/usr/bin/env python3
"""
E2E 테스트 실행기 - 현장에서 바로 사용

사용법:
  python e2e_test_runner.py \
    --restaurant "명동 교자" \
    --menu-photos /path/to/photos \
    --api-url http://localhost:8000 \
    --output-dir /app/data/e2e_test_20250218

현장에서 빠르게:
  python e2e_test_runner.py --restaurant "명동 교자" --quick-test menu1.jpg menu2.jpg
"""

import json
import sys
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import statistics


class E2ETestRunner:
    def __init__(self, restaurant: str, api_url: str, output_dir: str):
        self.restaurant = restaurant
        self.api_url = api_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.output_dir / f"{restaurant.replace(' ', '_')}_log.json"
        self.ocr_results = []
        self.matching_results = []
        self.response_times = []

    def test_ocr(self, image_path: str) -> Dict:
        """OCR 테스트"""
        print(f"🔄 OCR testing: {Path(image_path).name}")

        start = time.time()
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.api_url}/api/v1/menu/recognize",
                    files=files,
                    timeout=10
                )
            elapsed = time.time() - start

            if response.status_code == 200:
                result = response.json()
                self.ocr_results.append({
                    'image': Path(image_path).name,
                    'menu_count': len(result.get('menu_items', [])),
                    'confidence': result.get('ocr_confidence', 0),
                    'time_ms': int(elapsed * 1000),
                    'success': True
                })

                print(f"  ✅ Found {len(result.get('menu_items', []))} menus, "
                      f"confidence: {result.get('ocr_confidence', 0):.2%}")
                return result
            else:
                print(f"  ❌ Error: {response.status_code}")
                self.ocr_results.append({
                    'image': Path(image_path).name,
                    'success': False,
                    'error': response.text
                })
                return None
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            self.ocr_results.append({
                'image': Path(image_path).name,
                'success': False,
                'error': str(e)
            })
            return None

    def test_matching(self, menu_name_ko: str) -> Dict:
        """메뉴 매칭 테스트"""
        start = time.time()
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/menu/identify",
                json={"menu_name_ko": menu_name_ko},
                timeout=10
            )
            elapsed = time.time() - start
            self.response_times.append(elapsed)

            if response.status_code == 200:
                result = response.json()
                match_type = result.get('match_type', 'unknown')
                confidence = result.get('confidence', 0)

                self.matching_results.append({
                    'menu': menu_name_ko,
                    'match_type': match_type,
                    'confidence': confidence,
                    'time_ms': int(elapsed * 1000),
                    'success': True,
                    'canonical': result.get('canonical', {}).get('name_ko')
                })

                badge = {
                    'exact': '✅',
                    'modifier': '⚠️',
                    'ai_discovery': '🔍',
                    'failed': '❌'
                }.get(match_type, '❓')

                print(f"  {badge} {menu_name_ko}: {match_type} (confidence: {confidence:.2%})")
                return result
            else:
                print(f"  ❌ {menu_name_ko}: Error {response.status_code}")
                self.matching_results.append({
                    'menu': menu_name_ko,
                    'success': False,
                    'error': response.text
                })
                return None
        except Exception as e:
            print(f"  ❌ {menu_name_ko}: Exception {e}")
            self.matching_results.append({
                'menu': menu_name_ko,
                'success': False,
                'error': str(e)
            })
            return None

    def run_batch_matching(self, menu_names: List[str]):
        """여러 메뉴 매칭 테스트"""
        print(f"\n🔄 Testing {len(menu_names)} menus...")
        for menu in menu_names:
            self.test_matching(menu)

    def calculate_kpis(self) -> Dict:
        """KPI 계산"""
        total_ocr = len([r for r in self.ocr_results if r.get('success')])
        total_menus = sum(r.get('menu_count', 0) for r in self.ocr_results if r.get('success'))

        exact_matches = len([r for r in self.matching_results if r.get('match_type') == 'exact'])
        failed_matches = len([r for r in self.matching_results if not r.get('success')])
        total_matches = len(self.matching_results)

        response_times_sorted = sorted(self.response_times)
        p95_idx = int(len(response_times_sorted) * 0.95)
        p95_time = response_times_sorted[p95_idx] if p95_idx < len(response_times_sorted) else 0

        return {
            'ocr_success_rate': total_ocr / len(self.ocr_results) if self.ocr_results else 0,
            'total_menus_found': total_menus,
            'db_matching_rate': exact_matches / total_matches if total_matches > 0 else 0,
            'failed_menus': failed_matches,
            'average_response_time_ms': int(statistics.mean(self.response_times) * 1000) if self.response_times else 0,
            'p95_response_time_s': round(p95_time, 2),
            'test_timestamp': datetime.now().isoformat()
        }

    def save_results(self):
        """결과 저장"""
        kpis = self.calculate_kpis()

        final_log = {
            'restaurant': self.restaurant,
            'test_date': datetime.now().isoformat(),
            'ocr_results': self.ocr_results,
            'matching_results': self.matching_results,
            'kpis': kpis,
            'status': 'completed'
        }

        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(final_log, f, indent=2, ensure_ascii=False)

        print(f"\n📊 Results saved to: {self.log_file}")
        print("\n🎯 KPI Summary:")
        print(f"  OCR Success Rate: {kpis['ocr_success_rate']:.1%}")
        print(f"  DB Matching Rate: {kpis['db_matching_rate']:.1%}")
        print(f"  Average Response: {kpis['average_response_time_ms']}ms")
        print(f"  P95 Response: {kpis['p95_response_time_s']}s")

        return final_log

    def quick_test(self, image_files: List[str]):
        """빠른 테스트 모드 (1개 이미지)"""
        print(f"⚡ Quick test mode for {self.restaurant}")

        for image_file in image_files:
            ocr_result = self.test_ocr(image_file)

            if ocr_result:
                menu_names = [item['name_ko'] for item in ocr_result.get('menu_items', [])[:5]]
                self.run_batch_matching(menu_names)

        return self.save_results()


def main():
    parser = argparse.ArgumentParser(description='E2E Test Runner')
    parser.add_argument('--restaurant', required=True, help='Restaurant name')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API URL')
    parser.add_argument('--output-dir', default='/app/data/e2e_test', help='Output directory')
    parser.add_argument('--menu-photos', help='Directory with menu photos')
    parser.add_argument('--quick-test', nargs='+', help='Quick test with specific images')

    args = parser.parse_args()

    runner = E2ETestRunner(args.restaurant, args.api_url, args.output_dir)

    if args.quick_test:
        runner.quick_test(args.quick_test)
    elif args.menu_photos:
        photos_dir = Path(args.menu_photos)
        image_files = list(photos_dir.glob('*.jpg')) + list(photos_dir.glob('*.png'))

        print(f"📸 Found {len(image_files)} images")
        for image_file in image_files[:10]:  # 처음 10개만 테스트
            ocr_result = runner.test_ocr(str(image_file))

            if ocr_result:
                menu_names = [item['name_ko'] for item in ocr_result.get('menu_items', [])]
                runner.run_batch_matching(menu_names)

        runner.save_results()
    else:
        print("Use --quick-test or --menu-photos")


if __name__ == '__main__':
    main()
