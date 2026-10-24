@echo off
setlocal
chcp 65001 >nul
title UniSense Stop

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-services.ps1" %*
set "STOP_EXIT=%ERRORLEVEL%"
echo.
if /i "%~1"=="-WhatIf" goto preview
if not "%STOP_EXIT%"=="0" goto failed
echo UniSense Backend ve Frontend durdurma islemi tamamlandi.
echo UniSense Firebase Emulator da durduruldu; start.bat temizden baslatabilir.
echo Emulator icindeki gecici Auth/Firestore test verileri silinebilir.
goto done

:preview
echo Yukaridaki liste onizlemeydi; hicbir surec kapatilmadi.
goto done

:failed
echo [HATA] Servisleri durdurma betigi hata verdi. Yukaridaki ciktiyi kontrol edin.

:done
echo.
pause
exit /b %STOP_EXIT%
