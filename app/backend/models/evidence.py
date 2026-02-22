"""
Evidence Model - 출처/근거 추적
"""

from sqlalchemy import Column, String, Text, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from database import Base


class Evidence(Base):
    __tablename__ = "evidences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_type = Column(
        String(30), nullable=False
    )  # canonical, variant, modifier, concept
    target_id = Column(UUID(as_uuid=True), nullable=False)

    source_type = Column(String(30), nullable=False)
    # public_db, ai_discovery, human_review, web_search, user_report
    source_name = Column(String(200))
    source_url = Column(Text)
    content_summary = Column(Text)

    confidence_contribution = Column(Float, default=0)
    ai_model = Column(String(50))  # "gpt-4o", "hyperclova-x"
    ai_prompt_hash = Column(String(64))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Evidence {self.source_type} for {self.target_type}>"
