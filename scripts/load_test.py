"""
Production Load Testing Script
Measure P95 response time under realistic load
"""
import asyncio
import time
import statistics
from typing import List
import httpx

# Production API endpoint
API_URL = "http://localhost:8000/api/v1/menu/identify"

# Test menu names (realistic Korean menus)
TEST_MENUS = [
    "김치찌개", "된장찌개", "불고기", "비빔밥", "냉면",
    "갈비탕", "삼계탕", "떡볶이", "순대국", "설렁탕",
]

async def single_request(client: httpx.AsyncClient, menu_name: str) -> float:
    """Single API request with timing"""
    start = time.time()
    try:
        response = await client.post(
            API_URL,
            json={"menu_name": menu_name},
            timeout=10.0
        )
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error for '{menu_name}': {e}")
        return 0.0

    elapsed = (time.time() - start) * 1000  # milliseconds
    return elapsed

async def benchmark(num_requests: int = 100) -> dict:
    """Run benchmark with concurrent requests"""
    print(f"🚀 Starting benchmark: {num_requests} requests")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Warm-up (5 requests)
        print("🔥 Warm-up phase...")
        for _ in range(5):
            await single_request(client, TEST_MENUS[0])

        # Actual benchmark
        print(f"📊 Benchmark phase ({num_requests} requests)...")
        times: List[float] = []

        for i in range(num_requests):
            menu_name = TEST_MENUS[i % len(TEST_MENUS)]
            elapsed = await single_request(client, menu_name)

            if elapsed > 0:
                times.append(elapsed)

            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{num_requests}")

    # Calculate statistics
    if not times:
        return {"error": "No successful requests"}

    times_sorted = sorted(times)

    stats = {
        "total_requests": len(times),
        "average": statistics.mean(times),
        "median": statistics.median(times),
        "p50": times_sorted[int(len(times) * 0.50)],
        "p95": times_sorted[int(len(times) * 0.95)],
        "p99": times_sorted[int(len(times) * 0.99)],
        "min": min(times),
        "max": max(times),
    }

    return stats

def print_results(stats: dict):
    """Pretty print benchmark results"""
    print("\n" + "=" * 60)
    print("📊 BENCHMARK RESULTS")
    print("=" * 60)

    if "error" in stats:
        print(f"❌ {stats['error']}")
        return

    print(f"Total Requests:  {stats['total_requests']}")
    print(f"Average:         {stats['average']:.2f}ms")
    print(f"Median:          {stats['median']:.2f}ms")
    print(f"P50:             {stats['p50']:.2f}ms")
    print(f"P95:             {stats['p95']:.2f}ms {'✅' if stats['p95'] < 2000 else '❌'}")
    print(f"P99:             {stats['p99']:.2f}ms")
    print(f"Min:             {stats['min']:.2f}ms")
    print(f"Max:             {stats['max']:.2f}ms")
    print("=" * 60)

    # Target evaluation
    target_p95 = 2000
    if stats['p95'] < target_p95:
        print(f"✅ SUCCESS: P95 under target ({target_p95}ms)")
    else:
        diff = stats['p95'] - target_p95
        print(f"⚠️  WARNING: P95 over target by {diff:.2f}ms")

if __name__ == "__main__":
    stats = asyncio.run(benchmark(100))
    print_results(stats)
