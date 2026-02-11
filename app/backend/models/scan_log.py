"""
Scan Log Model - B2C 스캔 행동 로그
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100))  # 익명 세션
    language = Column(String(10), nullable=False)  # "en", "ja", "zh_cn"

    # 스캔 정보
    image_url = Column(Text)
    ocr_raw_text = Column(Text)
    matched_variant_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    unmatched_texts = Column(ARRAY(Text), default=[])

    # 위치 (대략적)
    area_tag = Column(String(50))
    shop_id = Column(UUID(as_uuid=True), ForeignKey("shops.id"))

    # AI 호출 여부
    ai_called = Column(Boolean, default=False)
    ai_new_entries = Column(Integer, default=0)

    # Admin 관리 (Sprint 3 P1-1)
    status = Column(String(20), default="pending")  # pending, confirmed, rejected
    matched_canonical_id = Column(UUID(as_uuid=True), ForeignKey("canonical_menus.id"))

    # 시간
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    shop = relationship("Shop", backref="scan_logs")
    matched_canonical = relationship("CanonicalMenu", backref="scan_logs")

    def __repr__(self):
        return f"<ScanLog {self.session_id}>"
