"""
Sprint 2 Phase 2: 이미지 URL DB 마이그레이션 실행 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import get_db_sync


def run_migration():
    """migrations/sprint2_update_images.sql 실행"""
    migration_file = (
        Path(__file__).parent.parent / "migrations" / "sprint2_update_images.sql"
    )

    if not migration_file.exists():
        print(f"❌ 마이그레이션 파일 없음: {migration_file}")
        return False

    print(f"📄 마이그레이션 파일 로드: {migration_file}")
    with open(migration_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # SQL 분할 (BEGIN/COMMIT 제거하고 개별 UPDATE문 실행)
    lines = sql_content.split("\n")
    update_statements = []

    for line in lines:
        line = line.strip()
        if line.startswith("UPDATE canonical_menus"):
            update_statements.append(line)

    print(f"📊 총 {len(update_statements)}개 UPDATE 문 발견")

    # DB 연결 및 실행
    print("🔌 DB 연결 중...")
    db = next(get_db_sync())

    try:
        print("🚀 마이그레이션 시작...")
        success_count = 0
        error_count = 0

        for i, stmt in enumerate(update_statements, 1):
            try:
                db.execute(text(stmt))
                success_count += 1

                if i % 20 == 0:
                    print(
                        f"  진행: {i}/{len(update_statements)} ({success_count} 성공, {error_count} 실패)"
                    )

            except Exception as e:
                error_count += 1
                if error_count <= 5:  # 처음 5개 에러만 출력
                    print(f"  ⚠️ UPDATE 실패 (#{i}): {str(e)[:100]}")

        # 커밋
        db.commit()
        print("\n✅ 마이그레이션 완료!")
        print(f"  성공: {success_count}/{len(update_statements)}")
        print(f"  실패: {error_count}/{len(update_statements)}")

        return error_count == 0

    except Exception as e:
        db.rollback()
        print(f"❌ 마이그레이션 실패: {e}")
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
