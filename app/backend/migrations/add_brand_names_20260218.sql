-- Task #4: 브랜드명 패턴 추가 (50개)
-- 목적: TC-02, TC-10 등 브랜드명 포함 메뉴 정확 분해
-- 날짜: 2026-02-18

BEGIN;

-- 50개 브랜드명 패턴 추가 (emotion type)
-- 패턴 1: "~씨네" (성씨 + 씨네) - 15개
INSERT INTO modifiers (id, text_ko, type, semantic_key, translation_en, priority, created_at)
VALUES
  (gen_random_uuid(), '고씨네', 'emotion', 'brand_gho', 'Gho Family Restaurant', 5, now()),
  (gen_random_uuid(), '김씨네', 'emotion', 'brand_kim', 'Kim Family Restaurant', 5, now()),
  (gen_random_uuid(), '이씨네', 'emotion', 'brand_lee', 'Lee Family Restaurant', 5, now()),
  (gen_random_uuid(), '박씨네', 'emotion', 'brand_park', 'Park Family Restaurant', 5, now()),
  (gen_random_uuid(), '최씨네', 'emotion', 'brand_choi', 'Choi Family Restaurant', 5, now()),
  (gen_random_uuid(), '정씨네', 'emotion', 'brand_jung', 'Jung Family Restaurant', 5, now()),
  (gen_random_uuid(), '윤씨네', 'emotion', 'brand_yun', 'Yun Family Restaurant', 5, now()),
  (gen_random_uuid(), '조씨네', 'emotion', 'brand_jo', 'Jo Family Restaurant', 5, now()),
  (gen_random_uuid(), '강씨네', 'emotion', 'brand_kang', 'Kang Family Restaurant', 5, now()),
  (gen_random_uuid(), '한씨네', 'emotion', 'brand_han', 'Han Family Restaurant', 5, now()),
  (gen_random_uuid(), '배씨네', 'emotion', 'brand_bae', 'Bae Family Restaurant', 5, now()),
  (gen_random_uuid(), '신씨네', 'emotion', 'brand_shin', 'Shin Family Restaurant', 5, now()),
  (gen_random_uuid(), '우씨네', 'emotion', 'brand_woo', 'Woo Family Restaurant', 5, now()),
  (gen_random_uuid(), '문씨네', 'emotion', 'brand_moon', 'Moon Family Restaurant', 5, now()),
  (gen_random_uuid(), '송씨네', 'emotion', 'brand_song', 'Song Family Restaurant', 5, now());

-- 패턴 2: "~식당" (명사 + 식당) - 15개
INSERT INTO modifiers (id, text_ko, type, semantic_key, translation_en, priority, created_at)
VALUES
  (gen_random_uuid(), '고기식당', 'emotion', 'brand_meat_restaurant', 'Meat Restaurant', 5, now()),
  (gen_random_uuid(), '우육식당', 'emotion', 'brand_beef_restaurant', 'Beef Restaurant', 5, now()),
  (gen_random_uuid(), '한우식당', 'emotion', 'brand_hanwoo_restaurant', 'Korean Beef Restaurant', 5, now()),
  (gen_random_uuid(), '돼지식당', 'emotion', 'brand_pork_restaurant', 'Pork Restaurant', 5, now()),
  (gen_random_uuid(), '닭식당', 'emotion', 'brand_chicken_restaurant', 'Chicken Restaurant', 5, now()),
  (gen_random_uuid(), '생선식당', 'emotion', 'brand_fish_restaurant', 'Fish Restaurant', 5, now()),
  (gen_random_uuid(), '해물식당', 'emotion', 'brand_seafood_restaurant', 'Seafood Restaurant', 5, now()),
  (gen_random_uuid(), '국밥식당', 'emotion', 'brand_soup_restaurant', 'Soup Rice Bowl Restaurant', 5, now()),
  (gen_random_uuid(), '찌개식당', 'emotion', 'brand_stew_restaurant', 'Stew Restaurant', 5, now()),
  (gen_random_uuid(), '쌀국수식당', 'emotion', 'brand_rice_noodle_restaurant', 'Rice Noodle Restaurant', 5, now()),
  (gen_random_uuid(), '면식당', 'emotion', 'brand_noodle_restaurant', 'Noodle Restaurant', 5, now()),
  (gen_random_uuid(), '밥식당', 'emotion', 'brand_rice_restaurant', 'Rice Bowl Restaurant', 5, now()),
  (gen_random_uuid(), '곱창식당', 'emotion', 'brand_intestine_restaurant', 'Intestine Restaurant', 5, now()),
  (gen_random_uuid(), '소곱창식당', 'emotion', 'brand_beef_intestine_restaurant', 'Beef Intestine Restaurant', 5, now()),
  (gen_random_uuid(), '양곱창식당', 'emotion', 'brand_pork_intestine_restaurant', 'Pork Intestine Restaurant', 5, now());

