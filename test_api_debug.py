#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API 디버깅 스크립트"""
import sys
import io
import requests
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_BASE = "https://menu-knowledge.chargeapp.net"

def test_api(menu_name):
    url = f"{API_BASE}/api/v1/menu/identify"
    payload = {"menu_name_ko": menu_name}

    print(f"\n===== 테스트: {menu_name} =====")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")

    response = requests.post(url, json=payload, timeout=10)

    print(f"\nStatus: {response.status_code}")
    print(f"\n전체 응답:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# TC-06
test_api("한우불고기")

# TC-08
test_api("옛날통닭")

# 추가: "불고기" 단독 테스트
test_api("불고기")
