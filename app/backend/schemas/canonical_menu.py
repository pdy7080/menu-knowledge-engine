"""
Pydantic schemas for CanonicalMenu API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class CanonicalMenuCreate(BaseModel):
    """Request schema for creating a new canonical menu"""

    # Required fields
    concept_id: UUID = Field(..., description="Concept ID (foreign key)")
    name_ko: str = Field(..., min_length=1, max_length=100, description="Korean name")
    name_en: str = Field(..., min_length=1, max_length=200, description="English name")
    explanation_short_en: str = Field(..., min_length=1, description="Short English description")

    # Optional multi-language names
    name_ja: Optional[str] = Field(None, max_length=200, description="Japanese name")
    name_zh_cn: Optional[str] = Field(None, max_length=200, description="Simplified Chinese name")
    name_zh_tw: Optional[str] = Field(None, max_length=200, description="Traditional Chinese name")
    romanization: Optional[str] = Field(None, max_length=200, description="Romanization")

    # Optional metadata
    main_ingredients: Optional[List[Dict[str, str]]] = Field(None, description="Main ingredients")
    allergens: Optional[List[str]] = Field(None, description="Allergens")
    dietary_tags: Optional[List[str]] = Field(None, description="Dietary tags")
    spice_level: Optional[int] = Field(0, ge=0, le=5, description="Spice level (0-5)")
    serving_style: Optional[str] = Field(None, description="Serving style")
    typical_price_min: Optional[int] = Field(None, description="Minimum price")
    typical_price_max: Optional[int] = Field(None, description="Maximum price")

    class Config:
        json_schema_extra = {
            "example": {
                "concept_id": "550e8400-e29b-41d4-a716-446655440000",
                "name_ko": "김치찌개",
                "name_en": "Kimchi Jjigae",
                "explanation_short_en": "Spicy kimchi stew with pork and tofu",
                "spice_level": 3,
                "main_ingredients": [
                    {"ko": "김치", "en": "kimchi"},
                    {"ko": "돼지고기", "en": "pork"},
                    {"ko": "두부", "en": "tofu"}
                ],
                "typical_price_min": 7000,
                "typical_price_max": 12000
            }
        }


class CanonicalMenuResponse(BaseModel):
    """Response schema for canonical menu creation/retrieval"""

    id: UUID
    name_ko: str
    name_en: str
    name_ja: Optional[str] = None
    name_zh_cn: Optional[str] = None
    name_zh_tw: Optional[str] = None
    romanization: Optional[str] = None

    concept_id: Optional[UUID] = None
    explanation_short: Dict[str, Any] = {}

    # Translation status
    translation_status: str = "pending"
    translation_attempted_at: Optional[datetime] = None

    # Metadata
    spice_level: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name_ko": "김치찌개",
                "name_en": "Kimchi Jjigae",
                "name_ja": None,
                "name_zh_cn": None,
                "explanation_short": {"en": "Spicy kimchi stew with pork and tofu"},
                "translation_status": "pending",
                "spice_level": 3
            }
        }


class TranslateRequest(BaseModel):
    """Request schema for manual re-translation"""
    status_filter: Optional[str] = Field("failed", description="Filter by status (failed, pending, all)")

    class Config:
        json_schema_extra = {
            "example": {
                "status_filter": "failed"
            }
        }
