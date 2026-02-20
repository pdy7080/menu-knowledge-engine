"""
Prompt Templates for Menu Content Generation
enrich_content_gemini_v2.py에서 추출한 카테고리별 프롬프트

Author: terminal-developer
Date: 2026-02-20
"""

# System prompt for JSON output (Ollama optimized)
SYSTEM_PROMPT = """You are a Korean food expert (한식 전문가).
You have deep knowledge of Korean cuisine: ingredients, preparation methods,
regional variations, history, and cultural context.
Always respond in valid JSON format. No markdown, no code blocks."""

# 카테고리 감지 키워드 (enrich_content_gemini_v2.py 패턴)
CATEGORY_KEYWORDS = {
    "stew": ["찌개", "전골", "탕"],
    "soup": ["국", "탕", "국밥", "해장"],
    "grilled": ["구이", "불고기", "갈비", "삼겹살", "목살"],
    "fried": ["튀김", "돈까스", "가스", "치킨", "전"],
    "rice": ["밥", "비빔", "볶음밥", "덮밥", "김밥"],
    "noodle": ["면", "국수", "냉면", "짜장", "짬뽕", "우동", "라멘"],
    "side": ["반찬", "김치", "나물", "젓갈", "장아찌"],
    "dessert": ["떡", "과자", "빵", "아이스", "음료"],
}


def detect_category(name_ko: str) -> str:
    """
    메뉴명에서 카테고리 감지

    Args:
        name_ko: 한국어 메뉴명

    Returns:
        카테고리 문자열 (stew, soup, grilled, fried, rice, noodle, side, dessert, other)
    """
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in name_ko:
                return category
    return "other"


def build_enrichment_prompt(
    name_ko: str,
    name_en: str,
    concept: str = "",
    ingredients: str = "",
    spice_level: int = 0,
    description_ko: str = "",
    description_en: str = "",
) -> str:
    """
    메뉴 콘텐츠 생성 프롬프트 (enrich_content_gemini_v2.py 라인 136-208 패턴)

    Args:
        name_ko: 한국어 메뉴명
        name_en: 영문 메뉴명
        concept: 상위 개념
        ingredients: 주재료 (쉼표 구분)
        spice_level: 매운 정도 (0-5)
        description_ko: 기존 한국어 설명
        description_en: 기존 영문 설명

    Returns:
        완전한 프롬프트 문자열
    """
    return f"""Generate comprehensive content for this Korean menu item in valid JSON format.

**Menu Information:**
- Korean Name: {name_ko}
- English Name: {name_en}
- Concept: {concept or 'N/A'}
- Main Ingredients: {ingredients or 'N/A'}
- Spice Level: {spice_level}/5
- Existing Description (KO): {description_ko or 'N/A'}
- Existing Description (EN): {description_en or 'N/A'}

**Required Output (MUST be valid JSON):**

{{
  "description_ko": "150-200자 상세 설명 (한국어). 이 음식의 맛, 질감, 특징을 생생하게 묘사",
  "description_en": "150-200 chars detailed description (English). Vivid portrayal of taste, texture, and characteristics",
  "regional_variants": [
    {{"name": "서울식", "difference": "서울에서의 특징 설명"}},
    {{"name": "전라도식", "difference": "전라도에서의 특징 설명"}},
    {{"name": "경상도식", "difference": "경상도에서의 특징 설명"}}
  ],
  "preparation_steps": [
    "1단계: 재료 준비 - 구체적 설명",
    "2단계: 조리 과정 1",
    "3단계: 조리 과정 2",
    "4단계: 조리 과정 3",
    "5단계: 완성 및 플레이팅"
  ],
  "nutrition": {{
    "calories": 0,
    "protein_g": 0,
    "fat_g": 0,
    "carbs_g": 0,
    "serving_size": "1인분 (000g)"
  }},
  "flavor_profile": {{
    "spiciness": {spice_level},
    "sweetness": 0,
    "saltiness": 0,
    "umami": 0,
    "sourness": 0
  }},
  "visitor_tips": {{
    "ordering": "외국인 관광객을 위한 주문 팁",
    "eating": "올바른 먹는 방법과 에티켓",
    "pairing": "함께 먹으면 좋은 사이드 메뉴"
  }},
  "similar_dishes": [
    {{"name": "유사 메뉴 1", "similarity": "유사점 설명"}},
    {{"name": "유사 메뉴 2", "similarity": "유사점 설명"}},
    {{"name": "유사 메뉴 3", "similarity": "유사점 설명"}}
  ],
  "cultural_background": {{
    "history": "역사적 배경 (2-3문장, 구체적 시대와 유래 포함)",
    "origin": "기원 지역",
    "cultural_notes": "문화적 특징 및 현대 한국에서의 의미 (2-3문장)"
  }}
}}

**Rules:**
1. Output ONLY the JSON object, nothing else
2. All Korean text must be culturally authentic and specific
3. Nutrition values should be realistic for this specific dish
4. Minimum 3 regional variants, 5 preparation steps, 3 similar dishes
5. Flavor profile values: 0 (none) to 5 (very strong)"""


