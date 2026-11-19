class ObstacleConfig:
    """
    Model thực thể ObstacleConfig theo thiết kế CSDL PTIT
    - id : long
    - seed : long
    - pipeSpawnInterval : Decimal
    - pipeGap : Decimal
    - baseSpeed : Decimal
    - overtimeStepPoints : int
    - speedIncrement : Decimal
    """
    def __init__(
        self,
        id: int = 1,
        seed: int = 0,
        pipe_spawn_interval: float = 100.0,
        pipe_gap: float = 120.0,
        base_speed: float = 5.0,
        overtime_step_points: int = 10,
        speed_increment: float = 1.0
    ):
        self.id = id
        self.seed = seed
        self.pipe_spawn_interval = pipe_spawn_interval
        self.pipe_gap = pipe_gap
        self.base_speed = base_speed
        self.overtime_step_points = overtime_step_points
        self.speed_increment = speed_increment

    def to_dict(self):
        return {
            "id": self.id,
            "seed": self.seed,
            "pipeSpawnInterval": self.pipe_spawn_interval,
            "pipeGap": self.pipe_gap,
            "baseSpeed": self.base_speed,
            "overtimeStepPoints": self.overtime_step_points,
            "speedIncrement": self.speed_increment
        }
