import os
import sys

# Đảm bảo in tiếng Việt không bị lỗi encoding trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pymysql
from config import DB_CONFIG
from dao.dao import _build_connect_kwargs


def _strip_leading_comments(stmt: str) -> str:
    """Loại bỏ các dòng comment '-- ...' ở đầu câu lệnh SQL."""
    lines = []
    skipping_header = True
    for line in stmt.splitlines():
        stripped = line.strip()
        if skipping_header and (not stripped or stripped.startswith("--")):
            continue
        skipping_header = False
        lines.append(line)
    return "\n".join(lines).strip()


def init_database() -> bool:
    print("=" * 60)
    print(" KHỞI TẠO CƠ SỞ DỮ LIỆU MYSQL CHO FLAPPY BIRD SERVER")
    print("=" * 60)

    db_name = DB_CONFIG["database"]

    # Thử kết nối trực tiếp vào DB trước (phù hợp với Cloud Managed MySQL cấp sẵn DB)
    conn = None
    try:
        conn = pymysql.connect(**_build_connect_kwargs(include_database=True))
        print(f"[OK] Đã kết nối tới cơ sở dữ liệu `{db_name}`!")
    except pymysql.err.OperationalError as e:
        err_code = e.args[0] if e.args else None
        if err_code == 1049:  # Unknown database -> tạo mới khi chạy local
            try:
                tmp_conn = pymysql.connect(**_build_connect_kwargs(include_database=False))
                with tmp_conn.cursor() as cur:
                    cur.execute(
                        f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                    )
                tmp_conn.close()
                conn = pymysql.connect(**_build_connect_kwargs(include_database=True))
                print(f"[OK] Đã tạo mới và kết nối cơ sở dữ liệu `{db_name}`!")
            except Exception as inner_e:
                print(f"[LỖI] Không thể tạo database `{db_name}`: {inner_e}")
                return False
        else:
            print(f"[LỖI] Không thể kết nối tới MySQL: {e}")
            return False
    except Exception as e:
        print(f"[LỖI] Không thể kết nối tới MySQL: {e}")
        return False

    try:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if not os.path.exists(schema_path):
            print(f"[LỖI] Không tìm thấy file `{schema_path}`")
            conn.close()
            return False

        with open(schema_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        raw_statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

        with conn.cursor() as cur:
            for raw_stmt in raw_statements:
                stmt = _strip_leading_comments(raw_stmt)
                if not stmt:
                    continue
                upper_stmt = stmt.upper()
                # Bỏ qua CREATE DATABASE / USE hardcode để tương thích tên DB do Cloud cấp
                if upper_stmt.startswith("CREATE DATABASE") or upper_stmt.startswith("USE "):
                    continue
                cur.execute(stmt)
        conn.commit()
        conn.close()
        print(f"[OK] Đã nạp toàn bộ bảng và dữ liệu mẫu vào `{db_name}` thành công!")
        return True
    except Exception as e:
        print(f"[LỖI] Lỗi khi nạp schema.sql: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return False


if __name__ == "__main__":
    success = init_database()
    if success:
        print(">> KHỞI TẠO CƠ SỞ DỮ LIỆU THÀNH CÔNG <<")
    else:
        print(">> KHỞI TẠO THẤT BẠI <<")
