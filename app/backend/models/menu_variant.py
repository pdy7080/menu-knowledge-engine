"""
Menu Variant Model - 실제 식당 메뉴 변형
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
    ARRAY,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class MenuVariant(Base):
    __tablename__ = "menu_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_id = Column(
        UUID(as_uuid=True), ForeignKey("canonical_menus.id"), nullable=False
    )
    canonical_menu_id = Column(
        UUID(as_uuid=True), ForeignKey("canonical_menus.id")
    )  # Alias for QR menu
    shop_id = Column(UUID(as_uuid=True), ForeignKey("shops.id"))

    # 실제 표시 이름
    display_name_ko = Column(String(200), nullable=False)
    menu_name_ko = Column(String(200))  # Alias for compatibility
    display_name_original = Column(Text)  # OCR 원본 텍스트

    # 수식어 연결
    modifier_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    # decomposition 구조: {"modifiers": ["왕", "얼큰"], "base": "뼈해장국", "method": "auto"}
    decomposition = Column(JSONB, default={})

    # 식당별 정보
    price = Column(Integer)
    price_display = Column(String(50))  # "15,000원" for QR menu
    description_ko = Column(Text)
    is_popular = Column(Boolean, default=False)
    is_seasonal = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)  # QR menu filter
    display_order = Column(Integer, default=0)  # QR menu sorting

    # 출처 & 신뢰도
    source = Column(String(30), nullable=False)  # b2b_upload, b2c_scan, manual, crawl
    ai_match_confidence = Column(Float, default=0)
    human_verified = Column(Boolean, default=False)

    # 메타
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    scan_count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    canonical_menu = relationship(
        "CanonicalMenu",
        foreign_keys=[canonical_menu_id],  # Specify which FK to use
        backref="variants",
    )
    shop = relationship("Shop", backref="menu_variants")

    def __repr__(self):
        return f"<MenuVariant {self.display_name_ko}>"
