@echo off
setlocal
title Installing Blink...

cd /d "%~dp0"
echo ==========================================
echo    Installing Blink
echo ==========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org and try again.
    pause
    exit /b
)

echo [INFO] Installing required Python packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b
)

echo [INFO] Creating Desktop Shortcut...
set SCRIPT="%TEMP%\%RANDOM%_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\Blink.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%~dp0Run_Project.bat" >> %SCRIPT%
echo oLink.WorkingDirectory = "%~dp0" >> %SCRIPT%
echo oLink.IconLocation = "shell32.dll, 43" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo [SUCCESS] Installation Complete!
echo You can now use the 'Blink' shortcut on your Desktop or run Run_Project.bat.
pause
endlocal
