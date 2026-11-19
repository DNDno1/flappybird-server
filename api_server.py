import os
import re
import sys
from contextlib import asynccontextmanager
from typing import Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config import API_CONFIG, AUTH_CONFIG
from dao.dao import DAO
from dao.player_dao import PlayerDAO
from dao.player_ranking_dao import PlayerRankingDAO
from model.player import Player
from security import create_access_token, verify_access_token

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Dependency factories (giúp dễ dàng inject/override trong unit & integration test)
# ---------------------------------------------------------------------------
def get_player_dao() -> PlayerDAO:
    return PlayerDAO()


def get_ranking_dao() -> PlayerRankingDAO:
    return PlayerRankingDAO()


def check_db_health() -> bool:
    return DAO.test_connection()


def get_current_persis_id(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu token xác thực. Vui lòng đăng nhập lại.",
        )
    token = authorization.split(" ", 1)[1].strip()
    payload = verify_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
        )
    return str(payload["sub"])


# ---------------------------------------------------------------------------
# Pydantic Request Schemas
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=200)
    email: str = Field(..., min_length=3, max_length=100)
    persis_id: Optional[str] = Field(default=None, max_length=64)


class UpdateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=3, max_length=100)
    password: Optional[str] = Field(default=None, max_length=200)


class UpdateScoreRequest(BaseModel):
    score: int = Field(..., ge=0)


# ---------------------------------------------------------------------------
# FastAPI App Initialization
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    if AUTH_CONFIG["jwt_secret"] == "flappy-bird-dev-secret-change-in-production":
        print(
            "[CẢNH BÁO BẢO MẬT] Đang dùng JWT_SECRET mặc định! "
            "Hãy thiết lập biến môi trường JWT_SECRET khi deploy Production.",
            flush=True,
        )
    if os.getenv("AUTO_INIT_DB", "").strip().lower() in ("1", "true", "yes"):
        try:
            dao = DAO()
            exists = dao.execute_query("SHOW TABLES LIKE 'Player'", fetchone=True)
            if not exists:
                print("[AUTO_INIT_DB] Bảng 'Player' chưa tồn tại, đang khởi tạo schema.sql...", flush=True)
                from init_db import init_database
                init_database()
        except Exception as e:
            print(f"[AUTO_INIT_DB] Không thể tự động khởi tạo DB: {e}", flush=True)
    yield


app = FastAPI(
    title="Flappy Bird Online API",
    description="HTTPS REST API cho ứng dụng Android FlappyBird (PTIT Nhóm 05)",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG["cors_origins"] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "FAIL",
            "message": str(exc.detail),
        },
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "SUCCESS",
        "service": "Flappy Bird Online API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    db_ok = check_db_health()
    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "ERROR",
                "message": "Không thể kết nối tới MySQL Database.",
                "database": "disconnected",
            },
        )
    return {
        "status": "SUCCESS",
        "message": "Máy chủ Online đang hoạt động bình thường!",
        "database": "connected",
    }


@app.post("/api/auth/login")
def login(body: LoginRequest, player_dao: PlayerDAO = Depends(get_player_dao)):
    username = body.username.strip()
    password = body.password.strip()
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.",
        )

    player = player_dao.checkLogin(Player(username=username, password_hash=password))
    if not player:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu!",
        )

    token = create_access_token(player.persis_id, player.username)
    return {
        "status": "SUCCESS",
        "message": "Đăng nhập thành công!",
        "token": token,
        "user": player.to_public_dict(include_email=True),
    }


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, player_dao: PlayerDAO = Depends(get_player_dao)):
    username = body.username.strip()
    email = body.email.strip()
    password = body.password.strip()

    if len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên đăng nhập tối thiểu 3 ký tự.",
        )
    if not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email không đúng định dạng.",
        )
    if len(password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu phải từ 4 ký tự trở lên.",
        )

    new_player = Player(
        persis_id=(body.persis_id or "").strip() or None,
        username=username,
        password_hash=password,
        email=email,
        score=0,
    )

    if not player_dao.checkRegister(new_player):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tên đăng nhập đã tồn tại, vui lòng chọn tên khác!",
        )

    added = player_dao.addPlayer(new_player)
    if not added:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Đăng ký thất bại trong cơ sở dữ liệu!",
        )

    created = player_dao.getPlayerByPersisId(new_player.persis_id) or new_player
    token = create_access_token(created.persis_id, created.username)
    return {
        "status": "SUCCESS",
        "message": "Đăng ký thành công!",
        "token": token,
        "user": created.to_public_dict(include_email=True),
    }


