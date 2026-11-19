import socket
import threading
import traceback
from datetime import datetime
from model.request import Request, Action
from model.response import Response
from model.player import Player
from dao.player_dao import PlayerDAO
from dao.player_ranking_dao import PlayerRankingDAO

class ServerListening(threading.Thread):
    """
    Lớp ServerListening kế thừa threading.Thread theo Biểu đồ lớp chi tiết và Biểu đồ tuần tự PTIT
    + ServerListening()
    + run()
    Lắng nghe các kết nối từ máy khách (LoginCtr, RegisterCtr, EditCtr, LeaderboardCtr),
    gọi các hàm xử lý tương ứng trong PlayerDAO và PlayerRankingDAO, sau đó trả về kết quả.
    """
    def __init__(self, server_ctr):
        super().__init__()
        self.server_ctr = server_ctr
        self.player_dao = PlayerDAO()
        self.player_ranking_dao = PlayerRankingDAO()
        self.daemon = True
        self.is_running = True

    def log(self, message: str):
        """Ghi log ra console và hiển thị trên giao diện ServerMainFrm nếu có"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{now}] {message}"
        print(formatted, flush=True)
        if self.server_ctr and self.server_ctr.view and hasattr(self.server_ctr.view, "showMessage"):
            self.server_ctr.view.showMessage(formatted)

    def run(self):
        self.log(f"ServerListening đã bắt đầu chạy trên cổng {self.server_ctr.myAddress.port}...")
        server_socket = self.server_ctr.myServer

        while self.is_running and server_socket:
            try:
                client_sock, client_addr = server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_sock, client_addr),
                    daemon=True
                )
                client_thread.start()
            except socket.timeout:
                continue
            except OSError:
                # Socket đã bị đóng khi tắt server
                break
            except Exception as e:
                if self.is_running:
                    self.log(f"Lỗi khi chấp nhận kết nối: {e}")
                break

        self.log("ServerListening đã dừng lắng nghe.")

    def handle_client(self, client_sock: socket.socket, client_addr):
        addr_str = f"{client_addr[0]}:{client_addr[1]}"
        self.log(f"Client đã kết nối từ {addr_str}")

        try:
            client_sock.settimeout(60.0)
            # Tạo file stream để đọc ghi text theo dòng định dạng UTF-8
            fileobj = client_sock.makefile(mode="rwb", buffering=0)

            while self.is_running:
                raw_line = fileobj.readline()
                if not raw_line:
                    self.log(f"Client {addr_str} đã ngắt kết nối.")
                    break

                # Kiểm tra nếu client vô tình gửi Java ObjectOutputStream header (0xAC 0xED)
                if len(raw_line) >= 2 and raw_line[0] == 0xAC and raw_line[1] == 0xED:
                    self.log(f"⚠️ Phát hiện byte mã hóa nhị phân Java ObjectOutputStream từ {addr_str}.")
                    err_resp = Response.error("Vui lòng sử dụng giao thức JSON Socket của ClientSocketManager.")
                    fileobj.write((err_resp.to_json() + "\n").encode("utf-8"))
                    fileobj.flush()
                    continue

                line_str = raw_line.decode("utf-8", errors="ignore").strip()
                if not line_str:
                    continue

                req = Request.from_json(line_str)
                if not req or not req.action:
                    self.log(f"[{addr_str}] Dữ liệu yêu cầu không hợp lệ: {line_str}")
                    resp = Response.error("Định dạng yêu cầu không hợp lệ!")
                else:
                    self.log(f"[{addr_str}] Nhận yêu cầu: {req.action}")
                    resp = self.process_request(req, addr_str)

                # Gửi chuỗi JSON phản hồi có kèm ký tự xuống dòng
                resp_json = resp.to_json() + "\n"
                fileobj.write(resp_json.encode("utf-8"))
                fileobj.flush()
                self.log(f"[{addr_str}] Đã gửi phản hồi: {resp.status} - {resp.message}")

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            self.log(f"Client {addr_str} đã đóng kết nối đột ngột.")
        except Exception as e:
            self.log(f"Lỗi xử lý kết nối với client {addr_str}: {e}")
            traceback.print_exc()
        finally:
            try:
                client_sock.close()
            except Exception:
                pass
            self.log(f"Đã đóng socket kết nối tới {addr_str}.")

    def process_request(self, req: Request, addr_str: str) -> Response:
        """
        Xử lý từng hành động nghiệp vụ theo đúng Biểu đồ tuần tự:
        - LOGIN -> PlayerDAO.checkLogin()
        - REGISTER -> PlayerDAO.checkRegister() & addPlayer()
        - GET_USER -> PlayerDAO.getPlayerByPersisId()
        - UPDATE_USER -> PlayerDAO.checkValid() & updatePlayer()
        - UPDATE_SCORE -> PlayerDAO.updateScore()
        - GET_LEADERBOARD -> PlayerRankingDAO.getPlayerRanking()
        """
        action = req.action

        # 1. ĐĂNG NHẬP
        if action == Action.LOGIN:
            username = req.username or ""
            password = req.password or ""
            self.log(f"[{addr_str}] Xử lý ĐĂNG NHẬP cho tài khoản: '{username}'")

            p = Player(username=username, password_hash=password)
            logged_in_player = self.player_dao.checkLogin(p)

            if logged_in_player:
                self.log(f"[{addr_str}] Đăng nhập THÀNH CÔNG cho: '{username}'")
                return Response.success("Đăng nhập thành công!", logged_in_player)
            else:
                self.log(f"[{addr_str}] Đăng nhập THẤT BẠI cho: '{username}' (Sai tên hoặc mật khẩu)")
                return Response.fail("Sai tên đăng nhập hoặc mật khẩu!")

        # 2. ĐĂNG KÝ
        elif action == Action.REGISTER:
            user = req.user
            if not user or not user.username or not user.password_hash:
                return Response.fail("Thông tin đăng ký không hợp lệ!")

            self.log(f"[{addr_str}] Xử lý ĐĂNG KÝ tài khoản: '{user.username}'")

            # Bước 1: checkRegister kiểm tra xem username đã tồn tại chưa
            if not self.player_dao.checkRegister(user):
                self.log(f"[{addr_str}] Đăng ký THẤT BẠI: Tên đăng nhập '{user.username}' đã tồn tại!")
                return Response.fail("Tên đăng nhập đã tồn tại, vui lòng chọn tên khác!")

            # Bước 2: addPlayer tạo người chơi mới
            added = self.player_dao.addPlayer(user)
            if added:
                self.log(f"[{addr_str}] Đăng ký THÀNH CÔNG tài khoản: '{user.username}'")
                return Response.success("Đăng ký thành công!", user)
            else:
                self.log(f"[{addr_str}] Đăng ký THẤT BẠI khi lưu vào MySQL cho: '{user.username}'")
                return Response.fail("Đăng ký thất bại trong cơ sở dữ liệu!")

        # 3. LẤY THÔNG TIN NGƯỜI DÙNG
        elif action == Action.GET_USER:
            persis_id = req.persis_id or ""
            self.log(f"[{addr_str}] Lấy thông tin tài khoản: persis_id='{persis_id}'")

            player = self.player_dao.getPlayerByPersisId(persis_id)
            if player:
                return Response.success("Lấy thông tin thành công!", player)
            else:
                return Response.fail("Không tìm thấy thông tin người dùng!")

        # 4. CHỈNH SỬA THÔNG TIN NGƯỜI DÙNG
        elif action == Action.UPDATE_USER:
            user = req.user
            if not user or not user.persis_id:
                return Response.fail("Dữ liệu cập nhật không hợp lệ!")

            self.log(f"[{addr_str}] Xử lý CẬP NHẬT thông tin cho tài khoản: '{user.username}' (persis_id='{user.persis_id}')")

            # Bước 1: checkValid kiểm tra tính hợp lệ
            if not self.player_dao.checkValid(user):
                self.log(f"[{addr_str}] Cập nhật THẤT BẠI: Tên '{user.username}' đã có người sử dụng hoặc không hợp lệ!")
                return Response.fail("Tên đăng nhập này đã được người khác sử dụng!")

            # Bước 2: updatePlayer cập nhật
            updated = self.player_dao.updatePlayer(user)
            if updated:
                self.log(f"[{addr_str}] Cập nhật THÀNH CÔNG cho tài khoản: '{user.username}'")
                refreshed = self.player_dao.getPlayerByPersisId(user.persis_id)
                return Response.success("Cập nhật thông tin thành công!", refreshed or user)
            else:
                self.log(f"[{addr_str}] Cập nhật THẤT BẠI trong MySQL cho tài khoản: '{user.username}'")
                return Response.fail("Cập nhật thất bại trong cơ sở dữ liệu!")

        # 5. CẬP NHẬT ĐIỂM SỐ SAU MỖI LƯỢT CHƠI
        elif action == Action.UPDATE_SCORE:
            persis_id = req.persis_id or ""
            score = req.score
            self.log(f"[{addr_str}] Cập nhật điểm cho persis_id='{persis_id}', điểm mới={score}")

            self.player_dao.updateScore(persis_id, score)
            refreshed = self.player_dao.getPlayerByPersisId(persis_id)
            return Response.success("Cập nhật điểm số thành công!", refreshed)

        # 6. XEM BẢNG XẾP HẠNG
        elif action == Action.GET_LEADERBOARD:
            self.log(f"[{addr_str}] Xử lý LẤY BẢNG XẾP HẠNG...")
            rankings = self.player_ranking_dao.getPlayerRanking()
            self.log(f"[{addr_str}] Đã lấy {len(rankings)} bản ghi xếp hạng thành công.")

            # Trích xuất danh sách user có điểm và rank cho view Android (sắp xếp theo điểm giảm dần)
            leaderboard_data = []
            for r in rankings:
                p = r.player
                if p:
                    score_val = r.highest_point if r.highest_point is not None else p.score
                    leaderboard_data.append({
                        "persis_id": p.persis_id,
                        "username": p.username,
                        "score": score_val,
                        "total_points": r.total_points,
                        "total_wins": r.total_wins,
                    })

            return Response.success_leaderboard("Lấy bảng xếp hạng thành công!", leaderboard_data)

        else:
            return Response.error(f"Hành động '{action}' không được hỗ trợ!")
