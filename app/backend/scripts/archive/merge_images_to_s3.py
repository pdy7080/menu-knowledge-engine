"""
Image Merger and S3 Uploader

Merges images from multiple sources and uploads to S3 or local storage.

Usage:
    python merge_images_to_s3.py --storage local
    python merge_images_to_s3.py --storage s3 --bucket menu-knowledge-images

Output:
    - Consolidated image directory
    - Updated metadata with storage URLs
"""

import json
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def merge_local_images(
    source_dirs: List[Path],
    output_dir: Path,
    metadata_file: Path,
) -> Dict[str, Any]:
    """
    Merge images from multiple sources into single directory.

    Args:
        source_dirs: List of source directories
        output_dir: Output directory
        metadata_file: Metadata JSON file

    Returns:
        Merge statistics
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load metadata
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        print("[ERROR] Metadata file not found!")
        return {"error": "Metadata not found"}

    copied = 0
    skipped = 0
    failed = 0

    print("=" * 60)
    print("Image Merge Tool")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Source directories: {len(source_dirs)}")
    print("-" * 60)

    # Process each image in metadata
    for img in metadata.get("images", []):
        source_path = Path(img["path"])

        if not source_path.exists():
            print(f"[SKIP] File not found: {source_path.name}")
            skipped += 1
            continue

        # Copy to output dir
        dest_path = output_dir / source_path.name

        if dest_path.exists():
            print(f"[SKIP] Already exists: {dest_path.name}")
            skipped += 1
            continue

        try:
            shutil.copy2(source_path, dest_path)
            copied += 1
            print(f"[OK] Copied: {dest_path.name}")

            # Update path in metadata
            img["merged_path"] = str(dest_path)

        except Exception as e:
            failed += 1
            print(f"[FAIL] {source_path.name}: {e}")

    # Save updated metadata
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("Merge Complete!")
    print(f"[OK] Copied: {copied}")
    print(f"[SKIP] Skipped: {skipped}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[DIR] Output: {output_dir}")
    print("=" * 60)

    return {
        "copied": copied,
        "skipped": skipped,
        "failed": failed,
        "output_dir": str(output_dir),
    }


def upload_to_s3(
    source_dir: Path,
    bucket_name: str,
    prefix: str = "menu-images",
    metadata_file: Path = Path("data/image_metadata.json"),
) -> Dict[str, Any]:
    """
    Upload images to S3.

    Note: This is a placeholder. Actual S3 upload requires:
    - boto3 library
    - AWS credentials
    - S3 bucket configuration

    Args:
        source_dir: Directory containing images
        bucket_name: S3 bucket name
        prefix: S3 key prefix
        metadata_file: Metadata file

    Returns:
        Upload statistics
    """
    print("=" * 60)
    print("S3 Upload Tool")
    print("=" * 60)
    print("\n[WARNING] S3 upload not yet implemented!")
    print("\nTo implement S3 upload:")
    print("1. Install boto3: pip install boto3")
    print("2. Configure AWS credentials")
    print("3. Create S3 bucket")
    print("4. Update this script with boto3 code")
    print("\nFor MVP, using local storage is sufficient.")
    print("=" * 60)

    return {
        "uploaded": 0,
        "status": "NOT_IMPLEMENTED",
        "reason": "S3 integration pending",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Merge and upload images")
    parser.add_argument(
        "--storage", choices=["local", "s3"], default="local", help="Storage type"
    )
    parser.add_argument("--bucket", type=str, help="S3 bucket name (if using S3)")
    parser.add_argument(
        "--output",
        type=str,
        default="C:/project/menu/data/images/merged",
        help="Output directory for local storage",
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default="C:/project/menu/data/image_metadata.json",
        help="Metadata JSON file",
    )

    args = parser.parse_args()

    metadata_path = Path(args.metadata)

    if args.storage == "local":
        # Merge to local directory
        source_dirs = [
            Path("C:/project/menu/data/images/wikipedia"),
            Path("C:/project/menu/data/images/ai_generated"),
        ]

        stats = merge_local_images(
            source_dirs=source_dirs,
            output_dir=Path(args.output),
            metadata_file=metadata_path,
        )

    elif args.storage == "s3":
        if not args.bucket:
            print("[ERROR] --bucket required for S3 storage")
            sys.exit(1)

        stats = upload_to_s3(
            source_dir=Path(args.output),
            bucket_name=args.bucket,
            metadata_file=metadata_path,
        )

    print("\nFinal Statistics:")
    print(json.dumps(stats, indent=2))
