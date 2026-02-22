"""
메뉴명 정규화 서비스
공공데이터 API 매칭률을 높이기 위한 메뉴명 전처리
"""

import re
from typing import Tuple, List


# 제거할 수식어 패턴 (정규화 시)
REMOVABLE_PREFIXES = [
    "왕",
    "특",
    "대",
    "소",
    "미니",
    "매운",
    "얼큰",
    "시원한",
    "차가운",
    "뜨거운",
    "숯불",
    "직화",
    "냉동",
    "할매",
    "할머니",
    "옛날",
    "원조",
    "전통",
    "수제",
    "홈메이드",
    "한우",
    "국내산",
]

# 제거할 접미사 패턴
REMOVABLE_SUFFIXES = [
    "정식",
    "세트",
    "셋트",
    "1인분",
    "2인분",
    "3인분",
    "4인분",
    "1인",
    "2인",
    "3인",
    "4인",
    "한상",
    "상차림",
    "스페셜",
    "특선",
    "모듬",
]


def normalize_menu_name(menu_name: str) -> str:
    """
    메뉴명 기본 정규화
    공백, 특수문자 제거 및 기본 클리닝

    Args:
        menu_name: 원본 메뉴명

    Returns:
        정규화된 메뉴명
    """
    s = menu_name.strip()

    # 메뉴 번호 제거: "1. 김치찌개"
    s = re.sub(r"^\d+[\.\)\-\s]+", "", s)

    # 괄호 내용 제거: "삼겹살(200g)"
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\[.*?\]", "", s)

    # 공백 제거
    s = re.sub(r"\s+", "", s)

    # 특수문자 제거
    s = re.sub(r'[~!@#$%^&*_+=|\\<>?/:;"\',.\-]', "", s)

    return s.strip()


def strip_modifiers(menu_name: str) -> Tuple[str, List[str]]:
    """
    수식어/접미사를 제거하여 기본 메뉴명 추출

    Args:
        menu_name: 정규화된 메뉴명

    Returns:
        (기본 메뉴명, 제거된 수식어 목록)
    """
    cleaned = menu_name
    removed = []

    # 접미사 제거 (뒤에서부터)
    for suffix in REMOVABLE_SUFFIXES:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            removed.append(suffix)

    # 접두사 제거 (앞에서부터, 긴 것 우선)
    sorted_prefixes = sorted(REMOVABLE_PREFIXES, key=len, reverse=True)
    for prefix in sorted_prefixes:
        if cleaned.startswith(prefix) and len(cleaned) > len(prefix):
            cleaned = cleaned[len(prefix) :]
            removed.append(prefix)

    return cleaned, removed


def generate_search_variants(menu_name: str) -> List[str]:
    """
    공공데이터 API 검색을 위한 메뉴명 변형 생성
    여러 가지 형태로 검색하여 매칭률을 높임

    Args:
        menu_name: 원본 메뉴명

    Returns:
        검색용 변형 목록 (우선순위 순)
    """
    variants = []
    normalized = normalize_menu_name(menu_name)

    # 1. 정규화된 원본
    variants.append(normalized)

    # 2. 수식어 제거 버전
    stripped, _ = strip_modifiers(normalized)
    if stripped != normalized and stripped:
        variants.append(stripped)

    # 3. 공백 포함 버전 (API가 공백 포함 검색 지원하는 경우)
    spaced = menu_name.strip()
    spaced = re.sub(r"^\d+[\.\)\-\s]+", "", spaced)
    spaced = re.sub(r"\(.*?\)", "", spaced).strip()
    if spaced != normalized and spaced:
        variants.append(spaced)

    # 중복 제거 (순서 유지)
    seen = set()
    unique = []
    for v in variants:
        if v not in seen and v:
            seen.add(v)
            unique.append(v)

    return unique
