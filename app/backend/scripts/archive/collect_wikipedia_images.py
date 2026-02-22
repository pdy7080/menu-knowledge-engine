"""
Wikipedia Korean Food Images Collector

Collects CC-licensed images from Wikipedia Commons for Korean food dishes.
All images are properly licensed under Creative Commons.

Usage:
    python collect_wikipedia_images.py

Output:
    - data/images/wikipedia/*.jpg
    - data/image_metadata.json (updated)
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import requests
from urllib.parse import quote

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Wikipedia API endpoint
WIKIPEDIA_API = "https://commons.wikimedia.org/w/api.php"

# User agent for API requests (required by Wikimedia)
# Per https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy
# Format: BotName/Version (Contact; Purpose) Library/Version
HEADERS = {
    "User-Agent": "MenuKnowledgeBot/1.0 (Contact: educational.research@example.com; Educational food image collection for non-commercial research) Python-requests/2.31"
}

# Korean food menu items (English names for Wikipedia search)
KOREAN_FOOD_ITEMS = [
    # Soups & Stews
    ("Kimchi-jjigae", "김치찌개"),
    ("Doenjang-jjigae", "된장찌개"),
    ("Sundubu-jjigae", "순두부찌개"),
    ("Budae-jjigae", "부대찌개"),
    ("Haemul-tang", "해물탕"),
    ("Galbi-tang", "갈비탕"),
    ("Seolleongtang", "설렁탕"),
    ("Gomtang", "곰탕"),
    ("Yukgaejang", "육개장"),
    ("Samgyetang", "삼계탕"),
    # Rice Dishes
    ("Bibimbap", "비빔밥"),
    ("Gimbap", "김밥"),
    ("Bokkeumbap", "볶음밥"),
    # Meat
    ("Bulgogi", "불고기"),
    ("Galbi", "갈비"),
    ("Samgyeopsal", "삼겹살"),
    ("Bossam", "보쌈"),
    ("Jokbal", "족발"),
    # Fried/Grilled
    ("Tonkatsu", "돈까스"),
    ("Korean fried chicken", "치킨"),
    # Noodles
    ("Naengmyeon", "냉면"),
    ("Japchae", "잡채"),
    ("Jajangmyeon", "짜장면"),
    ("Jjamppong", "짬뽕"),
    # Side Dishes
    ("Kimchi", "김치"),
    ("Kkakdugi", "깍두기"),
    ("Pajeon", "파전"),
    # Street Food
    ("Tteokbokki", "떡볶이"),
    ("Sundae", "순대"),
    ("Hotteok", "호떡"),
    ("Bungeoppang", "붕어빵"),
]


def search_wikimedia_commons(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search Wikimedia Commons for images related to query.

    Args:
        query: Search term (Korean food name)
        limit: Maximum number of images to retrieve

    Returns:
        List of image metadata dictionaries
    """
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrnamespace": "6",  # File namespace
        "gsrsearch": f"{query} Korean food",
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size",
        "iiurlwidth": 1024,  # Resize to max 1024px width
    }

    try:
        response = requests.get(
            WIKIPEDIA_API, params=params, headers=HEADERS, timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "query" not in data or "pages" not in data["query"]:
            return []

        images = []
        for page in data["query"]["pages"].values():
            if "imageinfo" not in page:
                continue

            imageinfo = page["imageinfo"][0]
            metadata = imageinfo.get("extmetadata", {})

            # Check for CC license
            license_name = metadata.get("LicenseShortName", {}).get("value", "")
            if not any(cc in license_name for cc in ["CC", "Public domain", "PD"]):
                continue  # Skip non-CC licensed images

            images.append(
                {
                    "title": page.get("title", ""),
                    "url": imageinfo.get("url", ""),
                    "thumb_url": imageinfo.get("thumburl", ""),
                    "width": imageinfo.get("width", 0),
                    "height": imageinfo.get("height", 0),
                    "license": license_name,
                    "attribution": metadata.get("Artist", {}).get("value", "Unknown"),
                    "description": metadata.get("ImageDescription", {}).get(
                        "value", ""
                    ),
                    "source": "Wikimedia Commons",
                    "source_url": f"https://commons.wikimedia.org/wiki/{quote(page.get('title', ''))}",
                }
            )

        return images

    except Exception as e:
        print(f"Error searching for '{query}': {e}")
        return []


def download_image(url: str, save_path: Path) -> bool:
    """
    Download image from URL.

    Args:
        url: Image URL
        save_path: Path to save image

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True

    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def collect_wikipedia_images(
    output_dir: Path = Path("data/images/wikipedia"),
    metadata_file: Path = Path("data/image_metadata.json"),
    images_per_item: int = 3,
    max_total: int = 200,
) -> Dict[str, Any]:
    """
    Collect Korean food images from Wikipedia Commons.

    Args:
        output_dir: Directory to save images
        metadata_file: Path to metadata JSON file
        images_per_item: Number of images per food item
        max_total: Maximum total images to collect

    Returns:
        Collection statistics
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load existing metadata
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = {"images": [], "sources": {}}

    collected = 0
    failed = 0
    skipped = 0

    print("Starting Wikipedia image collection...")
    print(f"Target: {max_total} images, {images_per_item} per food item")
    print(f"Output: {output_dir}")
    print("-" * 60)

    for english_name, korean_name in KOREAN_FOOD_ITEMS:
        if collected >= max_total:
            print(f"\nReached maximum total ({max_total}). Stopping.")
            break

        print(f"\nSearching for: {english_name} ({korean_name})")

        # Search for images (use English name for better Wikipedia results)
        images = search_wikimedia_commons(english_name, limit=images_per_item * 2)

        if not images:
            print(f"  No images found for '{english_name}'")
            skipped += 1
            continue

        # Download images
        for i, img in enumerate(images[:images_per_item]):
            if collected >= max_total:
                break

            # Generate filename (use Korean name for file)
            safe_name = korean_name.replace("/", "_").replace("\\", "_")
            filename = f"{safe_name}_{i+1}.jpg"
            filepath = output_dir / filename

            # Skip if already exists
            if filepath.exists():
                print(f"  [SKIP] Already exists: {filename}")
                continue

            # Download
            print(f"  [DOWN] Downloading: {filename}")
            if download_image(img["thumb_url"] or img["url"], filepath):
                # Add to metadata
                metadata["images"].append(
                    {
                        "filename": filename,
                        "path": str(filepath),
                        "menu_name": korean_name,
                        "menu_name_en": english_name,
                        "source": "wikipedia",
                        "license": img["license"],
                        "attribution": img["attribution"],
                        "source_url": img["source_url"],
                        "description": (
                            img["description"][:200] if img["description"] else ""
                        ),
                        "width": img["width"],
                        "height": img["height"],
                    }
                )
                collected += 1
                print(f"  [OK] Success ({collected}/{max_total})")
            else:
                failed += 1
                print("  [FAIL] Download failed")

            # Rate limiting (be respectful to Wikipedia servers)
            time.sleep(2)

    # Update source statistics
    metadata["sources"]["wikipedia"] = {
        "collected": collected,
        "failed": failed,
        "skipped": skipped,
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Save metadata
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("Wikipedia Collection Complete!")
    print(f"[OK] Collected: {collected}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[SKIP] Skipped: {skipped}")
    print(f"[DIR] Output: {output_dir}")
    print(f"[FILE] Metadata: {metadata_file}")
    print("=" * 60)

    return {
        "collected": collected,
        "failed": failed,
        "skipped": skipped,
        "output_dir": str(output_dir),
        "metadata_file": str(metadata_file),
    }


if __name__ == "__main__":
    # Run collection
    stats = collect_wikipedia_images(
        output_dir=Path("C:/project/menu/data/images/wikipedia"),
        metadata_file=Path("C:/project/menu/data/image_metadata.json"),
        images_per_item=3,
        max_total=200,
    )

    print("\nFinal Statistics:")
    print(json.dumps(stats, indent=2))
