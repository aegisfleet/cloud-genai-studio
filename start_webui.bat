@echo off
chcp 65001 > nul
title YuE2 Web UI (RTX 3060 Optimized)

cd /d %~dp0

echo ========================================================
echo   YuE2 Web UI Launcher (RTX 3060 12GB Optimized)
echo ========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv not found.
    pause
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Starting YuE2 Web UI...
echo The browser will open automatically at http://127.0.0.1:7860
echo.

python webui.py

pause
