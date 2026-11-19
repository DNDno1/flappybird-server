import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import subprocess
from datetime import datetime
from model.ip_address import IPAddress
from controller.server_ctr import ServerCtr

class ServerMainFrm:
    """
    Giao diện điều khiển máy chủ ServerMainFrm theo đúng Thiết kế Biểu đồ lớp PTIT:
    - btnStartServer : Button
    - btnStopServer : Button
    - mainText : TextView (scrolledtext trong Python Tkinter)
    - myServer : ServerCtr
    - txtServerHost : TextView / Entry
    - txtServerPort : TextView / Entry
    + ServerMainFrm()
    + onClick(v : View)
    + showMessage(s : String)
    + setServerInfo(a : IPAddress)
    """
    def __init__(self, root=None, default_port: int = 8888):
        self.is_standalone = root is None
        self.root = root or tk.Tk()
        self.root.title("Flappy Bird Server - PTIT Mobile Programming (Nhóm 05)")
        self.root.geometry("820x620")
        self.root.minsize(700, 500)

        # Khởi tạo Server Controller
        self.myServer = ServerCtr(view=self, port=default_port)

        self._init_ui(default_port)
        self._detect_local_ips()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_ui(self, default_port: int):
        # Thiết lập style hiện đại
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # 1. Header Frame
        header_frame = tk.Frame(self.root, bg="#1a365d", padx=15, pady=12)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="FLAPPY BIRD TCP SOCKET SERVER (MySQL)",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#1a365d"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header_frame,
            text="PTIT - Môn Lập trình Di Động | Nhóm 05: Nguyễn Bá Duy & Nguyễn Đức Dương",
            font=("Arial", 10),
            fg="#cbd5e1",
            bg="#1a365d"
        )
        sub_lbl.pack(anchor="w", pady=(3, 0))

        # 2. Control & Config Frame
        control_frame = ttk.LabelFrame(self.root, text=" Cấu hình & Trạng thái Máy chủ ", padding=12)
        control_frame.pack(fill=tk.X, padx=15, pady=10)

        # Host & Port row
        row1 = tk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=4)

        tk.Label(row1, text="Server Host:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.txtServerHost = ttk.Entry(row1, width=20)
        self.txtServerHost.insert(0, "0.0.0.0 (Tất cả mạng)")
        self.txtServerHost.config(state="readonly")
        self.txtServerHost.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(row1, text="Server Port:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.txtServerPort = ttk.Entry(row1, width=10)
        self.txtServerPort.insert(0, str(default_port))
        self.txtServerPort.pack(side=tk.LEFT, padx=(0, 25))

        # Buttons
        self.btnStartServer = tk.Button(
            row1,
            text="▶ Khởi động Server",
            font=("Arial", 10, "bold"),
            bg="#16a34a",
            fg="white",
            padx=14,
            pady=4,
            relief=tk.RAISED,
            command=lambda: self.onClick("start")
        )
        self.btnStartServer.pack(side=tk.LEFT, padx=(0, 10))

        self.btnStopServer = tk.Button(
            row1,
            text="⏹ Dừng Server",
            font=("Arial", 10, "bold"),
            bg="#dc2626",
            fg="white",
            padx=14,
            pady=4,
            state=tk.DISABLED,
            relief=tk.RAISED,
            command=lambda: self.onClick("stop")
        )
        self.btnStopServer.pack(side=tk.LEFT)

        # IP Detection & ADB row
        row2 = tk.Frame(control_frame)
        row2.pack(fill=tk.X, pady=(8, 0))

        self.lblDetectedIp = tk.Label(
            row2,
            text="Địa chỉ kết nối từ Android: Đang quét...",
            font=("Arial", 9),
            fg="#2563eb"
        )
        self.lblDetectedIp.pack(side=tk.LEFT)

        btn_adb = tk.Button(
            row2,
            text="⚡ Cài đặt ADB Reverse (Cáp USB)",
            font=("Arial", 8),
            bg="#f1f5f9",
            padx=8,
            command=self._setup_adb_reverse
        )
        btn_adb.pack(side=tk.RIGHT)

        # 3. Log Frame (mainText)
        log_frame = ttk.LabelFrame(self.root, text=" Nhật ký hoạt động máy chủ (Activity Logs) ", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.mainText = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#0f172a",
            fg="#f8fafc",
            insertbackground="white"
        )
        self.mainText.pack(fill=tk.BOTH, expand=True)

        # Clear logs button
        btn_clear = tk.Button(
            log_frame,
            text="Xóa nhật ký",
            font=("Arial", 8),
            command=lambda: self.mainText.delete("1.0", tk.END)
        )
        btn_clear.pack(anchor="e", pady=(5, 0))

    def _detect_local_ips(self):
        """Tự động phát hiện IP LAN Wi-Fi của máy để hiển thị cho người dùng tiện kết nối Android"""
        lan_ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            lan_ip = s.getsockname()[0]
            s.close()
        except Exception:
            pass

        self.lblDetectedIp.config(
            text=f"💡 IP kết nối app Android: Wi-Fi: {lan_ip} | Máy ảo: 10.0.2.2 | Cáp USB: 127.0.0.1"
        )

    def _setup_adb_reverse(self):
        """Hỗ trợ tự động chạy adb reverse tcp:8888 tcp:8888 khi cắm cáp USB điện thoại"""
        port = self.txtServerPort.get().strip() or "8888"
        try:
            res = subprocess.run(["adb", "reverse", f"tcp:{port}", f"tcp:{port}"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                self.showMessage(f"⚡ [ADB] Đã reverse thành công cổng {port} qua cáp USB!")
                messagebox.showinfo("ADB Reverse", f"Đã kết nối cổng {port} qua cáp USB thành công!\nTrên điện thoại hãy điền IP: 127.0.0.1")
            else:
                self.showMessage(f"⚠️ [ADB] Không tìm thấy thiết bị hoặc lỗi ADB: {res.stderr.strip()}")
                messagebox.showwarning("ADB Warning", f"Lỗi ADB: {res.stderr.strip()}\nVui lòng bật USB Debugging trên điện thoại!")
        except Exception as e:
            self.showMessage(f"⚠️ [ADB] Lỗi khi chạy lệnh adb: {e}")
            messagebox.showinfo("ADB Tip", f"Để dùng USB, hãy chạy thủ công trong platform-tools:\nadb reverse tcp:{port} tcp:{port}")

    def onClick(self, view_action: str):
        """Xử lý sự kiện nhấn nút theo Biểu đồ tuần tự PTIT"""
        if view_action == "start":
            port_str = self.txtServerPort.get().strip()
            try:
                port = int(port_str)
                if port <= 0 or port > 65535:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Lỗi cổng", "Cổng kết nối phải là một số nguyên từ 1 đến 65535!")
                return

            self.showMessage(f"--- Đang mở máy chủ tại cổng {port} ---")
            success = self.myServer.openServer(port)
            if success:
                self.btnStartServer.config(state=tk.DISABLED, bg="#9ca3af")
                self.btnStopServer.config(state=tk.NORMAL, bg="#dc2626")
                self.txtServerPort.config(state="readonly")
            else:
                messagebox.showerror("Khởi động thất bại", f"Không thể mở cổng {port}! Vui lòng kiểm tra lại xem cổng đã có ứng dụng nào dùng chưa.")

        elif view_action == "stop":
            self.showMessage("--- Đang dừng máy chủ ---")
            self.myServer.closeServer()
            self.btnStartServer.config(state=tk.NORMAL, bg="#16a34a")
            self.btnStopServer.config(state=tk.DISABLED, bg="#9ca3af")
            self.txtServerPort.config(state="normal")

    def showMessage(self, s: str):
        """Hiển thị thông báo trên giao diện ServerMainFrm một cách an toàn luồng (thread-safe)"""
        def append_text():
            if self.mainText:
                self.mainText.insert(tk.END, s + "\n")
                self.mainText.see(tk.END)
        self.root.after(0, append_text)

    def setServerInfo(self, a: IPAddress):
        """Cập nhật thông tin địa chỉ máy chủ theo Biểu đồ lớp chi tiết"""
        def update_info():
            self.txtServerHost.config(state="normal")
            self.txtServerHost.delete(0, tk.END)
            self.txtServerHost.insert(0, str(a.host))
            self.txtServerHost.config(state="readonly")
        self.root.after(0, update_info)

    def _on_close(self):
        if self.myServer and self.myServer.is_running:
            self.myServer.closeServer()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
