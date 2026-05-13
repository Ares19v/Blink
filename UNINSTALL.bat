@echo off
setlocal
title Uninstalling Blink...

cd /d "%~dp0"
echo ==========================================
echo    Uninstalling / Cleaning Blink
echo ==========================================
echo.
echo This will remove local configuration, logs, and session history databases.
echo The source code and Python packages will remain intact.
echo.
pause

echo [INFO] Removing database...
if exist "blink_history.db" del /Q "blink_history.db"

echo [INFO] Removing logs...
if exist "logs" rmdir /S /Q "logs"

echo [INFO] Removing configuration...
if exist "config.json" del /Q "config.json"

echo [INFO] Removing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
if exist ".pytest_cache" rmdir /S /Q ".pytest_cache"

echo [INFO] Removing Desktop Shortcut...
if exist "%USERPROFILE%\Desktop\Blink.lnk" del /Q "%USERPROFILE%\Desktop\Blink.lnk"

echo.
echo [SUCCESS] Blink local files and configurations have been cleaned.
pause
endlocal
