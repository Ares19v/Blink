@echo off
setlocal
title Building Blink.exe

cd /d "%~dp0"
echo ==========================================
echo    Blink — PyInstaller Build
echo ==========================================
echo.

python --version >nul 2>&1 || (echo [ERROR] Python not found. && pause && exit /b)

pip show pyinstaller >nul 2>&1 || pip install pyinstaller

echo [INFO] Building Blink.exe (this may take 1-2 minutes)...

pyinstaller ^
  --onefile ^
  --windowed ^
  --name Blink ^
  --add-data "gui/theme.qss;gui" ^
  --add-data "models;models" ^
  --add-data "config.json;." ^
  main.py

echo.
if exist "dist\Blink.exe" (
    echo [SUCCESS] dist\Blink.exe is ready!
) else (
    echo [ERROR] Build failed — check output above.
)
pause
endlocal
