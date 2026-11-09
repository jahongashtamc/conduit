@echo off
chcp 65001 >nul
title Stop Conduit Studio
color 0C

echo ===================================================
echo             CONDUIT STUDIO TO'XTATILMOQDA...
echo ===================================================
echo.

powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000, 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }; Write-Host '[OK] 8000 va 3000 portlardagi jarayonlar toxtatildi.'"

echo.
echo Conduit Studio to'liq to'xtatildi.
timeout /t 3 >nul
exit
