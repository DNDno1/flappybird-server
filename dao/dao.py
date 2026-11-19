import os
import queue
import ssl
import threading
from contextlib import contextmanager
from typing import Any, Dict, Optional, Tuple

import pymysql
from pymysql.cursors import DictCursor

from config import DB_CONFIG

try:
    import certifi  # type: ignore
except ImportError:
    certifi = None

try:
    from dbutils.pooled_db import PooledDB  # type: ignore
    HAS_DBUTILS = True
except ImportError:
    PooledDB = None
    HAS_DBUTILS = False


def _build_ssl_kwargs(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Xây dựng tham số SSL cho PyMySQL khi kết nối Cloud Managed MySQL."""
    ssl_mode = (cfg.get("ssl_mode") or "").upper()
    ssl_ca = (cfg.get("ssl_ca") or "").strip().strip('"').strip("'")
    ssl_ca_pem = cfg.get("ssl_ca_pem") or ""

    if not ssl_mode and not ssl_ca and not ssl_ca_pem:
        return {}

    if ssl_mode in ("DISABLED", "OFF", "FALSE", "0"):
        return {}

    if ssl_ca_pem:
        pem_normalized = ssl_ca_pem.replace("\\n", "\n")
        ctx = ssl.create_default_context(cadata=pem_normalized)
        if ssl_mode not in ("VERIFY_IDENTITY",):
            ctx.check_hostname = False
        return {"ssl": ctx}

    if ssl_ca:
        if not os.path.isfile(ssl_ca):
            raise FileNotFoundError(
                f"Không tìm thấy file chứng chỉ SSL tại DB_SSL_CA='{ssl_ca}'. "
                "Hãy kiểm tra lại đường dẫn file .pem hoặc xóa biến DB_SSL_CA ($env:DB_SSL_CA=\"\") để dùng CA mặc định."
            )
        ctx = ssl.create_default_context(cafile=ssl_ca)
        if ssl_mode not in ("VERIFY_IDENTITY",):
            ctx.check_hostname = False
        return {"ssl": ctx}

    # Khi không chỉ định DB_SSL_CA riêng: dùng certifi (nếu có) hoặc system CA cho VERIFY_CA/VERIFY_IDENTITY
    if ssl_mode in ("VERIFY_CA", "VERIFY_IDENTITY"):
        ca_bundle = certifi.where() if certifi is not None else None
        ctx = ssl.create_default_context(cafile=ca_bundle) if ca_bundle else ssl.create_default_context()
        ctx.check_hostname = (ssl_mode == "VERIFY_IDENTITY")
        ctx.verify_mode = ssl.CERT_REQUIRED
    else:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return {"ssl": ctx}


def _build_connect_kwargs(include_database: bool = True) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {
        "host": DB_CONFIG["host"],
        "port": DB_CONFIG["port"],
        "user": DB_CONFIG["user"],
        "password": DB_CONFIG["password"],
        "charset": DB_CONFIG["charset"],
        "cursorclass": DictCursor,
        "autocommit": True,
        "connect_timeout": 10,
        "read_timeout": 15,
        "write_timeout": 15,
    }
    if include_database and DB_CONFIG.get("database"):
        kwargs["database"] = DB_CONFIG["database"]
    kwargs.update(_build_ssl_kwargs(DB_CONFIG))
    return kwargs


class _SimpleConnectionPool:
    """Pool kết nối thread-safe dự phòng khi chưa cài DBUtils."""

    def __init__(self, max_connections: int = 20):
        self._max_connections = max_connections
        self._pool: queue.LifoQueue = queue.LifoQueue(maxsize=max_connections)
        self._lock = threading.Lock()

    def connection(self):
        conn = None
        while not self._pool.empty():
            try:
                candidate = self._pool.get_nowait()
            except queue.Empty:
                break
            try:
                candidate.ping(reconnect=True)
                conn = candidate
                break
            except Exception:
                try:
                    candidate.close()
                except Exception:
                    pass
        if conn is None:
            conn = pymysql.connect(**_build_connect_kwargs(include_database=True))
        return _PooledConnWrapper(self, conn)

    def _release(self, conn, broken: bool = False):
        if broken or not getattr(conn, "open", False):
            try:
                conn.close()
            except Exception:
                pass
            return
        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            try:
                conn.close()
            except Exception:
                pass


class _PooledConnWrapper:
    def __init__(self, pool: _SimpleConnectionPool, conn):
        self._pool = pool
        self._conn = conn
        self._broken = False

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)

    def mark_broken(self):
        self._broken = True

    def close(self):
        self._pool._release(self._conn, broken=self._broken)


class _PoolManager:
    _lock = threading.Lock()
    _pool = None

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            with cls._lock:
                if cls._pool is None:
                    if HAS_DBUTILS:
                        cls._pool = PooledDB(
                            creator=pymysql,
                            maxconnections=20,
                            mincached=1,
                            maxcached=5,
                            blocking=True,
                            ping=1,
                            **_build_connect_kwargs(include_database=True),
                        )
                    else:
                        cls._pool = _SimpleConnectionPool(max_connections=20)
        return cls._pool

    @classmethod
    def reset_pool(cls):
        with cls._lock:
            cls._pool = None


class DAO:
    """
    Lớp DAO cơ sở quản lý kết nối MySQL an toàn đa luồng (Thread-safe Connection Pool).
    """

    def __init__(self):
        self.con = None

    @contextmanager
    def borrow_connection(self):
        pool = _PoolManager.get_pool()
        conn = pool.connection()
        try:
            yield conn
        except pymysql.Error:
            if isinstance(conn, _PooledConnWrapper):
                conn.mark_broken()
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def get_connection(self):
        """Giữ tương thích ngược: mượn một connection từ pool."""
        return _PoolManager.get_pool().connection()

    def close_connection(self):
        """Không đóng toàn bộ pool khi gọi từ instance dùng chung."""
        self.con = None

    def execute_query(self, sql: str, params: Optional[tuple] = None, fetchone: bool = False):
        """Thực hiện câu lệnh SELECT an toàn luồng."""
        try:
            with self.borrow_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params or ())
                    if fetchone:
                        return cur.fetchone()
                    return cur.fetchall()
        except Exception as e:
            print(f"[DAO.execute_query] Lỗi SQL: {e}")
            return None

    def execute_update(self, sql: str, params: Optional[tuple] = None) -> int:
        """Thực hiện INSERT, UPDATE, DELETE và trả về số dòng bị ảnh hưởng."""
        ok, affected = self.execute_write(sql, params)
        return affected if ok else 0

    def execute_write(self, sql: str, params: Optional[tuple] = None) -> Tuple[bool, int]:
        """Thực hiện INSERT, UPDATE, DELETE và phân biệt rõ lỗi SQL với 0 dòng thay đổi."""
        try:
            with self.borrow_connection() as conn:
                with conn.cursor() as cur:
                    affected = cur.execute(sql, params or ())
                    return True, int(affected or 0)
        except Exception as e:
            print(f"[DAO.execute_write] Lỗi SQL: {e}")
            return False, 0

    @classmethod
    def test_connection(cls) -> bool:
        """Kiểm tra máy chủ MySQL có sẵn sàng kết nối hay không."""
        try:
            conn = pymysql.connect(**_build_connect_kwargs(include_database=True))
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            is_open = conn.open
            conn.close()
            return is_open
        except Exception as e:
            print(f"[DAO.test_connection] Lỗi: {e}")
            return False
