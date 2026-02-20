"""
Naver Image Search Collector (Placeholder)

⚠️ IMPORTANT: This script is for reference only and should NOT be used for production.

Naver Image Search results are subject to copyright and cannot be freely used
without permission from the original copyright holders.

For legal image collection, use:
1. Wikipedia Commons (CC-licensed)
2. Public Data Portal (공공데이터, if registered)
3. DALL-E 3 (AI-generated, owned by us)

This file exists only to show what NOT to do.

Usage:
    DO NOT RUN THIS SCRIPT

Output:
    N/A (Not implemented for legal reasons)
"""

import json
from pathlib import Path
from typing import Dict, Any


def collect_naver_images() -> Dict[str, Any]:
    """
    Placeholder function.

    Returns:
        Error status
    """
    print("=" * 60)
    print("⚠️  Naver Image Search - LEGAL WARNING")
    print("=" * 60)
    print("\n❌ This data source CANNOT be used!")
    print("\nReason:")
    print("- Naver Image Search results are copyrighted")
    print("- Scraping without permission violates Naver's ToS")
    print("- Using copyrighted images requires explicit permission")
    print("\n✅ Use these legal alternatives instead:")
    print("1. Wikipedia Commons (CC-licensed)")
    print("2. Public Data Portal (공공데이터, if registered)")
    print("3. DALL-E 3 (AI-generated, we own the copyright)")
    print("=" * 60)

    return {
        "collected": 0,
        "status": "ILLEGAL_SOURCE",
        "reason": "Copyright violation",
    }


if __name__ == "__main__":
    collect_naver_images()
