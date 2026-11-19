# BÁO CÁO PHÂN TÍCH TOÀN DIỆN FLAPPY BIRD SERVER

*Thời gian khởi tạo:* 2026-11-10 10:32:07  
*Phiên bản:* Python TCP Socket Server (Đồ án PTIT Nhóm 05)

---

## 1. Tổng Quan Mã Nguồn

- **Tổng số tệp mã nguồn Python:** `28`
- **Tổng số dòng mã (LOC):** `2,123`
- **Dòng mã thực thi (Code):** `1,828`
- **Dòng chú thích (Comments):** `61`

## 2. Kiến Trúc Phân Tầng (Layered Architecture)

| Tầng (Layer) | Vai trò | Danh sách tệp |
| :--- | :--- | :--- |
| **Controller** | Điều khiển máy chủ TCP, nhận kết nối, xử lý tiểu trình và điều phối nghiệp vụ | `controller\server_ctr.py, controller\server_listening.py, controller\__init__.py` |
| **DAO** | Kết nối cơ sở dữ liệu MySQL (PyMySQL) và thực thi câu truy vấn an toàn | `dao\dao.py, dao\player_dao.py, dao\player_ranking_dao.py, dao\__init__.py` |
| **Model** | Định nghĩa đối tượng thực thể (Player, Ranking, Request, Response,...) | `model\challenge.py, model\endless.py, model\ip_address.py, model\leaderboard.py, model\obstacle_config.py, model\online_session.py, model\player.py, model\player_ranking.py, model\player_result.py, model\pve_matches.py, model\pvp_matches.py, model\request.py, model\response.py, model\__init__.py` |
| **View** | Giao diện quản trị máy chủ bằng đồ họa Tkinter (`ServerMainFrm`) | `view\server_main_frm.py, view\__init__.py` |
| **Core/Entry** | Điểm khởi chạy hệ thống dòng lệnh và GUI (`server_main.py`, `config.py`) | `analyze_server.py, config.py, init_db.py, server_main.py, test_client.py` |

## 3. Giao Thức Mạng & Các Hành Động Socket (Protocol Actions)

Giao thức giao tiếp giữa Client Android và Python Server sử dụng **JSON qua TCP Socket theo dòng (Line-based JSON stream)**:

| Hành động (Action) | Dữ liệu gửi (Request) | Xử lý tại Server | Phản hồi (Response) |
| :--- | :--- | :--- | :--- |
| `LOGIN` | `username`, `password` | `PlayerDAO.checkLogin()` | Thông tin `User` & `persis_id` |
| `REGISTER` | `User` (username, pass, email) | `PlayerDAO.checkRegister()` & `addPlayer()` | Tạo bản ghi mới vào MySQL |
| `GET_USER` | `persis_id` | `PlayerDAO.getPlayerByPersisId()` | Chi tiết người chơi & điểm kỷ lục |
| `UPDATE_USER` | `User` (username, email, pass) | `PlayerDAO.checkValid()` & `updatePlayer()` | Trạng thái cập nhật thành công |
| `UPDATE_SCORE` | `persis_id`, `score` | `PlayerDAO.updateScore()` | Lưu điểm kỷ lục mới nếu cao hơn |
| `GET_LEADERBOARD` | Rỗng | `PlayerRankingDAO.getPlayerRanking()` | Danh sách xếp hạng sắp xếp điểm giảm dần |

## 4. Cơ Sở Dữ Liệu MySQL (`schema.sql`)

Hệ thống lưu trữ trên cơ sở dữ liệu MySQL `flappy_bird_db` gồm các bảng:

### Bảng `ObstacleConfig`
- **Cột:** id BIGINT(19), seed BIGINT(19), pipeSpawnInterval DECIMAL(19,, pipeGap DECIMAL(19,, baseSpeed DECIMAL(19,, overtimeStepPoints INT(10), speedIncrement DECIMAL(19,, ) ENGINE=InnoDB, -- 2.

### Bảng `Challenge`
- **Cột:** id INT(10), status VARCHAR(255), expiresAt DATETIME, CreatedAt DATETIME, ) ENGINE=InnoDB, -- 3.

### Bảng `PvPMatches`
- **Cột:** id INT(10), startAt DATETIME, status INT(10), Challengeid INT(10), ObstacleConfigid BIGINT(19), ) ENGINE=InnoDB, -- 4.

### Bảng `PvEMatches`
- **Cột:** id INT(10), startAt INT(10), status INT(10), botDifficulty INT(10), ObstacleConfigid BIGINT(19), ) ENGINE=InnoDB, -- 5.

