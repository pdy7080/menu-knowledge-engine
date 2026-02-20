# Image Collection Scripts

Korean food image collection system for Menu Knowledge Engine.

## Overview

This directory contains scripts for collecting, generating, and managing Korean food images.

### Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `collect_wikipedia_images.py` | Collect CC-licensed images from Wikipedia Commons | ⚠️ Blocked (403 API errors) |
| `collect_public_data_images.py` | Collect from Korean public data portal | ⏸️ Not implemented (requires API registration) |
| `collect_naver_images.py` | Placeholder (copyright warning) | ❌ Illegal (copyright violation) |
| `generate_ai_images.py` | Generate images using DALL-E 3 | ✅ Ready to use |
| `merge_images_to_s3.py` | Merge and upload images | ✅ Ready (local storage) |

## Recommended Approach

Given API limitations and licensing constraints, we recommend:

### Option 1: DALL-E 3 Generation (Recommended)

**Pros:**
- No licensing issues (we own the images)
- Immediate access (no API registration)
- Customizable (exact dishes we need)
- Cost-effective ($4.80 for 60 images)
- Consistent quality

**Cons:**
- AI-generated (not real food photos)
- API costs

**Usage:**
```bash
# Set API key
export OPENAI_API_KEY=sk-...

# Generate 60 images
python generate_ai_images.py --count 60

# Cost: $0.08/image × 60 = $4.80
```

### Option 2: Wikipedia Commons (Blocked)

**Status:** ❌ Currently blocked with 403 errors

**Issues:**
- Wikipedia API returns 403 Forbidden
- Requires proper API registration
- Rate limiting restrictions
- Licensing verification needed

**If unblocked:**
```bash
python collect_wikipedia_images.py
```

### Option 3: Public Data Portal (Not Implemented)

**Status:** ⏸️ Requires registration at data.go.kr

**Steps to implement:**
1. Register at https://www.data.go.kr/
2. Request API access for food/nutrition datasets
3. Get API key
4. Implement API integration

### Option 4: Manual Collection

**Alternative approach:**
1. Find public domain/CC0 Korean food images manually
2. Download and organize in `data/images/manual/`
3. Update metadata manually

## Quick Start

### 1. Generate AI Images (Recommended)

```bash
# Install dependencies
pip install openai requests

# Set OpenAI API key
export OPENAI_API_KEY=sk-...

# Generate 60 Korean food images
cd C:\project\menu
python app/backend/scripts/generate_ai_images.py --count 60

# Output:
# - data/images/ai_generated/*.png (60 images)
# - data/image_metadata.json (metadata)
```

### 2. Merge Images

```bash
# Merge all images to single directory
python app/backend/scripts/merge_images_to_s3.py --storage local

# Output:
# - data/images/merged/*.png (all images)
```

### 3. Upload to Backend (Future)

```bash
# When S3 is set up
python app/backend/scripts/merge_images_to_s3.py --storage s3 --bucket menu-knowledge-images
```

## Generated Image Details

### DALL-E 3 Prompt Strategy

Each image is generated with:
- Professional food photography style
- Authentic Korean tableware
- Studio lighting with soft shadows
- Top-down or 45-degree angle
- Traditional Korean garnishes
- Photorealistic quality

### Example Prompt

```
Professional food photography of Kimchi-jjigae (김치찌개), a traditional Korean dish.

Spicy kimchi stew with tofu and pork.

The dish is beautifully plated in authentic Korean tableware (ceramic bowl or plate).
Studio lighting with soft shadows. Clean white background or wooden table.
Top-down view (bird's eye) or 45-degree angle.
Garnished with sesame seeds, green onions, or other traditional Korean garnishes.
Photorealistic, appetizing, restaurant-quality presentation.
High resolution, sharp focus, vibrant colors.
```

### Top 60 Korean Dishes Covered

**Soups & Stews (15):**
김치찌개, 된장찌개, 순두부찌개, 부대찌개, 해물탕, 갈비탕, 설렁탕, 곰탕, 육개장, 삼계탕, 뼈해장국, 순대국, 콩나물국, 미역국, 떡국

