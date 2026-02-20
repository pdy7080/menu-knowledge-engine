"""
DALL-E 3 Korean Food Image Generator

Generates high-quality, royalty-free Korean food images using OpenAI's DALL-E 3.
All generated images are owned by us and can be used freely.

Cost: $0.08 per image (1024×1024)
Budget: 60 images = $4.80

Usage:
    python generate_ai_images.py --count 60

Output:
    - data/images/ai_generated/*.png
    - data/image_metadata.json (updated)

Requirements:
    - OPENAI_API_KEY environment variable
    - openai Python package
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import requests
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if env vars are already set


# Top 60 Korean dishes for image generation
KOREAN_DISHES = [
    # Soups & Stews (15)
    ("김치찌개", "Kimchi-jjigae", "Spicy kimchi stew with tofu and pork"),
    ("된장찌개", "Doenjang-jjigae", "Soybean paste stew with vegetables"),
    ("순두부찌개", "Sundubu-jjigae", "Soft tofu stew in hot stone bowl"),
    ("부대찌개", "Budae-jjigae", "Army stew with sausages and instant noodles"),
    ("해물탕", "Haemul-tang", "Spicy seafood hot pot"),
    ("갈비탕", "Galbi-tang", "Beef short rib soup"),
    ("설렁탕", "Seolleongtang", "Milky beef bone soup"),
    ("곰탕", "Gomtang", "Beef bone soup"),
    ("육개장", "Yukgaejang", "Spicy shredded beef soup"),
    ("삼계탕", "Samgyetang", "Ginseng chicken soup"),
    ("뼈해장국", "Ppyeo-haejangguk", "Pork bone hangover soup"),
    ("순대국", "Sundae-guk", "Blood sausage soup"),
    ("콩나물국", "Kongnamul-guk", "Bean sprout soup"),
    ("미역국", "Miyeok-guk", "Seaweed soup"),
    ("떡국", "Tteok-guk", "Rice cake soup"),

    # Rice Dishes (8)
    ("비빔밥", "Bibimbap", "Mixed rice with vegetables and gochujang"),
    ("돌솥비빔밥", "Dolsot bibimbap", "Stone pot bibimbap"),
    ("김밥", "Gimbap", "Korean seaweed rice rolls"),
    ("볶음밥", "Bokkeumbap", "Fried rice"),
    ("제육볶음밥", "Jeyuk bokkeumbap", "Spicy pork fried rice"),
    ("오므라이스", "Omurice", "Omelette rice"),
    ("치즈김밥", "Cheese gimbap", "Gimbap with cheese"),
    ("참치김밥", "Chamchi gimbap", "Tuna gimbap"),

    # Meat Dishes (10)
    ("불고기", "Bulgogi", "Marinated grilled beef"),
    ("갈비", "Galbi", "Grilled beef short ribs"),
    ("삼겹살", "Samgyeopsal", "Grilled pork belly"),
    ("목살", "Moksal", "Pork neck"),
    ("닭갈비", "Dak-galbi", "Spicy stir-fried chicken"),
    ("제육볶음", "Jeyuk-bokkeum", "Spicy stir-fried pork"),
    ("보쌈", "Bossam", "Steamed pork wraps"),
    ("족발", "Jokbal", "Braised pig's trotters"),
    ("순대", "Sundae", "Korean blood sausage"),
    ("양념치킨", "Yangnyeom chicken", "Sweet and spicy fried chicken"),

    # Fried/Grilled (5)
    ("돈까스", "Tonkatsu", "Breaded pork cutlet"),
    ("치킨", "Chikin", "Korean fried chicken"),
    ("생선구이", "Saengseon-gui", "Grilled fish"),
    ("고등어구이", "Godeungeo-gui", "Grilled mackerel"),
    ("삼치구이", "Samchi-gui", "Grilled Spanish mackerel"),

    # Noodles (10)
    ("냉면", "Naengmyeon", "Cold buckwheat noodles"),
    ("막국수", "Makguksu", "Buckwheat noodles"),
    ("칼국수", "Kalguksu", "Hand-cut noodle soup"),
    ("잔치국수", "Janchi-guksu", "Warm noodle soup"),
    ("짜장면", "Jajangmyeon", "Black bean noodles"),
    ("짬뽕", "Jjamppong", "Spicy seafood noodle soup"),
    ("우동", "Udon", "Korean-style udon"),
    ("쫄면", "Jjolmyeon", "Spicy chewy noodles"),
    ("비빔국수", "Bibim-guksu", "Spicy mixed noodles"),
    ("잡채", "Japchae", "Stir-fried glass noodles"),

    # Street Food & Snacks (12)
    ("떡볶이", "Tteokbokki", "Spicy rice cakes"),
    ("순대", "Sundae", "Korean blood sausage"),
    ("오징어튀김", "Ojingeo-twigim", "Fried squid"),
    ("호떡", "Hotteok", "Sweet syrup pancakes"),
    ("붕어빵", "Bungeoppang", "Fish-shaped pastry"),
    ("어묵", "Eomuk", "Fish cake skewers"),
    ("튀김만두", "Twigim mandu", "Fried dumplings"),
    ("군만두", "Gun mandu", "Pan-fried dumplings"),
    ("왕만두", "Wang mandu", "King-sized dumplings"),
    ("파전", "Pajeon", "Green onion pancake"),
    ("김치전", "Kimchijeon", "Kimchi pancake"),
    ("해물파전", "Haemul pajeon", "Seafood and green onion pancake"),
]


def generate_dalle3_prompt(dish_name_ko: str, dish_name_en: str, description: str) -> str:
    """
    Generate DALL-E 3 optimized prompt for Korean food photography.

    Args:
        dish_name_ko: Korean name
        dish_name_en: Romanized name
        description: Dish description

    Returns:
        DALL-E 3 prompt string
    """
    prompt = f"""Professional food photography of {dish_name_en} ({dish_name_ko}), a traditional Korean dish.

