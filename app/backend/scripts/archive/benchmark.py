"""
Performance Benchmark Script - Sprint 3 P2-2
Measure API response times and throughput
"""

import requests
import time
import statistics
from typing import Dict


API_BASE_URL = "http://localhost:8000"

# Test cases
TEST_CASES = [
    ("김치찌개", "exact match"),
    ("할머니김치찌개", "modifier decomposition"),
    ("스테이크", "AI discovery"),
    ("비빔밥", "exact match"),
    ("얼큰순두부찌개", "modifier"),
]


def benchmark_identify_api(iterations: int = 100) -> Dict:
    """
    /api/v1/menu/identify 엔드포인트 벤치마크

    Args:
        iterations: 반복 횟수

    Returns:
        {
            "avg_ms": float,
            "p50_ms": float,
            "p95_ms": float,
            "p99_ms": float,
            "max_ms": float,
            "min_ms": float
        }
    """
    response_times = []

    print(f"\n🔄 Benchmarking /api/v1/menu/identify ({iterations} requests)...")

    for i in range(iterations):
        menu_name, case_type = TEST_CASES[i % len(TEST_CASES)]

        start = time.time()
        response = requests.post(
            f"{API_BASE_URL}/api/v1/menu/identify", json={"menu_name_ko": menu_name}
        )
        end = time.time()

        elapsed_ms = (end - start) * 1000
        response_times.append(elapsed_ms)

        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{iterations} requests")

    # Calculate statistics
    response_times.sort()

    results = {
        "avg_ms": statistics.mean(response_times),
        "median_ms": statistics.median(response_times),
        "p50_ms": response_times[len(response_times) // 2],
        "p95_ms": response_times[int(len(response_times) * 0.95)],
        "p99_ms": response_times[int(len(response_times) * 0.99)],
        "max_ms": max(response_times),
        "min_ms": min(response_times),
    }

    return results


def print_results(results: Dict):
    """결과 출력"""
    print("\n" + "=" * 50)
    print("📊 Performance Benchmark Results")
    print("=" * 50)
    print(f"Average:    {results['avg_ms']:.2f} ms")
    print(f"Median:     {results['median_ms']:.2f} ms")
    print(f"P50:        {results['p50_ms']:.2f} ms")
    print(f"P95:        {results['p95_ms']:.2f} ms")
    print(f"P99:        {results['p99_ms']:.2f} ms")
    print(f"Max:        {results['max_ms']:.2f} ms")
    print(f"Min:        {results['min_ms']:.2f} ms")
    print("=" * 50)

    # Performance assessment
    p95 = results["p95_ms"]
    if p95 < 100:
        print("✅ Excellent performance (P95 < 100ms)")
    elif p95 < 500:
        print("✅ Good performance (P95 < 500ms)")
    elif p95 < 1000:
        print("⚠️  Acceptable performance (P95 < 1s)")
    elif p95 < 3000:
        print("⚠️  Needs optimization (P95 < 3s)")
    else:
        print("❌ Poor performance (P95 >= 3s)")

    print("\nTarget: P95 < 2000ms (2 seconds)")
    print(f"Current: P95 = {p95:.0f}ms")

    if p95 < 2000:
        print("🎯 TARGET ACHIEVED! ✅")
    else:
        print(f"❌ Need {p95 - 2000:.0f}ms improvement")


def run_benchmark():
    """Run full benchmark suite"""
    print("🚀 Starting Performance Benchmark...")
    print(f"API URL: {API_BASE_URL}")

    # Health check
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print("❌ API server health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        return

    # Run benchmark
    results = benchmark_identify_api(iterations=100)
    print_results(results)


if __name__ == "__main__":
    run_benchmark()
