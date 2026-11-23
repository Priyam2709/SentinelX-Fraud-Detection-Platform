@echo off
title SentinelX Test Suite
echo ========================================================
echo        Running SentinelX Automated Test Discovery
echo ========================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=%cd%
set PYTHONIOENCODING=utf-8

"C:\Users\Priyam\AppData\Local\Programs\Python\Python310\python.exe" -m unittest discover tests

echo.
pause
