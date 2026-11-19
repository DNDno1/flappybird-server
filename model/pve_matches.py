from datetime import datetime
from typing import Optional
from .player import Player
from .obstacle_config import ObstacleConfig
from .player_result import PlayerResult

class PvEMatches:
    """
    Model thực thể PvEMatches theo thiết kế lớp thực thể PTIT
    - id : long
    - player : Player
    - startAt : date
    - status : String
    - botDifficulty : String
    - obstacleConfig : ObstacleConfig
    - playerResult : PlayerResult
    """
    def __init__(
        self,
        id: Optional[int] = None,
        player: Optional[Player] = None,
        start_at: Optional[datetime] = None,
        status: str = "IN_PROGRESS",
        bot_difficulty: str = "NORMAL",
        obstacle_config: Optional[ObstacleConfig] = None,
        player_result: Optional[PlayerResult] = None
    ):
        self.id = id
        self.player = player
        self.start_at = start_at or datetime.now()
        self.status = status
        self.bot_difficulty = bot_difficulty
        self.obstacle_config = obstacle_config
        self.player_result = player_result

    def to_dict(self):
        return {
            "id": self.id,
            "player": self.player.to_dict() if self.player else None,
            "startAt": str(self.start_at),
            "status": self.status,
            "botDifficulty": self.bot_difficulty,
            "obstacleConfig": self.obstacle_config.to_dict() if self.obstacle_config else None,
            "playerResult": self.player_result.to_dict() if self.player_result else None
        }
