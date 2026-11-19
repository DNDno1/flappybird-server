from typing import Optional
from .player import Player

class PlayerRanking:
    """
    Model thực thể PlayerRanking theo thiết kế lớp thực thể & CSDL PTIT
    - rank : int
    - totalPoints : int
    - totalWins : int
    - highestPoint : int
    - player : Player
    """
    def __init__(
        self,
        player_id: Optional[int] = None,
        rank: int = 0,
        total_points: int = 0,
        highest_point: int = 0,
        total_wins: int = 0,
        leaderboard_id: Optional[int] = 1,
        player: Optional[Player] = None
    ):
        self.player_id = player_id
        self.rank = rank
        self.total_points = total_points
        self.highest_point = highest_point
        self.total_wins = total_wins
        self.leaderboard_id = leaderboard_id
        self.player = player

    def to_dict(self):
        result = {
            "playerId": self.player_id,
            "rank": self.rank,
            "totalPoints": self.total_points,
            "highestPoint": self.highest_point,
            "totalWins": self.total_wins,
            "leaderboardId": self.leaderboard_id
        }
        if self.player:
            result.update({
                "persis_id": self.player.persis_id,
                "username": self.player.username,
                "score": self.highest_point,
                "email": self.player.email
            })
        return result
