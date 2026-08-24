@echo off
setlocal
title Blink — Advanced Eye Health Monitor (FastAPI + React + Vite)

echo ======================================================
echo    Blink — Eye Health Monitor (FastAPI + React + Vite)
echo ======================================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

:: Dependency check
python -c "import fastapi, uvicorn, mediapipe, cv2" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing Python dependencies...
    pip install -r requirements.txt
)

:: Check if frontend is built
if not exist "frontend\dist\index.html" (
    echo [INFO] Frontend build not found. Building React + Vite app...
    cd frontend
    call npm install
    call npm run build
    cd ..
)

echo.
echo [INFO] Starting Blink Server on http://127.0.0.1:8000 ...
echo [INFO] Opening dashboard in your default browser...
echo.

python server.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)

endlocal
