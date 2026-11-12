@echo off
chcp 65001 >nul
title Conduit AI Studio - To'xtatish

echo ===================================================
echo          CONDUIT AI STUDIO TO'XTATILMOQDA
echo ===================================================
echo.

powershell -NoProfile -Command ^
  "Get-NetTCPConnection -LocalPort 8000,3000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }; Write-Host '[OK] Backend (8000) va Frontend (3000) toxtatildi.'"

powershell -NoProfile -Command ^
  "Get-Process msedge -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*Conduit*' } | Stop-Process -Force -ErrorAction SilentlyContinue"

echo.
echo Conduit AI Studio to'liq to'xtatildi.
timeout /t 2 >nul
