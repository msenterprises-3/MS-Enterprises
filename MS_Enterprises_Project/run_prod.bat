@echo off
title MS Enterprises - Production Server Launcher
color 0B

echo ====================================================
echo MS ENTERPRISES - PRODUCTION CATALOGUE SERVER
echo ====================================================
echo.

:: Check python is on path
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    pause
    exit /b 1
)

echo [1/3] Python detected.
echo [2/3] Installing/verifying production requirements...
pip install -r requirements.txt

echo [3/3] Starting web server in production mode (Waitress WSGI)...
start "" http://127.0.0.1:5000/
python wsgi.py

pause
