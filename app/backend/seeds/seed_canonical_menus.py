"""
Canonical Menu 시드 데이터 (112개)
관광객이 자주 마주치는 한국 음식 중심
Stage 1 확장: 300 메뉴 테스트 실패 케이스 분석하여 기본형 메뉴 추가
"""

from typing import List, Dict, Any


def get_canonical_menu_seeds() -> List[Dict[str, Any]]:
    """Canonical Menu 시드 데이터 반환 (112개)"""

    menus = []

    # ========================================
    # 국물요리 (Soups & Stews) - 25개
    # ========================================

    # 탕 (7개)
    menus.extend(
        [
            {
                "name_ko": "갈비탕",
                "name_en": "Galbitang (Beef Short Rib Soup)",
                "concept": "탕",
                "description_ko": "소갈비를 오래 끓여 깊은 맛을 낸 맑은 국물 요리",
                "description_en": "Clear beef short rib soup simmered for hours",
                "primary_ingredients": ["beef ribs", "radish", "green onion", "garlic"],
                "allergens": ["beef"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "삼계탕",
                "name_en": "Samgyetang (Ginseng Chicken Soup)",
                "concept": "탕",
                "description_ko": "어린 닭에 인삼, 대추, 찹쌀을 넣어 끓인 보양식",
                "description_en": "Whole young chicken stuffed with ginseng, jujube, and glutinous rice",
                "primary_ingredients": [
                    "chicken",
                    "ginseng",
                    "jujube",
                    "glutinous rice",
                    "garlic",
                ],
                "allergens": ["chicken"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "곰탕",
                "name_en": "Gomtang (Beef Bone Soup)",
                "concept": "탕",
                "description_ko": "소뼈와 고기를 장시간 끓여 진하고 구수한 국물을 낸 요리",
                "description_en": "Milky beef bone soup simmered for many hours",
                "primary_ingredients": ["beef bones", "brisket", "green onion"],
                "allergens": ["beef"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "설렁탕",
                "name_en": "Seolleongtang (Ox Bone Soup)",
                "concept": "탕",
                "description_ko": "소뼈를 장시간 끓여 뽀얀 국물을 낸 대표적인 한국 국물 요리",
                "description_en": "Milky ox bone soup, a Korean comfort food staple",
                "primary_ingredients": [
                    "ox bones",
                    "brisket",
                    "green onion",
                    "noodles",
                ],
                "allergens": ["beef", "wheat"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "감자탕",
                "name_en": "Gamjatang (Pork Bone Stew)",
                "concept": "탕",
                "description_ko": "돼지뼈와 감자를 얼큰하게 끓인 국물 요리",
                "description_en": "Spicy pork bone stew with potatoes",
                "primary_ingredients": [
                    "pork spine",
                    "potato",
                    "perilla leaves",
                    "green onion",
                ],
                "allergens": ["pork"],
                "spice_level": 2,
                "difficulty_score": 2,
            },
            {
                "name_ko": "해물탕",
                "name_en": "Haemultang (Spicy Seafood Stew)",
                "concept": "탕",
                "description_ko": "각종 해산물을 얼큰하게 끓인 국물 요리",
                "description_en": "Spicy stew with assorted seafood",
                "primary_ingredients": ["crab", "shrimp", "clams", "squid", "radish"],
                "allergens": ["shellfish", "seafood"],
                "spice_level": 3,
                "difficulty_score": 2,
            },
            {
                "name_ko": "갈비해장국",
                "name_en": "Galbi Haejangguk (Beef Rib Hangover Soup)",
                "concept": "탕",
                "description_ko": "소갈비를 넣고 얼큰하게 끓인 해장국",
                "description_en": "Spicy beef rib soup for hangovers",
                "primary_ingredients": ["beef ribs", "bean sprouts", "green onion"],
                "allergens": ["beef"],
                "spice_level": 2,
                "difficulty_score": 2,
            },
        ]
    )

    # 국 (4개)
    menus.extend(
        [
            {
                "name_ko": "미역국",
                "name_en": "Miyeokguk (Seaweed Soup)",
                "concept": "국",
                "description_ko": "미역을 주재료로 담백하게 끓인 국",
                "description_en": "Light seaweed soup, traditionally served on birthdays",
                "primary_ingredients": ["seaweed", "beef", "garlic", "sesame oil"],
                "allergens": ["beef", "sesame"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "콩나물국",
                "name_en": "Kongnamulguk (Bean Sprout Soup)",
                "concept": "국",
                "description_ko": "콩나물을 넣고 시원하게 끓인 국",
                "description_en": "Refreshing bean sprout soup",
                "primary_ingredients": ["bean sprouts", "anchovy broth", "garlic"],
                "allergens": ["fish"],
                "spice_level": 1,
                "difficulty_score": 1,
            },
            {
                "name_ko": "육개장",
                "name_en": "Yukgaejang (Spicy Beef Soup)",
                "concept": "국",
                "description_ko": "소고기와 고사리, 대파를 넣고 매콤하게 끓인 국",
                "description_en": "Spicy shredded beef soup with vegetables",
                "primary_ingredients": [
                    "beef brisket",
                    "gosari fern",
                    "bean sprouts",
                    "green onion",
                ],
                "allergens": ["beef"],
                "spice_level": 3,
                "difficulty_score": 2,
            },
            {
                "name_ko": "북어국",
                "name_en": "Bugeoguk (Dried Pollack Soup)",
                "concept": "국",
                "description_ko": "북어를 넣고 시원하게 끓인 해장국",
                "description_en": "Dried pollack soup, good for hangovers",
                "primary_ingredients": ["dried pollack", "bean sprouts", "tofu"],
                "allergens": ["fish", "soy"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
        ]
    )

    # 찌개 (8개)
    menus.extend(
        [
            {
                "name_ko": "김치찌개",
                "name_en": "Kimchi Jjigae (Kimchi Stew)",
                "concept": "찌개",
                "description_ko": "김치와 돼지고기를 넣고 얼큰하게 끓인 찌개",
                "description_en": "Spicy stew made with kimchi and pork",
                "primary_ingredients": ["kimchi", "pork", "tofu", "green onion"],
                "allergens": ["pork", "soy"],
                "spice_level": 3,
                "difficulty_score": 1,
            },
            {
                "name_ko": "된장찌개",
                "name_en": "Doenjang Jjigae (Soybean Paste Stew)",
                "concept": "찌개",
                "description_ko": "된장을 풀어 채소와 함께 끓인 한국의 대표 찌개",
                "description_en": "Savory soybean paste stew with vegetables",
                "primary_ingredients": [
                    "soybean paste",
                    "tofu",
                    "zucchini",
                    "potato",
                    "clams",
                ],
                "allergens": ["soy", "shellfish"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "순두부찌개",
                "name_en": "Sundubu Jjigae (Soft Tofu Stew)",
                "concept": "찌개",
                "description_ko": "부드러운 순두부를 주재료로 얼큰하게 끓인 찌개",
                "description_en": "Spicy soft tofu stew often served bubbling hot",
                "primary_ingredients": ["soft tofu", "seafood", "egg", "green onion"],
                "allergens": ["soy", "seafood", "egg"],
                "spice_level": 3,
                "difficulty_score": 1,
            },
            {
                "name_ko": "부대찌개",
                "name_en": "Budae Jjigae (Army Base Stew)",
                "concept": "찌개",
                "description_ko": "햄, 소시지, 라면 등을 넣고 얼큰하게 끓인 퓨전 찌개",
                "description_en": "Spicy fusion stew with ham, sausage, and ramen noodles",
                "primary_ingredients": ["ham", "sausage", "ramen", "kimchi", "cheese"],
                "allergens": ["pork", "wheat", "dairy"],
                "spice_level": 2,
                "difficulty_score": 1,
            },
            {
                "name_ko": "청국장찌개",
                "name_en": "Cheonggukjang Jjigae (Fermented Soybean Stew)",
                "concept": "찌개",
                "description_ko": "청국장을 풀어 구수하게 끓인 찌개, 향이 강함",
                "description_en": "Pungent fermented soybean stew with deep flavor",
                "primary_ingredients": ["fermented soybeans", "pork", "tofu", "kimchi"],
                "allergens": ["soy", "pork"],
                "spice_level": 1,
                "difficulty_score": 4,
            },
            {
                "name_ko": "참치찌개",
                "name_en": "Chamchi Jjigae (Tuna Stew)",
                "concept": "찌개",
                "description_ko": "참치 통조림을 넣고 얼큰하게 끓인 찌개",
                "description_en": "Spicy stew with canned tuna",
                "primary_ingredients": ["canned tuna", "kimchi", "tofu", "green onion"],
                "allergens": ["fish", "soy"],
                "spice_level": 2,
                "difficulty_score": 1,
            },
            {
                "name_ko": "돼지김치찌개",
                "name_en": "Dwaeji Kimchi Jjigae (Pork Kimchi Stew)",
                "concept": "찌개",
                "description_ko": "돼지고기와 김치를 넉넉히 넣고 끓인 찌개",
                "description_en": "Hearty kimchi stew with plenty of pork",
                "primary_ingredients": ["pork belly", "kimchi", "tofu", "green onion"],
                "allergens": ["pork", "soy"],
                "spice_level": 3,
                "difficulty_score": 1,
            },
            {
                "name_ko": "고등어찌개",
                "name_en": "Godeungeo Jjigae (Mackerel Stew)",
                "concept": "찌개",
                "description_ko": "고등어와 무를 넣고 얼큰하게 끓인 생선찌개",
                "description_en": "Spicy mackerel stew with radish",
                "primary_ingredients": [
                    "mackerel",
                    "radish",
                    "green onion",
                    "chili paste",
                ],
                "allergens": ["fish"],
                "spice_level": 2,
                "difficulty_score": 2,
            },
        ]
    )

    # 전골 (3개)
    menus.extend(
        [
            {
                "name_ko": "버섯전골",
                "name_en": "Beoseot Jeongol (Mushroom Hot Pot)",
                "concept": "전골",
                "description_ko": "각종 버섯을 넣고 끓이는 전골",
                "description_en": "Hot pot with assorted mushrooms",
                "primary_ingredients": ["shiitake", "enoki", "oyster mushroom", "tofu"],
                "allergens": ["soy"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
            {
                "name_ko": "해물전골",
                "name_en": "Haemul Jeongol (Seafood Hot Pot)",
                "concept": "전골",
                "description_ko": "각종 해산물을 넣고 끓이는 전골",
                "description_en": "Hot pot with assorted seafood",
                "primary_ingredients": [
                    "shrimp",
                    "clams",
                    "squid",
                    "crab",
                    "vegetables",
                ],
                "allergens": ["shellfish", "seafood"],
                "spice_level": 2,
                "difficulty_score": 2,
            },
            {
                "name_ko": "곱창전골",
                "name_en": "Gopchang Jeongol (Tripe Hot Pot)",
                "concept": "전골",
                "description_ko": "소곱창과 채소를 넣고 끓이는 전골",
                "description_en": "Hot pot with beef tripe and vegetables",
                "primary_ingredients": ["beef tripe", "vegetables", "glass noodles"],
                "allergens": ["beef"],
                "spice_level": 2,
                "difficulty_score": 4,
            },
        ]
    )

    # 해장국 (3개)
    menus.extend(
        [
            {
                "name_ko": "뼈해장국",
                "name_en": "Ppyeo Haejangguk (Pork Bone Hangover Soup)",
                "concept": "해장국",
                "description_ko": "돼지뼈를 우려낸 국물에 우거지를 넣고 얼큰하게 끓인 해장국",
                "description_en": "Spicy pork bone soup with cabbage, good for hangovers",
                "primary_ingredients": ["pork bones", "cabbage", "bean sprouts"],
                "allergens": ["pork"],
                "spice_level": 2,
                "difficulty_score": 2,
            },
            {
                "name_ko": "선지해장국",
                "name_en": "Seonji Haejangguk (Blood Sausage Hangover Soup)",
                "concept": "해장국",
                "description_ko": "선지와 우거지를 넣고 끓인 해장국",
                "description_en": "Hangover soup with ox blood and vegetables",
                "primary_ingredients": ["ox blood", "cabbage", "bean sprouts"],
                "allergens": ["beef"],
                "spice_level": 2,
                "difficulty_score": 4,
            },
            {
                "name_ko": "콩나물해장국",
                "name_en": "Kongnamul Haejangguk (Bean Sprout Hangover Soup)",
                "concept": "해장국",
                "description_ko": "콩나물을 넣고 시원하게 끓인 해장국",
                "description_en": "Refreshing bean sprout hangover soup",
                "primary_ingredients": ["bean sprouts", "green onion", "garlic"],
                "allergens": [],
                "spice_level": 1,
                "difficulty_score": 1,
            },
        ]
    )

    # ========================================
    # 밥류 (Rice Dishes) - 15개
    # ========================================

    # 비빔밥 (3개)
    menus.extend(
        [
            {
                "name_ko": "돌솥비빔밥",
                "name_en": "Dolsot Bibimbap (Stone Pot Mixed Rice)",
                "concept": "비빔밥",
                "description_ko": "뜨거운 돌솥에 밥과 나물, 고추장을 넣고 비벼 먹는 요리",
                "description_en": "Rice, vegetables, and egg mixed in a sizzling stone pot",
                "primary_ingredients": [
                    "rice",
                    "vegetables",
                    "egg",
                    "gochujang",
                    "sesame oil",
                ],
                "allergens": ["egg", "sesame", "soy"],
                "spice_level": 2,
                "difficulty_score": 1,
            },
            {
                "name_ko": "전주비빔밥",
                "name_en": "Jeonju Bibimbap (Jeonju-style Mixed Rice)",
                "concept": "비빔밥",
                "description_ko": "전주 지역 특산 비빔밥으로 나물과 육회를 올린 고급 비빔밥",
                "description_en": "Premium bibimbap from Jeonju with raw beef",
                "primary_ingredients": ["rice", "vegetables", "raw beef", "egg yolk"],
                "allergens": ["beef", "egg"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
            {
                "name_ko": "산채비빔밥",
                "name_en": "Sanchae Bibimbap (Wild Vegetable Bibimbap)",
                "concept": "비빔밥",
                "description_ko": "산나물을 넣은 비빔밥",
                "description_en": "Bibimbap with wild mountain vegetables",
                "primary_ingredients": ["rice", "wild vegetables", "gochujang"],
                "allergens": ["soy"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
        ]
    )

    # 덮밥 (3개)
    menus.extend(
        [
            {
                "name_ko": "제육덮밥",
                "name_en": "Jeyuk Deopbap (Spicy Pork Rice Bowl)",
                "concept": "덮밥",
                "description_ko": "매콤하게 볶은 돼지고기를 밥 위에 얹은 덮밥",
                "description_en": "Rice bowl topped with spicy stir-fried pork",
                "primary_ingredients": ["pork", "rice", "vegetables", "gochujang"],
                "allergens": ["pork", "soy"],
                "spice_level": 3,
                "difficulty_score": 1,
            },
            {
                "name_ko": "불고기덮밥",
                "name_en": "Bulgogi Deopbap (Bulgogi Rice Bowl)",
                "concept": "덮밥",
                "description_ko": "달콤하게 양념한 불고기를 밥 위에 얹은 덮밥",
                "description_en": "Rice bowl topped with sweet marinated beef",
                "primary_ingredients": ["beef", "rice", "onion", "soy sauce"],
                "allergens": ["beef", "soy"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "회덮밥",
                "name_en": "Hoe Deopbap (Raw Fish Rice Bowl)",
                "concept": "덮밥",
                "description_ko": "회와 채소를 밥 위에 얹고 초고추장에 비벼 먹는 덮밥",
                "description_en": "Rice bowl with raw fish and vegetables in spicy sauce",
                "primary_ingredients": ["raw fish", "rice", "vegetables", "gochujang"],
                "allergens": ["fish", "soy"],
                "spice_level": 2,
                "difficulty_score": 2,
            },
        ]
    )

    # 볶음밥 (3개)
    menus.extend(
        [
            {
                "name_ko": "김치볶음밥",
                "name_en": "Kimchi Bokkeumbap (Kimchi Fried Rice)",
                "concept": "볶음밥",
                "description_ko": "김치와 밥을 볶아 만든 한국식 볶음밥",
                "description_en": "Fried rice with kimchi",
                "primary_ingredients": ["rice", "kimchi", "pork", "egg"],
                "allergens": ["pork", "egg"],
                "spice_level": 2,
                "difficulty_score": 1,
            },
            {
                "name_ko": "새우볶음밥",
                "name_en": "Saeu Bokkeumbap (Shrimp Fried Rice)",
                "concept": "볶음밥",
                "description_ko": "새우와 채소를 넣고 볶은 볶음밥",
                "description_en": "Fried rice with shrimp and vegetables",
                "primary_ingredients": ["rice", "shrimp", "vegetables", "egg"],
                "allergens": ["shellfish", "egg"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "오므라이스",
                "name_en": "Omurice (Omelette Rice)",
                "concept": "볶음밥",
                "description_ko": "볶음밥을 얇은 계란지단으로 감싼 요리",
                "description_en": "Fried rice wrapped in a thin egg omelette",
                "primary_ingredients": ["rice", "egg", "ketchup", "vegetables"],
                "allergens": ["egg"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
        ]
    )

    # 죽 (2개)
    menus.extend(
        [
            {
                "name_ko": "전복죽",
                "name_en": "Jeonbok Juk (Abalone Porridge)",
                "concept": "죽",
                "description_ko": "전복을 넣고 끓인 고급 죽",
                "description_en": "Porridge with abalone, a luxury dish",
                "primary_ingredients": ["abalone", "rice", "sesame oil"],
                "allergens": ["shellfish", "sesame"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "팥죽",
                "name_en": "Patjuk (Red Bean Porridge)",
                "concept": "죽",
                "description_ko": "팥을 넣고 끓인 달콤한 죽",
                "description_en": "Sweet red bean porridge, often eaten in winter",
                "primary_ingredients": ["red beans", "rice", "sugar"],
                "allergens": [],
                "spice_level": 0,
                "difficulty_score": 1,
            },
        ]
    )

    # 국밥 (3개)
    menus.extend(
        [
            {
                "name_ko": "돼지국밥",
                "name_en": "Dwaeji Gukbap (Pork Soup with Rice)",
                "concept": "국밥",
                "description_ko": "돼지고기를 넣고 끓인 국에 밥을 말아 먹는 요리",
                "description_en": "Pork soup served with rice, a Busan specialty",
                "primary_ingredients": ["pork", "rice", "green onion"],
                "allergens": ["pork"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
            {
                "name_ko": "순대국밥",
                "name_en": "Sundae Gukbap (Blood Sausage Soup with Rice)",
                "concept": "국밥",
                "description_ko": "순대와 내장을 넣고 끓인 국에 밥을 말아 먹는 요리",
                "description_en": "Soup with blood sausage and offal, served with rice",
                "primary_ingredients": ["blood sausage", "offal", "rice"],
                "allergens": ["pork"],
                "spice_level": 1,
                "difficulty_score": 3,
            },
            {
                "name_ko": "해장국밥",
                "name_en": "Haejangguk Bap (Hangover Soup with Rice)",
                "concept": "국밥",
                "description_ko": "해장국에 밥을 말아 먹는 요리",
                "description_en": "Hangover soup served with rice",
                "primary_ingredients": ["pork bones", "cabbage", "rice"],
                "allergens": ["pork"],
                "spice_level": 2,
                "difficulty_score": 2,
            },
        ]
    )

    # 정식/백반 (1개)
    menus.extend(
        [
            {
                "name_ko": "한정식",
                "name_en": "Hanjeongsik (Korean Table d'hôte)",
                "concept": "정식/백반",
                "description_ko": "다양한 반찬과 메인 요리가 함께 나오는 한국 정찬",
                "description_en": "Full-course Korean meal with many side dishes",
                "primary_ingredients": [
                    "rice",
                    "soup",
                    "grilled fish",
                    "vegetables",
                    "kimchi",
                ],
                "allergens": ["fish", "soy", "sesame"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
        ]
    )

    # ========================================
    # 면류 (Noodle Dishes) - 12개
    # ========================================

    # 국수 (3개)
    menus.extend(
        [
            {
                "name_ko": "잔치국수",
                "name_en": "Janchi Guksu (Banquet Noodles)",
                "concept": "국수",
                "description_ko": "멸치 육수에 소면을 말아 먹는 국수",
                "description_en": "Thin wheat noodles in anchovy broth",
                "primary_ingredients": [
                    "wheat noodles",
                    "anchovy broth",
                    "zucchini",
                    "egg",
                ],
                "allergens": ["wheat", "fish", "egg"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "비빔국수",
                "name_en": "Bibim Guksu (Spicy Mixed Noodles)",
                "concept": "국수",
                "description_ko": "소면에 고추장 양념을 넣고 비벼 먹는 국수",
                "description_en": "Spicy mixed wheat noodles",
                "primary_ingredients": [
                    "wheat noodles",
                    "gochujang",
                    "vegetables",
                    "egg",
                ],
                "allergens": ["wheat", "egg", "soy"],
                "spice_level": 3,
                "difficulty_score": 1,
            },
            {
                "name_ko": "콩국수",
                "name_en": "Kongguksu (Cold Soy Milk Noodles)",
                "concept": "국수",
                "description_ko": "차가운 콩국물에 소면을 말아 먹는 여름 국수",
                "description_en": "Cold noodles in creamy soy milk broth, a summer dish",
                "primary_ingredients": ["wheat noodles", "soy milk", "cucumber"],
                "allergens": ["wheat", "soy"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
        ]
    )

    # 냉면 (3개)
    menus.extend(
        [
            {
                "name_ko": "물냉면",
                "name_en": "Mul Naengmyeon (Cold Noodles in Broth)",
                "concept": "냉면",
                "description_ko": "차가운 육수에 메밀면을 말아 먹는 냉면",
                "description_en": "Buckwheat noodles in cold broth",
                "primary_ingredients": [
                    "buckwheat noodles",
                    "beef broth",
                    "radish",
                    "cucumber",
                    "egg",
                ],
                "allergens": ["wheat", "buckwheat", "beef", "egg"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "비빔냉면",
                "name_en": "Bibim Naengmyeon (Spicy Cold Noodles)",
                "concept": "냉면",
                "description_ko": "메밀면에 고추장 양념을 넣고 비벼 먹는 냉면",
                "description_en": "Buckwheat noodles in spicy sauce",
                "primary_ingredients": [
                    "buckwheat noodles",
                    "gochujang",
                    "vegetables",
                    "egg",
                ],
                "allergens": ["wheat", "buckwheat", "egg", "soy"],
                "spice_level": 3,
                "difficulty_score": 2,
            },
            {
                "name_ko": "막국수",
                "name_en": "Makguksu (Buckwheat Noodles)",
                "concept": "냉면",
                "description_ko": "메밀면에 동치미 국물을 넣고 비벼 먹는 강원도 향토 음식",
                "description_en": "Buckwheat noodles with radish water kimchi, a Gangwon-do specialty",
                "primary_ingredients": [
                    "buckwheat noodles",
                    "radish kimchi",
                    "vegetables",
                ],
                "allergens": ["buckwheat"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
        ]
    )

    # 라면 (2개)
    menus.extend(
        [
            {
                "name_ko": "라면",
                "name_en": "Ramyeon (Ramen)",
                "concept": "라면",
                "description_ko": "한국식 인스턴트 라면",
                "description_en": "Korean-style instant ramen noodles",
                "primary_ingredients": ["ramen noodles", "soup powder", "green onion"],
                "allergens": ["wheat"],
                "spice_level": 2,
                "difficulty_score": 1,
            },
            {
                "name_ko": "치즈라면",
                "name_en": "Cheese Ramyeon (Cheese Ramen)",
                "concept": "라면",
                "description_ko": "라면에 치즈를 얹은 요리",
                "description_en": "Ramen topped with cheese",
                "primary_ingredients": ["ramen noodles", "cheese", "soup powder"],
                "allergens": ["wheat", "dairy"],
                "spice_level": 2,
                "difficulty_score": 1,
            },
        ]
    )

    # 칼국수 (4개)
    menus.extend(
        [
            {
                "name_ko": "바지락칼국수",
                "name_en": "Bajirak Kalguksu (Clam Noodle Soup)",
                "concept": "칼국수",
                "description_ko": "바지락을 넣고 끓인 칼국수",
                "description_en": "Hand-cut noodles in clam broth",
                "primary_ingredients": ["wheat noodles", "clams", "zucchini"],
                "allergens": ["wheat", "shellfish"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "닭칼국수",
                "name_en": "Dak Kalguksu (Chicken Noodle Soup)",
                "concept": "칼국수",
                "description_ko": "닭 육수에 칼국수를 넣고 끓인 요리",
                "description_en": "Hand-cut noodles in chicken broth",
                "primary_ingredients": ["wheat noodles", "chicken", "potato"],
                "allergens": ["wheat", "chicken"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "해물칼국수",
                "name_en": "Haemul Kalguksu (Seafood Noodle Soup)",
                "concept": "칼국수",
                "description_ko": "해물을 넣고 끓인 칼국수",
                "description_en": "Hand-cut noodles with seafood",
                "primary_ingredients": ["wheat noodles", "seafood", "zucchini"],
                "allergens": ["wheat", "seafood", "shellfish"],
                "spice_level": 1,
                "difficulty_score": 1,
            },
            {
                "name_ko": "얼큰칼국수",
                "name_en": "Eolkeun Kalguksu (Spicy Noodle Soup)",
                "concept": "칼국수",
                "description_ko": "고춧가루를 넣고 얼큰하게 끓인 칼국수",
                "description_en": "Spicy hand-cut noodle soup",
                "primary_ingredients": ["wheat noodles", "gochugaru", "vegetables"],
                "allergens": ["wheat"],
                "spice_level": 3,
                "difficulty_score": 1,
            },
        ]
    )

    # ========================================
    # 구이류 (Grilled Dishes) - 15개
    # ========================================

    # 고기구이 (10개)
    menus.extend(
        [
            {
                "name_ko": "삼겹살",
                "name_en": "Samgyeopsal (Pork Belly)",
                "concept": "고기구이",
                "description_ko": "돼지 삼겹살을 구워 먹는 한국의 대표 고기",
                "description_en": "Grilled pork belly, Korea's most popular BBQ",
                "primary_ingredients": ["pork belly"],
                "allergens": ["pork"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "목살",
                "name_en": "Moksal (Pork Neck)",
                "concept": "고기구이",
                "description_ko": "돼지 목살을 구워 먹는 고기",
                "description_en": "Grilled pork neck/shoulder",
                "primary_ingredients": ["pork neck"],
                "allergens": ["pork"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "갈비",
                "name_en": "Galbi (Marinated Beef Ribs)",
                "concept": "고기구이",
                "description_ko": "간장 양념에 재운 소갈비를 구워 먹는 고기",
                "description_en": "Marinated beef short ribs, grilled",
                "primary_ingredients": ["beef ribs", "soy sauce", "sugar", "garlic"],
                "allergens": ["beef", "soy"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "불고기",
                "name_en": "Bulgogi (Marinated Beef)",
                "concept": "고기구이",
                "description_ko": "달콤한 간장 양념에 재운 소고기를 구워 먹는 요리",
                "description_en": "Sweet marinated beef, a Korean classic",
                "primary_ingredients": ["beef", "soy sauce", "sugar", "sesame oil"],
                "allergens": ["beef", "soy", "sesame"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "LA갈비",
                "name_en": "LA Galbi (LA-style Beef Ribs)",
                "concept": "고기구이",
                "description_ko": "미국식으로 가로로 썬 갈비를 양념해 구운 고기",
                "description_en": "LA-style cross-cut beef ribs, marinated and grilled",
                "primary_ingredients": ["beef ribs", "soy sauce", "sugar"],
                "allergens": ["beef", "soy"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "항정살",
                "name_en": "Hangjeongsal (Pork Jowl)",
                "concept": "고기구이",
                "description_ko": "돼지 목 뒷부분의 고기를 구워 먹는 요리",
                "description_en": "Grilled pork jowl, a tender cut",
                "primary_ingredients": ["pork jowl"],
                "allergens": ["pork"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "대패삼겹살",
                "name_en": "Daepae Samgyeopsal (Thin Pork Belly)",
                "concept": "고기구이",
                "description_ko": "얇게 썬 삼겹살을 구워 먹는 요리",
                "description_en": "Thinly sliced pork belly, grilled quickly",
                "primary_ingredients": ["thin pork belly"],
                "allergens": ["pork"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "소갈비",
                "name_en": "So Galbi (Beef Ribs)",
                "concept": "고기구이",
                "description_ko": "소갈비를 구워 먹는 고급 고기",
                "description_en": "Grilled beef ribs, a premium cut",
                "primary_ingredients": ["beef ribs"],
                "allergens": ["beef"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "양념갈비",
                "name_en": "Yangnyeom Galbi (Marinated Pork Ribs)",
                "concept": "고기구이",
                "description_ko": "매콤달콤한 양념에 재운 돼지갈비",
                "description_en": "Spicy-sweet marinated pork ribs",
                "primary_ingredients": ["pork ribs", "gochujang", "sugar"],
                "allergens": ["pork", "soy"],
                "spice_level": 2,
                "difficulty_score": 1,
            },
            {
                "name_ko": "왕갈비",
                "name_en": "Wang Galbi (King-Size Ribs)",
                "concept": "고기구이",
                "description_ko": "크게 썬 소갈비를 구워 먹는 고기",
                "description_en": "King-size beef ribs",
                "primary_ingredients": ["large beef ribs", "soy sauce"],
                "allergens": ["beef", "soy"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
        ]
    )

    # 생선구이 (5개)
    menus.extend(
        [
            {
                "name_ko": "고등어구이",
                "name_en": "Godeungeo Gui (Grilled Mackerel)",
                "concept": "생선구이",
                "description_ko": "소금에 간한 고등어를 구운 요리",
                "description_en": "Salt-grilled mackerel",
                "primary_ingredients": ["mackerel", "salt"],
                "allergens": ["fish"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "갈치구이",
                "name_en": "Galchi Gui (Grilled Cutlassfish)",
                "concept": "생선구이",
                "description_ko": "갈치를 구워 먹는 요리",
                "description_en": "Grilled cutlassfish (hairtail)",
                "primary_ingredients": ["cutlassfish", "salt"],
                "allergens": ["fish"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "삼치구이",
                "name_en": "Samchi Gui (Grilled Spanish Mackerel)",
                "concept": "생선구이",
                "description_ko": "삼치를 구워 먹는 요리",
                "description_en": "Grilled Spanish mackerel",
                "primary_ingredients": ["Spanish mackerel", "salt"],
                "allergens": ["fish"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "조기구이",
                "name_en": "Jogi Gui (Grilled Yellow Croaker)",
                "concept": "생선구이",
                "description_ko": "조기를 구워 먹는 요리",
                "description_en": "Grilled yellow croaker",
                "primary_ingredients": ["yellow croaker", "salt"],
                "allergens": ["fish"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "가자미구이",
                "name_en": "Gajami Gui (Grilled Flounder)",
                "concept": "생선구이",
                "description_ko": "가자미를 구워 먹는 요리",
                "description_en": "Grilled flounder",
                "primary_ingredients": ["flounder", "salt"],
                "allergens": ["fish"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
        ]
    )

    # ========================================
    # 찜/조림류 (Braised & Steamed) - 8개
    # ========================================

    # 찜 (5개)
    menus.extend(
        [
            {
                "name_ko": "갈비찜",
                "name_en": "Galbijjim (Braised Beef Ribs)",
                "concept": "찜",
                "description_ko": "소갈비를 달콤하게 양념해 푹 익힌 요리",
                "description_en": "Sweet braised beef short ribs with vegetables",
                "primary_ingredients": [
                    "beef ribs",
                    "soy sauce",
                    "sugar",
                    "carrots",
                    "jujube",
                ],
                "allergens": ["beef", "soy"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "아구찜",
                "name_en": "Agujjim (Spicy Braised Monkfish)",
                "concept": "찜",
                "description_ko": "아귀를 콩나물과 함께 매콤하게 찐 요리",
                "description_en": "Spicy braised monkfish with bean sprouts",
                "primary_ingredients": ["monkfish", "bean sprouts", "gochugaru"],
                "allergens": ["fish"],
                "spice_level": 4,
                "difficulty_score": 3,
            },
            {
                "name_ko": "닭찜",
                "name_en": "Dakjjim (Braised Chicken)",
                "concept": "찜",
                "description_ko": "닭을 감자, 당근과 함께 간장 양념으로 찐 요리",
                "description_en": "Braised chicken with potatoes and carrots",
                "primary_ingredients": ["chicken", "potato", "carrot", "soy sauce"],
                "allergens": ["chicken", "soy"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
            {
                "name_ko": "돼지갈비찜",
                "name_en": "Dwaeji Galbijjim (Braised Pork Ribs)",
                "concept": "찜",
                "description_ko": "돼지갈비를 매콤달콤하게 양념해 찐 요리",
                "description_en": "Spicy-sweet braised pork ribs",
                "primary_ingredients": [
                    "pork ribs",
                    "gochujang",
                    "soy sauce",
                    "potato",
                ],
                "allergens": ["pork", "soy"],
                "spice_level": 2,
                "difficulty_score": 2,
            },
            {
                "name_ko": "해물찜",
                "name_en": "Haemul Jjim (Steamed Seafood)",
                "concept": "찜",
                "description_ko": "각종 해산물을 매콤하게 찐 요리",
                "description_en": "Spicy steamed seafood platter",
                "primary_ingredients": [
                    "crab",
                    "shrimp",
                    "squid",
                    "clams",
                    "glass noodles",
                ],
                "allergens": ["shellfish", "seafood"],
                "spice_level": 3,
                "difficulty_score": 2,
            },
        ]
    )

    # 조림 (3개)
    menus.extend(
        [
            {
                "name_ko": "고등어조림",
                "name_en": "Godeungeo Jorim (Braised Mackerel)",
                "concept": "조림",
                "description_ko": "고등어를 무와 함께 간장 양념으로 조린 요리",
                "description_en": "Mackerel braised with radish in soy sauce",
                "primary_ingredients": ["mackerel", "radish", "soy sauce", "gochugaru"],
                "allergens": ["fish", "soy"],
                "spice_level": 2,
                "difficulty_score": 2,
            },
            {
                "name_ko": "갈치조림",
                "name_en": "Galchi Jorim (Braised Cutlassfish)",
                "concept": "조림",
                "description_ko": "갈치를 무와 함께 매콤하게 조린 요리",
                "description_en": "Spicy braised cutlassfish with radish",
                "primary_ingredients": ["cutlassfish", "radish", "gochugaru"],
                "allergens": ["fish"],
                "spice_level": 2,
                "difficulty_score": 2,
            },
            {
                "name_ko": "두부조림",
                "name_en": "Dubu Jorim (Braised Tofu)",
                "concept": "조림",
                "description_ko": "두부를 간장 양념으로 조린 반찬",
                "description_en": "Tofu braised in soy sauce",
                "primary_ingredients": ["tofu", "soy sauce", "green onion"],
                "allergens": ["soy"],
                "spice_level": 1,
                "difficulty_score": 1,
            },
        ]
    )

    # ========================================
    # 볶음류 (Stir-fried Dishes) - 8개
    # ========================================

    # 고기볶음 (3개)
    menus.extend(
        [
            {
                "name_ko": "제육볶음",
                "name_en": "Jeyuk Bokkeum (Spicy Stir-fried Pork)",
                "concept": "고기볶음",
                "description_ko": "돼지고기를 고추장 양념에 매콤하게 볶은 요리",
                "description_en": "Spicy stir-fried pork with vegetables",
                "primary_ingredients": ["pork", "gochujang", "onion", "cabbage"],
                "allergens": ["pork", "soy"],
                "spice_level": 3,
                "difficulty_score": 1,
            },
            {
                "name_ko": "불고기",
                "name_en": "Bulgogi (Marinated Beef)",
                "concept": "고기볶음",
                "description_ko": "달콤한 간장 양념에 재운 소고기를 볶은 요리",
                "description_en": "Sweet marinated beef stir-fry",
                "primary_ingredients": ["beef", "soy sauce", "sugar", "onion"],
                "allergens": ["beef", "soy"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "돼지불고기",
                "name_en": "Dwaeji Bulgogi (Spicy Pork Bulgogi)",
                "concept": "고기볶음",
                "description_ko": "돼지고기를 양념해 볶은 요리",
                "description_en": "Spicy marinated pork stir-fry",
                "primary_ingredients": ["pork", "gochujang", "onion"],
                "allergens": ["pork", "soy"],
                "spice_level": 2,
                "difficulty_score": 1,
            },
        ]
    )

    # 해물볶음 (3개)
    menus.extend(
        [
            {
                "name_ko": "오징어볶음",
                "name_en": "Ojingeo Bokkeum (Spicy Stir-fried Squid)",
                "concept": "해물볶음",
                "description_ko": "오징어를 고추장 양념에 매콤하게 볶은 요리",
                "description_en": "Spicy stir-fried squid with vegetables",
                "primary_ingredients": ["squid", "gochujang", "vegetables"],
                "allergens": ["seafood", "soy"],
                "spice_level": 3,
                "difficulty_score": 2,
            },
            {
                "name_ko": "낙지볶음",
                "name_en": "Nakji Bokkeum (Spicy Stir-fried Octopus)",
                "concept": "해물볶음",
                "description_ko": "낙지를 고추장 양념에 매콤하게 볶은 요리",
                "description_en": "Spicy stir-fried octopus",
                "primary_ingredients": ["octopus", "gochujang", "vegetables"],
                "allergens": ["seafood", "soy"],
                "spice_level": 4,
                "difficulty_score": 3,
            },
            {
                "name_ko": "쭈꾸미볶음",
                "name_en": "Jjukkumi Bokkeum (Spicy Stir-fried Baby Octopus)",
                "concept": "해물볶음",
                "description_ko": "쭈꾸미를 고추장 양념에 매콤하게 볶은 요리",
                "description_en": "Spicy stir-fried baby octopus",
                "primary_ingredients": ["baby octopus", "gochujang", "vegetables"],
                "allergens": ["seafood", "soy"],
                "spice_level": 4,
                "difficulty_score": 3,
            },
        ]
    )

    # 채소볶음 (2개)
    menus.extend(
        [
            {
                "name_ko": "잡채",
                "name_en": "Japchae (Stir-fried Glass Noodles)",
                "concept": "채소볶음",
                "description_ko": "당면과 채소를 간장 양념으로 볶은 요리",
                "description_en": "Stir-fried glass noodles with vegetables",
                "primary_ingredients": [
                    "glass noodles",
                    "vegetables",
                    "soy sauce",
                    "sesame oil",
                ],
                "allergens": ["soy", "sesame"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "버섯볶음",
                "name_en": "Beoseot Bokkeum (Stir-fried Mushrooms)",
                "concept": "채소볶음",
                "description_ko": "각종 버섯을 볶은 요리",
                "description_en": "Stir-fried assorted mushrooms",
                "primary_ingredients": [
                    "shiitake",
                    "oyster mushroom",
                    "enoki",
                    "soy sauce",
                ],
                "allergens": ["soy"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
        ]
    )

    # ========================================
    # 전/부침류 (Pancakes & Fritters) - 6개
    # ========================================

    # 전 (4개)
    menus.extend(
        [
            {
                "name_ko": "김치전",
                "name_en": "Kimchi Jeon (Kimchi Pancake)",
                "concept": "전",
                "description_ko": "김치를 넣고 부친 전",
                "description_en": "Savory pancake with kimchi",
                "primary_ingredients": ["kimchi", "flour", "egg"],
                "allergens": ["wheat", "egg"],
                "spice_level": 2,
                "difficulty_score": 1,
            },
            {
                "name_ko": "파전",
                "name_en": "Pajeon (Green Onion Pancake)",
                "concept": "전",
                "description_ko": "파를 넣고 부친 전",
                "description_en": "Savory pancake with green onions",
                "primary_ingredients": ["green onion", "flour", "egg"],
                "allergens": ["wheat", "egg"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "해물파전",
                "name_en": "Haemul Pajeon (Seafood Green Onion Pancake)",
                "concept": "전",
                "description_ko": "해산물과 파를 넣고 부친 전",
                "description_en": "Savory pancake with seafood and green onions",
                "primary_ingredients": ["seafood", "green onion", "flour", "egg"],
                "allergens": ["wheat", "egg", "seafood", "shellfish"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "동그랑땡",
                "name_en": "Donggeurangtaeng (Pan-fried Meat Patty)",
                "concept": "전",
                "description_ko": "다진 고기를 동그랗게 빚어 부친 전",
                "description_en": "Pan-fried round meat patties",
                "primary_ingredients": ["ground beef", "tofu", "egg"],
                "allergens": ["beef", "egg", "soy"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
        ]
    )

    # 부침개 (2개)
    menus.extend(
        [
            {
                "name_ko": "호떡",
                "name_en": "Hotteok (Sweet Pancake)",
                "concept": "부침개",
                "description_ko": "흑설탕과 견과류를 넣고 부친 달콤한 부침개",
                "description_en": "Sweet pancake filled with brown sugar and nuts",
                "primary_ingredients": ["flour", "brown sugar", "peanuts", "cinnamon"],
                "allergens": ["wheat", "peanuts"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "빈대떡",
                "name_en": "Bindaetteok (Mung Bean Pancake)",
                "concept": "부침개",
                "description_ko": "녹두를 갈아 부친 부침개",
                "description_en": "Savory mung bean pancake",
                "primary_ingredients": ["mung beans", "pork", "kimchi", "vegetables"],
                "allergens": ["pork"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
        ]
    )

    # ========================================
    # 반찬류 (Side Dishes) - 3개
    # ========================================

    menus.extend(
        [
            {
                "name_ko": "나물반찬",
                "name_en": "Namul Banchan (Seasoned Vegetable Side Dishes)",
                "concept": "나물",
                "description_ko": "채소를 데쳐 양념한 반찬",
                "description_en": "Seasoned blanched vegetables",
                "primary_ingredients": ["spinach", "bean sprouts", "sesame oil"],
                "allergens": ["sesame"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "배추김치",
                "name_en": "Baechu Kimchi (Napa Cabbage Kimchi)",
                "concept": "김치",
                "description_ko": "배추를 소금에 절여 양념에 버무린 김치",
                "description_en": "Fermented napa cabbage, Korea's national dish",
                "primary_ingredients": [
                    "napa cabbage",
                    "gochugaru",
                    "garlic",
                    "fish sauce",
                ],
                "allergens": ["fish"],
                "spice_level": 2,
                "difficulty_score": 3,
            },
            {
                "name_ko": "명란젓",
                "name_en": "Myeongnanjeot (Spicy Cod Roe)",
                "concept": "젓갈",
                "description_ko": "명란을 소금에 절여 양념한 젓갈",
                "description_en": "Salted and seasoned cod roe",
                "primary_ingredients": ["cod roe", "gochugaru", "salt"],
                "allergens": ["fish"],
                "spice_level": 2,
                "difficulty_score": 3,
            },
        ]
    )

    # ========================================
    # 분식류 (Snack Foods) - 5개
    # ========================================

    menus.extend(
        [
            {
                "name_ko": "떡볶이",
                "name_en": "Tteokbokki (Spicy Rice Cakes)",
                "concept": "떡볶이",
                "description_ko": "가래떡을 고추장 양념에 매콤하게 볶은 분식",
                "description_en": "Spicy stir-fried rice cakes, a popular street food",
                "primary_ingredients": [
                    "rice cakes",
                    "gochujang",
                    "fish cakes",
                    "green onion",
                ],
                "allergens": ["fish", "soy"],
                "spice_level": 3,
                "difficulty_score": 1,
            },
            {
                "name_ko": "치즈떡볶이",
                "name_en": "Cheese Tteokbokki (Cheese Spicy Rice Cakes)",
                "concept": "떡볶이",
                "description_ko": "떡볶이 위에 치즈를 얹은 요리",
                "description_en": "Spicy rice cakes topped with melted cheese",
                "primary_ingredients": ["rice cakes", "gochujang", "cheese"],
                "allergens": ["fish", "soy", "dairy"],
                "spice_level": 3,
                "difficulty_score": 1,
            },
            {
                "name_ko": "순대",
                "name_en": "Sundae (Korean Blood Sausage)",
                "concept": "순대",
                "description_ko": "돼지 창자에 당면과 선지를 넣어 만든 순대",
                "description_en": "Korean blood sausage stuffed with glass noodles",
                "primary_ingredients": ["pork intestine", "glass noodles", "blood"],
                "allergens": ["pork"],
                "spice_level": 0,
                "difficulty_score": 3,
            },
            {
                "name_ko": "오징어튀김",
                "name_en": "Ojingeo Twigim (Fried Squid)",
                "concept": "튀김",
                "description_ko": "오징어에 튀김옷을 입혀 튀긴 요리",
                "description_en": "Battered and deep-fried squid",
                "primary_ingredients": ["squid", "flour", "batter"],
                "allergens": ["seafood", "wheat"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "만두",
                "name_en": "Mandu (Dumplings)",
                "concept": "튀김",
                "description_ko": "고기와 채소를 넣고 빚은 만두",
                "description_en": "Korean dumplings filled with meat and vegetables",
                "primary_ingredients": [
                    "dumpling wrapper",
                    "pork",
                    "vegetables",
                    "tofu",
                ],
                "allergens": ["wheat", "pork", "soy"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
        ]
    )

    # ========================================
    # 안주류 (Drinking Snacks) - 2개
    # ========================================

    menus.extend(
        [
            {
                "name_ko": "족발",
                "name_en": "Jokbal (Braised Pig's Trotters)",
                "concept": "육류안주",
                "description_ko": "돼지 족발을 삶아 먹는 술안주",
                "description_en": "Braised pig's trotters, a popular drinking snack",
                "primary_ingredients": ["pig's trotters", "soy sauce", "garlic"],
                "allergens": ["pork", "soy"],
                "spice_level": 0,
                "difficulty_score": 3,
            },
            {
                "name_ko": "오징어회",
                "name_en": "Ojingeo Hoe (Raw Squid)",
                "concept": "해물안주",
                "description_ko": "신선한 오징어를 얇게 썰어 먹는 회",
                "description_en": "Fresh raw squid slices",
                "primary_ingredients": ["raw squid"],
                "allergens": ["seafood"],
                "spice_level": 0,
                "difficulty_score": 3,
            },
        ]
    )

    # ========================================
    # 디저트류 (Desserts & Sweets) - 1개
    # ========================================

    menus.extend(
        [
            {
                "name_ko": "떡",
                "name_en": "Tteok (Rice Cake)",
                "concept": "떡/한과",
                "description_ko": "쌀가루를 쪄서 만든 한국 전통 떡",
                "description_en": "Traditional Korean rice cakes",
                "primary_ingredients": ["rice flour", "sugar"],
                "allergens": [],
                "spice_level": 0,
                "difficulty_score": 2,
            },
        ]
    )

    # ========================================
    # 추가 메뉴 (AI Discovery 분석 결과 - Stage 1)
    # 300 메뉴 테스트에서 누락된 기본형 메뉴 추가
    # ========================================
    menus.extend(
        [
            {
                "name_ko": "비빔밥",
                "name_en": "Bibimbap (Mixed Rice with Vegetables)",
                "concept": "비빔밥",
                "description_ko": "밥에 여러 가지 나물과 고기를 얹어 비벼 먹는 요리",
                "description_en": "Mixed rice with assorted vegetables and meat",
                "primary_ingredients": [
                    "rice",
                    "vegetables",
                    "beef",
                    "egg",
                    "gochujang",
                ],
                "allergens": ["egg", "beef", "soy", "sesame"],
                "spice_level": 2,
                "difficulty_score": 2,
            },
            {
                "name_ko": "냉면",
                "name_en": "Naengmyeon (Cold Noodles)",
                "concept": "냉면",
                "description_ko": "차가운 육수에 메밀면을 말아 먹는 여름 별미",
                "description_en": "Cold buckwheat noodles in chilled broth",
                "primary_ingredients": [
                    "buckwheat noodles",
                    "beef broth",
                    "cucumber",
                    "pear",
                    "egg",
                ],
                "allergens": ["egg", "beef", "buckwheat"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "칼국수",
                "name_en": "Kalguksu (Hand-cut Noodle Soup)",
                "concept": "칼국수",
                "description_ko": "칼로 썬 밀가루 면을 국물에 넣어 끓인 요리",
                "description_en": "Hand-cut wheat noodles in hot broth",
                "primary_ingredients": [
                    "wheat noodles",
                    "zucchini",
                    "potato",
                    "green onion",
                ],
                "allergens": ["wheat", "shellfish"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "국수",
                "name_en": "Noodles (Guksu)",
                "concept": "면류",
                "description_ko": "밀가루나 메밀로 만든 가늘고 긴 면 요리",
                "description_en": "Korean noodles in various styles",
                "primary_ingredients": ["noodles", "broth"],
                "allergens": ["wheat"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "돈까스",
                "name_en": "Donkatsu (Pork Cutlet)",
                "concept": "튀김",
                "description_ko": "돼지고기를 빵가루 입혀 튀긴 일본식 돈가스",
                "description_en": "Breaded and deep-fried pork cutlet",
                "primary_ingredients": ["pork", "breadcrumbs", "cabbage"],
                "allergens": ["pork", "wheat", "egg"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "육회",
                "name_en": "Yukhoe (Korean Beef Tartare)",
                "concept": "육류안주",
                "description_ko": "생소고기를 채 썰어 양념한 요리",
                "description_en": "Korean-style beef tartare with pear and sesame",
                "primary_ingredients": ["raw beef", "pear", "sesame oil", "egg yolk"],
                "allergens": ["beef", "egg", "sesame"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
            {
                "name_ko": "김밥",
                "name_en": "Gimbap (Seaweed Rice Roll)",
                "concept": "밥류",
                "description_ko": "김에 밥과 여러 재료를 싸서 만든 요리",
                "description_en": "Seaweed rice rolls with various fillings",
                "primary_ingredients": ["rice", "seaweed", "vegetables", "ham", "egg"],
                "allergens": ["egg", "soy", "sesame"],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "손칼국수",
                "name_en": "Son Kalguksu (Hand-made Noodle Soup)",
                "concept": "칼국수",
                "description_ko": "손으로 직접 반죽하여 만든 칼국수",
                "description_en": "Hand-made knife-cut noodle soup",
                "primary_ingredients": ["wheat noodles", "zucchini", "potato"],
                "allergens": ["wheat", "shellfish"],
                "spice_level": 0,
                "difficulty_score": 2,
            },
            {
                "name_ko": "국밥",
                "name_en": "Gukbap (Soup with Rice)",
                "concept": "국밥",
                "description_ko": "국물에 밥을 말아 먹는 요리",
                "description_en": "Korean soup served with rice",
                "primary_ingredients": ["rice", "broth", "meat"],
                "allergens": [],
                "spice_level": 0,
                "difficulty_score": 1,
            },
            {
                "name_ko": "뚝배기",
                "name_en": "Ttukbaegi (Earthenware Pot Dish)",
                "concept": "찌개",
                "description_ko": "뚝배기에 끓여 내는 뜨거운 찌개 요리",
                "description_en": "Hot stew served in earthenware pot",
                "primary_ingredients": [],
                "allergens": [],
                "spice_level": 1,
                "difficulty_score": 1,
            },
            {
                "name_ko": "막창",
                "name_en": "Makchang (Grilled Beef/Pork Intestines)",
                "concept": "육류안주",
                "description_ko": "소나 돼지의 막창을 구워 먹는 요리",
                "description_en": "Grilled beef or pork intestines",
                "primary_ingredients": ["beef intestines", "pork intestines"],
                "allergens": ["beef", "pork"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
            {
                "name_ko": "곱창",
                "name_en": "Gopchang (Grilled Beef/Pork Tripe)",
                "concept": "육류안주",
                "description_ko": "소나 돼지의 곱창을 구워 먹는 요리",
                "description_en": "Grilled beef or pork small intestines",
                "primary_ingredients": ["beef tripe", "pork tripe"],
                "allergens": ["beef", "pork"],
                "spice_level": 1,
                "difficulty_score": 2,
            },
        ]
    )

    return menus
