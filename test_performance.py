import requests
import time

for i in range(1, 6):
    start = time.time()
    r = requests.post('http://localhost:8000/api/v1/menu/identify', json={'menu_name_ko': '김치찌개'})
    elapsed = (time.time() - start) * 1000
    result = r.json()
    print(f'Try {i}: {elapsed:.2f}ms - {result["match_type"]}')
