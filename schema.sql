-- =======================================================
-- FLAPPY BIRD DATABASE SCHEMA (MySQL 8.0+)
-- HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
-- BỘ MÔN: LẬP TRÌNH MOBILE - NHÓM 05
-- =======================================================

CREATE DATABASE IF NOT EXISTS flappy_bird_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE flappy_bird_db;

-- 1. Bảng ObstacleConfig (Cấu hình chướng ngại vật)
CREATE TABLE IF NOT EXISTS ObstacleConfig (
    id BIGINT(19) AUTO_INCREMENT PRIMARY KEY,
    seed BIGINT(19) DEFAULT 0,
    pipeSpawnInterval DECIMAL(19, 0) DEFAULT 100,
    pipeGap DECIMAL(19, 0) DEFAULT 120,
    baseSpeed DECIMAL(19, 0) DEFAULT 5,
    overtimeStepPoints INT(10) DEFAULT 10,
    speedIncrement DECIMAL(19, 0) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Bảng Challenge (Thách đấu)
CREATE TABLE IF NOT EXISTS Challenge (
    id INT(10) AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(255) DEFAULT 'PENDING',
    expiresAt DATETIME NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Bảng PvPMatches (Trận đấu người vs người)
CREATE TABLE IF NOT EXISTS PvPMatches (
    id INT(10) AUTO_INCREMENT PRIMARY KEY,
    startAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    status INT(10) DEFAULT 0,
    Challengeid INT(10) NULL,
    ObstacleConfigid BIGINT(19) NULL,
    FOREIGN KEY (Challengeid) REFERENCES Challenge(id) ON DELETE SET NULL,
    FOREIGN KEY (ObstacleConfigid) REFERENCES ObstacleConfig(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Bảng PvEMatches (Trận đấu người vs máy)
CREATE TABLE IF NOT EXISTS PvEMatches (
    id INT(10) AUTO_INCREMENT PRIMARY KEY,
    startAt INT(10) DEFAULT 0,
    status INT(10) DEFAULT 0,
    botDifficulty INT(10) DEFAULT 1,
    ObstacleConfigid BIGINT(19) NULL,
    FOREIGN KEY (ObstacleConfigid) REFERENCES ObstacleConfig(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Bảng Endless (Chế độ chơi vô tận)
CREATE TABLE IF NOT EXISTS Endless (
    id INT(10) AUTO_INCREMENT PRIMARY KEY,
    status INT(10) DEFAULT 0,
    startAt INT(10) DEFAULT 0,
    ObstacleConfigid BIGINT(19) NULL,
    FOREIGN KEY (ObstacleConfigid) REFERENCES ObstacleConfig(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Bảng OnlineSession (Phiên trực tuyến của người chơi)
CREATE TABLE IF NOT EXISTS OnlineSession (
    id INT(10) AUTO_INCREMENT PRIMARY KEY,
    Presence VARCHAR(255) DEFAULT 'OFFLINE',
    lastSeenAt DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Bảng Player (Người chơi)
CREATE TABLE IF NOT EXISTS Player (
    id BIGINT(19) AUTO_INCREMENT PRIMARY KEY,
    persis_id VARCHAR(64) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NULL,
    score INT(10) DEFAULT 0,
    total_points INT(10) DEFAULT 0,
    total_wins INT(10) DEFAULT 0,
    total_losses INT(10) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Challengeid INT(10) NULL,
    online_session_id INT(10) NULL,
    FOREIGN KEY (Challengeid) REFERENCES Challenge(id) ON DELETE SET NULL,
    FOREIGN KEY (online_session_id) REFERENCES OnlineSession(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Bảng Leaderboard (Bảng xếp hạng theo danh mục)
CREATE TABLE IF NOT EXISTS Leaderboard (
    id INT(10) AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(255) DEFAULT 'All Time'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Bảng PlayerRanking (Xếp hạng người chơi)
CREATE TABLE IF NOT EXISTS PlayerRanking (
    Playerid BIGINT(19) PRIMARY KEY,
    `rank` INT(10) DEFAULT 0,
    totalPoints INT(10) DEFAULT 0,
    HighestPoint VARCHAR(255) DEFAULT '0',
    totalWins INT(10) DEFAULT 0,
    Leaderboardid INT(10) NULL,
    FOREIGN KEY (Playerid) REFERENCES Player(id) ON DELETE CASCADE,
    FOREIGN KEY (Leaderboardid) REFERENCES Leaderboard(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Bảng PlayerResult (Kết quả màn chơi)
CREATE TABLE IF NOT EXISTS PlayerResult (
    id INT(10) AUTO_INCREMENT PRIMARY KEY,
    totalPoint INT(10) DEFAULT 0,
    outcome VARCHAR(255) DEFAULT 'NONE',
    Playerid BIGINT(19) NULL,
    PvPMatchesid INT(10) NULL,
    PvEMatchesid INT(10) NULL,
    Endlessid INT(10) NULL,
    FOREIGN KEY (Playerid) REFERENCES Player(id) ON DELETE CASCADE,
    FOREIGN KEY (PvPMatchesid) REFERENCES PvPMatches(id) ON DELETE SET NULL,
    FOREIGN KEY (PvEMatchesid) REFERENCES PvEMatches(id) ON DELETE SET NULL,
    FOREIGN KEY (Endlessid) REFERENCES Endless(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Bảng users (Tương thích ngược với app FlappyBird đã có)
CREATE TABLE IF NOT EXISTS users (
    persis_id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dữ liệu mẫu Leaderboard
INSERT INTO Leaderboard (id, category) VALUES (1, 'All Time')
ON DUPLICATE KEY UPDATE category = VALUES(category);

-- Dữ liệu mẫu Player (theo báo cáo PTIT Nhóm 05)
INSERT INTO Player (id, persis_id, username, password_hash, email, score, total_points, total_wins) VALUES
(1, 'usr_001', 'Hip', '123456', 'hip@ptit.edu.vn', 500, 1200, 119),
(2, 'usr_002', 'Pity', '123456', 'pity@ptit.edu.vn', 300, 1200, 123),
(3, 'usr_003', 'Hopyt', '123456', 'hopyt@ptit.edu.vn', 450, 1100, 95),
(4, 'usr_004', 'Yoshi', '123456', 'yoshi@ptit.edu.vn', 320, 990, 80),
(5, 'usr_005', 'Naoma', '123456', 'naoma@ptit.edu.vn', 280, 970, 75),
(6, 'usr_006', 'ProPTIT', '123456', 'proptit@ptit.edu.vn', 250, 800, 60),
(7, 'usr_007', 'BirdMaster', '123456', 'birdmaster@flappy.com', 185, 185, 10),
(8, 'usr_008', 'player1', '123456', 'player1@flappy.com', 35, 35, 2)
ON DUPLICATE KEY UPDATE 
    username = VALUES(username),
    password_hash = VALUES(password_hash),
    score = VALUES(score),
    total_points = VALUES(total_points),
    total_wins = VALUES(total_wins);

-- Dữ liệu mẫu PlayerRanking (theo đúng bảng trong tài liệu báo cáo)
INSERT INTO PlayerRanking (Playerid, `rank`, totalPoints, HighestPoint, totalWins, Leaderboardid) VALUES
(1, 1, 1200, '500', 119, 1),
(2, 2, 1200, '300', 123, 1),
(3, 3, 1100, '450', 95, 1),
(4, 4, 990, '320', 80, 1),
(5, 5, 970, '280', 75, 1),
(6, 6, 800, '250', 60, 1),
(7, 7, 185, '185', 10, 1),
(8, 8, 35, '35', 2, 1)
ON DUPLICATE KEY UPDATE
    `rank` = VALUES(`rank`),
    totalPoints = VALUES(totalPoints),
    HighestPoint = VALUES(HighestPoint),
    totalWins = VALUES(totalWins);

-- Đồng bộ sang bảng users để tương thích hoàn toàn
INSERT INTO users (persis_id, username, password, email, score)
SELECT persis_id, username, password_hash, email, score FROM Player
ON DUPLICATE KEY UPDATE 
    username = VALUES(username),
    password = VALUES(password),
    email = VALUES(email),
    score = VALUES(score);

