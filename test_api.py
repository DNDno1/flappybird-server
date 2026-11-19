"""
Kiểm thử toàn diện cho FlappyBirdServer Online API (api_server.py & security.py).

Cách dùng:
  1) Chạy kiểm thử tự động offline (không cần MySQL đang chạy):
     python test_api.py

  2) Kiểm thử trực tiếp một server Online đã deploy:
     python test_api.py --url https://your-domain.onrender.com
"""
import argparse
import asyncio
import os
import sqlite3
import sys
import threading
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import httpx

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi.testclient import TestClient

import api_server
from model.player import Player
from model.player_ranking import PlayerRanking
from security import (
    create_access_token,
    hash_password,
    is_password_hashed,
    verify_access_token,
    verify_password,
)


class InMemorySqlitePlayerDAO:
    """Test double dùng SQLite memory mô phỏng đầy đủ logic PlayerDAO & PlayerRankingDAO."""

    def __init__(self):
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE Player (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persis_id TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    score INTEGER DEFAULT 0,
                    total_points INTEGER DEFAULT 0,
                    total_wins INTEGER DEFAULT 0,
                    total_losses INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Seed tài khoản mẫu kiểu cũ (plaintext '123456') để test nâng cấp hash tự động
            self.conn.execute(
                """
                INSERT INTO Player (persis_id, username, password_hash, email, score, total_points, total_wins)
                VALUES ('usr_001', 'Hip', '123456', 'hip@ptit.edu.vn', 500, 1200, 119)
                """
            )

    def checkLogin(self, p: Player):
        if not p or not p.username or not p.password_hash:
            return None
        with self._lock:
            row = self.conn.execute(
                "SELECT * FROM Player WHERE username = ?",
                (p.username.strip(),),
            ).fetchone()
            if not row:
                return None
            ok, needs_rehash = verify_password(p.password_hash, row["password_hash"])
            if not ok:
                return None
            if needs_rehash:
                upgraded = hash_password(p.password_hash)
                with self.conn:
                    self.conn.execute(
                        "UPDATE Player SET password_hash = ? WHERE id = ?",
                        (upgraded, row["id"]),
                    )
            return self._row_to_player(row)

    def checkRegister(self, p: Player) -> bool:
        if not p or not p.username:
            return False
        with self._lock:
            row = self.conn.execute(
                "SELECT id FROM Player WHERE username = ?",
                (p.username.strip(),),
            ).fetchone()
            return row is None

    def addPlayer(self, p: Player) -> bool:
        if not p or not p.username or not p.password_hash:
            return False
        if not p.persis_id:
            p.persis_id = f"usr_{uuid.uuid4().hex[:8]}"
        hashed = p.password_hash if is_password_hashed(p.password_hash) else hash_password(p.password_hash)
        with self._lock:
            try:
                with self.conn:
                    cur = self.conn.execute(
                        """
                        INSERT INTO Player (persis_id, username, password_hash, email, score, total_points, total_wins, total_losses)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            p.persis_id,
                            p.username.strip(),
                            hashed,
                            (p.email or "").strip(),
                            p.score,
                            p.total_points,
                            p.total_wins,
                            p.total_losses,
                        ),
                    )
                    p.id = cur.lastrowid
                p.password_hash = ""
                return True
            except sqlite3.IntegrityError:
                return False

    def checkValid(self, p: Player) -> bool:
        if not p or not p.persis_id:
            return False
        existing = self.getPlayerByPersisId(p.persis_id)
        if not existing:
            return False
        new_username = (p.username or "").strip()
        if new_username and new_username.lower() != existing.username.lower():
            with self._lock:
                dup = self.conn.execute(
                    "SELECT id FROM Player WHERE username = ? AND persis_id != ?",
                    (new_username, p.persis_id),
                ).fetchone()
                if dup:
                    return False
        return True

    def updatePlayer(self, p: Player, new_password=None) -> bool:
        existing = self.getPlayerByPersisId(p.persis_id)
        if not existing:
            return False
        raw_pw = (new_password if new_password is not None else p.password_hash or "").strip()
        username = (p.username or existing.username).strip()
        email = (p.email if p.email is not None else existing.email or "").strip()
        with self._lock:
            with self.conn:
                if raw_pw:
                    hashed = raw_pw if is_password_hashed(raw_pw) else hash_password(raw_pw)
                    self.conn.execute(
                        "UPDATE Player SET username = ?, password_hash = ?, email = ? WHERE persis_id = ?",
                        (username, hashed, email, p.persis_id),
                    )
                else:
                    self.conn.execute(
                        "UPDATE Player SET username = ?, email = ? WHERE persis_id = ?",
                        (username, email, p.persis_id),
                    )
        return True

    def getPlayerByPersisId(self, persis_id: str):
        with self._lock:
            row = self.conn.execute(
                "SELECT * FROM Player WHERE persis_id = ?",
                (persis_id,),
            ).fetchone()
            return self._row_to_player(row) if row else None

    def updateScore(self, persis_id: str, new_score: int) -> bool:
        if new_score < 0:
            return False
        with self._lock:
            row = self.conn.execute(
                "SELECT score, total_points FROM Player WHERE persis_id = ?",
                (persis_id,),
            ).fetchone()
            if not row:
                return False
            best = max(int(row["score"]), new_score)
            total = max(int(row["total_points"]), new_score)
            with self.conn:
                self.conn.execute(
                    "UPDATE Player SET score = ?, total_points = ? WHERE persis_id = ?",
                    (best, total, persis_id),
                )
        return True

    def getPlayerRanking(self, limit: int = 100):
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM Player ORDER BY score DESC, total_points DESC, username ASC LIMIT ?",
                (limit,),
            ).fetchall()
        rankings = []
        for idx, row in enumerate(rows, start=1):
            player = self._row_to_player(row)
            player.email = ""
            rankings.append(
                PlayerRanking(
                    player_id=player.id,
                    rank=idx,
                    total_points=player.total_points,
                    highest_point=player.score,
                    total_wins=player.total_wins,
                    leaderboard_id=1,
                    player=player,
                )
            )
        return rankings

    def get_raw_password_hash(self, persis_id: str) -> str:
        with self._lock:
            row = self.conn.execute(
                "SELECT password_hash FROM Player WHERE persis_id = ?",
                (persis_id,),
            ).fetchone()
            return row["password_hash"] if row else ""

    @staticmethod
    def _row_to_player(row) -> Player:
        return Player(
            id=row["id"],
            persis_id=row["persis_id"],
            username=row["username"],
            password_hash="",
            email=row["email"] or "",
            score=int(row["score"]),
            total_points=int(row["total_points"]),
            total_wins=int(row["total_wins"]),
            total_losses=int(row["total_losses"]),
            created_at=row["created_at"],
        )


class SecurityAndApiTests(unittest.TestCase):
    def setUp(self):
        self.fake_dao = InMemorySqlitePlayerDAO()
        api_server.app.dependency_overrides[api_server.get_player_dao] = lambda: self.fake_dao
        api_server.app.dependency_overrides[api_server.get_ranking_dao] = lambda: self.fake_dao
        self.orig_health = api_server.check_db_health
        api_server.check_db_health = lambda: True
        self.client = TestClient(api_server.app)

    def tearDown(self):
        api_server.app.dependency_overrides.clear()
        api_server.check_db_health = self.orig_health
        self.fake_dao.conn.close()

    def test_password_hashing_and_jwt(self):
        hashed = hash_password("Secret123")
        self.assertTrue(is_password_hashed(hashed))
        self.assertNotEqual(hashed, "Secret123")
        ok, needs_rehash = verify_password("Secret123", hashed)
        self.assertTrue(ok)
        self.assertFalse(needs_rehash)
        ok_bad, _ = verify_password("Wrong", hashed)
        self.assertFalse(ok_bad)

        token = create_access_token("usr_abc", "tester")
        payload = verify_access_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "usr_abc")
        self.assertEqual(payload["username"], "tester")
        self.assertIsNone(verify_access_token(token + "tamper"))

    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["database"], "connected")

    def test_legacy_seed_login_upgrades_hash_and_returns_token(self):
        res = self.client.post("/api/auth/login", json={"username": "Hip", "password": "123456"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "SUCCESS")
        self.assertIn("token", body)
        self.assertNotIn("password", body["user"])
        self.assertNotIn("password_hash", body["user"])

        # Kiểm tra password trong DB đã tự động nâng cấp lên dạng hash
        stored = self.fake_dao.get_raw_password_hash("usr_001")
        self.assertTrue(is_password_hashed(stored))

        # Đăng nhập lại bằng mật khẩu cũ sau khi nâng cấp vẫn thành công
        res2 = self.client.post("/api/auth/login", json={"username": "Hip", "password": "123456"})
        self.assertEqual(res2.status_code, 200)

    def test_full_online_flow_and_auth_guards(self):
        # 1. Truy cập protected route không có token -> 401
        unauth = self.client.get("/api/users/me")
        self.assertEqual(unauth.status_code, 401)

        # 2. Đăng ký tài khoản mới
        reg = self.client.post(
            "/api/auth/register",
            json={
                "username": "sky_pilot",
                "password": "myPassword99",
                "email": "pilot@example.com",
            },
        )
        self.assertEqual(reg.status_code, 201)
        reg_body = reg.json()
        token = reg_body["token"]
        user = reg_body["user"]
        self.assertEqual(user["username"], "sky_pilot")
        self.assertNotIn("password", user)

        # Trùng username -> 409
        dup = self.client.post(
            "/api/auth/register",
            json={"username": "sky_pilot", "password": "otherPassword", "email": "x@example.com"},
        )
        self.assertEqual(dup.status_code, 409)

        headers = {"Authorization": f"Bearer {token}"}

        # 3. Lấy hồ sơ cá nhân
        me = self.client.get("/api/users/me", headers=headers)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["user"]["email"], "pilot@example.com")

        # 4. Cập nhật profile KHÔNG đổi mật khẩu (password=None)
        upd = self.client.put(
            "/api/users/me",
            headers=headers,
            json={"username": "sky_ace", "email": "ace@example.com"},
        )
        self.assertEqual(upd.status_code, 200)
        self.assertEqual(upd.json()["user"]["username"], "sky_ace")

        # Đăng nhập vẫn dùng mật khẩu cũ thành công
        login_old_pw = self.client.post(
            "/api/auth/login",
            json={"username": "sky_ace", "password": "myPassword99"},
        )
        self.assertEqual(login_old_pw.status_code, 200)

        # 5. Cập nhật điểm cao & không bị hạ điểm khi gửi điểm thấp hơn
        sc1 = self.client.post("/api/scores", headers=headers, json={"score": 720})
        self.assertEqual(sc1.status_code, 200)
        self.assertEqual(sc1.json()["user"]["score"], 720)

        sc2 = self.client.post("/api/scores", headers=headers, json={"score": 120})
        self.assertEqual(sc2.status_code, 200)
        self.assertEqual(sc2.json()["user"]["score"], 720)

        # 6. Leaderboard xếp giảm dần và không lộ email/password
        lb = self.client.get("/api/leaderboard")
        self.assertEqual(lb.status_code, 200)
        board = lb.json()["leaderboard"]
        self.assertGreaterEqual(len(board), 2)
        self.assertEqual(board[0]["username"], "sky_ace")
        self.assertEqual(board[0]["score"], 720)
        for item in board:
            self.assertNotIn("email", item)
            self.assertNotIn("password", item)

    def test_concurrent_leaderboard_and_score_requests(self):
        async def run_concurrent():
            transport = httpx.ASGITransport(app=api_server.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                reg = await ac.post(
                    "/api/auth/register",
                    json={"username": "concurrent_bird", "password": "pass1234", "email": "c@example.com"},
                )
                self.assertEqual(reg.status_code, 201)
                token = reg.json()["token"]
                headers = {"Authorization": f"Bearer {token}"}

                async def worker(i: int):
                    r1 = await ac.post("/api/scores", headers=headers, json={"score": i * 10})
                    r2 = await ac.get("/api/leaderboard")
                    return r1.status_code, r2.status_code

                results = await asyncio.gather(*(worker(i) for i in range(1, 21)))
                for code1, code2 in results:
                    self.assertEqual(code1, 200)
                    self.assertEqual(code2, 200)

                me = await ac.get("/api/users/me", headers=headers)
                self.assertEqual(me.json()["user"]["score"], 200)

        asyncio.run(run_concurrent())

    def test_mysql_connection_pool_thread_safety(self):
        from dao.dao import DAO, _PoolManager

        class FakeCursor:
            def __init__(self):
                self.closed = False

            def execute(self, sql, params=()):
                return 1

            def fetchone(self):
                return {"ok": 1}

            def fetchall(self):
                return [{"ok": 1}]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                self.closed = True

        class FakeConn:
            def __init__(self):
                self.open = True

            def ping(self, reconnect=True):
                if not self.open:
                    raise RuntimeError("closed")

            def cursor(self, *args, **kwargs):
                return FakeCursor()

            def close(self):
                self.open = False

        _PoolManager.reset_pool()
        created_conns = []

        def fake_connect(**kwargs):
            c = FakeConn()
            created_conns.append(c)
            return c

        with patch("dao.dao.HAS_DBUTILS", False), patch("dao.dao.pymysql.connect", side_effect=fake_connect):
            dao = DAO()

            def run_query(_):
                return dao.execute_query("SELECT 1", fetchone=True)

            with ThreadPoolExecutor(max_workers=8) as pool:
                outs = list(pool.map(run_query, range(40)))

            self.assertEqual(len(outs), 40)
            self.assertTrue(all(o == {"ok": 1} for o in outs))
            self.assertLessEqual(len(created_conns), 8)
            _PoolManager.reset_pool()

    def test_ssl_kwargs_certifi_and_missing_file_message(self):
        from dao.dao import _build_ssl_kwargs

        res = _build_ssl_kwargs({"ssl_mode": "VERIFY_IDENTITY", "ssl_ca": "", "ssl_ca_pem": ""})
        self.assertIn("ssl", res)
        self.assertTrue(res["ssl"].check_hostname)

        with self.assertRaises(FileNotFoundError) as ctx:
            _build_ssl_kwargs({"ssl_mode": "VERIFY_IDENTITY", "ssl_ca": "D:\\not_found\\ca.pem", "ssl_ca_pem": ""})
        self.assertIn("DB_SSL_CA", str(ctx.exception))


def test_live_server(base_url: str):
    import httpx

    base = base_url.rstrip("/")
    print(f"=== KIỂM THỬ SERVER LIVE TẠI: {base} ===")
    with httpx.Client(timeout=20.0) as client:
        health = client.get(f"{base}/health")
        print("GET /health ->", health.status_code, health.json())
        health.raise_for_status()

        suffix = uuid.uuid4().hex[:6]
        uname = f"online_{suffix}"
        reg = client.post(
            f"{base}/api/auth/register",
            json={"username": uname, "password": "TestPass123", "email": f"{uname}@example.com"},
        )
        print("POST /api/auth/register ->", reg.status_code)
        reg.raise_for_status()
        token = reg.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        sc = client.post(f"{base}/api/scores", headers=headers, json={"score": 88})
        print("POST /api/scores ->", sc.status_code, sc.json()["user"]["score"])
        sc.raise_for_status()

        lb = client.get(f"{base}/api/leaderboard")
        print("GET /api/leaderboard ->", lb.status_code, f"({len(lb.json()['leaderboard'])} players)")
        lb.raise_for_status()
        print("✅ KIỂM THỬ SERVER LIVE THÀNH CÔNG!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Base URL của server đã deploy để test end-to-end")
    args, remaining = parser.parse_known_args()

    if args.url:
        test_live_server(args.url)
    else:
        unittest.main(argv=[sys.argv[0]] + remaining, verbosity=2)
