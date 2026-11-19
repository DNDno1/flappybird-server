import socket
from typing import Optional
from config import SERVER_CONFIG
from model.ip_address import IPAddress
from .server_listening import ServerListening

class ServerCtr:
    """
    Lớp điều khiển máy chủ ServerCtr theo Thiết kế Biểu đồ lớp chi tiết PTIT:
    - myAddress : IPAddress
    - myServer : ServerSocket (socket.socket trong Python)
    - myListening : ServerListening
    + ServerCtr(v : ServerMainFrm, p : int)
    + openServer(p : int)
    + closeServer()
    """
    def __init__(self, view=None, port: int = None):
        if port is None:
            port = SERVER_CONFIG.get('port', 8889)
        self.view = view
        self.myAddress = IPAddress(host="0.0.0.0", port=port)
        self.myServer: Optional[socket.socket] = None
        self.myListening: Optional[ServerListening] = None
        self.is_running = False

    def openServer(self, port: int = None) -> bool:
        """
        Khởi tạo ServerSocket lắng nghe trên cổng được chỉ định,
        sau đó khởi tạo và start luồng ServerListening
        """
        if port is None:
            port = self.myAddress.port or SERVER_CONFIG.get('port', 8889)
        if self.is_running:
            self._log("[ServerCtr] Máy chủ đã đang hoạt động!")
            return True

        self.myAddress.port = port
        try:
            self.myServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Cho phép tái sử dụng cổng ngay sau khi đóng
            self.myServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.myServer.bind((self.myAddress.host, self.myAddress.port))
            self.myServer.listen(50)
            self.is_running = True

            self._log(f"[ServerCtr] ✅ ServerSocket đã mở thành công tại cổng: {port}")

            # Khởi động tiểu trình lắng nghe ServerListening
            self.myListening = ServerListening(self)
            self.myListening.start()

            if self.view and hasattr(self.view, "setServerInfo"):
                self.view.setServerInfo(self.myAddress)

            return True

        except Exception as e:
            self._log(f"[ServerCtr] ❌ Lỗi không thể mở Server trên cổng {port}: {e}")
            self.closeServer()
            return False

    def closeServer(self):
        """
        Đóng ServerSocket và dừng ServerListening
        """
        self.is_running = False

        if self.myListening:
            self.myListening.is_running = False

        if self.myServer:
            try:
                self.myServer.close()
            except Exception:
                pass
            self.myServer = None

        self._log("[ServerCtr] 🛑 Máy chủ ServerSocket đã đóng.")

    def _log(self, message: str):
        print(message, flush=True)
        if self.view and hasattr(self.view, "showMessage"):
            self.view.showMessage(message)
