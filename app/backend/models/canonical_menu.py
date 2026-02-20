"""
Canonical Menu Model - 표준 메뉴 (핵심 테이블)
"""
from sqlalchemy import Column, String, Integer, SmallInteger, Text, ForeignKey, DateTime, ARRAY, CheckConstraint, Float, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class CanonicalMenu(Base):
    __tablename__ = "canonical_menus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id"))

    # 이름 (다국어)
    name_ko = Column(String(100), nullable=False)
    name_en = Column(String(200), nullable=False)
    name_ja = Column(String(200))
    name_zh_cn = Column(String(200))
    name_zh_tw = Column(String(200))
    romanization = Column(String(200))

    # 설명 (다국어, JSONB)
    # 구조: {"en": "...", "ja": "...", "zh_cn": "...", "zh_tw": "..."}
    explanation_short = Column(JSONB, nullable=False, default={})
    explanation_long = Column(JSONB, default={})
    cultural_context = Column(JSONB, default={})

    # 식재료 & 식이 정보
    # main_ingredients 구조: [{"ko": "돼지등뼈", "en": "pork spine"}, ...]
    main_ingredients = Column(JSONB, default=[])
    allergens = Column(ARRAY(String(50)), default=[])
    dietary_tags = Column(ARRAY(String(50)), default=[])
    spice_level = Column(SmallInteger, default=0)
    serving_style = Column(String(100))

    # 가격 & 이미지
    typical_price_min = Column(Integer)
    typical_price_max = Column(Integer)
    image_url = Column(Text)  # Legacy field - deprecated in favor of primary_image
    image_ai_prompt = Column(Text)

    # Sprint 2 Phase 1: Multi-image and enriched content
    # primary_image 구조: {"url": "...", "source": "...", "license": "...", "attribution": "..."}
    primary_image = Column(JSONB, default=None)
    # images 구조: 배열 [{url, source, license, attribution}, ...]
    images = Column(ARRAY(JSONB), default=None)

    # Long-form descriptions (Sprint 2 Phase 1)
    description_long_ko = Column(Text, default=None)
    description_long_en = Column(Text, default=None)

    # Enriched content fields (Sprint 2 Phase 1)
    # regional_variants 구조: [{"region": "...", "differences": "...", "local_name": "..."}, ...]
    regional_variants = Column(JSONB, default=None)
    # preparation_steps 구조: {"steps": [...], "serving_suggestions": [...], "etiquette": [...]}
    preparation_steps = Column(JSONB, default=None)
    # nutrition_detail 구조: {"calories": 0, "protein": 0.0, "carbs": 0.0, "fat": 0.0, "sodium": 0}
    nutrition_detail = Column(JSONB, default=None)
    # flavor_profile 구조: {"primary": [...], "balance": {"sweet": 0, "salty": 0, "sour": 0, "bitter": 0, "umami": 0}}
    flavor_profile = Column(JSONB, default=None)
    # visitor_tips 구조: {"common_mistakes": [...], "ordering_tips": [...], "pairing": [...]}
    visitor_tips = Column(JSONB, default=None)
    # similar_dishes 구조: [{"name_ko": "...", "name_en": "...", "similarity_reason": "...", "difference": "..."}, ...]
    similar_dishes = Column(ARRAY(JSONB), default=None)

    # Content completeness score (0-100)
    content_completeness = Column(Numeric(5, 2), default=0.00)

    # 난이도 & 신뢰도
    difficulty_score = Column(SmallInteger, default=3)
    difficulty_factors = Column(JSONB, default={})
    ai_confidence = Column(Float, default=0)
    verified_by = Column(String(20), default="ai")

    # Sprint 0: 공공데이터 연동 필드
    standard_code = Column(String(10))  # 메뉴젠 API 음식코드
    category_1 = Column(String(50))  # 정부 분류 대분류
    category_2 = Column(String(50))  # 정부 분류 중분류
    serving_size = Column(String(20))  # 1인분 기준 (예: "300g")
    # nutrition_info 구조: {"energy": 500, "protein": 20.5, "fat": 15.0, ...}
    nutrition_info = Column(JSONB, default={})
    last_nutrition_updated = Column(DateTime(timezone=True))

    # Auto-translation tracking (Sprint 2 Phase 3)
    translation_status = Column(String(20), default="pending")  # pending, completed, failed, partial, disabled
    translation_attempted_at = Column(DateTime(timezone=True))
    translation_error = Column(Text)

    # 벡터 (유사 메뉴 검색용) - v0.2에서 활성화
    # embedding = Column(Vector(1536))  # pgvector

    # 메타
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint("spice_level >= 0 AND spice_level <= 5", name="check_spice_level"),
        CheckConstraint("difficulty_score >= 1 AND difficulty_score <= 5", name="check_difficulty_score"),
        CheckConstraint("ai_confidence >= 0 AND ai_confidence <= 1", name="check_ai_confidence"),
        CheckConstraint("content_completeness >= 0 AND content_completeness <= 100", name="check_content_completeness"),
    )

    # Relationships
    concept = relationship("Concept", backref="canonical_menus")

    def __repr__(self):
        return f"<CanonicalMenu {self.name_ko}>"
