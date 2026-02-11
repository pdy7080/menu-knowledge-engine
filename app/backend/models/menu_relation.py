"""
Menu Relation Model - 메뉴 간 관계
"""
from sqlalchemy import Column, String, Boolean, Text, Float, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from database import Base


class MenuRelation(Base):
    __tablename__ = "menu_relations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    relation_type = Column(String(30), nullable=False)
    # similar_to, often_confused_with, served_with, evolved_from, regional_variant, cooking_variant

    from_type = Column(String(30), nullable=False)  # 'canonical' or 'concept'
    from_id = Column(UUID(as_uuid=True), nullable=False)
    to_type = Column(String(30), nullable=False)
    to_id = Column(UUID(as_uuid=True), nullable=False)

    is_bidirectional = Column(Boolean, default=True)
    description_ko = Column(Text)
    description_en = Column(Text)
    strength = Column(Float, default=0.5)  # 관계 강도 (0~1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "relation_type",
            "from_type",
            "from_id",
            "to_type",
            "to_id",
            name="uq_menu_relation",
        ),
    )

    def __repr__(self):
        return f"<MenuRelation {self.relation_type}>"
