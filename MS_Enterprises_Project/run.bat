@echo off
title MS Enterprises Web Server Launcher
color 0A

echo ====================================================
echo MS ENTERPRISES - PREMIUM CATALOGUE SERVER LAUNCHER
echo ====================================================
echo.

:: Check python is on path
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.10+ and tick "Add Python to PATH" during setup.
    pause
    exit /b 1
)

echo [1/3] Python detected.
echo [2/3] Starting web server in local environment...

:: Open browser in 2 seconds
start "" http://127.0.0.1:5000/

:: Start Flask app
python app.py

pause
