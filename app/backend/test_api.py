import requests

# Test the menu identify API
test_cases = [
    ("김치찌개", "Basic search"),
    ("왕얼큰순두부찌개", "Modifier decomposition"),
    ("스테이크", "AI discovery needed"),
]

print("Testing Menu Identify API\n" + "="*50)

for menu_name, description in test_cases:
    print(f"\nTest: {description}")
    print(f"Input: {menu_name}")

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/menu/identify",
            json={"menu_name_ko": menu_name}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Match Type: {data['match_type']}")

            if data.get('canonical'):
                print(f"     Canonical: {data['canonical']['name_ko']}")
                print(f"     English: {data['canonical']['name_en']}")

            if data.get('modifiers'):
                print(f"     Modifiers: {len(data['modifiers'])} found")
                for mod in data['modifiers']:
                    print(f"       - {mod['text_ko']} = {mod['translation_en']}")
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"[ERROR] {str(e)}")

print("\n" + "="*50)
print("Frontend URL: http://localhost:8080")
print("Backend API: http://localhost:8000")