def build_translation_prompt(
    name_ko: str,
    description_ko: str,
    target_languages: list = None,
) -> str:
    """
    번역 프롬프트 (JA/ZH 번역용)

    Args:
        name_ko: 한국어 메뉴명
        description_ko: 한국어 설명
        target_languages: 대상 언어 목록 (기본: ["en", "ja", "zh_cn"])

    Returns:
        번역 프롬프트
    """
    languages = target_languages or ["en", "ja", "zh_cn"]

    lang_instructions = []
    if "en" in languages:
        lang_instructions.append('"name_en": "English name (romanized Korean preferred, e.g. Kimchi-jjigae)"')
        lang_instructions.append('"description_en": "English description (150-200 chars)"')
    if "ja" in languages:
        lang_instructions.append('"name_ja": "Japanese name (カタカナ or 漢字, e.g. キムチチゲ)"')
        lang_instructions.append('"description_ja": "Japanese description (150-200 chars)"')
    if "zh_cn" in languages:
        lang_instructions.append('"name_zh_cn": "Simplified Chinese name (e.g. 泡菜汤)"')
        lang_instructions.append('"description_zh_cn": "Chinese description (150-200 chars)"')

    fields = ",\n  ".join(lang_instructions)

    return f"""Translate this Korean menu item. Maintain cultural authenticity.

**Korean Menu:**
- Name: {name_ko}
- Description: {description_ko}

**Output (valid JSON only):**

{{
  {fields}
}}

**Rules:**
1. Use natural, culturally appropriate translations (not literal)
2. Keep food-specific terms authentic (김치 → キムチ, not 漬物)
3. Japanese: use katakana for Korean food names
4. Chinese: use common Chinese food terminology"""


def build_categorization_prompt(name_ko: str) -> str:
    """
    메뉴 분류 프롬프트

    Args:
        name_ko: 한국어 메뉴명

    Returns:
        분류 프롬프트
    """
    return f"""Classify this Korean food menu item.

Menu: {name_ko}

Output valid JSON:
{{
  "category_1": "대분류 (밥류, 면류, 국/탕류, 찌개류, 구이류, 볶음류, 튀김류, 반찬류, 디저트류, 음료류, 기타)",
  "category_2": "중분류 (more specific subcategory)",
  "spice_level": 0,
  "dietary_tags": ["vegan", "vegetarian", "gluten_free", "halal", "pork", "beef", "seafood", "contains_alcohol"],
  "allergens": ["대두", "밀", "우유", "계란", "갑각류", "견과류", "땅콩"],
  "difficulty_score": 3,
  "typical_price_min": 0,
  "typical_price_max": 0
}}

Rules:
1. spice_level: 0 (not spicy) to 5 (extremely spicy)
2. difficulty_score: 1 (very easy) to 5 (very difficult to prepare)
3. typical_price: average Korean restaurant price in KRW
4. Only include relevant dietary_tags and allergens
5. Output ONLY valid JSON"""


# 검증 함수 (enrich_content_gemini_v2.py 라인 210-235 패턴)
REQUIRED_ENRICHMENT_KEYS = [
    "description_ko", "description_en",
    "regional_variants", "preparation_steps",
    "nutrition", "flavor_profile",
    "visitor_tips", "similar_dishes",
    "cultural_background",
]


def validate_enrichment(content: dict) -> bool:
    """
    생성된 콘텐츠 검증

    Args:
        content: 생성된 JSON dict

    Returns:
        유효하면 True
    """
    for key in REQUIRED_ENRICHMENT_KEYS:
        if key not in content:
            return False

    if len(content.get("regional_variants", [])) < 2:
        return False
    if len(content.get("preparation_steps", [])) < 3:
        return False
    if len(content.get("similar_dishes", [])) < 2:
        return False

    return True
