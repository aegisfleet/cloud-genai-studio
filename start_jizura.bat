@echo off
chcp 65001 > nul
echo ========================================================
echo Starting JIZURA Lyric Motion Video Studio (Local Edition)
echo ========================================================
echo.

if not exist "%~dp0tools\jizura\index.html" (
    echo [Info] JIZURA not found in tools/jizura.
    echo [Info] Cloning JIZURA repository into tools/jizura...
    git clone --depth 1 https://github.com/852wa/JIZURA "%~dp0tools\jizura"
)

echo [Source Audio]: outputs\10deg_take3_expressive.wav
echo [Source Lyrics]: examples\lyrics\10deg_jizura_lyrics.lrc
echo.
echo Opening JIZURA in your default browser...
start "" "%~dp0tools\jizura\index.html"
echo.
echo Ready! Drag and drop the WAV file and paste the LRC lyrics.
pause
