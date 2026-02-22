"""
S3/R2 Uploader Utility - CloudFlare R2 및 AWS S3 호환 스토리지 클라이언트
Sprint 2 Phase 2

CloudFlare R2:
  - S3 호환 API (boto3 사용 가능)
  - egress 비용 없음
  - endpoint: https://<ACCOUNT_ID>.r2.cloudflarestorage.com
  - 공개 접근: R2 Public Bucket URL 또는 Custom Domain

AWS S3:
  - endpoint: None (기본 AWS 엔드포인트)
  - 공개 접근: ACL public-read 또는 CloudFront

설정 (.env):
  R2_ACCOUNT_ID=your_cloudflare_account_id
  R2_ACCESS_KEY_ID=your_r2_access_key
  R2_SECRET_ACCESS_KEY=your_r2_secret_key
  R2_BUCKET_NAME=menu-images
  R2_PUBLIC_URL=https://pub-xxx.r2.dev  (R2 Public Bucket URL)
"""

import os
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, Tuple
import mimetypes
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class S3Uploader:
    """
    S3/R2 호환 스토리지 업로더

    Usage (R2):
        uploader = S3Uploader()  # .env에서 R2 설정 자동 로드
        url = uploader.upload_image("local.jpg", "menu-images/kimchi.jpg")

    Usage (AWS S3):
        uploader = S3Uploader(provider="s3")
        url = uploader.upload_image("local.jpg", "menu-images/kimchi.jpg")
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        bucket_name: Optional[str] = None,
        account_id: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        public_url: Optional[str] = None,
        region: Optional[str] = None,
    ):
        """
        Initialize storage client

        Args:
            provider: "r2" (default) or "s3"
            bucket_name: Bucket name
            account_id: CloudFlare Account ID (R2 only)
            access_key: Access key
            secret_key: Secret key
            public_url: Public URL base (R2 public bucket URL)
            region: AWS region (S3 only, default: ap-northeast-2)
        """
        self.provider = provider or os.getenv("STORAGE_PROVIDER", "r2")
        self.bucket_name = (
            bucket_name or os.getenv("R2_BUCKET_NAME") or os.getenv("MENU_S3_BUCKET")
        )

        if not self.bucket_name:
            raise ValueError(
                "Bucket name not provided. Set R2_BUCKET_NAME or MENU_S3_BUCKET env variable."
            )

        if self.provider == "r2":
            self._init_r2(account_id, access_key, secret_key, public_url)
        else:
            self._init_s3(access_key, secret_key, region)

    def _init_r2(self, account_id, access_key, secret_key, public_url):
        """CloudFlare R2 클라이언트 초기화"""
        account_id = account_id or os.getenv("R2_ACCOUNT_ID")
        access_key = access_key or os.getenv("R2_ACCESS_KEY_ID")
        secret_key = secret_key or os.getenv("R2_SECRET_ACCESS_KEY")
        self.public_url = (public_url or os.getenv("R2_PUBLIC_URL", "")).rstrip("/")

        if not account_id:
            raise ValueError("R2_ACCOUNT_ID not set")

        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=BotoConfig(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "adaptive"},
            ),
            region_name="auto",
        )

        # R2 public bucket URL 또는 endpoint 기반
        if not self.public_url:
            self.public_url = f"{endpoint_url}/{self.bucket_name}"

        self.base_url = self.public_url

    def _init_s3(self, access_key, secret_key, region):
        """AWS S3 클라이언트 초기화"""
        self.region = region or os.getenv("AWS_REGION", "ap-northeast-2")

        session_kwargs = {"region_name": self.region}
        if access_key and secret_key:
            session_kwargs["aws_access_key_id"] = access_key
            session_kwargs["aws_secret_access_key"] = secret_key

        self.s3_client = boto3.client("s3", **session_kwargs)
        self.base_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com"
        self.public_url = self.base_url

    def upload_image(
        self,
        file_path: str,
        s3_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        이미지 파일 업로드

        Args:
            file_path: 로컬 파일 경로
            s3_key: 스토리지 키 (예: "menu-images/kimchi.jpg")
            content_type: MIME 타입 (자동 감지)
            metadata: 커스텀 메타데이터

        Returns:
            Public URL
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if content_type is None:
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = "application/octet-stream"

        extra_args = {"ContentType": content_type}

        # R2는 ACL 미지원, S3는 public-read 설정
        if self.provider == "s3":
            extra_args["ACL"] = "public-read"

        if metadata:
            extra_args["Metadata"] = metadata

        try:
            self.s3_client.upload_file(
                file_path, self.bucket_name, s3_key, ExtraArgs=extra_args
            )
            url = f"{self.base_url}/{s3_key}"
            logger.info(f"Uploaded: {file_path} -> {url}")
            return url

        except NoCredentialsError:
            logger.error("Credentials not found")
            raise
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            raise

    def upload_bytes(
        self,
        data: bytes,
        s3_key: str,
        content_type: str = "image/jpeg",
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """바이트 데이터 직접 업로드"""
        put_kwargs = {
            "Bucket": self.bucket_name,
            "Key": s3_key,
            "Body": data,
            "ContentType": content_type,
        }

        if metadata:
            put_kwargs["Metadata"] = metadata

        try:
            self.s3_client.put_object(**put_kwargs)
            url = f"{self.base_url}/{s3_key}"
            logger.info(f"Uploaded bytes -> {url}")
            return url
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            raise

    def delete_file(self, s3_key: str) -> bool:
        """파일 삭제"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            logger.error(f"Delete failed: {e}")
            return False

    def file_exists(self, s3_key: str) -> bool:
        """파일 존재 확인"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False

    def list_files(self, prefix: str = "", max_keys: int = 1000) -> list:
        """파일 목록 조회"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix, MaxKeys=max_keys
            )
            return [obj["Key"] for obj in response.get("Contents", [])]
        except ClientError as e:
            logger.error(f"List failed: {e}")
            return []

    def generate_menu_key(
        self, menu_name_ko: str, source: str = "wiki", ext: str = ".jpg"
    ) -> str:
        """
        메뉴용 스토리지 키 생성

        Args:
            menu_name_ko: 한글 메뉴명
            source: 이미지 소스 (wiki, ai, public)
            ext: 파일 확장자

        Returns:
            키 (예: "menu-images/wiki/김치찌개.jpg")
        """
        import re

        clean_name = re.sub(r"[^\w가-힣\-_]", "", menu_name_ko)
        return f"menu-images/{source}/{clean_name}{ext}"

    def get_public_url(self, s3_key: str) -> str:
        """스토리지 키의 공개 URL 반환"""
        return f"{self.base_url}/{s3_key}"


# Convenience function
def upload_menu_image(
    file_path: str,
    menu_name_ko: str,
    source: str = "upload",
) -> Tuple[str, Dict]:
    """
    메뉴 이미지 업로드 편의 함수

    Args:
        file_path: 로컬 이미지 경로
        menu_name_ko: 한글 메뉴명
        source: 이미지 소스

    Returns:
        (url, metadata)
    """
    uploader = get_s3_uploader()
    s3_key = uploader.generate_menu_key(menu_name_ko, source)
    url = uploader.upload_image(
        file_path, s3_key, metadata={"menu_name": menu_name_ko, "source": source}
    )
    metadata = {
        "url": url,
        "s3_key": s3_key,
        "source": source,
        "uploaded_at": datetime.now().isoformat(),
    }
    return url, metadata


# Singleton
_uploader_instance = None


def get_s3_uploader() -> S3Uploader:
    """싱글톤 S3Uploader 인스턴스"""
    global _uploader_instance
    if _uploader_instance is None:
        _uploader_instance = S3Uploader()
    return _uploader_instance
