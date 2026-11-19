@echo off
title Flappy Bird Online HTTP API Server
cd /d "%~dp0"
echo ==================================================================
echo   FLAPPY BIRD ONLINE HTTPS/REST API SERVER (FastAPI + Uvicorn)
echo ==================================================================
echo.
echo API Docs: http://127.0.0.1:8000/docs
echo Health  : http://127.0.0.1:8000/health
echo ------------------------------------------------------------------
python api_server.py
pause
