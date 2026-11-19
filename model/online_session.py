from datetime import datetime
from typing import Optional

class OnlineSession:
    """
    Model thực thể OnlineSession theo thiết kế lớp thực thể PTIT
    - id : long / int
    - Presence : String
    - lastSeenAt : date / datetime
    """
    def __init__(self, id: Optional[int] = None, presence: str = "OFFLINE", last_seen_at: Optional[datetime] = None):
        self.id = id
        self.presence = presence
        self.last_seen_at = last_seen_at or datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "presence": self.presence,
            "lastSeenAt": self.last_seen_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(self.last_seen_at, datetime) else str(self.last_seen_at)
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(
            id=data.get("id"),
            presence=data.get("presence", "OFFLINE"),
            last_seen_at=data.get("lastSeenAt")
        )