{description}.

The dish is beautifully plated in authentic Korean tableware (ceramic bowl or plate).
Studio lighting with soft shadows. Clean white background or wooden table.
Top-down view (bird's eye) or 45-degree angle.
Garnished with sesame seeds, green onions, or other traditional Korean garnishes.
Photorealistic, appetizing, restaurant-quality presentation.
High resolution, sharp focus, vibrant colors."""

    return prompt


def generate_image_dalle3(
    prompt: str,
    filename: str,
    output_dir: Path,
    api_key: str,
    size: str = "1024x1024",
    quality: str = "standard",
) -> Dict[str, Any]:
    """
    Generate image using DALL-E 3 API.

    Args:
        prompt: Image generation prompt
        filename: Output filename
        output_dir: Output directory
        api_key: OpenAI API key
        size: Image size (1024x1024, 1792x1024, 1024x1792)
        quality: Quality (standard or hd)

    Returns:
        Result dictionary with status and metadata
    """
    try:
        import openai

        client = openai.OpenAI(api_key=api_key)

        # Generate image
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )

        image_url = response.data[0].url

        # Download image
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()

        # Save image
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename

        with open(filepath, 'wb') as f:
            f.write(img_response.content)

        return {
            "success": True,
            "filepath": str(filepath),
            "url": image_url,
            "revised_prompt": response.data[0].revised_prompt,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def generate_korean_food_images(
    output_dir: Path = Path("data/images/ai_generated"),
    metadata_file: Path = Path("data/image_metadata.json"),
    count: int = 60,
    api_key: str = None,
) -> Dict[str, Any]:
    """
    Generate Korean food images using DALL-E 3.

    Args:
        output_dir: Output directory
        metadata_file: Metadata JSON file path
        count: Number of images to generate
        api_key: OpenAI API key

    Returns:
        Generation statistics
    """
    # Get API key
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("[ERROR] OPENAI_API_KEY environment variable not set!")
        print("Please set it: export OPENAI_API_KEY=sk-...")
        return {
            "generated": 0,
            "failed": 0,
            "error": "Missing API key",
        }

    # Load existing metadata
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = {"images": [], "sources": {}}

    output_dir.mkdir(parents=True, exist_ok=True)

    generated = 0
    failed = 0
    total_cost = 0.0

    print("=" * 60)
    print("DALL-E 3 Korean Food Image Generator")
    print("=" * 60)
    print(f"Target: {count} images")
    print(f"Cost per image: $0.08 (1024×1024, standard quality)")
    print(f"Estimated total cost: ${count * 0.08:.2f}")
    print(f"Output: {output_dir}")
    print("-" * 60)

    dishes_to_generate = KOREAN_DISHES[:count]

    for i, (name_ko, name_en, description) in enumerate(dishes_to_generate, 1):
        if generated >= count:
            break

        print(f"\n[{i}/{count}] Generating: {name_ko} ({name_en})")

        # Generate filename
        safe_name = name_ko.replace("/", "_").replace("\\", "_")
        filename = f"{safe_name}_ai.png"
        filepath = output_dir / filename

        # Skip if exists
        if filepath.exists():
            print(f"  [SKIP] Already exists")
            continue

        # Generate prompt
        prompt = generate_dalle3_prompt(name_ko, name_en, description)
        print(f"  [PROMPT] {prompt[:100]}...")

        # Generate image
        print(f"  [GEN] Calling DALL-E 3 API...")
        result = generate_image_dalle3(
            prompt=prompt,
            filename=filename,
            output_dir=output_dir,
            api_key=api_key,
        )

        if result["success"]:
            # Add to metadata
            metadata["images"].append({
                "filename": filename,
                "path": str(filepath),
                "menu_name": name_ko,
                "menu_name_en": name_en,
                "description": description,
                "source": "dalle3",
                "model": "dall-e-3",
                "size": "1024x1024",
                "quality": "standard",
                "original_prompt": prompt,
                "revised_prompt": result.get("revised_prompt", ""),
                "generated_at": datetime.now().isoformat(),
                "cost_usd": 0.08,
            })

            generated += 1
            total_cost += 0.08
            print(f"  [OK] Generated successfully (Cost: $0.08, Total: ${total_cost:.2f})")

        else:
            failed += 1
            print(f"  [FAIL] {result.get('error', 'Unknown error')}")

        # Rate limiting (DALL-E 3: 5 requests/min for tier 1)
        if i < count:
            print(f"  [WAIT] Cooling down (rate limit)...")
            time.sleep(15)  # 4 images per minute

    # Update metadata
    metadata["sources"]["dalle3"] = {
        "generated": generated,
        "failed": failed,
        "total_cost_usd": total_cost,
        "last_updated": datetime.now().isoformat(),
    }

    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("DALL-E 3 Generation Complete!")
    print(f"[OK] Generated: {generated}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[COST] Total cost: ${total_cost:.2f}")
    print(f"[DIR] Output: {output_dir}")
    print(f"[FILE] Metadata: {metadata_file}")
    print("=" * 60)

    return {
        "generated": generated,
        "failed": failed,
        "total_cost_usd": total_cost,
        "output_dir": str(output_dir),
        "metadata_file": str(metadata_file),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Korean food images using DALL-E 3")
    parser.add_argument("--count", type=int, default=60, help="Number of images to generate")
    parser.add_argument("--output", type=str, default="C:/project/menu/data/images/ai_generated",
                        help="Output directory")
    parser.add_argument("--metadata", type=str, default="C:/project/menu/data/image_metadata.json",
                        help="Metadata JSON file")

    args = parser.parse_args()

    stats = generate_korean_food_images(
        output_dir=Path(args.output),
        metadata_file=Path(args.metadata),
        count=args.count,
    )

    print(f"\nFinal Statistics:")
    print(json.dumps(stats, indent=2))
