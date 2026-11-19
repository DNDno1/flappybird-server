import uuid
from typing import Optional

from .dao import DAO
from model.player import Player
from security import hash_password, is_password_hashed, verify_password


class PlayerDAO(DAO):
    """
    Lớp PlayerDAO kế thừa từ DAO, thực hiện các thao tác dữ liệu với bảng Player.
    """

    def __init__(self):
        super().__init__()

    def checkLogin(self, p: Player) -> Optional[Player]:
        """
        Kiểm tra đăng nhập người dùng bằng username và mật khẩu.
        Hỗ trợ xác thực hash an toàn và tự động nâng cấp mật khẩu seed cũ sang hash.
        """
        if not p or not p.username or not p.password_hash:
            return None

        sql = """
            SELECT id, persis_id, username, password_hash, email, score,
                   total_points, total_wins, total_losses, created_at
            FROM Player
            WHERE username = %s
        """
        row = self.execute_query(sql, (p.username.strip(),), fetchone=True)
        if not row:
            return None

        stored_hash = row.get("password_hash") or ""
        is_valid, needs_rehash = verify_password(p.password_hash, stored_hash)
        if not is_valid:
            return None

        if needs_rehash:
            try:
                upgraded_hash = hash_password(p.password_hash)
                self.execute_write(
                    "UPDATE Player SET password_hash = %s WHERE id = %s",
                    (upgraded_hash, row["id"]),
                )
                self.execute_write(
                    "UPDATE users SET password = %s WHERE persis_id = %s",
                    (upgraded_hash, row["persis_id"]),
                )
                row["password_hash"] = upgraded_hash
            except Exception as e:
                print(f"[PlayerDAO.checkLogin] Không thể nâng cấp password hash: {e}")

        return self._map_row_to_player(row)

    def checkRegister(self, p: Player) -> bool:
        """
        Kiểm tra tính hợp lệ khi đăng ký (username đã tồn tại chưa).
        Trả về True nếu username chưa ai dùng, False nếu đã bị trùng.
        """
        if not p or not p.username:
            return False

        sql = "SELECT id FROM Player WHERE username = %s"
        row = self.execute_query(sql, (p.username.strip(),), fetchone=True)
        return row is None

    def addPlayer(self, p: Player) -> bool:
        """
        Thêm mới người chơi vào MySQL với mật khẩu đã băm an toàn.
        Đồng thời tạo bản ghi xếp hạng ban đầu trong PlayerRanking và users.
        """
        if not p or not p.username or not p.password_hash:
            return False

        username = p.username.strip()
        p.username = username

        if not p.persis_id:
            p.persis_id = f"usr_{uuid.uuid4().hex[:8]}"

        hashed_pw = (
            p.password_hash
            if is_password_hashed(p.password_hash)
            else hash_password(p.password_hash)
        )

        sql_player = """
            INSERT INTO Player (persis_id, username, password_hash, email, score, total_points, total_wins, total_losses)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            p.persis_id,
            username,
            hashed_pw,
            (p.email or "").strip(),
            p.score,
            p.total_points,
            p.total_wins,
            p.total_losses,
        )
        ok, affected = self.execute_write(sql_player, params)
        if ok and affected > 0:
            inserted = self.getPlayerByPersisId(p.persis_id)
            if inserted and inserted.id:
                p.id = inserted.id
                sql_ranking = """
                    INSERT INTO PlayerRanking (Playerid, `rank`, totalPoints, HighestPoint, totalWins, Leaderboardid)
                    VALUES (%s, 999, %s, %s, %s, 1)
                    ON DUPLICATE KEY UPDATE totalPoints = VALUES(totalPoints), HighestPoint = VALUES(HighestPoint)
                """
                self.execute_write(sql_ranking, (p.id, p.total_points, str(p.score), p.total_wins))

            sql_users = """
                INSERT INTO users (persis_id, username, password, email, score)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE username = VALUES(username), password = VALUES(password), email = VALUES(email)
            """
            self.execute_write(sql_users, (p.persis_id, username, hashed_pw, (p.email or "").strip(), p.score))
            p.password_hash = ""
            return True
        return False

    def checkValid(self, p: Player) -> bool:
        """
        Kiểm tra tính hợp lệ khi sửa thông tin cá nhân:
        - Người dùng phải tồn tại theo persis_id
        - Nếu username thay đổi, không được trùng với người chơi khác
        """
        if not p or not p.persis_id:
            return False

        existing = self.getPlayerByPersisId(p.persis_id)
        if not existing:
            return False

        new_username = (p.username or "").strip()
        if new_username and new_username.lower() != existing.username.lower():
            sql = "SELECT id FROM Player WHERE username = %s AND persis_id != %s"
            duplicate = self.execute_query(sql, (new_username, p.persis_id), fetchone=True)
            if duplicate:
                return False

        return True

    def updatePlayer(self, p: Player, new_password: Optional[str] = None) -> bool:
        """
        Cập nhật thông tin cá nhân (username, email, và mật khẩu mới nếu có).
        Nếu không truyền mật khẩu mới, giữ nguyên password_hash hiện có trong DB.
        """
        if not p or not p.persis_id:
            return False

        existing = self.getPlayerByPersisId(p.persis_id)
        if not existing:
            return False

        raw_pw = new_password if new_password is not None else p.password_hash
        raw_pw = (raw_pw or "").strip()
        username = (p.username or existing.username).strip()
        email = (p.email if p.email is not None else existing.email or "").strip()

        if raw_pw:
            hashed_pw = raw_pw if is_password_hashed(raw_pw) else hash_password(raw_pw)
            sql_player = """
                UPDATE Player
                SET username = %s, password_hash = %s, email = %s
                WHERE persis_id = %s
            """
            ok, _ = self.execute_write(sql_player, (username, hashed_pw, email, p.persis_id))
            if not ok:
                return False
            self.execute_write(
                "UPDATE users SET username = %s, password = %s, email = %s WHERE persis_id = %s",
                (username, hashed_pw, email, p.persis_id),
            )
        else:
            sql_player = """
                UPDATE Player
                SET username = %s, email = %s
                WHERE persis_id = %s
            """
            ok, _ = self.execute_write(sql_player, (username, email, p.persis_id))
            if not ok:
                return False
            self.execute_write(
                "UPDATE users SET username = %s, email = %s WHERE persis_id = %s",
                (username, email, p.persis_id),
            )

        return True

    def getPlayerByPersisId(self, persis_id: str) -> Optional[Player]:
        """Lấy thông tin người chơi theo persis_id."""
        if not persis_id:
            return None

        sql = """
            SELECT id, persis_id, username, email, score,
                   total_points, total_wins, total_losses, created_at
            FROM Player
            WHERE persis_id = %s
        """
        row = self.execute_query(sql, (persis_id,), fetchone=True)
        if row:
            return self._map_row_to_player(row)
        return None

    def updateScore(self, persis_id: str, new_score: int) -> bool:
        """
        Cập nhật điểm kỷ lục cho người chơi nếu điểm mới cao hơn điểm hiện tại.
        """
        if not persis_id or new_score < 0:
            return False

        existing = self.getPlayerByPersisId(persis_id)
        if not existing:
            return False

        sql_player = """
            UPDATE Player
            SET score = GREATEST(score, %s),
                total_points = GREATEST(total_points, %s)
            WHERE persis_id = %s
        """
        ok, _ = self.execute_write(sql_player, (new_score, new_score, persis_id))
        if not ok:
            return False

        sql_users = "UPDATE users SET score = GREATEST(score, %s) WHERE persis_id = %s"
        self.execute_write(sql_users, (new_score, persis_id))

        player = self.getPlayerByPersisId(persis_id)
        if player and player.id:
            sql_ranking = """
                INSERT INTO PlayerRanking (Playerid, `rank`, totalPoints, HighestPoint, totalWins, Leaderboardid)
                VALUES (%s, 999, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE
                    HighestPoint = CAST(GREATEST(CAST(COALESCE(HighestPoint, '0') AS UNSIGNED), %s) AS CHAR),
                    totalPoints = GREATEST(totalPoints, %s)
            """
            self.execute_write(
                sql_ranking,
                (player.id, player.score, str(player.score), player.total_wins, player.score, player.score),
            )

        return True

    def _map_row_to_player(self, row: dict) -> Player:
        """Ánh xạ hàng dữ liệu MySQL sang Model Player (không giữ password_hash trong bộ nhớ)."""
        return Player(
            id=row.get("id"),
            persis_id=row.get("persis_id"),
            username=row.get("username", ""),
            password_hash="",
            email=row.get("email", ""),
            score=int(row.get("score", 0)),
            total_points=int(row.get("total_points", row.get("score", 0))),
            total_wins=int(row.get("total_wins", 0)),
            total_losses=int(row.get("total_losses", 0)),
            created_at=row.get("created_at"),
        )
