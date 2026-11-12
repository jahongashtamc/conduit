@echo off
rem Conduit dispatcher: args berilsa CLI, argsiz studiya ishga tushadi.
chcp 65001 >nul
cd /d "%~dp0"

set "PYEXE=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PYEXE=%~dp0.venv\Scripts\python.exe"

if "%~1"=="" (
    title Conduit AI Studio
    "%PYEXE%" "%~dp0conduit_app.py" %*
) else (
    "%PYEXE%" "%~dp0conduit.py" %*
)