**Rice Dishes (8):**
비빔밥, 돌솥비빔밥, 김밥, 볶음밥, 제육볶음밥, 오므라이스, 치즈김밥, 참치김밥

**Meat Dishes (10):**
불고기, 갈비, 삼겹살, 목살, 닭갈비, 제육볶음, 보쌈, 족발, 순대, 양념치킨

**Fried/Grilled (5):**
돈까스, 치킨, 생선구이, 고등어구이, 삼치구이

**Noodles (10):**
냉면, 막국수, 칼국수, 잔치국수, 짜장면, 짬뽕, 우동, 쫄면, 비빔국수, 잡채

**Street Food (12):**
떡볶이, 순대, 오징어튀김, 호떡, 붕어빵, 어묵, 튀김만두, 군만두, 왕만두, 파전, 김치전, 해물파전

## Metadata Structure

```json
{
  "images": [
    {
      "filename": "김치찌개_ai.png",
      "path": "C:/project/menu/data/images/ai_generated/김치찌개_ai.png",
      "menu_name": "김치찌개",
      "menu_name_en": "Kimchi-jjigae",
      "description": "Spicy kimchi stew with tofu and pork",
      "source": "dalle3",
      "model": "dall-e-3",
      "size": "1024x1024",
      "quality": "standard",
      "original_prompt": "...",
      "revised_prompt": "...",
      "generated_at": "2026-02-18T10:30:00",
      "cost_usd": 0.08
    }
  ],
  "sources": {
    "dalle3": {
      "generated": 60,
      "failed": 0,
      "total_cost_usd": 4.80,
      "last_updated": "2026-02-18T12:00:00"
    }
  }
}
```

## Cost Breakdown

### DALL-E 3 Pricing

| Size | Quality | Price | Recommended |
|------|---------|-------|-------------|
| 1024×1024 | Standard | $0.080/image | ✅ Yes |
| 1024×1024 | HD | $0.120/image | ❌ Too expensive |
| 1792×1024 | Standard | $0.120/image | ❌ Overkill |

**For 60 images:** 60 × $0.08 = **$4.80 total**

## Troubleshooting

### Wikipedia API 403 Error

**Problem:** `403 Client Error: Forbidden`

**Cause:** Missing/invalid User-Agent or rate limiting

**Fix attempts:**
1. ✅ Added proper User-Agent header
2. ✅ Increased delay between requests (2s)
3. ✅ Used English search terms
4. ❌ Still blocked

**Solution:** Use DALL-E 3 instead

### DALL-E 3 Rate Limits

**Tier 1:** 5 requests/minute

**Script behavior:**
- 15-second delay between requests = 4 images/minute
- 60 images = ~15 minutes total

### Unicode Encoding Error (Windows)

**Problem:** `UnicodeEncodeError: 'cp949' codec can't encode character`

**Fix:**
```python
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
```

## Future Enhancements

### Phase 2 (v0.2)

1. **S3 Integration**
   - Implement boto3 upload
   - Configure CloudFront CDN
   - Add image optimization (WebP conversion)

2. **Image Quality Check**
   - Verify image dimensions
   - Check for corruption
   - Remove duplicates

3. **Batch Processing**
   - Parallel downloads
   - Resume interrupted sessions
   - Progress tracking

4. **Image Augmentation**
   - Cropping/resizing
   - Format conversion
   - Watermarking

## License Information

### DALL-E 3 Images

- **Copyright:** Owned by us (Menu Knowledge Engine)
- **License:** Can be used freely in our application
- **Attribution:** Not required
- **Commercial use:** Allowed

### Wikipedia Commons Images

- **License:** CC BY-SA 3.0/4.0 or Public Domain
- **Attribution:** Required (artist name + link)
- **Commercial use:** Depends on specific license
- **Derivatives:** Must share under same license (SA)

## Contact

For questions about image collection:
- See: `C:\project\menu\PHASE_1_COMPREHENSIVE_PLAN_20260218.md`
- Team: image-collector (this agent)
