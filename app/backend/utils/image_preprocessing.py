"""
Image preprocessing utilities for OCR accuracy improvement.

Uses OpenCV for:
- Auto rotation (text orientation detection)
- Contrast enhancement (CLAHE)
- Noise removal (Gaussian blur)
"""

import os
import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def auto_rotate_image(image: np.ndarray) -> np.ndarray:
    """
    Detect text orientation and rotate image for optimal OCR.

    Tries 0, 90, 180, 270 degree rotations and picks the one
    with the most horizontal text lines (detected via edge analysis).

    Args:
        image: Input image as numpy array (BGR)

    Returns:
        Rotated image as numpy array (BGR)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    best_angle = 0
    best_score = _score_text_orientation(gray)

    for angle in [90, 180, 270]:
        rotated = _rotate_90(gray, angle)
        score = _score_text_orientation(rotated)
        if score > best_score:
            best_score = score
            best_angle = angle

    if best_angle == 0:
        return image

    logger.info(f"Auto-rotating image by {best_angle} degrees")
    return _rotate_90(image, best_angle)


def _rotate_90(image: np.ndarray, angle: int) -> np.ndarray:
    """Rotate image by 90, 180, or 270 degrees."""
    if angle == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    elif angle == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image


def _score_text_orientation(gray: np.ndarray) -> float:
    """
    Score how well text is horizontally aligned.

    Uses Sobel edge detection to count horizontal vs vertical edges.
    Higher score = more horizontal text lines = correct orientation.
    """
    # Detect horizontal edges (text lines appear as horizontal features)
    sobel_h = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    # Detect vertical edges
    sobel_v = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)

    h_energy = np.sum(np.abs(sobel_h))
    v_energy = np.sum(np.abs(sobel_v))

    # Horizontal text has more horizontal edge energy
    if v_energy == 0:
        return 0.0
    return h_energy / v_energy


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast using CLAHE algorithm.

    CLAHE (Contrast Limited Adaptive Histogram Equalization) improves
    local contrast, making text more readable even in uneven lighting.

    Args:
        image: Input image as numpy array (BGR)

    Returns:
        Contrast-enhanced image as numpy array (BGR)
    """
    # Convert to LAB color space for luminance-only enhancement
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    # Apply CLAHE to luminance channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_l = clahe.apply(l_channel)

    # Merge back
    enhanced_lab = cv2.merge([enhanced_l, a_channel, b_channel])
    enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    return enhanced_bgr


def remove_noise(image: np.ndarray) -> np.ndarray:
    """
    Remove noise using Gaussian blur.

    Args:
        image: Input image as numpy array (BGR)

    Returns:
        Denoised image as numpy array (BGR)
    """
    return cv2.GaussianBlur(image, (3, 3), 0)


def preprocess_menu_image(image_path: str) -> str:
    """
    Full preprocessing pipeline for menu images.

    Pipeline:
    1. Load image
    2. Auto-rotate for correct text orientation
    3. Enhance contrast (CLAHE)
    4. Remove noise (Gaussian blur)
    5. Save preprocessed image

    Args:
        image_path: Path to the original menu image

    Returns:
        Path to the preprocessed image ({original}_preprocessed.jpg)

    Raises:
        FileNotFoundError: If image_path does not exist
        ValueError: If image cannot be loaded by OpenCV
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Step 1: Load
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")

    logger.info(f"Preprocessing image: {image_path} ({image.shape})")

    # Step 2: Auto-rotate
    image = auto_rotate_image(image)

    # Step 3: Enhance contrast
    image = enhance_contrast(image)

    # Step 4: Remove noise
    image = remove_noise(image)

    # Step 5: Save
    base, ext = os.path.splitext(image_path)
    output_path = f"{base}_preprocessed.jpg"
    cv2.imwrite(output_path, image)

    logger.info(f"Preprocessed image saved: {output_path}")
    return output_path
