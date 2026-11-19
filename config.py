import os
from pathlib import Path


def _load_dotenv_if_present() -> None:
    """Tải các biến từ file .env cục bộ nếu tồn tại (không ghi đè biến môi trường hệ thống)."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.is_file():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception:
        pass


_load_dotenv_if_present()

# Cấu hình kết nối MySQL Database (hỗ trợ cả Local lẫn Cloud Managed MySQL qua biến môi trường)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'flappy_bird_db'),
    'charset': 'utf8mb4',
    # Tùy chọn SSL cho Cloud MySQL (VERIFY_IDENTITY, VERIFY_CA, REQUIRED hoặc để trống nếu local)
    'ssl_mode': os.getenv('DB_SSL_MODE', '').strip(),
    'ssl_ca': os.getenv('DB_SSL_CA', '').strip(),
    'ssl_ca_pem': os.getenv('DB_SSL_CA_PEM', '').strip(),
}

# Cấu hình Server TCP Socket (Legacy LAN Mode)
SERVER_CONFIG = {
    'host': os.getenv('SERVER_HOST', '0.0.0.0'),
    'port': int(os.getenv('SERVER_PORT', 8889)),
    'buffer_size': 4096
}

# Cấu hình API HTTP/HTTPS (Online Production Mode)
API_CONFIG = {
    'host': os.getenv('API_HOST', '0.0.0.0'),
    'port': int(os.getenv('PORT', os.getenv('API_PORT', 8000))),
    'cors_origins': [
        origin.strip()
        for origin in os.getenv('CORS_ORIGINS', '*').split(',')
        if origin.strip()
    ],
}

# Cấu hình Bảo mật & Xác thực JWT
AUTH_CONFIG = {
    'jwt_secret': os.getenv('JWT_SECRET', 'flappy-bird-dev-secret-change-in-production'),
    'jwt_algorithm': 'HS256',
    'jwt_expire_hours': int(os.getenv('JWT_EXPIRE_HOURS', 24 * 30)),
    'max_score_per_submit': int(os.getenv('MAX_SCORE_PER_SUBMIT', 100000)),
}
