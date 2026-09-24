@echo off
setlocal EnableDelayedExpansion
title Nail POS — Starting...
color 0D
cd /d "%~dp0"

echo.
echo  ==========================================
echo    Nail POS  ^|  Launching...
echo  ==========================================
echo.

REM ── 1. Stop any existing Nail POS instances ────────────────────────────────
echo  [1/4] Closing old instances...
taskkill /f /im NailPOS.exe    >nul 2>&1
taskkill /f /im python.exe     >nul 2>&1
taskkill /f /im py.exe         >nul 2>&1
timeout /t 1 /nobreak          >nul

REM ── 2. Find Python ────────────────────────────────────────────────────────
set PYEXE=
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set PYEXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" if "!PYEXE!"=="" set PYEXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" if "!PYEXE!"=="" set PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" if "!PYEXE!"=="" set PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
where py     >nul 2>&1 && if "!PYEXE!"=="" set PYEXE=py
where python >nul 2>&1 && if "!PYEXE!"=="" set PYEXE=python

if "!PYEXE!"=="" (
    color 0C
    echo  ERROR: Python not found.
    echo  Please install Python from https://www.python.org
    pause & exit /b 1
)
echo  Python: !PYEXE!

REM ── 3. Start server in minimized background window ─────────────────────────
echo  [2/4] Starting server...
start "Nail POS Server" /min cmd /c ""!PYEXE!" "%~dp0server.py""

REM Wait up to 10 seconds for server to be ready
echo  [3/4] Waiting for server to be ready...
set READY=0
for /L %%i in (1,1,10) do (
    if !READY!==0 (
        timeout /t 1 /nobreak >nul
        "!PYEXE!" -c "import urllib.request; urllib.request.urlopen('http://localhost:3000')" >nul 2>&1
        if not errorlevel 1 set READY=1
    )
)
if !READY!==0 (
    echo  WARNING: Server took longer than expected — opening browser anyway...
)

REM ── 4. Open browser windows ────────────────────────────────────────────────
echo  [4/4] Opening Nail POS...

REM Find best browser (prefer app-mode for clean window with no browser UI)
set BROWSER=
if exist "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"              set BROWSER=%PROGRAMFILES%\Google\Chrome\Application\chrome.exe
if exist "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"         if "!BROWSER!"=="" set BROWSER=%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"              if "!BROWSER!"=="" set BROWSER=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe
if exist "%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe" if "!BROWSER!"=="" set BROWSER=%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe
if exist "%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe" if "!BROWSER!"=="" set BROWSER=%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe
if exist "%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"        if "!BROWSER!"=="" set BROWSER=%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe
if exist "%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"             if "!BROWSER!"=="" set BROWSER=%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe

if not "!BROWSER!"=="" (
    REM Open POS Manager (staff screen)
    start "" "!BROWSER!" --app=http://localhost:3000 --window-size=1400,900 --window-position=0,0
    timeout /t 1 /nobreak >nul
    REM Open Customer Display (faces the customer)
    start "" "!BROWSER!" --app=http://localhost:3000/customer-display.html --window-size=1024,768 --kiosk
    timeout /t 1 /nobreak >nul
    REM Open Check-In Kiosk
    start "" "!BROWSER!" --app=http://localhost:3000/checkin.html --window-size=900,700
) else (
    REM Fallback: open in default browser
    start "" "http://localhost:3000"
    start "" "http://localhost:3000/customer-display.html"
    start "" "http://localhost:3000/checkin.html"
)

echo.
echo  ==========================================
echo    Nail POS is running!
echo.
echo    POS Manager:  http://localhost:3000
echo    Check-In:     http://localhost:3000/checkin.html
echo.
echo    On other devices (same WiFi):
echo    http://[your-ip]:3000
echo  ==========================================
echo.
echo  Keep this window minimized — close it to stop the server.
echo  ==========================================

REM Keep window alive (server runs in its own minimized window)
pause
