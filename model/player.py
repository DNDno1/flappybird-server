from datetime import datetime
from typing import Optional
from .online_session import OnlineSession


class Player:
    """
    Model thực thể Player theo thiết kế lớp thực thể & CSDL PTIT
    - id : long / int
    - persis_id : String (mã định danh duy nhất cho app FlappyBird)
    - username : String
    - password_hash : String (mật khẩu đã băm)
    - email : String
    - score : int (điểm kỷ lục trong game)
    - total_points : int (tổng điểm)
    - total_wins : int (tổng số trận thắng)
    - total_losses : int (tổng số trận thua)
    - created_at : datetime
    - onlineSession : OnlineSession
    """

    def __init__(
        self,
        id: Optional[int] = None,
        persis_id: Optional[str] = None,
        username: str = "",
        password_hash: str = "",
        email: Optional[str] = "",
        score: int = 0,
        total_points: int = 0,
        total_wins: int = 0,
        total_losses: int = 0,
        created_at: Optional[datetime] = None,
        online_session: Optional[OnlineSession] = None,
        challenge_id: Optional[int] = None,
    ):
        self.id = id
        self.persis_id = persis_id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.score = score
        self.total_points = total_points if total_points != 0 else score
        self.total_wins = total_wins
        self.total_losses = total_losses
        self.created_at = created_at or datetime.now()
        self.online_session = online_session
        self.challenge_id = challenge_id

    @property
    def password(self) -> str:
        return self.password_hash

    @password.setter
    def password(self, val: str):
        self.password_hash = val

    def to_public_dict(self, include_email: bool = False) -> dict:
        """
        Chuyển đổi sang Dictionary an toàn để trả về qua API/Socket.
        Tuyệt đối không trả password hay password_hash về client.
        """
        data = {
            "id": self.id,
            "persis_id": self.persis_id,
            "username": self.username,
            "score": self.score,
            "total_points": self.total_points,
            "total_wins": self.total_wins,
            "total_losses": self.total_losses,
            "created_at": (
                self.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if isinstance(self.created_at, datetime)
                else str(self.created_at)
            ),
        }
        if include_email:
            data["email"] = self.email or ""
        return data

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Mặc định ẩn mật khẩu; chỉ include_email=True cho chủ tài khoản."""
        data = self.to_public_dict(include_email=True)
        if include_sensitive:
            data["password"] = self.password_hash
            data["password_hash"] = self.password_hash
        return data

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(
            id=data.get("id"),
            persis_id=data.get("persis_id") or data.get("persisId"),
            username=data.get("username", ""),
            password_hash=data.get("password") or data.get("password_hash", ""),
            email=data.get("email", ""),
            score=int(data.get("score", 0)),
            total_points=int(data.get("total_points", data.get("score", 0))),
            total_wins=int(data.get("total_wins", 0)),
            total_losses=int(data.get("total_losses", 0)),
        )
