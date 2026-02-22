"""
Menu Name Quality Filter
브랜드명, 매장명, 개념어, 레시피 제목 등 비유효 메뉴명 필터링

첫 파이프라인 실행 분석 결과:
- 50개 수집 중 유효 ~16개 (32%)
- 브랜드명: 농심어묵우동, 농심김치우동
- 매장명: 마성떡볶이, 말죽거리소고기국밥
- 개념어: 한국요리, 반찬, 안주
- 레시피: 백종원의감자전만들기♪♪
- 재료: 검은팥, 앉은뱅이밀
- 세트/곱배기: 짬뽕정식, 짜장면곱배기

목표: 유효율 32% → 80%+

Author: terminal-developer
Date: 2026-02-20
"""

import re
import logging
from typing import Optional

logger = logging.getLogger("automation.filter")

# === 필터링 규칙 ===

# 브랜드 접두사 (제거 후 재평가)
BRAND_PREFIXES = [
    "농심",
    "오뚜기",
    "삼양",
    "풀무원",
    "CJ",
    "비비고",
    "동원",
    "해찬들",
    "청정원",
    "백설",
    "진라면",
    "신라면",
    "불닭",
]

# 매장/프랜차이즈 접두사 (제거 후 재평가)
STORE_PREFIXES = [
    "마성",
    "말죽거리",
    "소식좌",
    "교동",
    "명인",
    "맛남",
]

# 무효 접미사 (세트/정식/곱배기는 변형이지 새 메뉴가 아님)
INVALID_SUFFIXES = [
    "세트",
    "정식",
    "곱배기",
    "만들기",
    "만드는법",
    "레시피",
    "만들기♪",
    "만들기♪♪",
]

# 개념어/비음식 (메뉴가 아닌 카테고리 또는 개념)
NON_MENU_KEYWORDS = [
    "요리",
    "향토음식",
    "cuisine",
    "regional",
    "culture",
    "history",
    "food culture",
]

# 카테고리/재료 (단독으로는 메뉴가 아님)
NON_MENU_EXACT = {
    "반찬",
    "안주",
    "한국요리",
    "한국의향토음식",
    "검은팥",
    "앉은뱅이밀",
}

# 재료만으로 구성된 이름 패턴
INGREDIENT_ONLY_WORDS = [
    "밀",
    "팥",
    "콩",
    "쌀",
    "보리",
    "귀리",
    "수수",
]

# 특수문자 패턴 (음식명에 있으면 안 되는 문자)
SPECIAL_CHARS_PATTERN = re.compile(r"[♪♫♩♬愛EX\(\)\[\]{}]")

# 레시피 제목 키워드 (제거 대상)
RECIPE_KEYWORDS = [
    "만들기",
    "만드는법",
    "레시피",
    "간단",
    "초간단",
    "백종원의",
    "백종원",
    "황금레시피",
    "밑반찬",
    "반찬",
    "간장",
    "비엔나",
]


