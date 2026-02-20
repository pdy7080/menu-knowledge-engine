# Changelog

All notable changes to Menu Knowledge Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v0.1.1-sprint2-phase1] - 2026-02-19

### 🎉 Sprint 2 Phase 1: Enriched Content & Multi-Image Support

**배포 상태**: ✅ 프로덕션 운영 중

### Added

#### Database Schema
- `description_long_ko` TEXT - 한국어 상세 설명 (150-200자)
- `description_long_en` TEXT - 영문 상세 설명 (150-200자)
- `regional_variants` JSONB - 지역별 변종 정보 (서울식, 전라도식, 경상도식 등)
- `preparation_steps` JSONB - 조리 단계 (steps, serving_suggestions, etiquette)
- `nutrition_detail` JSONB - 영양 정보 상세 (calories, protein, carbs, fat, sodium, serving_size)
- `flavor_profile` JSONB - 맛 프로필 (sweet, salty, sour, bitter, umami 0-5 점수)
- `visitor_tips` JSONB - 방문자 팁 (ordering_tips, pairing, eating_method)
- `similar_dishes` JSONB[] - 유사 메뉴 목록
- `content_completeness` NUMERIC(5,2) - 콘텐츠 완성도 점수 (0-100)
- `primary_image` JSONB - 대표 이미지 (url, source, license, attribution)
- `images` JSONB[] - 추가 이미지 배열 (다중 이미지 지원)

#### API Endpoints
- GET `/api/v1/canonical-menus?include_enriched=true` - 메뉴 목록 조회 (enriched content 포함)
- GET `/api/v1/canonical-menus/{menu_id}` - 메뉴 상세 조회 (enriched content 자동 포함)

#### Features
- Claude 3.5 Haiku API 기반 콘텐츠 자동 생성 (111개 메뉴 완료)
- Content completeness scoring 시스템 (채워진 필드 비율로 0-100 점수)
- JSONB 필드 GIN 인덱스 추가 (regional_variants, flavor_profile)
- Multi-image metadata support (출처, 라이선스, 저작권 정보)

#### Scripts
- `enrich_content_claude.py` - Claude API 기반 콘텐츠 생성 스크립트
- `load_enriched_data_direct.py` - Direct SQL UPDATE 기반 데이터 로드
- `test_tc02_tc10.py` - Sprint 2 Phase 1 API 테스트 케이스
- `scripts/upload_images_to_server.py` - scp 기반 이미지 업로드 스크립트
- `run_migration.py` - DB 마이그레이션 실행 도구
- `check_columns.py` - DB 스키마 검증 도구

#### Migrations
- `migrations/sprint2_phase1_add_columns.sql` - Enriched content 필드 추가
- `migrations/sprint2_phase1_add_images.sql` - Image 필드 추가
- `migrations/sprint0_public_data.sql` - 공공데이터 필드 추가

### Changed
- `_serialize_canonical_menu()` 함수에 `include_enriched` 파라미터 추가
- `similar_dishes` 컬럼 타입 변경: JSONB → JSONB[] (배열)

### Fixed
- SQLAlchemy ORM metadata caching 문제 (Direct SQL로 우회)
- DB-Model 컬럼 불일치 문제 (primary_image, images, Sprint 0 필드)
- PostgreSQL type casting 문법 오류 (::jsonb → CAST() 사용)

### Statistics
- **총 메뉴**: 260개
- **강화된 메뉴**: 111개 (42.7% coverage)
- **평균 완성도**: 100% (모든 강화 메뉴)
- **고품질 메뉴** (90%+): 111개 (100%)
- **처리 시간**: 28.7분 (Claude API)
- **성공률**: 99.1% (111/112 메뉴)

### Testing
- TC-02 (Menu Detail): ✅ PASS
- TC-10 (Menu List): ✅ PASS
- 통과율: 100% (2/2)

### Documentation
- `DEPLOYMENT_SPRINT2_PHASE1_COMPLETE_20260219.md` - 배포 완료 보고서 (117줄)
- README.md Sprint 2 Phase 1 섹션 추가
- CHANGELOG.md 생성

---

## [v0.1.0] - 2026-02-13

### 🚀 Initial Production Release

**배포 상태**: ✅ 프로덕션 운영 중

### Added

