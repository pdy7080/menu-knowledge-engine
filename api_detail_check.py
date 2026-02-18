"""Quick detail check for key API responses."""
import requests
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://localhost:8000"

# Test 1: Exact Match
r1 = requests.post(f"{BASE}/api/v1/menu/identify", json={"menu_name_ko": "김치찌개"})
print("=== Exact Match: kimchi-jjigae ===")
print(json.dumps(r1.json(), ensure_ascii=False, indent=2))

# Test 2: Multi Modifier
r2 = requests.post(f"{BASE}/api/v1/menu/identify", json={"menu_name_ko": "왕얼큰뼈해장국"})
print("\n=== Multi Modifier: wang-eolkeun-ppyeo-haejangguk ===")
print(json.dumps(r2.json(), ensure_ascii=False, indent=2))

# Test 3: Admin Stats
r3 = requests.get(f"{BASE}/api/v1/admin/stats")
print("\n=== Admin Stats ===")
print(json.dumps(r3.json(), ensure_ascii=False, indent=2))

# Test 4: Data counts
r4 = requests.get(f"{BASE}/api/v1/concepts")
r5 = requests.get(f"{BASE}/api/v1/modifiers")
r6 = requests.get(f"{BASE}/api/v1/canonical-menus")
print(f"\nConcepts: {r4.json()['total']}")
print(f"Modifiers: {r5.json()['total']}")
print(f"Canonical Menus: {r6.json()['total']}")

# Test 5: Empty input bug
r7 = requests.post(f"{BASE}/api/v1/menu/identify", json={"menu_name_ko": ""})
print(f"\n=== Empty Input Bug ===")
print(f"Status: {r7.status_code}")
print(json.dumps(r7.json(), ensure_ascii=False, indent=2))

# Test 6: Restaurant list
r8 = requests.get(f"{BASE}/api/v1/b2b/restaurants")
print(f"\n=== Restaurants ===")
print(f"Total: {r8.json()['total']}")

# Test 7: Queue
r9 = requests.get(f"{BASE}/api/v1/admin/queue")
print(f"\n=== Admin Queue ===")
print(f"Total: {r9.json()['total']}")
