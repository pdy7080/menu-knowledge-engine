"""
Menu Upload Models - B2B 메뉴 일괄 업로드 추적
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from database import Base


class UploadStatus(str, enum.Enum):
    """업로드 작업 상태"""

    pending = "pending"  # 대기 중
    processing = "processing"  # 처리 중
    completed = "completed"  # 완료
    failed = "failed"  # 실패


class MenuItemStatus(str, enum.Enum):
    """개별 메뉴 아이템 상태"""

    success = "success"  # 성공
    failed = "failed"  # 실패
    skipped = "skipped"  # 중복으로 건너뜀


class MenuUploadTask(Base):
    """메뉴 업로드 작업 추적"""

    __tablename__ = "menu_upload_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Restaurant 연결
    restaurant_id = Column(
        UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False
    )

    # 파일 정보
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500))  # 임시 저장 경로 (옵션)
    file_type = Column(String(10))  # csv, json

    # 통계
    total_menus = Column(Integer, default=0)
    successful = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)  # 중복 메뉴

    # 상태
    status = Column(String(20), nullable=False, default=UploadStatus.pending.value)

    # 에러 로그 (JSON 형식)
    error_log = Column(Text)  # JSON string: [{"row": 1, "error": "..."}, ...]

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<MenuUploadTask {self.file_name} ({self.status})>"


class MenuUploadDetail(Base):
    """개별 메뉴 업로드 상세"""

    __tablename__ = "menu_upload_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Upload Task 연결
    upload_task_id = Column(
        UUID(as_uuid=True), ForeignKey("menu_upload_tasks.id"), nullable=False
    )

    # 메뉴 데이터
    name_ko = Column(String(200), nullable=False)
    name_en = Column(String(200))
    description_en = Column(Text)
    price = Column(Integer)

    # 상태
    status = Column(String(20), nullable=False, default=MenuItemStatus.success.value)
    error_message = Column(Text)

    # 생성된 메뉴 ID (성공 시)
    created_menu_id = Column(UUID(as_uuid=True))

    # 메타데이터
    row_number = Column(Integer)  # CSV/JSON의 행 번호
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<MenuUploadDetail {self.name_ko} ({self.status})>"
