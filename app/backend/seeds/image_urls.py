"""
한식 메뉴 이미지 URL 매핑
소스: Wikimedia Commons (CC BY-SA / Public Domain)
형식: { "메뉴명_ko": "이미지_URL" }

URL 패턴: https://commons.wikimedia.org/wiki/Special:FilePath/{파일명}?width=400
- 라이선스 준수를 위해 Wikimedia Commons Special:FilePath 사용
- width=400으로 적절한 썸네일 크기 지정
- 상업적 사용 가능한 CC BY-SA / CC0 라이선스 이미지만 선별

대안 소스 (매핑 안 되는 경우):
- AI Hub 공공데이터 (한국 음식 이미지 84만장)
- 서울관광재단 음식이미지정보 API
- 크라우드픽 (상업용 무료)
"""


def get_image_url_map() -> dict:
    """한식 메뉴명 → 이미지 URL 매핑 반환"""

    WC = "https://commons.wikimedia.org/wiki/Special:FilePath"

    return {
        # ========================================
        # 국물요리 (Soups & Stews)
        # ========================================
        "갈비탕": f"{WC}/Galbitang.jpg?width=400",
        "삼계탕": f"{WC}/Korean_soup-Samgyetang-01.jpg?width=400",
        "곰탕": f"{WC}/Gomguk.jpg?width=400",
        "설렁탕": f"{WC}/Seolleongtang.jpg?width=400",
        "감자탕": f"{WC}/Gamjatang_(pork_back-bone_stew).jpg?width=400",
        "해물탕": f"{WC}/Haemultang.jpg?width=400",
        "뼈해장국": f"{WC}/Ppyeo_haejangguk_(Hangover_soup_with_ox_bones).jpg?width=400",
        "순대국": f"{WC}/Sundaeguk.jpg?width=400",
        "육개장": f"{WC}/Yukgaejang.jpg?width=400",
        "추어탕": f"{WC}/Chueotang.jpg?width=400",
        # 찌개
        "김치찌개": f"{WC}/Kimchi_jjigae.jpg?width=400",
        "된장찌개": f"{WC}/Doenjang_jjigae.jpg?width=400",
        "순두부찌개": f"{WC}/Sundubu-jjigae.jpg?width=400",
        "부대찌개": f"{WC}/Budae-jjigae.jpg?width=400",
        "청국장찌개": f"{WC}/Cheonggukjang_jjigae.jpg?width=400",
        # 국
        "미역국": f"{WC}/Miyeokguk.jpg?width=400",
        "떡국": f"{WC}/Tteokguk.jpg?width=400",
        "콩나물국": f"{WC}/Kongnamul-guk.jpg?width=400",
        # ========================================
        # 밥류 (Rice Dishes)
        # ========================================
        "비빔밥": f"{WC}/Bibimbap_jeonju.jpg?width=400",
        "돌솥비빔밥": f"{WC}/Dolsot-bibimbap.jpg?width=400",
        "김밥": f"{WC}/Gimbap_(pixabay).jpg?width=400",
        "볶음밥": f"{WC}/Bokkeumbap.jpg?width=400",
        "김치볶음밥": f"{WC}/Kimchi-bokkeumbap.jpg?width=400",
        "제육덮밥": f"{WC}/Jeyuk-deopbap.jpg?width=400",
        "오므라이스": f"{WC}/Omurice_by_jetalone_in_Ginza,_Tokyo.jpg?width=400",
        "카레라이스": f"{WC}/Japanese_curry_rice_002.jpg?width=400",
        "전복죽": f"{WC}/Jeonbok-juk.jpg?width=400",
        "호박죽": f"{WC}/Hobakjuk.jpg?width=400",
        # ========================================
        # 면류 (Noodles)
        # ========================================
        "냉면": f"{WC}/Naengmyeon.jpg?width=400",
        "물냉면": f"{WC}/Mul_naengmyeon.jpg?width=400",
        "비빔냉면": f"{WC}/Bibim_naengmyeon.jpg?width=400",
        "잔치국수": f"{WC}/Janchi-guksu.jpg?width=400",
        "칼국수": f"{WC}/Kalguksu.jpg?width=400",
        "짜장면": f"{WC}/Jajangmyeon.jpg?width=400",
        "짬뽕": f"{WC}/Jjamppong.jpg?width=400",
        "콩국수": f"{WC}/Kongguksu.jpg?width=400",
        "라면": f"{WC}/Ramyeon.jpg?width=400",
        "쫄면": f"{WC}/Jjolmyeon.jpg?width=400",
        "막국수": f"{WC}/Makguksu.jpg?width=400",
        "수제비": f"{WC}/Sujebi.jpg?width=400",
        # ========================================
        # 고기구이 (Grilled Meat)
        # ========================================
        "삼겹살": f"{WC}/Korean_barbeque-Samgyeopsal-05.jpg?width=400",
        "불고기": f"{WC}/Korean_bulgogi.jpg?width=400",
        "갈비": f"{WC}/Korean.food-Galbi-02.jpg?width=400",
        "소갈비": f"{WC}/Korean.food-Galbi-02.jpg?width=400",
        "돼지갈비": f"{WC}/Dwaeji_galbi.jpg?width=400",
        "닭갈비": f"{WC}/Dakgalbi.jpg?width=400",
        "LA갈비": f"{WC}/LA_Galbi.jpg?width=400",
        "양념갈비": f"{WC}/Korean_barbeque-Galbi-01.jpg?width=400",
        "목살": f"{WC}/Mokssal_gui.jpg?width=400",
        "항정살": f"{WC}/Hangjeongsal.jpg?width=400",
        "차돌박이": f"{WC}/Chadolbagi.jpg?width=400",
        "곱창": f"{WC}/Gopchang-gui.jpg?width=400",
        "막창": f"{WC}/Makchang.jpg?width=400",
        "대창": f"{WC}/Daechang-gui.jpg?width=400",
        # ========================================
        # 찜/조림 (Braised/Steamed)
        # ========================================
        "갈비찜": f"{WC}/Galbijjim.jpg?width=400",
        "안동찜닭": f"{WC}/Andong_jjimdak.jpg?width=400",
        "닭볶음탕": f"{WC}/Dakbokkeumtang.jpg?width=400",
        "족발": f"{WC}/Jokbal.jpg?width=400",
        "보쌈": f"{WC}/Bossam.jpg?width=400",
        "해물찜": f"{WC}/Haemul-jjim.jpg?width=400",
        "아귀찜": f"{WC}/Agujjim.jpg?width=400",
        "고등어조림": f"{WC}/Godeungeo-jorim.jpg?width=400",
        "두부조림": f"{WC}/Dubu-jorim.jpg?width=400",
        "장조림": f"{WC}/Jangjorim.jpg?width=400",
        # ========================================
        # 전/부침개 (Pancakes)
        # ========================================
        "파전": f"{WC}/Pajeon.jpg?width=400",
        "해물파전": f"{WC}/Haemul-pajeon.jpg?width=400",
        "김치전": f"{WC}/Kimchijeon.jpg?width=400",
        "감자전": f"{WC}/Gamjajeon.jpg?width=400",
        "녹두전": f"{WC}/Bindaetteok.jpg?width=400",
        "동그랑땡": f"{WC}/Donggeurangttaeng.jpg?width=400",
        "호박전": f"{WC}/Hobakjeon.jpg?width=400",
        # ========================================
        # 반찬/나물 (Side Dishes)
        # ========================================
        "김치": f"{WC}/Korean_kimchi.jpg?width=400",
        "깍두기": f"{WC}/Kkakdugi.jpg?width=400",
        "잡채": f"{WC}/Korean_cuisine-Japchae-01.jpg?width=400",
        "시금치나물": f"{WC}/Sigumchi-namul.jpg?width=400",
        "콩나물무침": f"{WC}/Kongnamul-muchim.jpg?width=400",
        "멸치볶음": f"{WC}/Myeolchi-bokkeum.jpg?width=400",
        "어묵볶음": f"{WC}/Eomuk-bokkeum.jpg?width=400",
        # ========================================
        # 분식/길거리음식 (Snacks/Street Food)
        # ========================================
        "떡볶이": f"{WC}/Tteok-bokki.jpg?width=400",
        "순대": f"{WC}/Sundae_(sausage).jpg?width=400",
        "튀김": f"{WC}/Twigim.jpg?width=400",
        "어묵": f"{WC}/Eomuk.jpg?width=400",
        "호떡": f"{WC}/Hotteok.jpg?width=400",
        "붕어빵": f"{WC}/Bungeoppang.jpg?width=400",
        "계란빵": f"{WC}/Gyeran-ppang.jpg?width=400",
        "토스트": f"{WC}/Korean_street_toast.jpg?width=400",
        "핫도그": f"{WC}/Korean_corn_dog.jpg?width=400",
        # ========================================
        # 해산물 (Seafood)
        # ========================================
        "회": f"{WC}/Korean_cuisine-Hoe-01.jpg?width=400",
        "물회": f"{WC}/Mulhoe.jpg?width=400",
        "간장게장": f"{WC}/Ganjang_gejang.jpg?width=400",
        "양념게장": f"{WC}/Yangnyeom_gejang.jpg?width=400",
        "오징어볶음": f"{WC}/Ojingeo-bokkeum.jpg?width=400",
        "낙지볶음": f"{WC}/Nakji-bokkeum.jpg?width=400",
        "조개구이": f"{WC}/Jogaegui.jpg?width=400",
        "산낙지": f"{WC}/Sannakji.jpg?width=400",
        # ========================================
        # 치킨/튀김 (Fried Chicken)
        # ========================================
        "치킨": f"{WC}/Korean_fried_chicken.jpg?width=400",
        "양념치킨": f"{WC}/Yangnyeom_chicken.jpg?width=400",
        "간장치킨": f"{WC}/Ganjang_chicken.jpg?width=400",
        "돈까스": f"{WC}/Tonkatsu_by_ayustety_in_Osaka.jpg?width=400",
        # ========================================
        # 디저트/음료 (Desserts/Drinks)
        # ========================================
        "팥빙수": f"{WC}/Patbingsu.jpg?width=400",
        "식혜": f"{WC}/Sikhye.jpg?width=400",
        "수정과": f"{WC}/Sujeonggwa.jpg?width=400",
        "인절미": f"{WC}/Injeolmi.jpg?width=400",
        "약과": f"{WC}/Yakgwa.jpg?width=400",
        "떡": f"{WC}/Tteok.jpg?width=400",
        # ========================================
        # 주류/안주 (Drinks/Bar Snacks)
        # ========================================
        "소주": f"{WC}/Soju.jpg?width=400",
        "막걸리": f"{WC}/Makgeolli.jpg?width=400",
        "동동주": f"{WC}/Dongdongju.jpg?width=400",
        "닭발": f"{WC}/Dakbal.jpg?width=400",
        "골뱅이무침": f"{WC}/Golbaengi-muchim.jpg?width=400",
        # ========================================
        # 한정식/정식 (Set Meals)
        # ========================================
        "한정식": f"{WC}/Korean.food-Hanjeongsik-01.jpg?width=400",
        "백반": f"{WC}/Baekban.jpg?width=400",
    }


# 매칭 안 되는 메뉴용 기본 placeholder 이미지
DEFAULT_FOOD_IMAGE = "https://commons.wikimedia.org/wiki/Special:FilePath/Korean_cuisine-Banchan-01.jpg?width=400"
