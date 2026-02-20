"""
Menu Knowledge Engine - Automated Daily DB Expansion System

사무실 PC에서 24시간 무료로 메뉴 DB를 자동 확충하는 시스템

Modules:
- gemini_client: Google Gemini 2.5 Flash 비동기 LLM 클라이언트 (무료 tier)
- content_generator: 콘텐츠 생성 (설명/번역/분류) — Gemini 기반
- menu_name_filter: 메뉴명 품질 필터 (브랜드/매장/레시피 제거)
- collectors: 메뉴 데이터 수집 (Wikipedia/공공데이터/레시피)
- image_collectors: 이미지 수집 (Unsplash/Pixabay/Wikimedia)
- scheduler: APScheduler 일일 자동화
- db_sync: 프로덕션 DB 동기화

Author: terminal-developer
Date: 2026-02-20
Cost: $0 (Gemini 무료 tier + 공공데이터)
"""
