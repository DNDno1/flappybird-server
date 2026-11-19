import sys
import argparse
import time
import socket

# Đảm bảo in tiếng Việt chuẩn và không bị buffer trên console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

from config import SERVER_CONFIG, DB_CONFIG
from dao.dao import DAO
from init_db import init_database
from controller.server_ctr import ServerCtr

def get_local_ip_addresses():
    ip_list = []
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127."):
                ip_list.append(ip)
    except Exception:
        pass
    return ip_list

def run_cli_server(port: int):
    print("=" * 68)
    print("      FLAPPY BIRD TCP SOCKET SERVER    ")
    print("=" * 68)

    # 1. Kiểm tra kết nối MySQL
    print(f"[MySQL] Đang kiểm tra kết nối tới Database '{DB_CONFIG['database']}'...")
    if not DAO.test_connection():
        print(f"[MySQL CẢNH BÁO] Chưa kết nối được DB '{DB_CONFIG['database']}'! Đang thử khởi tạo...")
        if not init_database():
            print("[MySQL LỖI] Vui lòng kiểm tra MySQL service và mật khẩu trong config.py!")
            return
        print("[MySQL] Khởi tạo cơ sở dữ liệu thành công!")
    else:
        print(f"[MySQL] ✅ Đã kết nối cơ sở dữ liệu '{DB_CONFIG['database']}' thành công.")

    # 2. Khởi tạo Controller và lắng nghe
    server_ctr = ServerCtr(view=None, port=port)
    success = server_ctr.openServer(port)
    if not success:
        print(f"[SERVER LỖI] Không thể lắng nghe trên cổng {port}!")
        return

    # 3. Hiển thị thông tin kết nối qua mạng LAN cho Client Android
    local_ips = get_local_ip_addresses()
    primary_ip = local_ips[0] if local_ips else "172.16.13.45"

    print("-" * 68)
    print("📡 THÔNG TIN KẾT NỐI QUA MẠNG LAN CHO APP FLAPPY BIRD:")
    print(f"  • Cổng Server (Port) : {port}")
    print(f"  • IP Máy chủ (LAN)   : {primary_ip}")
    if len(local_ips) > 1:
        print(f"  • Các IP mạng khác   : {', '.join(local_ips[1:])}")
    print("-" * 68)
    print("👉 Hãy đảm bảo điện thoại và máy tính cùng kết nối chung một mạng Wi-Fi/LAN.")
    print("   Nhập địa chỉ trên vào mục 'Cấu hình Máy chủ' trên App Flappy Bird.")
    print("💡 Nếu kết nối thất bại, hãy chuột phải vào 'open_firewall.bat' -> Run as administrator")
    print("   để mở cổng tường lửa Windows cho mạng LAN.")
    print("------------------------------------------------------------------")
    print("Sẵn sàng phục vụ yêu cầu từ FlappyBird Android!")
    print("Nhấn Ctrl + C để dừng máy chủ bất kỳ lúc nào.")
    print("=" * 68)

    try:
        while server_ctr.is_running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[SERVER] Đang dừng máy chủ theo yêu cầu người dùng...")
    finally:
        server_ctr.closeServer()
        print("[SERVER] Đã tắt máy chủ an toàn.")

def run_gui_server(port: int):
    # Kiểm tra kết nối MySQL trước
    if not DAO.test_connection():
        init_database()

    from view.server_main_frm import ServerMainFrm
    app = ServerMainFrm(default_port=port)
    app.run()

def main():
    parser = argparse.ArgumentParser(description="Flappy Bird Python TCP Socket Server (PTIT Nhóm 05)")
    parser.add_argument("--gui", action="store_true", help="Chạy giao diện đồ họa GUI Tkinter (mặc định chạy Terminal CLI)")
    parser.add_argument("--cli", action="store_true", help="Chạy chế độ dòng lệnh Terminal (mặc định)")
    parser.add_argument("--port", type=int, default=SERVER_CONFIG['port'], help=f"Cổng Server (mặc định: {SERVER_CONFIG['port']})")
    args = parser.parse_args()

    # Mặc định chạy Terminal CLI để đơn giản và tiện lợi nhất
    if args.gui:
        try:
            run_gui_server(args.port)
        except Exception as e:
            print(f"[GUI Fallback] Không thể mở giao diện đồ họa ({e}), chuyển sang Terminal CLI...")
            run_cli_server(args.port)
    else:
        run_cli_server(args.port)

if __name__ == '__main__':
    main()

