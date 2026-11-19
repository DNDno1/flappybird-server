from datetime import datetime
from typing import Optional, List
from .challenge import Challenge
from .obstacle_config import ObstacleConfig

class PvPMatches:
    """
    Model thực thể PvPMatches theo thiết kế lớp thực thể PTIT
    - id : long
    - startAt : date
    - status : String
    - challenge : Challenge
    - obstacleConfig : ObstacleConfig
    - playerResult : PlayerResult[]
    """
    def __init__(
        self,
        id: Optional[int] = None,
        start_at: Optional[datetime] = None,
        status: str = "WAITING",
        challenge: Optional[Challenge] = None,
        obstacle_config: Optional[ObstacleConfig] = None,
        player_results: Optional[List] = None
    ):
        self.id = id
        self.start_at = start_at or datetime.now()
        self.status = status
        self.challenge = challenge
        self.obstacle_config = obstacle_config
        self.player_results = player_results or []

    def to_dict(self):
        return {
            "id": self.id,
            "startAt": str(self.start_at),
            "status": self.status,
            "challenge": self.challenge.to_dict() if self.challenge else None,
            "obstacleConfig": self.obstacle_config.to_dict() if self.obstacle_config else None
        }
