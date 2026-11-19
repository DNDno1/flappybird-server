from typing import List, Optional
from .player_ranking import PlayerRanking

class Leaderboard:
    """
    Model thực thể Leaderboard theo thiết kế lớp thực thể & CSDL PTIT
    - id : long / int
    - playerRanking : PlayerRanking[]
    - category : String
    """
    def __init__(self, id: Optional[int] = 1, category: str = "All Time", player_rankings: Optional[List[PlayerRanking]] = None):
        self.id = id
        self.category = category
        self.player_rankings = player_rankings or []

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "playerRanking": [pr.to_dict() for pr in self.player_rankings]
        }
