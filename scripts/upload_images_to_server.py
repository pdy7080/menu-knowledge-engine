"""
이미지 파일을 FastComet 서버에 업로드하는 스크립트
scp를 사용하여 안전하게 전송

Author: terminal-developer
Date: 2026-02-19
"""
import os
import subprocess
from pathlib import Path
from typing import List, Tuple
import sys

# Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 설정
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "data" / "images"
SERVER_HOST = "chargeap@d11475.sgp1.stableserver.net"
SERVER_PATH = "~/menu-knowledge.chargeapp.net/public_html/images"

# 이미지 폴더 목록
IMAGE_FOLDERS = [
    "ai_generated",
    "wikipedia"
]


def ensure_server_directory():
    """서버에 이미지 디렉토리 생성"""
    print("\n서버 디렉토리 확인 중...")

    cmd = f'ssh {SERVER_HOST} "mkdir -p {SERVER_PATH}/ai_generated {SERVER_PATH}/wikipedia && echo \'Directories created\'"'

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"  ✅ 서버 디렉토리 준비 완료")
            print(f"     {result.stdout.strip()}")
        else:
            print(f"  ❌ 오류: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ 예외: {str(e)}")
        return False

    return True


def collect_images() -> List[Tuple[Path, str]]:
    """업로드할 이미지 파일 목록 수집"""
    images = []

    for folder in IMAGE_FOLDERS:
        folder_path = IMAGES_DIR / folder
        if not folder_path.exists():
            print(f"  ⚠️  폴더 없음: {folder}")
            continue

        # 이미지 파일 찾기 (png, jpg, jpeg, webp)
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
            for img_file in folder_path.glob(ext):
                images.append((img_file, folder))

    return images


def upload_image(local_path: Path, folder: str) -> bool:
    """단일 이미지 파일 업로드"""
    file_name = local_path.name
    remote_path = f"{SERVER_PATH}/{folder}/{file_name}"

    # scp 명령어
    cmd = f'scp "{local_path}" {SERVER_HOST}:{remote_path}'

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            print(f"      ❌ scp 오류: {result.stderr}")
            return False
    except Exception as e:
        print(f"      ❌ 예외: {str(e)}")
        return False


def main():
    """메인 업로드 프로세스"""
    print("=" * 60)
    print("이미지 서버 업로드")
    print("=" * 60)
    print(f"서버: {SERVER_HOST}")
    print(f"대상 경로: {SERVER_PATH}")

    # 1. 이미지 수집
    print("\n이미지 파일 수집 중...")
    images = collect_images()

    if not images:
        print("  ⚠️  업로드할 이미지가 없습니다.")
        return

    print(f"  ✅ {len(images)}개 이미지 발견")

    # 이미지별 통계
    stats = {}
    for _, folder in images:
        stats[folder] = stats.get(folder, 0) + 1

    for folder, count in stats.items():
        print(f"     - {folder}: {count}개")

    # 2. 서버 디렉토리 준비
    if not ensure_server_directory():
        print("\n❌ 서버 디렉토리 생성 실패")
        return

    # 3. 업로드
    print(f"\n{len(images)}개 이미지 업로드 시작...")
    uploaded = 0
    failed = 0

    for i, (img_path, folder) in enumerate(images, 1):
        file_size_mb = img_path.stat().st_size / (1024 * 1024)
        print(f"  [{i}/{len(images)}] {img_path.name} ({file_size_mb:.2f} MB) 업로드 중...")

        if upload_image(img_path, folder):
            print(f"      ✅ 완료")
            uploaded += 1
        else:
            failed += 1

    # 4. 결과 출력
    print("\n" + "=" * 60)
    print(f"✅ 업로드 완료: {uploaded}개")
    print(f"❌ 실패: {failed}개")
    print(f"성공률: {(uploaded / len(images) * 100):.1f}%")

    # 5. 접근 URL 안내
    if uploaded > 0:
        print(f"\n📌 이미지 접근 URL:")
        print(f"   https://menu-knowledge.chargeapp.net/images/ai_generated/[파일명]")
        print(f"   https://menu-knowledge.chargeapp.net/images/wikipedia/[파일명]")

        print(f"\n예시:")
        if images:
            first_img = images[0]
            print(f"   https://menu-knowledge.chargeapp.net/images/{first_img[1]}/{first_img[0].name}")


if __name__ == "__main__":
    main()
