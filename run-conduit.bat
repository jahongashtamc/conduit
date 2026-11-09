@echo off
chcp 65001 > nul
title Conduit AI Studio - Desktop Workstation
echo ========================================================
echo    CONDUIT AI STUDIO - PC APPLICATION LAUNCHER
echo ========================================================
cd /d "%~dp0"
python conduit-desktop.py
pause
