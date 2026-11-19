from datetime import datetime
from typing import Optional, List

class Challenge:
    """
    Model thực thể Challenge theo thiết kế lớp thực thể PTIT
    - id : long
    - status : String
    - player : Player[]
    - expiresAt : date
    - createdAt : date
    """
    def __init__(
        self,
        id: Optional[int] = None,
        status: str = "PENDING",
        players: Optional[List] = None,
        expires_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.status = status
        self.players = players or []
        self.expires_at = expires_at
        self.created_at = created_at or datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "expiresAt": str(self.expires_at) if self.expires_at else None,
            "createdAt": str(self.created_at)
        }
