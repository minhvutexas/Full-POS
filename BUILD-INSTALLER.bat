@echo off
title Nail POS - Build Windows Installer
color 0A
echo.
echo ==========================================
echo   Nail POS - Build Windows Installer
echo ==========================================
echo.

:: ── Step 1: Build NailPOS.exe ──
echo [1/3] Building app with PyInstaller...

set PYTHON=C:\Users\minhv\AppData\Local\Programs\Python\Python314\python.exe
if not exist "%PYTHON%" (
    for /f "delims=" %%i in ('where python 2^>nul') do set PYTHON=%%i
)
if not exist "%PYTHON%" (
    echo ERROR: Python not found. Please install Python 3.
    pause & exit /b 1
)

pip install pywebview pyinstaller --quiet --upgrade

if exist "dist\NailPOS.exe" del /f /q "dist\NailPOS.exe"
if exist "build" rd /s /q "build"

"%PYTHON%" -m PyInstaller ^
  --onefile --noconsole ^
  --name "NailPOS" ^
  --add-data "index.html;." ^
  --add-data "checkin.html;." ^
  --add-data "booking.html;." ^
  --collect-all webview ^
  --hidden-import "webview.platforms.winforms" ^
  --hidden-import "clr" ^
  --icon "icon.ico" ^
  app.py

if not exist "dist\NailPOS.exe" (
    echo ERROR: PyInstaller build failed.
    pause & exit /b 1
)
echo    NailPOS.exe built OK.
echo.

:: ── Step 2: Find or auto-install Inno Setup ──
echo [2/3] Checking for Inno Setup...

set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
    echo    Not found. Downloading Inno Setup...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://jrsoftware.org/download.php/is.exe' -OutFile '%TEMP%\innosetup.exe' -UseBasicParsing"
    "%TEMP%\innosetup.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if "%ISCC%"=="" (
    echo ERROR: Could not install Inno Setup. Please install manually from https://jrsoftware.org/isinfo.php
    pause & exit /b 1
)
echo    Found Inno Setup.
echo.

:: ── Step 3: Compile the installer ──
echo [3/3] Compiling installer...
if not exist "installer" mkdir installer

"%ISCC%" "NailPOS-Installer.iss"

if not exist "installer\NailPOS-Setup.exe" (
    echo ERROR: Installer compilation failed.
    pause & exit /b 1
)

echo.
echo ==========================================
echo   SUCCESS!
echo ==========================================
echo.
echo   Installer: installer\NailPOS-Setup.exe
echo.
echo   Copy NailPOS-Setup.exe to any Windows 11
echo   PC and double-click to install Nail POS.
echo.
explorer installer
pause
