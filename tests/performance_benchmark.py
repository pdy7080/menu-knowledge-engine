# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Performance Benchmark - Redis Caching Effectiveness
Measures response time with and without Redis cache
"""
import requests
import time
import statistics
import json
import sys
from typing import List, Dict

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"
ITERATIONS = 10

def measure_response_time(url: str, payload: Dict) -> float:
    """Measure single API call response time"""
    start = time.time()
    response = requests.post(url, json=payload)
    elapsed = time.time() - start

    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")

    return elapsed

def clear_redis_cache():
    """Clear Redis cache via admin endpoint"""
    try:
        requests.delete(f"{BASE_URL}/api/v1/admin/cache/clear")
    except:
        pass  # Endpoint may not exist

def run_benchmark(test_name: str, endpoint: str, payload: Dict) -> Dict:
    """Run benchmark for a specific test case"""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"{'='*60}")

    # Clear cache before test
    clear_redis_cache()
    time.sleep(1)

    # Phase 1: Cold cache (no Redis)
    print(f"\n[Phase 1] Cold Cache (first {ITERATIONS} calls)")
    cold_times: List[float] = []

    for i in range(ITERATIONS):
        elapsed = measure_response_time(f"{BASE_URL}{endpoint}", payload)
        cold_times.append(elapsed)
        print(f"  Call {i+1}: {elapsed:.4f}s")

    # Phase 2: Warm cache (Redis hits)
    print(f"\n[Phase 2] Warm Cache (next {ITERATIONS} calls)")
    warm_times: List[float] = []

    for i in range(ITERATIONS):
        elapsed = measure_response_time(f"{BASE_URL}{endpoint}", payload)
        warm_times.append(elapsed)
        print(f"  Call {i+1}: {elapsed:.4f}s")

    # Calculate statistics
    cold_avg = statistics.mean(cold_times)
    cold_median = statistics.median(cold_times)
    cold_stdev = statistics.stdev(cold_times) if len(cold_times) > 1 else 0

    warm_avg = statistics.mean(warm_times)
    warm_median = statistics.median(warm_times)
    warm_stdev = statistics.stdev(warm_times) if len(warm_times) > 1 else 0

    improvement_pct = ((cold_avg - warm_avg) / cold_avg * 100) if cold_avg > 0 else 0
    speedup = cold_avg / warm_avg if warm_avg > 0 else 0

    results = {
        "test_name": test_name,
        "cold_cache": {
            "avg": cold_avg,
            "median": cold_median,
            "stdev": cold_stdev,
            "min": min(cold_times),
            "max": max(cold_times)
        },
        "warm_cache": {
            "avg": warm_avg,
            "median": warm_median,
            "stdev": warm_stdev,
            "min": min(warm_times),
            "max": max(warm_times)
        },
        "improvement_pct": improvement_pct,
        "speedup": speedup
    }

    print(f"\n{'-'*60}")
    print(f"[*] Results Summary:")
    print(f"{'-'*60}")
    print(f"Cold Cache (DB):   Avg={cold_avg:.4f}s  Median={cold_median:.4f}s  StdDev={cold_stdev:.4f}s")
    print(f"Warm Cache (Redis): Avg={warm_avg:.4f}s  Median={warm_median:.4f}s  StdDev={warm_stdev:.4f}s")
    print(f"Improvement:       {improvement_pct:.1f}% faster ({speedup:.2f}x speedup)")

    return results

def get_redis_stats() -> Dict:
    """Get Redis keyspace statistics"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/admin/stats")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {}

def main():
    print("==> Menu Knowledge Engine - Performance Benchmark")
    print(f"Iterations per phase: {ITERATIONS}")
    print(f"Target: {BASE_URL}")

    all_results = []

    # Test 1: Menu Identification (Exact Match)
    test1_payload = {
        "menu_name_ko": "김치찌개"
    }
    results1 = run_benchmark(
        "Menu Identification - Exact Match (김치찌개)",
        "/api/v1/menu/identify",
        test1_payload
    )
    all_results.append(results1)

    # Test 2: Menu Identification (Modifier Decomposition)
    test2_payload = {
        "menu_name_ko": "매운 김치찌개"
    }
    results2 = run_benchmark(
        "Menu Identification - Modifier Decomposition (매운 김치찌개)",
        "/api/v1/menu/identify",
        test2_payload
    )
    all_results.append(results2)

    # Final Summary
    print(f"\n{'='*60}")
    print("[*] Overall Performance Summary")
    print(f"{'='*60}\n")

    for result in all_results:
        print(f"[OK] {result['test_name']}")
        print(f"   Improvement: {result['improvement_pct']:.1f}% ({result['speedup']:.2f}x speedup)")
        print(f"   Cold: {result['cold_cache']['avg']:.4f}s -> Warm: {result['warm_cache']['avg']:.4f}s")
        print()

    # Redis Stats
    stats = get_redis_stats()
    if stats:
        print("[*] Redis Cache Statistics:")
        print(f"   Total Scans: {stats.get('total_scans', 0)}")
        print(f"   Total Menus: {stats.get('total_menus', 0)}")

    # Save results to JSON
    with open('C:/project/menu/tests/performance_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Results saved to: tests/performance_results.json")

if __name__ == "__main__":
    main()
