@echo off
setlocal
chcp 65001 >nul
title UniSense Local Test Orchestrator
cls

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
set "BACKEND=%PROJECT_ROOT%\backend"
set "FRONTEND=%PROJECT_ROOT%\frontend"

echo.
echo ============================================================
echo   UniSense Local Test Orchestrator v1.0
echo   ============================================================
echo.
echo [1/5] Ortam kontrol ediliyor...

REM ---------------------------------------------------------
REM Gerekli araclari kontrol et
REM ---------------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [HATA] python bulunamadi!
    pause
    exit /b 1
)
echo [OK] python bulundu

where node >nul 2>nul
if errorlevel 1 (
    echo [HATA] node/npm bulunamadi!
    pause
    exit /b 1
)
echo [OK] node/npm bulundu

where npm >nul 2>nul
if errorlevel 1 (
    echo [HATA] npm bulunamadi!
    pause
    exit /b 1
)
echo [OK] npm bulundu

where firebase >nul 2>nul
if errorlevel 1 (
    echo [HATA] Firebase CLI bulunamadi. Yerel Firestore/Auth emulatoru gerekli.
    pause
    exit /b 1
)
echo [OK] Firebase CLI bulundu

REM ---------------------------------------------------------
REM Proje dizinini kontrol et
REM ---------------------------------------------------------
if not exist "%PROJECT_ROOT%" (
    echo [HATA] Proje klasoru bulunamadi: %PROJECT_ROOT%
    pause
    exit /b 1
)
cd /d "%PROJECT_ROOT%"
echo [OK] Proje dizini: %PROJECT_ROOT%

REM ---------------------------------------------------------
REM .env.local dosyalarini kontrol/olustur
REM ---------------------------------------------------------
echo.
echo [2/5] Environment dosyalari kontrol ediliyor...

if not exist "%BACKEND%\.env" (
    echo [HATA] backend\.env bulunamadi. backend\.env.example dosyasini kopyalayip ayarlayin.
    pause
    exit /b 1
)
if not exist "%FRONTEND%\.env.local" (
    echo [UYARI] frontend\.env.local bulunamadi; frontend API ayarlarinizi kontrol edin.
)

REM ---------------------------------------------------------
REM Firebase Emulator'lari baslat (yalnizca bu projede yerel)
REM ---------------------------------------------------------
echo.
echo [3/5] Firebase Emulator'lar baslatiliyor...
if not exist "%PROJECT_ROOT%\firebase.json" (
    echo [HATA] firebase.json bulunamadi.
    pause
    exit /b 1
)
REM Eski/guncel backend veya Vite aciksa ikinci kopya baslatip "hazir" demeyelim.
powershell -NoProfile -Command "if (Get-NetTCPConnection -State Listen -LocalPort 8002,5174 -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
    echo [HATA] 8002 veya 5174 portu zaten kullanimda.
    echo Once UniSense'e ait eski Backend/Frontend pencerelerini kapatin, sonra tekrar deneyin.
    echo Calisan surecleri guvenlik icin bu betik otomatik kapatmaz.
    pause
    exit /b 1
)
REM Ayni UniSense emulator'u zaten calisiyorsa ikinci kez baslatma (port cakismasi).
powershell -NoProfile -Command "$p=Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'firebase\.js emulators:start' -and $_.CommandLine -match '--project unisense-test' }; $l=Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue; if($p -and ($l.LocalPort -contains 8085) -and ($l.LocalPort -contains 9099)){exit 0}else{exit 1}"
if not errorlevel 1 (
    echo [OK] Mevcut UniSense Firebase Emulator'u yeniden kullaniliyor (Firestore: 8085, Auth: 9099)
) else (
    start "UniSense Firebase Emulators" cmd /k "cd /d ""%PROJECT_ROOT%"" && firebase emulators:start --only firestore,auth --project unisense-test"
    echo [OK] Firebase Emulator'lari baslatiliyor (Firestore: 8085, Auth: 9099)
    timeout /t 5 /nobreak >nul
)

REM ---------------------------------------------------------
REM Backend baslat
REM ---------------------------------------------------------
echo.
echo [4/5] Backend baslatiliyor (port 8002)...
set "FIRESTORE_EMULATOR_HOST=localhost:8085"
set FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
set BACKEND_URL=http://localhost:8002
set FRONTEND_URL=http://localhost:5174
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

start "UniSense Backend" cmd /k "cd /d ""%BACKEND%"" && python -m uvicorn unisense.main:app --reload --host 127.0.0.1 --port 8002"
echo [OK] Backend baslatildi (http://localhost:8002)
timeout /t 5 /nobreak >nul

REM ---------------------------------------------------------
REM Frontend baslat
REM ---------------------------------------------------------
cd /d "%FRONTEND%"
echo [5/5] Frontend baslatiliyor (port 5174)...
start "UniSense Frontend" cmd /k "cd /d ""%FRONTEND%"" && npm run dev -- --host 127.0.0.1 --port 5174"
echo [OK] Frontend baslatildi (http://localhost:5174)
timeout /t 3 /nobreak >nul

REM ---------------------------------------------------------
REM Ozet
REM ---------------------------------------------------------
echo.
echo ============================================================
echo   UniSense Yerel Test Ortami HAZIR!
echo   ============================================================
echo.
echo  Backend API:     http://localhost:8002
echo  API Docs:        http://localhost:8002/api/docs
echo  Frontend:        http://localhost:5174
echo  Firebase UI:     http://localhost:4000/firestore
echo.
echo [TEST] Hizli test:
echo   curl http://localhost:8002/api/v1/health
echo.
echo [DURDURMA] UniSense servislerini kapatmak icin stop.bat calistirin.
echo ============================================================
echo.

REM ---------------------------------------------------------
REM Tum pencereyi acik tut
REM ---------------------------------------------------------
echo.
echo Servisler kendi pencerelerinde calisiyor.
echo.
pause
