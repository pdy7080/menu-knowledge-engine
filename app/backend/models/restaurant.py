"""
Restaurant Model - B2B 식당 정보
"""
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from database import Base


class RestaurantStatus(str, enum.Enum):
    """식당 승인 상태"""
    pending_approval = "pending_approval"  # 승인 대기
    active = "active"                      # 활성화
    inactive = "inactive"                  # 비활성화
    rejected = "rejected"                  # 거부됨


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 기본 정보
    name = Column(String(200), nullable=False)
    name_en = Column(String(200))

    # 사장님 정보
    owner_name = Column(String(100), nullable=False)
    owner_phone = Column(String(20), nullable=False)
    owner_email = Column(String(100))

    # 주소
    address = Column(String(500), nullable=False)
    address_detail = Column(String(200))
    postal_code = Column(String(10))

    # 사업자 정보
    business_license = Column(String(50), unique=True, nullable=False)
    business_type = Column(String(50))  # Korean, Japanese, Chinese, etc.

    # 상태
    status = Column(
        Enum(RestaurantStatus),
        nullable=False,
        default=RestaurantStatus.pending_approval
    )

    # 승인 정보
    approved_at = Column(DateTime(timezone=True))
    approved_by = Column(String(100))  # Admin user ID
    rejection_reason = Column(String(500))

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Restaurant {self.name} ({self.status})>"
