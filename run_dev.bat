@echo off
title SentinelX Platform Launcher
echo ========================================================
echo    SentinelX Fraud Detection & Risk Intelligence Platform
echo ========================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=%cd%
set PYTHONIOENCODING=utf-8

echo [1/2] Launching SentinelX Backend (FastAPI + XGBoost + PyMongo)...
start "SentinelX Backend Server (Port 8000)" cmd /k ""C:\Users\Priyam\AppData\Local\Programs\Python\Python310\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching SentinelX Frontend (Vite + React Dashboard)...
cd frontend
start "SentinelX React Dashboard (Port 5173)" cmd /k "npm run dev"

echo.
echo ========================================================
echo SentinelX is running!
echo   Dashboard:    http://localhost:5173
echo   REST API:     http://localhost:8000
echo   Swagger Docs: http://localhost:8000/docs
echo ========================================================
pause
