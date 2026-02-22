"""
Sprint 2 Phase 2: 이미지 URL DB 마이그레이션 (psycopg2 직접 사용)
"""

import psycopg2
from pathlib import Path
import os

# .env 파일 로드
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())


def run_migration():
    """migrations/sprint2_update_images.sql 실행"""
    # DB 연결 정보
    db_params = {
        "host": "localhost",
        "port": 5432,
        "database": "chargeap_menu_knowledge",
        "user": "chargeap_dcclab2022",
        "password": os.environ.get("DB_PASSWORD", ""),
    }

    migration_file = (
        Path(__file__).parent.parent / "migrations" / "sprint2_update_images.sql"
    )

    if not migration_file.exists():
        print(f"❌ 마이그레이션 파일 없음: {migration_file}")
        return False

    print(f"📄 마이그레이션 파일 로드: {migration_file}")
    with open(migration_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # SQL 분할 (개별 UPDATE문만 추출)
    lines = sql_content.split("\n")
    update_statements = []

    for line in lines:
        line = line.strip()
        if line.startswith("UPDATE canonical_menus"):
            update_statements.append(line)

    print(f"📊 총 {len(update_statements)}개 UPDATE 문 발견")

    # DB 연결
    print("🔌 DB 연결 중...")
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        print("🚀 마이그레이션 시작...")
        success_count = 0
        error_count = 0

        for i, stmt in enumerate(update_statements, 1):
            try:
                cur.execute(stmt)
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
        conn.commit()
        print("\n✅ 마이그레이션 완료!")
        print(f"  성공: {success_count}/{len(update_statements)}")
        print(f"  실패: {error_count}/{len(update_statements)}")

        # 결과 확인
        cur.execute(
            """
            SELECT COUNT(*)
            FROM canonical_menus
            WHERE primary_image IS NOT NULL
        """
        )
        count = cur.fetchone()[0]
        print(f"  DB 확인: {count}개 메뉴에 primary_image 설정됨")

        cur.close()
        conn.close()

        return error_count == 0

    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        return False


if __name__ == "__main__":
    import sys

    success = run_migration()
    sys.exit(0 if success else 1)