-- 패턴 3: "~집" (명사 + 집) - 10개
INSERT INTO modifiers (id, text_ko, type, semantic_key, translation_en, priority, created_at)
VALUES
  (gen_random_uuid(), '엄마집', 'emotion', 'brand_moms_place', "Mom's Place", 5, now()),
  (gen_random_uuid(), '할머니집', 'emotion', 'brand_grandmas_place', "Grandma's Place", 5, now()),
  (gen_random_uuid(), '이모집', 'emotion', 'brand_aunts_place', "Aunt's Place", 5, now()),
  (gen_random_uuid(), '할아버지집', 'emotion', 'brand_granddads_place', "Grandpa's Place", 5, now()),
  (gen_random_uuid(), '아빠집', 'emotion', 'brand_dads_place', "Dad's Place", 5, now()),
  (gen_random_uuid(), '고향집', 'emotion', 'brand_hometown_place', 'Hometown Place', 5, now()),
  (gen_random_uuid(), '시골집', 'emotion', 'brand_countryside_place', 'Countryside Place', 5, now()),
  (gen_random_uuid(), '농촌집', 'emotion', 'brand_rural_place', 'Rural Place', 5, now()),
  (gen_random_uuid(), '마을집', 'emotion', 'brand_village_place', 'Village Place', 5, now()),
  (gen_random_uuid(), '뜨락집', 'emotion', 'brand_farmyard_place', 'Farm House', 5, now());

-- 패턴 4: "~네" (성씨 + 네, 축약형) - 5개
INSERT INTO modifiers (id, text_ko, type, semantic_key, translation_en, priority, created_at)
VALUES
  (gen_random_uuid(), '어머니네', 'emotion', 'brand_mothers_home', "Mother's Home", 5, now()),
  (gen_random_uuid(), '시어머니네', 'emotion', 'brand_mothers_in_law_home', "Mother-in-law's Home", 5, now()),
  (gen_random_uuid(), '친구네', 'emotion', 'brand_friends_place', "Friend's Place", 5, now()),
  (gen_random_uuid(), '이웃네', 'emotion', 'brand_neighbors_place', "Neighbor's Place", 5, now()),
  (gen_random_uuid(), '동네네', 'emotion', 'brand_neighborhood_place', 'Neighborhood Place', 5, now());

-- 패턴 5: "~하우스" (영어 차용) - 5개
INSERT INTO modifiers (id, text_ko, type, semantic_key, translation_en, priority, created_at)
VALUES
  (gen_random_uuid(), '미트하우스', 'emotion', 'brand_meat_house', 'Meat House', 5, now()),
  (gen_random_uuid(), '스테이크하우스', 'emotion', 'brand_steak_house', 'Steakhouse', 5, now()),
  (gen_random_uuid(), '치킨하우스', 'emotion', 'brand_chicken_house', 'Chicken House', 5, now()),
  (gen_random_uuid(), '갈비하우스', 'emotion', 'brand_galbi_house', 'Galbi House', 5, now()),
  (gen_random_uuid(), '삼겹살하우스', 'emotion', 'brand_pork_belly_house', 'Pork Belly House', 5, now());

-- 총 50개 추가됨 (15 + 15 + 10 + 5 + 5 = 50)
-- 기존 54개 + 50개 = 104개 (emotion 11개 + 50개 = 61개 emotion 타입)

COMMIT;
