"""
수식어 분해 테스트 케이스 (30개)
"할머니김치찌개", "왕돈까스" 같은 수식어가 분해되어 매칭되어야 함
"""

# (입력, 기대되는 canonical 이름, 기대되는 매칭 타입)
MODIFIER_CASES = [
    # 크기 수식어
    ("왕돈까스", "돈까스", "modifier_decomposition"),
    ("왕갈비", "왕갈비", "exact"),  # DB에 "왕갈비"가 있으면 exact
    ("왕만두", "왕만두", "exact"),  # DB에 "왕만두"가 있으면 exact
    ("미니김밥", "김밥", "modifier_decomposition"),
    # 맛 수식어
    ("얼큰순두부찌개", "순두부찌개", "modifier_decomposition"),
    ("얼큰칼국수", "얼큰칼국수", "exact"),  # DB에 "얼큰칼국수"가 있으면 exact
    ("매운갈비찜", "갈비찜", "modifier_decomposition"),
    # 감성/브랜드 수식어
    ("할머니김치찌개", "김치찌개", "modifier_decomposition"),
    ("할매뼈해장국", "뼈해장국", "modifier_decomposition"),
    ("원조불고기", "불고기", "modifier_decomposition"),
    ("옛날통닭", "통닭", "exact"),  # DB에 "통닭"이 있으면 exact
    ("전통갈비찜", "갈비찜", "modifier_decomposition"),
    # 재료 수식어
    ("한우불고기", "불고기", "modifier_decomposition"),
    ("한우등심", "한우등심", "exact"),  # DB에 "한우등심"이 있으면 exact
    ("흑돼지삼겹살", "삼겹살", "modifier_decomposition"),
    ("해물짬뽕", "짬뽕", "modifier_decomposition"),
    ("해물칼국수", "해물칼국수", "exact"),  # DB에 "해물칼국수"가 있으면 exact
    # 조리법 수식어
    ("숯불갈비", "갈비", "modifier_decomposition"),
    ("직화구이삼겹살", "삼겹살", "modifier_decomposition"),
    ("훈제오리", "훈제오리", "exact"),  # DB에 "훈제오리"가 있으면 exact
    # 다중 수식어 (핵심 테스트!)
    (
        "왕얼큰뼈해장국",
        "뼈해장국",
        "modifier_decomposition",
    ),  # "왕" + "얼큰" + "뼈해장국"
    (
        "할머니얼큰순두부찌개",
        "순두부찌개",
        "modifier_decomposition",
    ),  # "할머니" + "얼큰" + "순두부찌개"
    ("한우숯불갈비", "갈비", "modifier_decomposition"),  # "한우" + "숯불" + "갈비"
    (
        "옛날얼큰손칼국수",
        "손칼국수",
        "modifier_decomposition",
    ),  # "옛날" + "얼큰" + "손칼국수"
    # 복합 케이스
    (
        "왕돈까스정식",
        "돈까스",
        "modifier_decomposition",
    ),  # "왕" + "돈까스" + "정식"(접미사)
    (
        "한우불고기1인분",
        "불고기",
        "modifier_decomposition",
    ),  # "한우" + "불고기" + "1인분"(접미사)
    (
        "할머니김치찌개세트",
        "김치찌개",
        "modifier_decomposition",
    ),  # "할머니" + "김치찌개" + "세트"(접미사)
    ("특대왕갈비", "갈비", "modifier_decomposition"),  # "특" + "대" + "왕" + "갈비"
    # 엣지 케이스
    (
        "고씨네묵은지감자탕",
        "감자탕",
        "modifier_decomposition",
    ),  # "고씨네" + "묵은지" + "감자탕"
    ("고향막국수", "막국수", "modifier_decomposition"),  # "고향" + "막국수"
]