### Bảng `Endless`
- **Cột:** id INT(10), status INT(10), startAt INT(10), ObstacleConfigid BIGINT(19), ) ENGINE=InnoDB, -- 6.

### Bảng `OnlineSession`
- **Cột:** id INT(10), Presence VARCHAR(255), lastSeenAt DATETIME, ) ENGINE=InnoDB, -- 7.

### Bảng `Player`
- **Cột:** id BIGINT(19), persis_id VARCHAR(64), username VARCHAR(255), password_hash VARCHAR(255), email VARCHAR(100), score INT(10), total_points INT(10), total_wins INT(10), total_losses INT(10), created_at TIMESTAMP, Challengeid INT(10), online_session_id INT(10), ) ENGINE=InnoDB, -- 8.

### Bảng `Leaderboard`
- **Cột:** id INT(10), category VARCHAR(255), ) ENGINE=InnoDB, -- 9.

### Bảng `PlayerRanking`
- **Cột:** Playerid BIGINT(19), rank INT(10), totalPoints INT(10), HighestPoint VARCHAR(255), totalWins INT(10), Leaderboardid INT(10), ) ENGINE=InnoDB, -- 10.

### Bảng `PlayerResult`
- **Cột:** id INT(10), totalPoint INT(10), outcome VARCHAR(255), Playerid BIGINT(19), PvPMatchesid INT(10), PvEMatchesid INT(10), Endlessid INT(10), ) ENGINE=InnoDB, -- 11.

### Bảng `users`
- **Cột:** persis_id VARCHAR(64), username VARCHAR(50), password VARCHAR(100), email VARCHAR(100), score INT, created_at TIMESTAMP, ) ENGINE=InnoDB, -- Dữ, INSERT INTO, ON DUPLICATE, -- Dữ, INSERT INTO, (1, 'usr_001',, (2, 'usr_002',, (3, 'usr_003',, (4, 'usr_004',, (5, 'usr_005',, (6, 'usr_006',, (7, 'usr_007',, (8, 'usr_008',, ON DUPLICATE, username =, password_hash =, score =, total_points =, total_wins =, -- Dữ, INSERT INTO, (1, 1,, (2, 2,, (3, 3,, (4, 4,, (5, 5,, (6, 6,, (7, 7,, (8, 8,, ON DUPLICATE, rank =, totalPoints =, HighestPoint =, totalWins =, -- Đồng, INSERT INTO, SELECT persis_id,, ON DUPLICATE, username =, password =, email =, score =

## 5. Đánh Giá Điểm Mạnh & Đề Xuất Nâng Cấp

### Điểm mạnh:
1. **Kiến trúc phân tầng chuẩn mực:** Tách biệt rành mạch giữa Controller, Model, DAO và View theo chuẩn đồ án phần mềm PTIT.
2. **Kết nối phi trạng thái (Stateless On-Demand):** Client chỉ kết nối khi cần gửi packet và đóng socket ngay, giúp không bao giờ bị nghẽn hay stale socket.
3. **Hỗ trợ chạy linh hoạt:** Có cả chế độ Terminal CLI đơn giản lẫn chế độ GUI Tkinter trực quan.
4. **Tối ưu bảng xếp hạng:** Xếp hạng điểm từ cao nhất đến thấp nhất (`highestPoint DESC`).

### Đề xuất mở rộng:
1. **Mã hóa mật khẩu:** Hiện tại đang so sánh mật khẩu dạng chuỗi text hoặc hash đơn giản, nên nâng cấp lên thuật toán `bcrypt` hoặc `pbkdf2_sha256`.
2. **Connection Pool:** Cải tiến quản lý kết nối MySQL bằng thư viện Connection Pooling (như `DBUtils` hoặc `mysql-connector-python pooling`) khi có lượng người chơi đồng thời lớn.
3. **Bổ sung tính năng PVP thời gian thực:** Tận dụng các Model đã định nghĩa sẵn như `PVPMatches`, `Challenge` để làm chế độ đấu 2 người trực tiếp.
