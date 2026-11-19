import json
from enum import Enum
from typing import Optional
from .player import Player

class Action(str, Enum):
    LOGIN = "LOGIN"
    REGISTER = "REGISTER"
    GET_USER = "GET_USER"
    UPDATE_USER = "UPDATE_USER"
    UPDATE_SCORE = "UPDATE_SCORE"
    GET_LEADERBOARD = "GET_LEADERBOARD"

class Request:
    """
    Model Request nhận từ ứng dụng Android FlappyBird
    """
    def __init__(
        self,
        action: Optional[Action] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        persis_id: Optional[str] = None,
        score: int = 0,
        user: Optional[Player] = None
    ):
        self.action = action
        self.username = username
        self.password = password
        self.persis_id = persis_id
        self.score = score
        self.user = user

    @classmethod
    def from_dict(cls, data: dict):
        action_str = data.get("action")
        action = None
        if action_str:
            try:
                action = Action(action_str)
            except ValueError:
                action = None

        user_data = data.get("user")
        user = Player.from_dict(user_data) if user_data else None

        return cls(
            action=action,
            username=data.get("username"),
            password=data.get("password"),
            persis_id=data.get("persisId") or data.get("persis_id"),
            score=int(data.get("score", 0)),
            user=user
        )

    @classmethod
    def from_json(cls, json_str: str):
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except Exception:
            return None

    def to_dict(self):
        result = {
            "action": self.action.value if self.action else None,
            "username": self.username,
            "password": self.password,
            "persisId": self.persis_id,
            "score": self.score
        }
        if self.user:
            result["user"] = self.user.to_dict()
        return result
