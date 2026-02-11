"""
Concept Model - 한식 개념 트리 (대분류/중분류)
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_ko = Column(String(100), nullable=False)
    name_en = Column(String(200))
    parent_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id"))
    definition_ko = Column(Text)
    definition_en = Column(Text)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    parent = relationship("Concept", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<Concept {self.name_ko}>"
