import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional, Tuple

from config import AUTH_CONFIG

try:
    import bcrypt  # type: ignore
    HAS_BCRYPT = True
except ImportError:
    bcrypt = None
    HAS_BCRYPT = False

try:
    import jwt  # type: ignore
    HAS_PYJWT = True
except ImportError:
    jwt = None
    HAS_PYJWT = False

PBKDF2_PREFIX = "$pbkdf2-sha256$"
PBKDF2_ITERATIONS = 260_000


def hash_password(plain_password: str) -> str:
    """
    Băm mật khẩu an toàn trước khi lưu vào MySQL.
    Ưu tiên dùng bcrypt nếu được cài đặt; fallback sang PBKDF2-HMAC-SHA256 chuẩn stdlib.
    """
    if plain_password is None:
        raise ValueError("Mật khẩu không được rỗng")

    if HAS_BCRYPT:
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt(rounds=12))
        return hashed.decode("utf-8")

    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(derived).decode("ascii")
    return f"{PBKDF2_PREFIX}{PBKDF2_ITERATIONS}${salt_b64}${hash_b64}"


def is_password_hashed(stored_value: str) -> bool:
    if not stored_value:
        return False
    return (
        stored_value.startswith("$2a$")
        or stored_value.startswith("$2b$")
        or stored_value.startswith("$2y$")
        or stored_value.startswith(PBKDF2_PREFIX)
    )


def verify_password(plain_password: str, stored_value: str) -> Tuple[bool, bool]:
    """
    Kiểm tra mật khẩu người dùng nhập vào so với giá trị lưu trong DB.
    Trả về (is_valid, needs_rehash):
    - Nếu dữ liệu cũ đang là plaintext (vd tài khoản seed '123456'), vẫn xác thực 1 lần
      và đánh dấu needs_rehash=True để nâng cấp tự động lên hash an toàn.
    """
    if not plain_password or not stored_value:
        return False, False

    if stored_value.startswith(("$2a$", "$2b$", "$2y$")):
        if not HAS_BCRYPT:
            return False, False
        try:
            ok = bcrypt.checkpw(plain_password.encode("utf-8"), stored_value.encode("utf-8"))
            return ok, False
        except Exception:
            return False, False

    if stored_value.startswith(PBKDF2_PREFIX):
        try:
            parts = stored_value.split("$")
            # ['', 'pbkdf2-sha256', '<iters>', '<salt_b64>', '<hash_b64>']
            if len(parts) != 5:
                return False, False
            iterations = int(parts[2])
            salt = base64.b64decode(parts[3].encode("ascii"))
            expected = base64.b64decode(parts[4].encode("ascii"))
            derived = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt,
                iterations,
            )
            ok = hmac.compare_digest(derived, expected)
            return ok, (HAS_BCRYPT and ok)
        except Exception:
            return False, False

    # Tương thích ngược với tài khoản mẫu lưu plaintext trong schema cũ
    ok = hmac.compare_digest(plain_password, stored_value)
    return ok, ok


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(encoded: str) -> bytes:
    padding = "=" * ((4 - len(encoded) % 4) % 4)
    return base64.urlsafe_b64decode((encoded + padding).encode("ascii"))


def create_access_token(persis_id: str, username: str) -> str:
    """Sinh JWT HS256 phục vụ xác thực các request Online."""
    now = int(time.time())
    exp = now + AUTH_CONFIG["jwt_expire_hours"] * 3600
    payload = {
        "sub": persis_id,
        "username": username,
        "iat": now,
        "exp": exp,
    }
    secret = AUTH_CONFIG["jwt_secret"]
    algorithm = AUTH_CONFIG["jwt_algorithm"]

    if HAS_PYJWT:
        token = jwt.encode(payload, secret, algorithm=algorithm)
        return token.decode("utf-8") if isinstance(token, bytes) else token

    header_b64 = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(sig)}"


def verify_access_token(token: str) -> Optional[dict]:
    """Xác thực JWT và trả về payload nếu hợp lệ, None nếu hết hạn hoặc sai chữ ký."""
    if not token:
        return None
    secret = AUTH_CONFIG["jwt_secret"]
    algorithm = AUTH_CONFIG["jwt_algorithm"]

    if HAS_PYJWT:
        try:
            return jwt.decode(token, secret, algorithms=[algorithm])
        except Exception:
            return None

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        if header.get("alg") != "HS256":
            return None

        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        exp = payload.get("exp")
        if exp is not None and int(time.time()) > int(exp):
            return None
        return payload
    except Exception:
        return None
