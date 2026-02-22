"""
Image validation utilities
"""

from PIL import Image
import io
from typing import Tuple

# Allowed formats
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DIMENSIONS = (4096, 4096)  # 4K


class ImageValidationError(Exception):
    """Custom exception for image validation failures"""

    pass


def validate_image(file_bytes: bytes) -> Tuple[str, int, int]:
    """
    Validate uploaded image

    Returns:
        (format, width, height)

    Raises:
        ImageValidationError: If validation fails
    """
    # 1. Check file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ImageValidationError(
            f"File too large: {len(file_bytes)} bytes (max: {MAX_FILE_SIZE})"
        )

    # 2. Try to open as image
    try:
        img = Image.open(io.BytesIO(file_bytes))
    except Exception as e:
        raise ImageValidationError(f"Invalid image file: {e}")

    # 3. Check format
    if img.format not in ALLOWED_FORMATS:
        raise ImageValidationError(
            f"Unsupported format: {img.format}. Allowed: {ALLOWED_FORMATS}"
        )

    # 4. Check dimensions
    width, height = img.size
    if width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]:
        raise ImageValidationError(
            f"Image too large: {width}x{height} (max: {MAX_DIMENSIONS[0]}x{MAX_DIMENSIONS[1]})"
        )

    return img.format, width, height
