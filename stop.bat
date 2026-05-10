@echo off
echo Servisler durduruluyor...

REM Backend (8002)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8002.*LISTENING"') do (
    echo   [Backend] PID %%a kapatiliyor...
    taskkill /F /PID %%a >nul 2>&1
)

REM Frontend (5174)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5174.*LISTENING"') do (
    echo   [Frontend] PID %%a kapatiliyor...
    taskkill /F /PID %%a >nul 2>&1
)

REM Pencere baslik
taskkill /FI "WindowTitle eq UniSense Backend*" /F >nul 2>&1
taskkill /FI "WindowTitle eq UniSense Frontend*" /F >nul 2>&1

echo Tamam.
timeout /t 2 /nobreak >nul
