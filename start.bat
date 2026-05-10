@echo off
chcp 65001 >nul
REM ============================================================
REM  UniSense - Tum servisler baslatici
REM  - Backend (FastAPI 8002)
REM  - Frontend (Vite 5174)
REM ============================================================

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

REM === Python UTF-8 modu (ana shell'de, tirnakli format â€” bosluk korumasi) ===
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

echo.
echo ============================================================
echo   UniSense - Tum servisler baslatiliyor
echo ============================================================
echo.

REM --- 1/2 Backend (FastAPI 8002) ---
echo [1/2] Backend baslatiliyor (FastAPI 8002)...
start "UniSense Backend" cmd /k "cd /d %BACKEND% && python -m uvicorn unisense.main:app --host 0.0.0.0 --port 8002 --reload"
timeout /t 4 /nobreak >nul

REM --- 2/2 Frontend (Vite 5174) ---
echo [2/2] Frontend baslatiliyor (Vite 5174)...
start "UniSense Frontend" cmd /k "cd /d %FRONTEND% && npm run dev"
timeout /t 4 /nobreak >nul

echo.
echo ============================================================
echo   Adresler:
echo     Frontend  http://localhost:5174
echo     Backend   http://localhost:8002/api/docs
echo     Health    http://localhost:8002/api/v1/health
echo ============================================================

REM Tarayicida frontend'i ac
start http://localhost:5174

echo.
echo Kapatmak icin: stop.bat
echo.
pause