@app.get("/api/users/me")
def get_me(
    persis_id: str = Depends(get_current_persis_id),
    player_dao: PlayerDAO = Depends(get_player_dao),
):
    player = player_dao.getPlayerByPersisId(persis_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin người dùng!",
        )
    return {
        "status": "SUCCESS",
        "message": "Lấy thông tin thành công!",
        "user": player.to_public_dict(include_email=True),
    }


@app.put("/api/users/me")
def update_me(
    body: UpdateUserRequest,
    persis_id: str = Depends(get_current_persis_id),
    player_dao: PlayerDAO = Depends(get_player_dao),
):
    username = body.username.strip()
    email = body.email.strip()
    new_password = body.password.strip() if body.password else ""

    if len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên đăng nhập phải có ít nhất 3 ký tự.",
        )
    if not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email không đúng định dạng.",
        )
    if new_password and len(new_password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu mới phải từ 4 ký tự trở lên.",
        )

    candidate = Player(persis_id=persis_id, username=username, email=email)
    if not player_dao.checkValid(candidate):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tên đăng nhập này đã được người khác sử dụng!",
        )

    updated = player_dao.updatePlayer(candidate, new_password=new_password if new_password else None)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cập nhật thất bại trong cơ sở dữ liệu!",
        )

    refreshed = player_dao.getPlayerByPersisId(persis_id) or candidate
    return {
        "status": "SUCCESS",
        "message": "Cập nhật thông tin thành công!",
        "user": refreshed.to_public_dict(include_email=True),
    }


@app.post("/api/scores")
def submit_score(
    body: UpdateScoreRequest,
    persis_id: str = Depends(get_current_persis_id),
    player_dao: PlayerDAO = Depends(get_player_dao),
):
    max_score = AUTH_CONFIG["max_score_per_submit"]
    if body.score < 0 or body.score > max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Điểm số không hợp lệ (phải từ 0 đến {max_score}).",
        )

    ok = player_dao.updateScore(persis_id, body.score)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người chơi để cập nhật điểm.",
        )

    refreshed = player_dao.getPlayerByPersisId(persis_id)
    return {
        "status": "SUCCESS",
        "message": "Cập nhật điểm số thành công!",
        "user": refreshed.to_public_dict(include_email=True) if refreshed else None,
    }


@app.get("/api/leaderboard")
def get_leaderboard(
    limit: int = Query(default=100, ge=1, le=500),
    ranking_dao: PlayerRankingDAO = Depends(get_ranking_dao),
):
    rankings = ranking_dao.getPlayerRanking(limit=limit)
    leaderboard_data = []
    for r in rankings:
        p = r.player
        if p:
            score_val = r.highest_point if r.highest_point is not None else p.score
            leaderboard_data.append(
                {
                    "rank": r.rank,
                    "persis_id": p.persis_id,
                    "username": p.username,
                    "score": score_val,
                    "total_points": r.total_points,
                    "total_wins": r.total_wins,
                }
            )
    return {
        "status": "SUCCESS",
        "message": "Lấy bảng xếp hạng thành công!",
        "leaderboard": leaderboard_data,
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", API_CONFIG["port"]))
    uvicorn.run("api_server:app", host=API_CONFIG["host"], port=port, reload=False)