def filter_menu_name(name: str) -> Optional[str]:
    """
    메뉴명 품질 필터. 유효하면 정규화된 이름 반환, 무효면 None.

    처리 순서:
    1. 특수문자 제거
    2. 브랜드/매장 접두사 제거
    3. 레시피 키워드 제거 → 핵심 음식명 추출
    4. 세트/정식/곱배기 제거
    5. 개념/재료 필터
    6. 길이 검증 (2~15자)

    Args:
        name: 원본 메뉴명

    Returns:
        정규화된 유효 메뉴명 또는 None (무효)
    """
    if not name:
        return None

    original = name
    cleaned = name.strip()

    # 1. 특수문자 제거
    cleaned = SPECIAL_CHARS_PATTERN.sub("", cleaned)
    cleaned = cleaned.strip()

    # 2. 정확 일치 비음식 제외
    if cleaned in NON_MENU_EXACT:
        logger.debug(f"Filtered (non-menu exact): {original}")
        return None

    # 3. 비음식 키워드 체크
    for kw in NON_MENU_KEYWORDS:
        if kw in cleaned.lower():
            logger.debug(f"Filtered (non-menu keyword '{kw}'): {original}")
            return None

    # 4. 레시피 키워드 제거 → 핵심 음식명 추출
    for kw in RECIPE_KEYWORDS:
        cleaned = cleaned.replace(kw, "")
    cleaned = cleaned.strip()

    # 5. 브랜드 접두사 제거
    for brand in BRAND_PREFIXES:
        if cleaned.startswith(brand):
            cleaned = cleaned[len(brand) :]
            break

    # 6. 매장 접두사 제거
    for store in STORE_PREFIXES:
        if cleaned.startswith(store):
            cleaned = cleaned[len(store) :]
            break

    # 7. 무효 접미사 제거
    for suffix in INVALID_SUFFIXES:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break

    cleaned = cleaned.strip()

    # 8. 빈 결과 체크
    if not cleaned:
        logger.debug(f"Filtered (empty after cleanup): {original}")
        return None

    # 9. 한글 최소 1자 포함
    if not re.search(r"[가-힣]", cleaned):
        logger.debug(f"Filtered (no Korean): {original}")
        return None

    # 10. 길이 검증 (2~15자)
    if len(cleaned) < 2:
        logger.debug(f"Filtered (too short: {len(cleaned)}): {original}")
        return None
    if len(cleaned) > 15:
        logger.debug(f"Filtered (too long: {len(cleaned)}): {original}")
        return None

    # 11. 재료만으로 구성된 이름 필터
    if cleaned in INGREDIENT_ONLY_WORDS:
        logger.debug(f"Filtered (ingredient only): {original}")
        return None

    # 12. 긴 이름 잘라내기 (10자 초과 시 조리법 키워드로 분할)
    if len(cleaned) > 10:
        cooking_words = [
            "볶음",
            "무침",
            "조림",
            "구이",
            "찜",
            "전",
            "탕",
            "국",
            "찌개",
            "밥",
        ]
        for cw in cooking_words:
            idx = cleaned.find(cw)
            if 0 < idx and idx + len(cw) <= 10:
                cleaned = cleaned[: idx + len(cw)]
                break
        else:
            # 조리법 키워드 없으면 앞 8자
            if len(cleaned) > 15:
                cleaned = cleaned[:8]

    # 13. 반복 패턴 (라면라면, 라면EX라면 → 라면)
    # 짧은 이름(≤8자)에서 2자+ 반복, 긴 이름에서 3자+ 반복
    min_word = 2 if len(cleaned) <= 8 else 3
    for word_len in range(min_word, len(cleaned) // 2 + 1):
        word = cleaned[:word_len]
        if cleaned.count(word) >= 2:
            # 반복 제거 후 남은 부분이 유의미하면 사용
            remaining = cleaned.replace(word, "", 1).strip()
            if remaining and len(remaining) >= 2:
                cleaned = remaining
                break
            elif not remaining or len(remaining) < 2:
                # 반복만으로 이루어진 경우 (라면라면 → 라면)
                cleaned = word
                break

    if original != cleaned:
        logger.info(f"Menu name normalized: '{original}' -> '{cleaned}'")

    return cleaned


def batch_filter(names: list[str]) -> dict:
    """
    메뉴명 리스트 일괄 필터링

    Args:
        names: 메뉴명 리스트

    Returns:
        {"valid": [...], "filtered": [...], "stats": {...}}
    """
    valid = []
    filtered = []

    for name in names:
        result = filter_menu_name(name)
        if result:
            valid.append({"original": name, "normalized": result})
        else:
            filtered.append(name)

    stats = {
        "total": len(names),
        "valid": len(valid),
        "filtered": len(filtered),
        "valid_rate": f"{len(valid) / len(names) * 100:.1f}%" if names else "0%",
    }

    logger.info(
        f"Filter stats: {stats['valid']}/{stats['total']} valid "
        f"({stats['valid_rate']})"
    )

    return {"valid": valid, "filtered": filtered, "stats": stats}
