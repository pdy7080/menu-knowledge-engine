"""
Shop Model - 식당 정보
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, Float, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from database import Base


class Shop(Base):
    __tablename__ = "shops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_code = Column(String(50), unique=True)  # QR code identifier
    name_ko = Column(String(200), nullable=False)
    name_en = Column(String(200))

    # 위치
    address_ko = Column(Text)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    area_tag = Column(String(50))  # "명동", "홍대", "성수"

    # 외부 연동
    seongsuya_id = Column(String(50))
    naver_place_id = Column(String(50))
    google_place_id = Column(String(50))

    # 메뉴 현황
    menu_count = Column(Integer, default=0)
    has_multilingual = Column(Boolean, default=False)
    difficulty_avg = Column(Float)

    # QR
    qr_page_url = Column(Text)
    qr_page_generated_at = Column(DateTime(timezone=True))

    # 출처
    source = Column(String(30))  # seongsuya, b2c_discover, manual
    status = Column(String(20), default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Shop {self.name_ko}>"
