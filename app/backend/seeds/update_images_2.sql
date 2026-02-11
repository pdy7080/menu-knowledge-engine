-- 2차 이미지 URL 업데이트: 유사 메뉴 매핑
-- DB에 있지만 image_urls.py에 정확히 매핑되지 않은 52개 메뉴

-- 구이류 → 유사 이미지 매핑
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Galchi-gui.jpg?width=400' WHERE name_ko = '갈치구이';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Galchi-jorim.jpg?width=400' WHERE name_ko = '갈치조림';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Godeungeo-gui.jpg?width=400' WHERE name_ko = '고등어구이';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Samchi-gui.jpg?width=400' WHERE name_ko = '삼치구이';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Jogi-gui.jpg?width=400' WHERE name_ko = '조기구이';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Gajami-gui.jpg?width=400' WHERE name_ko = '가자미구이';

-- 국밥류
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Dwaeji-gukbap.jpg?width=400' WHERE name_ko = '돼지국밥';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Sundae-gukbap.jpg?width=400' WHERE name_ko = '순대국밥';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Ppyeo_haejangguk_(Hangover_soup_with_ox_bones).jpg?width=400' WHERE name_ko = '갈비해장국';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Ppyeo_haejangguk_(Hangover_soup_with_ox_bones).jpg?width=400' WHERE name_ko = '선지해장국';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Ppyeo_haejangguk_(Hangover_soup_with_ox_bones).jpg?width=400' WHERE name_ko = '콩나물해장국';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Ppyeo_haejangguk_(Hangover_soup_with_ox_bones).jpg?width=400' WHERE name_ko = '해장국밥';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Gukbap.jpg?width=400' WHERE name_ko = '국밥';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Bugeoguk.jpg?width=400' WHERE name_ko = '북어국';

-- 비빔밥 변형
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Bibimbap_jeonju.jpg?width=400' WHERE name_ko = '산채비빔밥';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Bibimbap_jeonju.jpg?width=400' WHERE name_ko = '전주비빔밥';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Hoedeopbap.jpg?width=400' WHERE name_ko = '회덮밥';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Jeyuk-deopbap.jpg?width=400' WHERE name_ko = '불고기덮밥';

-- 칼국수 변형
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kalguksu.jpg?width=400' WHERE name_ko = '닭칼국수';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kalguksu.jpg?width=400' WHERE name_ko = '바지락칼국수';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kalguksu.jpg?width=400' WHERE name_ko = '손칼국수';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kalguksu.jpg?width=400' WHERE name_ko = '얼큰칼국수';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kalguksu.jpg?width=400' WHERE name_ko = '해물칼국수';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Janchi-guksu.jpg?width=400' WHERE name_ko = '국수';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Bibim_naengmyeon.jpg?width=400' WHERE name_ko = '비빔국수';

-- 찌개 변형
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kimchi_jjigae.jpg?width=400' WHERE name_ko = '돼지김치찌개';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Godeungeo-jorim.jpg?width=400' WHERE name_ko = '고등어찌개';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Chamchi-jjigae.jpg?width=400' WHERE name_ko = '참치찌개';

-- 고기 변형
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Korean_barbeque-Samgyeopsal-05.jpg?width=400' WHERE name_ko = '대패삼겹살';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Korean_bulgogi.jpg?width=400' WHERE name_ko = '돼지불고기';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Korean.food-Galbi-02.jpg?width=400' WHERE name_ko = '왕갈비';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Jeyuk-bokkeum.jpg?width=400' WHERE name_ko = '제육볶음';

-- 찜/조림 변형
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Galbijjim.jpg?width=400' WHERE name_ko = '돼지갈비찜';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Andong_jjimdak.jpg?width=400' WHERE name_ko = '닭찜';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Agujjim.jpg?width=400' WHERE name_ko = '아구찜';

-- 전골
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Gopchang-jeongol.jpg?width=400' WHERE name_ko = '곱창전골';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Beoseot-jeongol.jpg?width=400' WHERE name_ko = '버섯전골';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Haemul-jjim.jpg?width=400' WHERE name_ko = '해물전골';

-- 볶음류
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Ojingeo-bokkeum.jpg?width=400' WHERE name_ko = '쭈꾸미볶음';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Beoseot-bokkeum.jpg?width=400' WHERE name_ko = '버섯볶음';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kimchi-bokkeumbap.jpg?width=400' WHERE name_ko = '새우볶음밥';

-- 분식 변형
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Tteok-bokki.jpg?width=400' WHERE name_ko = '치즈떡볶이';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Ramyeon.jpg?width=400' WHERE name_ko = '치즈라면';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Twigim.jpg?width=400' WHERE name_ko = '오징어튀김';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Mandu.jpg?width=400' WHERE name_ko = '만두';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Bindaetteok.jpg?width=400' WHERE name_ko = '빈대떡';

-- 기타
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Doenjang_jjigae.jpg?width=400' WHERE name_ko = '뚝배기';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Korean_cuisine-Japchae-01.jpg?width=400' WHERE name_ko = '나물반찬';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Korean_kimchi.jpg?width=400' WHERE name_ko = '배추김치';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Yukhoe.jpg?width=400' WHERE name_ko = '육회';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Myeongnan-jeot.jpg?width=400' WHERE name_ko = '명란젓';
UPDATE canonical_menus SET image_url = 'https://commons.wikimedia.org/wiki/Special:FilePath/Patjuk.jpg?width=400' WHERE name_ko = '팥죽';
