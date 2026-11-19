# Hướng Dẫn Triển Khai FlappyBirdServer Lên Internet (Online Thực Sự)

Hệ thống đã được nâng cấp từ **TCP Socket nội bộ (cổng 8889)** sang **HTTPS REST API (`api_server.py`)** kèm xác thực **JWT** và băm mật khẩu **bcrypt/PBKDF2**, giúp ứng dụng Android kết nối xuyên mạng (4G/5G, Wi-Fi khác nhau) mà không cần chung mạng LAN.

---

## Bước 1: Tạo MySQL Database Online (Miễn phí)

Bạn có thể chọn một trong các dịch vụ Cloud MySQL sau:
- **Aiven for MySQL** (gói Free tier có MySQL 8 chuẩn)
- **TiDB Cloud Serverless** (gói Free, tương thích giao thức MySQL)
- **Railway MySQL**

Sau khi tạo xong, ghi lại các thông số kết nối:
- `DB_HOST`
- `DB_PORT` (thường `3306` hoặc cổng tùy chỉnh trên Aiven/Railway)
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME` (vd: `defaultdb` hoặc `railway` hoặc `flappy_bird_db`)
- Nếu dùng Aiven yêu cầu TLS, tải file `ca.pem` (hoặc copy nội dung PEM vào `DB_SSL_CA_PEM`) và đặt `DB_SSL_MODE=REQUIRED`.

---

## Bước 2: Deploy Backend Python lên Cloud PaaS (Miễn phí / Nhanh nhất)

### Cách A: Deploy lên Render (khuyên dùng)
1. Đưa thư mục `FlappyBirdServer` lên GitHub repository của bạn.
2. Đăng nhập [Render](https://render.com) -> **New +** -> **Web Service** (hoặc **Blueprint** dùng file `render.yaml` có sẵn).
3. Nếu tạo **Web Service** thủ công:
   - **Environment**: `Docker` (hoặc `Python 3`, Start Command: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`).
   - **Health Check Path**: `/health`.
4. Thêm các **Environment Variables** theo mẫu `.env.example`:
   - `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_SSL_MODE=REQUIRED`
   - `DB_SSL_CA_PEM` (nếu nhà cung cấp yêu cầu CA riêng)
   - `JWT_SECRET` (chuỗi ngẫu nhiên dài ít nhất 32 ký tự)
   - `AUTO_INIT_DB=true` (tự động nạp `schema.sql` ở lần khởi chạy đầu tiên nếu bảng `Player` chưa tồn tại)
5. Sau khi deploy xong, Render cấp cho bạn một URL HTTPS cố định, ví dụ:
   `https://flappybird-online-api.onrender.com`
6. Mở trình duyệt vào `https://flappybird-online-api.onrender.com/health`: nếu thấy `"database": "connected"` là thành công!

### Cách B: Deploy lên VPS Ubuntu (AWS EC2 / DigitalOcean / VPS Việt Nam)
1. Cài Docker và chạy:
   ```bash
   docker build -t flappybird-api .
   docker run -d --name flappybird-api --env-file .env -p 8000:8000 --restart unless-stopped flappybird-api
   ```
2. Dùng **Caddy** hoặc **Nginx + Let's Encrypt** trỏ domain về cổng `8000` để bật HTTPS (cổng `443`).

---

## Bước 3: Gắn URL Online Vào Ứng Dụng Android (`FlappyBird`)

1. Mở file `FlappyBird/gradle.properties` và cập nhật:
   ```properties
   FLAPPY_API_URL=https://flappybird-online-api.onrender.com
   ```
   *(Hoặc sửa trực tiếp trong `FlappyBird/app/build.gradle.kts`)*
2. Build lại APK (`Build -> Build APK(s)` trong Android Studio) rồi cài lên điện thoại.
3. Bạn cũng có thể đổi nhanh URL trực tiếp trên màn hình đăng nhập của app bằng cách chạm vào dòng trạng thái **Máy chủ Online** (không cần build lại app khi test).

---

## Chạy Thử Trên Máy Cá Nhân Trước Khi Deploy
1. Mở terminal tại thư mục `FlappyBirdServer`:
   ```bash
   python api_server.py
   ```
   (hoặc chạy `run_api.bat`).
2. Kiểm tra Swagger Docs tại `http://127.0.0.1:8000/docs`.
3. Trên Android Emulator, vào cấu hình server trong app nhập `http://10.0.2.2:8000` (bản `debug` đã cho phép HTTP local tới emulator/localhost, còn bản `release` mặc định bắt buộc HTTPS).
