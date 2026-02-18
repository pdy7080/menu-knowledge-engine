"""
OCR Service for Menu Image Recognition
Integrates CLOVA OCR API + GPT-4o for menu text extraction
"""

import os
import json
import base64
import uuid
import logging
from typing import List, Dict, Optional
import requests
from openai import OpenAI

from config import settings
from utils.image_preprocessing import preprocess_menu_image

logger = logging.getLogger(__name__)


class OCRService:
    """
    CLOVA OCR + GPT-4o Menu Recognition Pipeline

    Flow:
    1. Image → CLOVA OCR → Raw text
    2. Raw text → GPT-4o → Structured menu items (name, price)
    """

    def __init__(self):
        self.clova_api_url = "https://kko5u71wza.apigw.ntruss.com/custom/v1/33367/0ef5b16de3cdd8fb766e13f6a67a0aeb4b5a2c3c9e5a5b0dd79a1d58fe6e5cf6/general"
        self.clova_secret = settings.CLOVA_OCR_SECRET
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    def recognize_menu_image(
        self,
        image_path: str,
        enable_preprocessing: bool = True
    ) -> Dict:
        """
        Main entry point: Image → Menu items

        Args:
            image_path: Path to menu image file
            enable_preprocessing: Whether to apply image preprocessing (default True)

        Returns:
            {
                "success": bool,
                "menu_items": [{"name_ko": str, "price_ko": str}, ...],
                "raw_text": str,
                "error": str (if failed)
            }
        """
        try:
            # Step 1: Preprocessing (optional)
            if enable_preprocessing:
                try:
                    preprocessed_path = preprocess_menu_image(image_path)
                    ocr_result = self._call_clova_ocr(preprocessed_path)
                except Exception as e:
                    logger.warning(f"Preprocessing failed: {e}, using original")
                    ocr_result = self._call_clova_ocr(image_path)
            else:
                ocr_result = self._call_clova_ocr(image_path)

            if not ocr_result["success"]:
                return ocr_result

            raw_text = ocr_result["text"]

            # Step 2: GPT-4o parsing
            menu_items = self._parse_menu_with_llm(raw_text)

            return {
                "success": True,
                "menu_items": menu_items,
                "raw_text": raw_text,
                "ocr_confidence": ocr_result.get("confidence", 0.0)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "menu_items": []
            }

    def _call_clova_ocr(self, image_path: str) -> Dict:
        """
        Call CLOVA OCR API

        Returns:
            {
                "success": bool,
                "text": str (combined text from all fields),
                "confidence": float,
                "raw_response": dict
            }
        """
        if not self.clova_secret:
            return {
                "success": False,
                "error": "CLOVA_OCR_SECRET not configured"
            }

        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Prepare request
            headers = {
                "X-OCR-SECRET": self.clova_secret,
                "Content-Type": "application/json"
            }

            request_json = {
                "version": "V2",
                "requestId": str(uuid.uuid4()),
                "timestamp": 0,
                "images": [
                    {
                        "format": "jpg",  # Auto-detect in production
                        "name": "menu_image",
                        "data": base64.b64encode(image_data).decode('utf-8')
                    }
                ]
            }

            # Call CLOVA OCR
            response = requests.post(
                self.clova_api_url,
                headers=headers,
                json=request_json,
                timeout=30
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"CLOVA OCR API error: {response.status_code} {response.text}"
                }

            result = response.json()

            # Extract text from OCR result
            text_lines = []
            total_confidence = 0.0
            field_count = 0

            for image in result.get("images", []):
                for field in image.get("fields", []):
                    text_lines.append(field.get("inferText", ""))
                    total_confidence += field.get("inferConfidence", 0.0)
                    field_count += 1

            combined_text = "\n".join(text_lines)
            avg_confidence = total_confidence / field_count if field_count > 0 else 0.0

            return {
                "success": True,
                "text": combined_text,
                "confidence": avg_confidence,
                "raw_response": result
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"CLOVA OCR error: {str(e)}"
            }

    def _parse_menu_with_llm(self, raw_text: str) -> List[Dict]:
        """
        Parse OCR text with GPT-4o to extract menu items

        Args:
            raw_text: Raw OCR text output

        Returns:
            [{"name_ko": str, "price_ko": str}, ...]
        """
        if not self.openai_client:
            # Fallback: Simple regex parsing
            return self._parse_menu_fallback(raw_text)

        try:
            prompt = f"""You are a Korean menu parser. Extract menu items from this OCR text.

OCR Text:
```
{raw_text}
```

Rules:
1. Each menu item has a Korean name and a price (e.g., "8,000원" or "8000")
2. Ignore section headers, descriptions, or non-menu text
3. Return ONLY menu items with clear prices
4. Price format: Keep original format (e.g., "8,000" or "8,000원")

Return JSON array:
[
  {{"name_ko": "김치찌개", "price_ko": "8,000"}},
  {{"name_ko": "순두부찌개", "price_ko": "9,500"}},
  ...
]

If you cannot parse any menu items, return empty array [].
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective for parsing
                messages=[
                    {"role": "system", "content": "You are a precise Korean menu text parser. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON from markdown code block if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            menu_items = json.loads(content)

            # Validate structure
            if not isinstance(menu_items, list):
                return []

            validated_items = []
            for item in menu_items:
                if isinstance(item, dict) and "name_ko" in item:
                    validated_items.append({
                        "name_ko": item["name_ko"],
                        "price_ko": item.get("price_ko", "")
                    })

            return validated_items

        except Exception as e:
            print(f"LLM parsing error: {e}")
            return self._parse_menu_fallback(raw_text)

    def _parse_menu_fallback(self, raw_text: str) -> List[Dict]:
        """
        Fallback: Simple regex-based parsing
        Pattern: Korean text followed by price (숫자,숫자원 or 숫자원)
        """
        import re

        menu_items = []
        lines = raw_text.split("\n")

        # Pattern: Korean menu name + price
        # Example: "김치찌개 8,000원" or "순두부찌개          9,500"
        pattern = r'([가-힣\s]+)\s*([\d,]+)원?'

        for line in lines:
            match = re.search(pattern, line)
            if match:
                name = match.group(1).strip()
                price = match.group(2).strip()

                # Filter out too short names (likely not menu items)
                if len(name) >= 2:
                    menu_items.append({
                        "name_ko": name,
                        "price_ko": price
                    })

        return menu_items


# Singleton instance
ocr_service = OCRService()
