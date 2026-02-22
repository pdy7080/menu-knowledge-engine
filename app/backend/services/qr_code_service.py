"""
QR Code Service - QR 코드 생성 서비스
"""

import qrcode
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import json
import uuid
import io


class QRCodeService:
    """QR 코드 생성 서비스"""

    def __init__(self, output_dir: str = "static/qr"):
        """
        Args:
            output_dir: QR 코드 저장 경로 (기본: static/qr)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_qr(
        self,
        restaurant_id: uuid.UUID,
        shop_code: str,
        menu_count: int,
        languages: List[str],
    ) -> Dict[str, Any]:
        """
        QR 코드 생성

        Args:
            restaurant_id: 식당 ID
            shop_code: 식당 코드
            menu_count: 승인된 메뉴 수
            languages: 지원 언어 목록 (예: ['ko', 'en', 'ja', 'zh'])

        Returns:
            {
                "qr_code_url": str,          # QR 코드 파일 경로
                "qr_code_data": str,         # QR에 인코딩된 데이터
                "activation_date": str,      # 활성화 일시
                "menu_count": int,
                "languages": List[str]
            }
        """
        # QR 코드에 포함될 데이터
        activation_date = datetime.utcnow().isoformat()

        qr_data = {
            "restaurant_id": str(restaurant_id),
            "shop_code": shop_code,
            "activation_date": activation_date,
            "menu_count": menu_count,
            "languages": languages,
            "qr_url": f"/qr/{shop_code}",  # QR 스캔 시 이동할 URL
        }

        qr_data_str = json.dumps(qr_data, ensure_ascii=False)

        # QR 코드 생성
        qr = qrcode.QRCode(
            version=1,  # 1-40 (크기)
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data_str)
        qr.make(fit=True)

        # 이미지 생성
        img = qr.make_image(fill_color="black", back_color="white")

        # 파일명 생성 (shop_code 기반)
        filename = f"{shop_code}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        file_path = self.output_dir / filename

        # 저장
        img.save(str(file_path))

        # 상대 경로 (웹 서빙용)
        relative_path = f"/static/qr/{filename}"

        return {
            "qr_code_url": relative_path,
            "qr_code_file_path": str(file_path),
            "qr_code_data": qr_data_str,
            "activation_date": activation_date,
            "menu_count": menu_count,
            "languages": languages,
        }

    def generate_qr_bytes(
        self,
        restaurant_id: uuid.UUID,
        shop_code: str,
        menu_count: int,
        languages: List[str],
    ) -> bytes:
        """
        QR 코드를 바이트로 생성 (파일 저장 없이)

        Returns:
            PNG 이미지 바이트
        """
        activation_date = datetime.utcnow().isoformat()

        qr_data = {
            "restaurant_id": str(restaurant_id),
            "shop_code": shop_code,
            "activation_date": activation_date,
            "menu_count": menu_count,
            "languages": languages,
            "qr_url": f"/qr/{shop_code}",
        }

        qr_data_str = json.dumps(qr_data, ensure_ascii=False)

        # QR 코드 생성
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data_str)
        qr.make(fit=True)

        # 이미지 생성
        img = qr.make_image(fill_color="black", back_color="white")

        # 바이트로 변환
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        return img_byte_arr.getvalue()
