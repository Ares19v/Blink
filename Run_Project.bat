@echo off
setlocal
title Blink Eye Health Monitor

echo ==========================================
echo    Blink Eye Health Monitor
echo ==========================================
echo.

cd /d "%~dp0"

:: Check if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from python.org and try again.
    pause
    exit /b
)

:: Quick dependency check (using mediapipe as proxy)
python -c "import mediapipe" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Dependencies not found. Installing...
    pip install -r requirements.txt
)

echo [INFO] Starting application...
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)

endlocal
