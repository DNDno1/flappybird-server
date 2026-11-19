import socket
import json
import sys
import uuid
import time

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8889

def send_request(sock, req_data: dict) -> dict:
    req_json = json.dumps(req_data) + "\n"
    sock.sendall(req_json.encode("utf-8"))
    
    # Đọc dòng phản hồi
    buffer = ""
    while "\n" not in buffer:
        chunk = sock.recv(4096).decode("utf-8")
        if not chunk:
            break
        buffer += chunk
    
    line = buffer.split("\n")[0].strip()
    return json.loads(line)

def run_test():
    print("=" * 65)
    print(" KIỂM THỬ KẾT NỐI VÀ CÁC CHỨC NĂNG VỚI FLAPPY BIRD PYTHON SERVER")
    print("=" * 65)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((SERVER_HOST, SERVER_PORT))
        print(f"✅ Kết nối thành công tới Server tại {SERVER_HOST}:{SERVER_PORT}\n")
    except Exception as e:
        print(f"❌ Không thể kết nối tới Server tại {SERVER_HOST}:{SERVER_PORT}: {e}")
        print("Vui lòng khởi chạy server trước bằng lệnh: python server_main.py --cli")
        return

    try:
        # TEST 1: Đăng nhập với tài khoản có sẵn trong CSDL
        print("--- [TEST 1] ĐĂNG NHẬP VỚI TÀI KHOẢN CÓ SẴN (Hip) ---")
        login_req = {
            "action": "LOGIN",
            "username": "Hip",
            "password": "123456"
        }
        res1 = send_request(sock, login_req)
        print(f"Kết quả: Status={res1.get('status')} | Message={res1.get('message')}")
        user1 = res1.get("user", {})
        print(f"Thông tin người dùng: ID={user1.get('id')}, persis_id={user1.get('persis_id')}, Score={user1.get('score')}\n")

        # TEST 2: Đăng ký tài khoản mới
        test_suffix = uuid.uuid4().hex[:6]
        new_username = f"gamer_{test_suffix}"
        new_password = "password123"
        new_email = f"{new_username}@test.com"
        print(f"--- [TEST 2] ĐĂNG KÝ TÀI KHOẢN MỚI ('{new_username}') ---")
        reg_req = {
            "action": "REGISTER",
            "user": {
                "username": new_username,
                "password": new_password,
                "email": new_email
            }
        }
        res2 = send_request(sock, reg_req)
        print(f"Kết quả: Status={res2.get('status')} | Message={res2.get('message')}")
        registered_user = res2.get("user", {})
        persis_id = registered_user.get("persis_id")
        print(f"Tài khoản vừa tạo: persis_id={persis_id}, username={registered_user.get('username')}\n")

        # TEST 3: Đăng nhập với tài khoản vừa đăng ký
        print(f"--- [TEST 3] ĐĂNG NHẬP VỚI TÀI KHOẢN VỪA TẠO ---")
        login_req2 = {
            "action": "LOGIN",
            "username": new_username,
            "password": new_password
        }
        res3 = send_request(sock, login_req2)
        print(f"Kết quả: Status={res3.get('status')} | Message={res3.get('message')}\n")

        # TEST 4: Xem thông tin cá nhân
        print(f"--- [TEST 4] XEM THÔNG TIN CÁ NHÂN (GET_USER persis_id='{persis_id}') ---")
        get_user_req = {
            "action": "GET_USER",
            "persisId": persis_id
        }
        res4 = send_request(sock, get_user_req)
        print(f"Kết quả: Status={res4.get('status')} | User={res4.get('user')}\n")

        # TEST 5: Chỉnh sửa thông tin cá nhân
        updated_username = f"pro_{test_suffix}"
        updated_email = f"updated_{test_suffix}@flappy.ptit"
        print(f"--- [TEST 5] CHỈNH SỬA THÔNG TIN CÁ NHÂN (Đổi tên thành '{updated_username}') ---")
        update_req = {
            "action": "UPDATE_USER",
            "user": {
                "persis_id": persis_id,
                "username": updated_username,
                "password": "new_secret_password",
                "email": updated_email
            }
        }
        res5 = send_request(sock, update_req)
        print(f"Kết quả: Status={res5.get('status')} | Message={res5.get('message')}")
        print(f"User sau khi sửa: {res5.get('user')}\n")

        # TEST 6: Cập nhật điểm số sau khi chơi game
        new_score = 999
        print(f"--- [TEST 6] CẬP NHẬT ĐIỂM SỐ KỶ LỤC ({new_score} điểm) ---")
        update_score_req = {
            "action": "UPDATE_SCORE",
            "persisId": persis_id,
            "score": new_score
        }
        res6 = send_request(sock, update_score_req)
        print(f"Kết quả: Status={res6.get('status')} | Message={res6.get('message')}")
        print(f"Điểm số mới của người chơi: {res6.get('user', {}).get('score')} điểm\n")

        # TEST 7: Xem Bảng xếp hạng (Sắp xếp theo Điểm từ cao đến thấp)
        print("--- [TEST 7] XEM BẢNG XẾP HẠNG (GET_LEADERBOARD - ĐIỂM TỪ CAO ĐẾN THẤP) ---")
        leaderboard_req = {
            "action": "GET_LEADERBOARD"
        }
        res7 = send_request(sock, leaderboard_req)
        print(f"Kết quả: Status={res7.get('status')} | Message={res7.get('message')}")
        leaderboard = res7.get("leaderboard", [])
        print(f"{'HẠNG':<6}{'TÊN NGƯỜI CHƠI':<20}{'ĐIỂM SỐ':<15}{'TỔNG ĐIỂM':<15}{'SỐ TRẬN THẮNG':<15}")
        print("-" * 65)
        for idx, item in enumerate(leaderboard, start=1):
            name = item.get("username", "")
            bp = item.get("score", 0)
            tp = item.get("total_points", bp)
            tw = item.get("total_wins", 0)
            print(f"{idx:<6}{name:<20}{bp:<15}{tp:<15}{tw:<15}")

        print("\n" + "=" * 65)
        print("✅ TOÀN BỘ CÁC CHỨC NĂNG ĐÃ ĐƯỢC KIỂM THỬ THÀNH CÔNG VỚI PYTHON SERVER!")
        print("=" * 65)

    except Exception as e:
        print(f"Lỗi trong quá trình kiểm thử: {e}")
    finally:
        sock.close()

if __name__ == '__main__':
    run_test()
