"""
Cultural Concept Model - 식당 문화 개념 (반찬, 곱빼기 등)
"""
from sqlalchemy import Column, String, Integer, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from database import Base


class CulturalConcept(Base):
    __tablename__ = "cultural_concepts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_ko = Column(String(100), nullable=False)
    name_en = Column(String(200))
    type = Column(String(30), nullable=False)  # ordering, serving, payment, etiquette

    # 설명 (다국어)
    # 구조: {"en": "...", "ja": "...", "zh_cn": "..."}
    explanation = Column(JSONB, nullable=False, default={})

    related_menu_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    icon = Column(String(10))  # 이모지
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<CulturalConcept {self.name_ko}>"
