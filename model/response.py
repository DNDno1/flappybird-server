import json
from enum import Enum
from typing import Optional, List, Union
from .player import Player

class Status(str, Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    ERROR = "ERROR"

class Response:
    """
    Model Response gửi về ứng dụng Android FlappyBird
    """
    def __init__(
        self,
        status: Status = Status.SUCCESS,
        message: str = "",
        user: Optional[Union[Player, dict]] = None,
        leaderboard: Optional[List] = None
    ):
        self.status = status
        self.message = message
        self.user = user
        self.leaderboard = leaderboard or []

    @classmethod
    def success(cls, message: str, user: Optional[Union[Player, dict]] = None):
        return cls(status=Status.SUCCESS, message=message, user=user)

    @classmethod
    def success_leaderboard(cls, message: str, leaderboard: List):
        return cls(status=Status.SUCCESS, message=message, leaderboard=leaderboard)

    @classmethod
    def fail(cls, message: str):
        return cls(status=Status.FAIL, message=message)

    @classmethod
    def error(cls, message: str):
        return cls(status=Status.ERROR, message=message)

    def to_dict(self):
        user_dict = None
        if isinstance(self.user, Player):
            user_dict = self.user.to_dict()
        elif isinstance(self.user, dict):
            user_dict = self.user

        leaderboard_list = []
        if self.leaderboard:
            for item in self.leaderboard:
                if hasattr(item, 'to_dict'):
                    leaderboard_list.append(item.to_dict())
                elif isinstance(item, dict):
                    leaderboard_list.append(item)

        return {
            "status": self.status.value,
            "message": self.message,
            "user": user_dict,
            "leaderboard": leaderboard_list
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False)
