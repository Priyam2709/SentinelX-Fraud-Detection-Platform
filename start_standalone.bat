@echo off
title SentinelX Standalone Server
echo ========================================================
echo    SentinelX Unified Server (Single Port: 8000)
echo ========================================================
echo.
cd /d "%~dp0"
set PYTHONPATH=%cd%
set PYTHONIOENCODING=utf-8

echo Launching unified platform (React SPA + FastAPI + ML Engine)...
"C:\Users\Priyam\AppData\Local\Programs\Python\Python310\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
pause
