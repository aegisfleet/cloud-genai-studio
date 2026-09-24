@echo off
chcp 65001 > nul
title JIZURA Lyric Motion Studio

echo ========================================================
echo   JIZURA Lyric Motion Video Studio (Auto-Update Enabled)
echo ========================================================
echo.

if not exist "%~dp0tools\jizura\index.html" (
    echo [Info] JIZURA not found in tools/jizura.
    echo [Info] Cloning JIZURA repository into tools/jizura...
    git clone https://github.com/852wa/JIZURA "%~dp0tools\jizura"
) else (
    echo [Info] Checking and updating JIZURA to the latest version...
    git -C "%~dp0tools\jizura" pull
)

echo.
echo --------------------------------------------------------
echo [Active Project Audio]:
echo   outputs\weight_of_the_world_celtic_sacred.wav
echo.
echo [Active Project Lyrics (JIZURA Motion Tags)]:
echo   outputs\weight_of_the_world_jizura.lrc
echo --------------------------------------------------------
echo.
echo Opening JIZURA Studio in your default browser...
start "" "%~dp0tools\jizura\index.html"
echo.
echo Ready!
echo 1. Drag and drop the WAV audio into JIZURA.
echo 2. Copy and paste the contents of weight_of_the_world_jizura.lrc.
echo 3. Customize font/theme and export video!
echo.
pause
