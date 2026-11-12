@echo off
rem Conduit CLI shim — PowerShell PATH'ida turadi (conduit list, conduit run ...).
set "PYEXE=python"
if exist "%~dp0..\venv\Scripts\python.exe" set "PYEXE=%~dp0..\venv\Scripts\python.exe"
"%PYEXE%" "%~dp0..\conduit.py" %*
