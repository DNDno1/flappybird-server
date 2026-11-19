from typing import Optional
from .player import Player

class PlayerResult:
    """
    Model thực thể PlayerResult theo thiết kế lớp thực thể PTIT
    - id : long
    - totalPoint : int
    - player : Player
    - outcome : String
    """
    def __init__(
        self,
        id: Optional[int] = None,
        total_point: int = 0,
        player: Optional[Player] = None,
        outcome: str = "NONE"
    ):
        self.id = id
        self.total_point = total_point
        self.player = player
        self.outcome = outcome

    def to_dict(self):
        return {
            "id": self.id,
            "totalPoint": self.total_point,
            "outcome": self.outcome,
            "player": self.player.to_dict() if self.player else None
        }
