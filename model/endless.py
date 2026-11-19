from datetime import datetime
from typing import Optional
from .player import Player
from .obstacle_config import ObstacleConfig
from .player_result import PlayerResult

class Endless:
    """
    Model thực thể Endless theo thiết kế lớp thực thể PTIT
    - id : long
    - player : Player
    - status : String
    - startAt : date
    - obstacleConfig : ObstacleConfig
    - playerResult : PlayerResult
    """
    def __init__(
        self,
        id: Optional[int] = None,
        player: Optional[Player] = None,
        status: str = "IN_PROGRESS",
        start_at: Optional[datetime] = None,
        obstacle_config: Optional[ObstacleConfig] = None,
        player_result: Optional[PlayerResult] = None
    ):
        self.id = id
        self.player = player
        self.status = status
        self.start_at = start_at or datetime.now()
        self.obstacle_config = obstacle_config
        self.player_result = player_result

    def to_dict(self):
        return {
            "id": self.id,
            "player": self.player.to_dict() if self.player else None,
            "status": self.status,
            "startAt": str(self.start_at),
            "obstacleConfig": self.obstacle_config.to_dict() if self.obstacle_config else None,
            "playerResult": self.player_result.to_dict() if self.player_result else None
        }
