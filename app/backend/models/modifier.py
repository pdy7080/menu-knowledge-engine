"""
Modifier Model - 수식어 사전
"""
from sqlalchemy import Column, String, Integer, SmallInteger, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from database import Base


class Modifier(Base):
    __tablename__ = "modifiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text_ko = Column(String(30), nullable=False, unique=True)
    type = Column(String(30), nullable=False)  # taste, size, emotion, ingredient, cooking, grade, origin
    semantic_key = Column(String(50), nullable=False)  # spicy_variant, large_serving, etc.

    # 번역
    translation_en = Column(String(100))
    translation_ja = Column(String(100))
    translation_zh = Column(String(100))

    # 효과
    affects_spice = Column(SmallInteger)  # +1, +2, -1, null
    affects_size = Column(String(20))  # 'large', 'small', 'double', null
    affects_price = Column(String(20))  # 'premium', 'budget', null

    # 분해 알고리즘용
    priority = Column(Integer, default=10)
    min_length = Column(Integer, default=1)
    is_prefix = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Modifier {self.text_ko} ({self.type})>"
