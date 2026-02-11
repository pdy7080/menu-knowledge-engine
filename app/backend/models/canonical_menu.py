"""
Canonical Menu Model - 표준 메뉴 (핵심 테이블)
"""
from sqlalchemy import Column, String, Integer, SmallInteger, Text, ForeignKey, DateTime, ARRAY, CheckConstraint, Float
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
    image_url = Column(Text)
    image_ai_prompt = Column(Text)

    # 난이도 & 신뢰도
    difficulty_score = Column(SmallInteger, default=3)
    difficulty_factors = Column(JSONB, default={})
    ai_confidence = Column(Float, default=0)
    verified_by = Column(String(20), default="ai")

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
    )

    # Relationships
    concept = relationship("Concept", backref="canonical_menus")

    def __repr__(self):
        return f"<CanonicalMenu {self.name_ko}>"
