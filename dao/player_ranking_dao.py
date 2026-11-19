from typing import List
from .dao import DAO
from model.player_ranking import PlayerRanking
from model.player import Player


class PlayerRankingDAO(DAO):
    """
    Lớp PlayerRankingDAO kế thừa từ DAO, thực hiện truy vấn bảng xếp hạng người chơi.
    """

    def __init__(self):
        super().__init__()

    def getPlayerRanking(self, limit: int = 100) -> List[PlayerRanking]:
        """
        Truy vấn danh sách xếp hạng người chơi sắp xếp theo ĐIỂM SỐ TỪ CAO NHẤT ĐẾN THẤP NHẤT.
        Không truy vấn password_hash và không trả thông tin nhạy cảm.
        """
        safe_limit = max(1, min(int(limit or 100), 500))
        sql = """
            SELECT
                p.id, p.persis_id, p.username, p.score,
                GREATEST(p.score, CAST(COALESCE(pr.HighestPoint, 0) AS UNSIGNED)) AS highestPoint,
                COALESCE(pr.totalPoints, p.total_points, p.score) AS totalPoints,
                COALESCE(pr.totalWins, p.total_wins, 0) AS totalWins,
                COALESCE(pr.Leaderboardid, 1) AS leaderboardId
            FROM Player p
            LEFT JOIN PlayerRanking pr ON p.id = pr.Playerid
            ORDER BY highestPoint DESC, totalPoints DESC, p.username ASC
            LIMIT %s
        """
        rows = self.execute_query(sql, (safe_limit,)) or []
        rankings: List[PlayerRanking] = []

        for index, row in enumerate(rows, start=1):
            try:
                score_val = int(row.get("highestPoint") or 0)
            except Exception:
                score_val = int(row.get("score") or 0)

            total_pts = int(row.get("totalPoints") or score_val)
            wins = int(row.get("totalWins") or 0)

            player = Player(
                id=row.get("id"),
                persis_id=row.get("persis_id"),
                username=row.get("username", ""),
                password_hash="",
                email="",
                score=score_val,
                total_points=total_pts,
                total_wins=wins,
            )

            ranking = PlayerRanking(
                player_id=player.id,
                rank=index,
                total_points=total_pts,
                highest_point=score_val,
                total_wins=wins,
                leaderboard_id=row.get("leaderboardId"),
                player=player,
            )
            rankings.append(ranking)

        return rankings
