import os
import sys
import re
import ast
from collections import defaultdict
from datetime import datetime

# Đảm bảo in tiếng Việt chuẩn trên Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def scan_python_file(filepath):
    """Phân tích cú pháp AST của một file Python"""
    stats = {
        'lines': 0,
        'code_lines': 0,
        'comment_lines': 0,
        'blank_lines': 0,
        'classes': [],
        'functions': [],
        'imports': []
    }
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.splitlines()
            stats['lines'] = len(lines)
            for line in lines:
                s = line.strip()
                if not s:
                    stats['blank_lines'] += 1
                elif s.startswith('#'):
                    stats['comment_lines'] += 1
                else:
                    stats['code_lines'] += 1

        tree = ast.parse(content, filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                stats['classes'].append({'name': node.name, 'methods': methods})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Chỉ lấy các top-level function
                if hasattr(node, 'parent') and not isinstance(node.parent, ast.ClassDef):
                    stats['functions'].append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    stats['imports'].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ''
                for alias in node.names:
                    stats['imports'].append(f"{mod}.{alias.name}")

    except Exception as e:
        stats['error'] = str(e)

    return stats

def analyze_actions():
    """Phát hiện các Action socket được server hỗ trợ từ server_listening.py và request.py"""
    actions = []
    listening_file = os.path.join(PROJECT_DIR, 'controller', 'server_listening.py')
    request_file = os.path.join(PROJECT_DIR, 'model', 'request.py')

    if os.path.exists(request_file):
        with open(request_file, 'r', encoding='utf-8', errors='ignore') as f:
            for match in re.finditer(r'([A-Z_]+)\s*=\s*["\']([A-Z_]+)["\']', f.read()):
                actions.append(match.group(2))

    handled = []
    if os.path.exists(listening_file):
        with open(listening_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for match in re.finditer(r'action\s*==\s*Action\.([A-Z_]+)', content):
                handled.append(match.group(1))

    return list(dict.fromkeys(actions)), list(dict.fromkeys(handled))

def analyze_database_schema():
    """Phân tích cấu trúc bảng từ schema.sql"""
    schema_file = os.path.join(PROJECT_DIR, 'schema.sql')
    tables = {}
    if os.path.exists(schema_file):
        with open(schema_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Tách theo từng khối CREATE TABLE
            statements = re.split(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?', content, flags=re.IGNORECASE)
            for stmt in statements[1:]:
                header = stmt.split('(')[0].strip().replace('`', '')
                if not header:
                    continue
                tname = header.split()[0]
                
                # Lấy phần trong ngoặc tròn đầu tiên
                m = re.search(r'\((.*)\)\s*(?:ENGINE|;|$)', stmt, flags=re.DOTALL)
                body = m.group(1) if m else stmt
                
                cols = []
                for line in body.splitlines():
                    line = line.strip().rstrip(',')
                    if line and not line.upper().startswith(('PRIMARY KEY', 'KEY', 'CONSTRAINT', 'FOREIGN KEY', 'UNIQUE', 'INDEX')):
                        parts = line.split()
                        if parts and len(parts) >= 2:
                            cname = parts[0].replace('`', '')
                            ctype = parts[1]
                            cols.append(f"{cname} {ctype}")
                tables[tname] = cols
    return tables

def generate_report():
    print("=" * 70)
    print("      HỆ THỐNG PHÂN TÍCH TOÀN DIỆN MÃ NGUỒN FLAPPY BIRD SERVER      ")
    print("=" * 70)

    total_files = 0
    total_lines = 0
    total_code = 0
    total_comments = 0
    layers = defaultdict(list)
    file_details = {}

    for root, dirs, files in os.walk(PROJECT_DIR):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', '.idea', 'venv', '.pytest_cache')]
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, PROJECT_DIR)
                total_files += 1

                stats = scan_python_file(filepath)
                total_lines += stats['lines']
                total_code += stats['code_lines']
                total_comments += stats['comment_lines']
                file_details[rel_path] = stats

                # Phân tầng kiến trúc
                if rel_path.startswith('controller'):
                    layers['Controller'].append(rel_path)
                elif rel_path.startswith('dao'):
                    layers['DAO (Data Access Object)'].append(rel_path)
                elif rel_path.startswith('model'):
                    layers['Model (Domain/Entity)'].append(rel_path)
                elif rel_path.startswith('view'):
                    layers['View (GUI)'].append(rel_path)
                else:
                    layers['Core & Utilities'].append(rel_path)

    actions_defined, actions_handled = analyze_actions()
    db_tables = analyze_database_schema()

    # Báo cáo ra màn hình
    print(f"\n📊 TỔNG QUAN DỰ ÁN:")
    print(f"  • Thư mục gốc      : {PROJECT_DIR}")
    print(f"  • Tổng số file .py : {total_files} files")
    print(f"  • Tổng số dòng mã  : {total_lines:,} lines ({total_code:,} code, {total_comments:,} comments)")
    print(f"  • Số bảng Database : {len(db_tables)} tables (MySQL)")
    print(f"  • Socket Actions   : {len(actions_handled)} hành động xử lý mạng")

    print(f"\n🏛️ KIẾN TRÚC PHÂN TẦNG (MVC / LAYERED PATTERN):")
    for layer_name, flist in layers.items():
        print(f"  [{layer_name}] ({len(flist)} files):")
        for f in flist:
            cls_count = len(file_details[f]['classes'])
            print(f"    - {f:<35} : {file_details[f]['code_lines']:>4} LOC | {cls_count} classes")

    print(f"\n📡 GIAO THỨC SOCKET TCP & ACTION PACKETS:")
    for act in actions_handled:
        print(f"  ✅ Action: {act:<20} -> Xử lý trong Controller & DAO")

    print(f"\n🗄️ CẤU TRÚC DATABASE (schema.sql):")
    for tname, cols in db_tables.items():
        print(f"  • Bảng `{tname}` ({len(cols)} cột):")
        print(f"    {', '.join(cols[:5])}{'...' if len(cols) > 5 else ''}")

    # Xuất file Markdown chi tiết
    report_md_path = os.path.join(PROJECT_DIR, 'PROJECT_ANALYSIS.md')
    with open(report_md_path, 'w', encoding='utf-8') as f:
        f.write("# BÁO CÁO PHÂN TÍCH TOÀN DIỆN FLAPPY BIRD SERVER\n\n")
        f.write(f"*Thời gian khởi tạo:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"*Phiên bản:* Python TCP Socket Server (Đồ án PTIT Nhóm 05)\n\n")
        f.write("---\n\n")

        f.write("## 1. Tổng Quan Mã Nguồn\n\n")
        f.write(f"- **Tổng số tệp mã nguồn Python:** `{total_files}`\n")
        f.write(f"- **Tổng số dòng mã (LOC):** `{total_lines:,}`\n")
        f.write(f"- **Dòng mã thực thi (Code):** `{total_code:,}`\n")
        f.write(f"- **Dòng chú thích (Comments):** `{total_comments:,}`\n\n")

        f.write("## 2. Kiến Trúc Phân Tầng (Layered Architecture)\n\n")
        f.write("| Tầng (Layer) | Vai trò | Danh sách tệp |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write(f"| **Controller** | Điều khiển máy chủ TCP, nhận kết nối, xử lý tiểu trình và điều phối nghiệp vụ | `{', '.join(layers['Controller'])}` |\n")
        f.write(f"| **DAO** | Kết nối cơ sở dữ liệu MySQL (PyMySQL) và thực thi câu truy vấn an toàn | `{', '.join(layers['DAO (Data Access Object)'])}` |\n")
        f.write(f"| **Model** | Định nghĩa đối tượng thực thể (Player, Ranking, Request, Response,...) | `{', '.join(layers['Model (Domain/Entity)'])}` |\n")
        f.write(f"| **View** | Giao diện quản trị máy chủ bằng đồ họa Tkinter (`ServerMainFrm`) | `{', '.join(layers['View (GUI)'])}` |\n")
        f.write(f"| **Core/Entry** | Điểm khởi chạy hệ thống dòng lệnh và GUI (`server_main.py`, `config.py`) | `{', '.join(layers['Core & Utilities'])}` |\n\n")

        f.write("## 3. Giao Thức Mạng & Các Hành Động Socket (Protocol Actions)\n\n")
        f.write("Giao thức giao tiếp giữa Client Android và Python Server sử dụng **JSON qua TCP Socket theo dòng (Line-based JSON stream)**:\n\n")
        f.write("| Hành động (Action) | Dữ liệu gửi (Request) | Xử lý tại Server | Phản hồi (Response) |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        f.write("| `LOGIN` | `username`, `password` | `PlayerDAO.checkLogin()` | Thông tin `User` & `persis_id` |\n")
        f.write("| `REGISTER` | `User` (username, pass, email) | `PlayerDAO.checkRegister()` & `addPlayer()` | Tạo bản ghi mới vào MySQL |\n")
        f.write("| `GET_USER` | `persis_id` | `PlayerDAO.getPlayerByPersisId()` | Chi tiết người chơi & điểm kỷ lục |\n")
        f.write("| `UPDATE_USER` | `User` (username, email, pass) | `PlayerDAO.checkValid()` & `updatePlayer()` | Trạng thái cập nhật thành công |\n")
        f.write("| `UPDATE_SCORE` | `persis_id`, `score` | `PlayerDAO.updateScore()` | Lưu điểm kỷ lục mới nếu cao hơn |\n")
        f.write("| `GET_LEADERBOARD` | Rỗng | `PlayerRankingDAO.getPlayerRanking()` | Danh sách xếp hạng sắp xếp điểm giảm dần |\n\n")

        f.write("## 4. Cơ Sở Dữ Liệu MySQL (`schema.sql`)\n\n")
        f.write("Hệ thống lưu trữ trên cơ sở dữ liệu MySQL `flappy_bird_db` gồm các bảng:\n\n")
        for tname, cols in db_tables.items():
            f.write(f"### Bảng `{tname}`\n")
            f.write(f"- **Cột:** {', '.join(cols)}\n\n")

        f.write("## 5. Đánh Giá Điểm Mạnh & Đề Xuất Nâng Cấp\n\n")
        f.write("### Điểm mạnh:\n")
        f.write("1. **Kiến trúc phân tầng chuẩn mực:** Tách biệt rành mạch giữa Controller, Model, DAO và View theo chuẩn đồ án phần mềm PTIT.\n")
        f.write("2. **Kết nối phi trạng thái (Stateless On-Demand):** Client chỉ kết nối khi cần gửi packet và đóng socket ngay, giúp không bao giờ bị nghẽn hay stale socket.\n")
        f.write("3. **Hỗ trợ chạy linh hoạt:** Có cả chế độ Terminal CLI đơn giản lẫn chế độ GUI Tkinter trực quan.\n")
        f.write("4. **Tối ưu bảng xếp hạng:** Xếp hạng điểm từ cao nhất đến thấp nhất (`highestPoint DESC`).\n\n")
        f.write("### Đề xuất mở rộng:\n")
        f.write("1. **Mã hóa mật khẩu:** Hiện tại đang so sánh mật khẩu dạng chuỗi text hoặc hash đơn giản, nên nâng cấp lên thuật toán `bcrypt` hoặc `pbkdf2_sha256`.\n")
        f.write("2. **Connection Pool:** Cải tiến quản lý kết nối MySQL bằng thư viện Connection Pooling (như `DBUtils` hoặc `mysql-connector-python pooling`) khi có lượng người chơi đồng thời lớn.\n")
        f.write("3. **Bổ sung tính năng PVP thời gian thực:** Tận dụng các Model đã định nghĩa sẵn như `PVPMatches`, `Challenge` để làm chế độ đấu 2 người trực tiếp.\n")

    print(f"\n📄 Đã tự động tạo tệp báo cáo chi tiết tại: {report_md_path}")
    print("=" * 70)

if __name__ == '__main__':
    generate_report()
