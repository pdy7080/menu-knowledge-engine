"""
접미사 패턴 테스트 케이스 (15개)
"정식", "세트", "1인분" 같은 접미사가 제거되어 매칭되어야 함
"""

# (입력, 기대되는 canonical 이름, 기대되는 매칭 타입)
SUFFIX_CASES = [
    # 정식
    ("불고기정식", "불고기", "modifier_decomposition"),
    ("갈비정식", "갈비", "modifier_decomposition"),
    ("생선구이정식", "고등어구이", "modifier_decomposition"),  # 주의: 구체적인 생선명은 불일치할 수 있음

    # 세트/셋트
    ("갈비세트", "갈비", "modifier_decomposition"),
    ("삼겹살셋트", "삼겹살", "modifier_decomposition"),

    # 인분
    ("삼겹살1인분", "삼겹살", "modifier_decomposition"),
    ("갈비2인분", "갈비", "modifier_decomposition"),
    ("불고기3인", "불고기", "modifier_decomposition"),
    ("삼겹살4인", "삼겹살", "modifier_decomposition"),

    # 한상/상차림
    ("한정식한상", "한정식", "modifier_decomposition"),
    ("불고기상차림", "불고기", "modifier_decomposition"),

    # (대)/(중)/(소)
    ("갈비탕(대)", "갈비탕", "exact"),  # 정규화로 괄호 제거
    ("김치찌개(중)", "김치찌개", "exact"),
    ("비빔밥(소)", "비빔밥", "exact"),

    # 특선/스페셜
    ("갈비특선", "갈비", "modifier_decomposition"),
]
