class IPAddress:
    """
    Model biểu diễn địa chỉ IP và Cổng của máy chủ / máy khách theo biểu đồ lớp chi tiết PTIT
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        self.host = host
        self.port = port

    def __str__(self):
        return f"{self.host}:{self.port}"

    def to_dict(self):
        return {
            "host": self.host,
            "port": self.port
        }