#### Core Features
- Knowledge Graph 기반 메뉴 구조화
- 3단계 매칭 엔진 (정확 매칭 → 유사 검색 → 수식어 분해)
- 수식어 분해 시스템 (54개 수식어 사전)
- CLOVA OCR + GPT-4o 파싱
- Papago 번역 API 통합

#### Database Schema (9 tables)
- `concepts` - 메뉴 개념 트리 (대분류/중분류)
- `modifiers` - 수식어 사전 (크기, 맛, 재료, 조리법 등)
- `canonical_menus` - 표준 메뉴 (112개 시드)
- `menu_variants` - 메뉴 변형
- `menu_relations` - 메뉴 관계
- `shops` - 식당 정보
- `scan_logs` - OCR 로그
- `evidences` - 검증 증거
- `cultural_concepts` - 문화적 맥락

#### API Endpoints
- POST `/api/v1/menu/identify` - 메뉴명 텍스트 입력 매칭
- POST `/api/v1/menu/recognize` - 메뉴판 이미지 OCR + 매칭
- GET `/api/v1/concepts` - 개념 트리 조회
- GET `/api/v1/modifiers` - 수식어 사전 조회
- GET `/api/v1/canonical-menus` - 표준 메뉴 목록 조회
- GET `/health` - 헬스 체크

#### Frontend
- B2C 모바일 웹 (검색 UI)
- B2B 관리자 대시보드 (메뉴판 업로드)

### Infrastructure
- FastAPI + uvicorn (port 8001)
- PostgreSQL 13.23 with pg_trgm extension
- FastComet Managed VPS 배포
- Nginx reverse proxy
- Python venv 환경

### Documentation
- `DEPLOYMENT_FINAL_V0.1.0_20260213.md` - 초기 배포 문서
- `README.md` - 프로젝트 개요
- `CLAUDE.md` - 개발 규칙
- `기획/3차_설계문서_20250211/` - 상세 설계 문서 (7개 파일)

---

## [Unreleased]

### Planned for Sprint 2 Phase 2

#### Image Migration (P0)
- [ ] S3 버킷 생성 및 설정
- [ ] CloudFront CDN 구성
- [ ] 기존 이미지 S3 업로드
- [ ] image_url → primary_image 변환
- [ ] URL 교체 및 검증

#### Content Expansion (P1)
- [ ] 나머지 149개 메뉴 enriched content 생성
- [ ] 배치 단위 Claude API 호출 (50개씩)
- [ ] 자동 재시도 로직
- [ ] 완성도 80%+ 목표

#### UI Components (P1)
- [ ] 메뉴 상세 페이지 개선
- [ ] 이미지 캐러셀 컴포넌트
- [ ] 지역 변종 탭
- [ ] 조리법 단계 표시
- [ ] 영양정보 차트
- [ ] 방문자 팁 섹션

#### Performance Optimization (P2)
- [ ] Redis 캐싱 (API 응답)
- [ ] JSONB 인덱싱 검증
- [ ] 이미지 lazy loading
- [ ] API 응답 시간 < 300ms 목표

---

## Version History

| Version | Date | Description | Status |
|---------|------|-------------|--------|
| **v0.1.1-sprint2-phase1** | 2026-02-19 | Enriched Content & Multi-Image | ✅ Deployed |
| **v0.1.0** | 2026-02-13 | Initial Production Release | ✅ Deployed |
| **v0.0.1** | 2026-02-11 | Project Inception | 📝 Planning |

---

## Notes

### Semantic Versioning

이 프로젝트는 [Semantic Versioning](https://semver.org/)을 따릅니다:

- **MAJOR** (v1.0.0): Breaking changes in API
- **MINOR** (v0.1.0): New features, backward compatible
- **PATCH** (v0.0.1): Bug fixes, backward compatible
- **Sprint Tags** (v0.1.1-sprint2-phase1): Sprint milestone releases

### Git Tags

모든 배포 버전은 Git tag로 표시됩니다:
```bash
git tag -l
# v0.1.0
# v0.1.1-sprint2-phase1
```

### Documentation References

각 버전의 상세 배포 문서:
- v0.1.1-sprint2-phase1: `DEPLOYMENT_SPRINT2_PHASE1_COMPLETE_20260219.md`
- v0.1.0: `DEPLOYMENT_FINAL_V0.1.0_20260213.md`
