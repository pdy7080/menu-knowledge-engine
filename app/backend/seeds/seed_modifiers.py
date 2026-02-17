"""
Modifier 시드 데이터 (104개)
Stage 3 확장: 브랜드명 패턴 추가 (54 → 104)
- emotion 타입에 50개 브랜드명 패턴 추가
- "~씨네" (15개), "~식당" (15개), "~집" (10개), "~네" (5개), "~하우스" (5개)
"""
from typing import List, Dict, Any


def get_modifier_seeds() -> List[Dict[str, Any]]:
    """Modifier 사전 시드 데이터 반환 (104개)"""

    modifiers = []

    # taste (맛) - 14개
    taste_modifiers = [
        {"text_ko": "얼큰", "type": "taste", "semantic_key": "spicy_hearty", "translation_en": "Extra Spicy", "affects_spice": 1, "priority": 10},
        {"text_ko": "얼큰한", "type": "taste", "semantic_key": "spicy_hearty", "translation_en": "Extra Spicy", "affects_spice": 1, "priority": 10},
        {"text_ko": "매운", "type": "taste", "semantic_key": "spicy", "translation_en": "Spicy", "affects_spice": 2, "priority": 10},
        {"text_ko": "순", "type": "taste", "semantic_key": "mild", "translation_en": "Mild", "affects_spice": -2, "priority": 10},
        {"text_ko": "순한", "type": "taste", "semantic_key": "mild", "translation_en": "Mild", "affects_spice": -2, "priority": 10},
        {"text_ko": "담백한", "type": "taste", "semantic_key": "light_clean", "translation_en": "Light & Clean", "affects_spice": 0, "priority": 8},
        {"text_ko": "달콤한", "type": "taste", "semantic_key": "sweet", "translation_en": "Sweet", "affects_spice": 0, "priority": 8},
        {"text_ko": "시원한", "type": "taste", "semantic_key": "refreshing", "translation_en": "Refreshing", "affects_spice": 0, "priority": 8},
        {"text_ko": "새콤한", "type": "taste", "semantic_key": "tangy", "translation_en": "Tangy/Sour", "affects_spice": 0, "priority": 8},
        {"text_ko": "고소한", "type": "taste", "semantic_key": "nutty_savory", "translation_en": "Nutty & Savory", "affects_spice": 0, "priority": 8},
        {"text_ko": "짭짤한", "type": "taste", "semantic_key": "salty_savory", "translation_en": "Savory & Salty", "affects_spice": 0, "priority": 8},
        {"text_ko": "칼칼한", "type": "taste", "semantic_key": "sharp_spicy", "translation_en": "Sharp Spicy", "affects_spice": 1, "priority": 8},
        {"text_ko": "알싸한", "type": "taste", "semantic_key": "pungent", "translation_en": "Pungent", "affects_spice": 0, "priority": 8},
        {"text_ko": "구수한", "type": "taste", "semantic_key": "deep_savory", "translation_en": "Deep & Savory", "affects_spice": 0, "priority": 8},
    ]

    # size (크기/양) - 7개
    size_modifiers = [
        {"text_ko": "왕", "type": "size", "semantic_key": "x_large", "translation_en": "King-Size", "affects_size": "x_large", "priority": 15},
        {"text_ko": "대", "type": "size", "semantic_key": "large", "translation_en": "Large", "affects_size": "large", "priority": 12},
        {"text_ko": "소", "type": "size", "semantic_key": "small", "translation_en": "Small", "affects_size": "small", "priority": 12},
        {"text_ko": "곱빼기", "type": "size", "semantic_key": "double", "translation_en": "Double Portion", "affects_size": "double", "priority": 15},
        {"text_ko": "반", "type": "size", "semantic_key": "half", "translation_en": "Half Portion", "affects_size": "half", "priority": 15},
        {"text_ko": "미니", "type": "size", "semantic_key": "mini", "translation_en": "Mini", "affects_size": "mini", "priority": 12},
        {"text_ko": "점보", "type": "size", "semantic_key": "jumbo", "translation_en": "Jumbo", "affects_size": "jumbo", "priority": 10},
    ]

    # emotion (감성/브랜드) - 61개 (기존 11개 + 브랜드명 50개)
    emotion_modifiers = [
        # 기존 11개
        {"text_ko": "할머니", "type": "emotion", "semantic_key": "homestyle_grandma", "translation_en": "Grandma's / Homestyle", "priority": 5},
        {"text_ko": "할매", "type": "emotion", "semantic_key": "homestyle_grandma", "translation_en": "Grandma's / Homestyle", "priority": 5},
        {"text_ko": "옛날", "type": "emotion", "semantic_key": "old_fashioned", "translation_en": "Old-fashioned / Traditional", "priority": 5},
        {"text_ko": "시골", "type": "emotion", "semantic_key": "countryside", "translation_en": "Countryside-style", "priority": 5},
        {"text_ko": "원조", "type": "emotion", "semantic_key": "original", "translation_en": "The Original", "priority": 5},
        {"text_ko": "본가", "type": "emotion", "semantic_key": "main_house", "translation_en": "Main House / Authentic", "priority": 5},
        {"text_ko": "맛있는", "type": "emotion", "semantic_key": "delicious", "translation_en": "Delicious", "priority": 3},
        {"text_ko": "엄마손", "type": "emotion", "semantic_key": "mothers_touch", "translation_en": "Mother's Touch", "priority": 5},
        {"text_ko": "고향", "type": "emotion", "semantic_key": "hometown", "translation_en": "Hometown-style", "priority": 5},
        {"text_ko": "전통", "type": "emotion", "semantic_key": "traditional", "translation_en": "Traditional", "priority": 5},
        {"text_ko": "명품", "type": "emotion", "semantic_key": "premium_brand", "translation_en": "Premium", "priority": 5},

        # 패턴 1: "~씨네" (성씨 + 씨네) - 15개
        {"text_ko": "고씨네", "type": "emotion", "semantic_key": "brand_gho", "translation_en": "Gho Family Restaurant", "priority": 5},
        {"text_ko": "김씨네", "type": "emotion", "semantic_key": "brand_kim", "translation_en": "Kim Family Restaurant", "priority": 5},
        {"text_ko": "이씨네", "type": "emotion", "semantic_key": "brand_lee", "translation_en": "Lee Family Restaurant", "priority": 5},
        {"text_ko": "박씨네", "type": "emotion", "semantic_key": "brand_park", "translation_en": "Park Family Restaurant", "priority": 5},
        {"text_ko": "최씨네", "type": "emotion", "semantic_key": "brand_choi", "translation_en": "Choi Family Restaurant", "priority": 5},
        {"text_ko": "정씨네", "type": "emotion", "semantic_key": "brand_jung", "translation_en": "Jung Family Restaurant", "priority": 5},
        {"text_ko": "윤씨네", "type": "emotion", "semantic_key": "brand_yun", "translation_en": "Yun Family Restaurant", "priority": 5},
        {"text_ko": "조씨네", "type": "emotion", "semantic_key": "brand_jo", "translation_en": "Jo Family Restaurant", "priority": 5},
        {"text_ko": "강씨네", "type": "emotion", "semantic_key": "brand_kang", "translation_en": "Kang Family Restaurant", "priority": 5},
        {"text_ko": "한씨네", "type": "emotion", "semantic_key": "brand_han", "translation_en": "Han Family Restaurant", "priority": 5},
        {"text_ko": "배씨네", "type": "emotion", "semantic_key": "brand_bae", "translation_en": "Bae Family Restaurant", "priority": 5},
        {"text_ko": "신씨네", "type": "emotion", "semantic_key": "brand_shin", "translation_en": "Shin Family Restaurant", "priority": 5},
        {"text_ko": "우씨네", "type": "emotion", "semantic_key": "brand_woo", "translation_en": "Woo Family Restaurant", "priority": 5},
        {"text_ko": "문씨네", "type": "emotion", "semantic_key": "brand_moon", "translation_en": "Moon Family Restaurant", "priority": 5},
        {"text_ko": "송씨네", "type": "emotion", "semantic_key": "brand_song", "translation_en": "Song Family Restaurant", "priority": 5},

        # 패턴 2: "~식당" (명사 + 식당) - 15개
        {"text_ko": "고기식당", "type": "emotion", "semantic_key": "brand_meat_restaurant", "translation_en": "Meat Restaurant", "priority": 5},
        {"text_ko": "우육식당", "type": "emotion", "semantic_key": "brand_beef_restaurant", "translation_en": "Beef Restaurant", "priority": 5},
        {"text_ko": "한우식당", "type": "emotion", "semantic_key": "brand_hanwoo_restaurant", "translation_en": "Korean Beef Restaurant", "priority": 5},
        {"text_ko": "돼지식당", "type": "emotion", "semantic_key": "brand_pork_restaurant", "translation_en": "Pork Restaurant", "priority": 5},
        {"text_ko": "닭식당", "type": "emotion", "semantic_key": "brand_chicken_restaurant", "translation_en": "Chicken Restaurant", "priority": 5},
        {"text_ko": "생선식당", "type": "emotion", "semantic_key": "brand_fish_restaurant", "translation_en": "Fish Restaurant", "priority": 5},
        {"text_ko": "해물식당", "type": "emotion", "semantic_key": "brand_seafood_restaurant", "translation_en": "Seafood Restaurant", "priority": 5},
        {"text_ko": "국밥식당", "type": "emotion", "semantic_key": "brand_soup_restaurant", "translation_en": "Soup Rice Bowl Restaurant", "priority": 5},
        {"text_ko": "찌개식당", "type": "emotion", "semantic_key": "brand_stew_restaurant", "translation_en": "Stew Restaurant", "priority": 5},
        {"text_ko": "쌀국수식당", "type": "emotion", "semantic_key": "brand_rice_noodle_restaurant", "translation_en": "Rice Noodle Restaurant", "priority": 5},
        {"text_ko": "면식당", "type": "emotion", "semantic_key": "brand_noodle_restaurant", "translation_en": "Noodle Restaurant", "priority": 5},
        {"text_ko": "밥식당", "type": "emotion", "semantic_key": "brand_rice_restaurant", "translation_en": "Rice Bowl Restaurant", "priority": 5},
        {"text_ko": "곱창식당", "type": "emotion", "semantic_key": "brand_intestine_restaurant", "translation_en": "Intestine Restaurant", "priority": 5},
        {"text_ko": "소곱창식당", "type": "emotion", "semantic_key": "brand_beef_intestine_restaurant", "translation_en": "Beef Intestine Restaurant", "priority": 5},
        {"text_ko": "양곱창식당", "type": "emotion", "semantic_key": "brand_pork_intestine_restaurant", "translation_en": "Pork Intestine Restaurant", "priority": 5},

        # 패턴 3: "~집" (명사 + 집) - 10개
        {"text_ko": "엄마집", "type": "emotion", "semantic_key": "brand_moms_place", "translation_en": "Mom's Place", "priority": 5},
        {"text_ko": "할머니집", "type": "emotion", "semantic_key": "brand_grandmas_place", "translation_en": "Grandma's Place", "priority": 5},
        {"text_ko": "이모집", "type": "emotion", "semantic_key": "brand_aunts_place", "translation_en": "Aunt's Place", "priority": 5},
        {"text_ko": "할아버지집", "type": "emotion", "semantic_key": "brand_granddads_place", "translation_en": "Grandpa's Place", "priority": 5},
        {"text_ko": "아빠집", "type": "emotion", "semantic_key": "brand_dads_place", "translation_en": "Dad's Place", "priority": 5},
        {"text_ko": "고향집", "type": "emotion", "semantic_key": "brand_hometown_place", "translation_en": "Hometown Place", "priority": 5},
        {"text_ko": "시골집", "type": "emotion", "semantic_key": "brand_countryside_place", "translation_en": "Countryside Place", "priority": 5},
        {"text_ko": "농촌집", "type": "emotion", "semantic_key": "brand_rural_place", "translation_en": "Rural Place", "priority": 5},
        {"text_ko": "마을집", "type": "emotion", "semantic_key": "brand_village_place", "translation_en": "Village Place", "priority": 5},
        {"text_ko": "뜨락집", "type": "emotion", "semantic_key": "brand_farmyard_place", "translation_en": "Farm House", "priority": 5},

        # 패턴 4: "~네" (축약형) - 5개
        {"text_ko": "어머니네", "type": "emotion", "semantic_key": "brand_mothers_home", "translation_en": "Mother's Home", "priority": 5},
        {"text_ko": "시어머니네", "type": "emotion", "semantic_key": "brand_mothers_in_law_home", "translation_en": "Mother-in-law's Home", "priority": 5},
        {"text_ko": "친구네", "type": "emotion", "semantic_key": "brand_friends_place", "translation_en": "Friend's Place", "priority": 5},
        {"text_ko": "이웃네", "type": "emotion", "semantic_key": "brand_neighbors_place", "translation_en": "Neighbor's Place", "priority": 5},
        {"text_ko": "동네네", "type": "emotion", "semantic_key": "brand_neighborhood_place", "translation_en": "Neighborhood Place", "priority": 5},

        # 패턴 5: "~하우스" (영어 차용) - 5개
        {"text_ko": "미트하우스", "type": "emotion", "semantic_key": "brand_meat_house", "translation_en": "Meat House", "priority": 5},
        {"text_ko": "스테이크하우스", "type": "emotion", "semantic_key": "brand_steak_house", "translation_en": "Steakhouse", "priority": 5},
        {"text_ko": "치킨하우스", "type": "emotion", "semantic_key": "brand_chicken_house", "translation_en": "Chicken House", "priority": 5},
        {"text_ko": "갈비하우스", "type": "emotion", "semantic_key": "brand_galbi_house", "translation_en": "Galbi House", "priority": 5},
        {"text_ko": "삼겹살하우스", "type": "emotion", "semantic_key": "brand_pork_belly_house", "translation_en": "Pork Belly House", "priority": 5},
    ]

    # ingredient (재료 강조) - 9개
    ingredient_modifiers = [
        {"text_ko": "해물", "type": "ingredient", "semantic_key": "seafood", "translation_en": "Seafood", "priority": 18},
        {"text_ko": "야채", "type": "ingredient", "semantic_key": "vegetable", "translation_en": "Vegetable", "priority": 15},
        {"text_ko": "순두부", "type": "ingredient", "semantic_key": "soft_tofu", "translation_en": "Soft Tofu", "priority": 18},
        {"text_ko": "치즈", "type": "ingredient", "semantic_key": "cheese", "translation_en": "Cheese", "priority": 15},
        {"text_ko": "묵은지", "type": "ingredient", "semantic_key": "aged_kimchi", "translation_en": "Aged Kimchi", "priority": 18},
        {"text_ko": "모듬", "type": "ingredient", "semantic_key": "assorted", "translation_en": "Assorted", "priority": 15},
        {"text_ko": "날치알", "type": "ingredient", "semantic_key": "flying_fish_roe", "translation_en": "Flying Fish Roe", "priority": 12},
        {"text_ko": "계란", "type": "ingredient", "semantic_key": "egg", "translation_en": "Egg", "priority": 12},
        {"text_ko": "버섯", "type": "ingredient", "semantic_key": "mushroom", "translation_en": "Mushroom", "priority": 15},
    ]

    # cooking (조리법) - 7개
    cooking_modifiers = [
        {"text_ko": "불", "type": "cooking", "semantic_key": "fire_grilled", "translation_en": "Fire-Grilled", "priority": 12},
        {"text_ko": "숯불", "type": "cooking", "semantic_key": "charcoal", "translation_en": "Charcoal-Grilled", "priority": 15},
        {"text_ko": "직화", "type": "cooking", "semantic_key": "direct_flame", "translation_en": "Direct Flame", "priority": 12},
        {"text_ko": "수제", "type": "cooking", "semantic_key": "handmade", "translation_en": "Handmade", "priority": 10},
        {"text_ko": "생", "type": "cooking", "semantic_key": "raw", "translation_en": "Raw/Fresh", "priority": 15},
        {"text_ko": "통", "type": "cooking", "semantic_key": "whole", "translation_en": "Whole", "priority": 12},
        {"text_ko": "대패", "type": "cooking", "semantic_key": "thinly_sliced", "translation_en": "Thinly Sliced", "priority": 12},
    ]

    # grade (등급) - 4개
    grade_modifiers = [
        {"text_ko": "한우", "type": "grade", "semantic_key": "korean_beef", "translation_en": "Korean Beef (Hanwoo)", "priority": 20},
        {"text_ko": "특", "type": "grade", "semantic_key": "special_grade", "translation_en": "Special Grade", "priority": 10},
        {"text_ko": "프리미엄", "type": "grade", "semantic_key": "premium", "translation_en": "Premium", "priority": 10},
        {"text_ko": "스페셜", "type": "grade", "semantic_key": "special", "translation_en": "Special", "priority": 10},
    ]

    # origin (지역) - 2개
    origin_modifiers = [
        {"text_ko": "궁중", "type": "origin", "semantic_key": "royal_court", "translation_en": "Royal Court", "priority": 8},
        {"text_ko": "부산", "type": "origin", "semantic_key": "busan_style", "translation_en": "Busan-style", "priority": 8},
    ]

    # 전체 합치기
    modifiers.extend(taste_modifiers)
    modifiers.extend(size_modifiers)
    modifiers.extend(emotion_modifiers)
    modifiers.extend(ingredient_modifiers)
    modifiers.extend(cooking_modifiers)
    modifiers.extend(grade_modifiers)
    modifiers.extend(origin_modifiers)

    return modifiers
