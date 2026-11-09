@echo off
chcp 65001 >nul
title Conduit Studio Launcher
color 0A

echo ===================================================
echo             CONDUIT STUDIO PC APP
echo ===================================================
echo.

set "CONDUIT_ROOT=C:\Users\user\.gemini\antigravity\scratch\conduit"
set "PYTHON_EXE=C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"

echo [Conduit] Standalone PC Ilova sifatida ishga tushirilmoqda...
start "" "%PYTHON_EXE%" "%CONDUIT_ROOT%\desktop_app.py"

exit
