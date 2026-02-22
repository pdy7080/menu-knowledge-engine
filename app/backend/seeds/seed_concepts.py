"""
Concept 시드 데이터 (대분류 12개 + 중분류 35개 = 47개)
"""

from typing import List, Dict, Any


def get_concept_seeds() -> List[Dict[str, Any]]:
    """Concept 트리 시드 데이터 반환"""
    # 1. 국물요리
    soup_stew = {
        "name_ko": "국물요리",
        "name_en": "Soups & Stews",
        "definition_ko": "국물이 주가 되는 한국 요리 총칭",
        "definition_en": "Korean dishes where broth or soup is the main component",
        "parent": None,
        "children": [
            {
                "name_ko": "탕",
                "name_en": "Tang (Rich Soup)",
                "definition_ko": "오랜 시간 끓여 진한 국물을 낸 요리",
                "definition_en": "Deeply simmered soups with rich, concentrated broth",
            },
            {
                "name_ko": "국",
                "name_en": "Guk (Light Soup)",
                "definition_ko": "가볍게 끓인 맑은 국물 요리, 밥과 함께 먹음",
                "definition_en": "Light soups typically served with rice as part of a meal",
            },
            {
                "name_ko": "찌개",
                "name_en": "Jjigae (Stew)",
                "definition_ko": "국보다 걸쭉하고 양념이 진한 국물 요리",
                "definition_en": "Thicker and more heavily seasoned than guk, served bubbling hot",
            },
            {
                "name_ko": "전골",
                "name_en": "Jeongol (Hot Pot)",
                "definition_ko": "여러 재료를 넣고 식탁에서 끓이는 냄비 요리",
                "definition_en": "Elaborate hot pot cooked at the table with various ingredients",
            },
            {
                "name_ko": "해장국",
                "name_en": "Haejangguk (Hangover Soup)",
                "definition_ko": "술 마신 다음날 해장을 위해 먹는 국물 요리 총칭",
                "definition_en": "Category of soups traditionally consumed to cure hangovers",
            },
        ],
    }

    # 2. 밥류
    rice_dishes = {
        "name_ko": "밥류",
        "name_en": "Rice Dishes",
        "definition_ko": "쌀밥을 주식으로 하는 요리 총칭",
        "definition_en": "Dishes centered around cooked rice",
        "parent": None,
        "children": [
            {"name_ko": "비빔밥", "name_en": "Bibimbap (Mixed Rice)"},
            {"name_ko": "덮밥", "name_en": "Deopbap (Rice Bowl)"},
            {"name_ko": "볶음밥", "name_en": "Bokkeumbap (Fried Rice)"},
            {"name_ko": "죽", "name_en": "Juk (Porridge)"},
            {"name_ko": "국밥", "name_en": "Gukbap (Soup with Rice)"},
            {"name_ko": "정식/백반", "name_en": "Jeongsik/Baekban (Set Meal)"},
        ],
    }

    # 3. 면류
    noodles = {
        "name_ko": "면류",
        "name_en": "Noodle Dishes",
        "definition_ko": "면을 주재료로 하는 요리",
        "definition_en": "Dishes featuring noodles as the main ingredient",
        "parent": None,
        "children": [
            {"name_ko": "국수", "name_en": "Guksu (Noodle Soup)"},
            {"name_ko": "냉면", "name_en": "Naengmyeon (Cold Noodles)"},
            {"name_ko": "라면", "name_en": "Ramyeon (Ramen)"},
            {"name_ko": "칼국수", "name_en": "Kalguksu (Knife-cut Noodles)"},
        ],
    }

    # 4. 구이류
    grilled = {
        "name_ko": "구이류",
        "name_en": "Grilled Dishes",
        "definition_ko": "석쇠나 불판에 구워 먹는 요리",
        "definition_en": "Dishes cooked by grilling or broiling",
        "parent": None,
        "children": [
            {"name_ko": "고기구이", "name_en": "Meat Grill (BBQ)"},
            {"name_ko": "생선구이", "name_en": "Grilled Fish"},
        ],
    }

    # 5. 찜/조림류
    braised = {
        "name_ko": "찜/조림류",
        "name_en": "Braised & Steamed",
        "definition_ko": "찌거나 조려서 만드는 요리",
        "definition_en": "Dishes prepared by steaming or simmering",
        "parent": None,
        "children": [
            {"name_ko": "찜", "name_en": "Jjim (Steamed/Braised)"},
            {"name_ko": "조림", "name_en": "Jorim (Simmered)"},
        ],
    }

    # 6. 볶음류
    stirfried = {
        "name_ko": "볶음류",
        "name_en": "Stir-fried Dishes",
        "definition_ko": "센 불에 빠르게 볶아내는 요리",
        "definition_en": "Dishes cooked by stir-frying over high heat",
        "parent": None,
        "children": [
            {"name_ko": "고기볶음", "name_en": "Stir-fried Meat"},
            {"name_ko": "해물볶음", "name_en": "Stir-fried Seafood"},
            {"name_ko": "채소볶음", "name_en": "Stir-fried Vegetables"},
        ],
    }

    # 7. 전/부침류
    pancakes = {
        "name_ko": "전/부침류",
        "name_en": "Pancakes & Fritters",
        "definition_ko": "기름에 지져내는 요리",
        "definition_en": "Pan-fried or deep-fried dishes",
        "parent": None,
        "children": [
            {"name_ko": "전", "name_en": "Jeon (Savory Pancake)"},
            {"name_ko": "부침개", "name_en": "Buchimgae (Fritter)"},
        ],
    }

    # 8. 반찬류
    banchan = {
        "name_ko": "반찬류",
        "name_en": "Side Dishes",
        "definition_ko": "밥과 함께 먹는 곁들이 음식",
        "definition_en": "Side dishes served with rice",
        "parent": None,
        "children": [
            {"name_ko": "나물", "name_en": "Namul (Seasoned Vegetables)"},
            {"name_ko": "김치", "name_en": "Kimchi"},
            {"name_ko": "젓갈", "name_en": "Jeotgal (Fermented Seafood)"},
        ],
    }

    # 9. 분식류
    snacks = {
        "name_ko": "분식류",
        "name_en": "Snack Foods",
        "definition_ko": "간단하고 빠르게 먹을 수 있는 음식",
        "definition_en": "Quick, casual Korean snack foods",
        "parent": None,
        "children": [
            {"name_ko": "떡볶이", "name_en": "Tteokbokki"},
            {"name_ko": "순대", "name_en": "Sundae (Blood Sausage)"},
            {"name_ko": "튀김", "name_en": "Deep-fried Snacks"},
        ],
    }

    # 10. 안주류
    anju = {
        "name_ko": "안주류",
        "name_en": "Drinking Snacks (Anju)",
        "definition_ko": "술과 함께 먹는 음식",
        "definition_en": "Foods traditionally served with alcoholic beverages",
        "parent": None,
        "children": [
            {"name_ko": "육류안주", "name_en": "Meat Anju"},
            {"name_ko": "해산물안주", "name_en": "Seafood Anju"},
        ],
    }

    # 11. 음료류
    beverages = {
        "name_ko": "음료류",
        "name_en": "Beverages",
        "definition_ko": "마시는 음료",
        "definition_en": "Drinks and beverages",
        "parent": None,
        "children": [
            {"name_ko": "술", "name_en": "Alcoholic Beverages"},
            {"name_ko": "비알콜", "name_en": "Non-Alcoholic Beverages"},
        ],
    }

    # 12. 디저트류
    desserts = {
        "name_ko": "디저트류",
        "name_en": "Desserts & Sweets",
        "definition_ko": "한국 전통 디저트와 과자",
        "definition_en": "Traditional Korean desserts and confections",
        "parent": None,
        "children": [
            {"name_ko": "떡/한과", "name_en": "Rice Cake & Traditional Sweets"},
            {"name_ko": "음료디저트", "name_en": "Beverage Desserts"},
        ],
    }

    return [
        soup_stew,
        rice_dishes,
        noodles,
        grilled,
        braised,
        stirfried,
        pancakes,
        banchan,
        snacks,
        anju,
        beverages,
        desserts,
    ]
