@echo off
title Nail POS — Build Windows App
color 0D
echo.
echo  ==========================================
echo    Nail POS  ^|  Building Windows App
echo    (using Python — no Node.js required)
echo  ==========================================
echo.

REM ── Find Python 3.14 ────────────────────────────────────────────────────────
set PYEXE=
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe" (
    set PYEXE=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe
)
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
    if "%PYEXE%"=="" set PYEXE=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe
)
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
    if "%PYEXE%"=="" set PYEXE=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe
)

REM Try PATH as fallback
if "%PYEXE%"=="" (
    where python >nul 2>&1
    if not errorlevel 1 set PYEXE=python
)

if "%PYEXE%"=="" (
    color 0C
    echo  ERROR: Python not found.
    echo  Please install Python from https://www.python.org
    pause
    exit /b 1
)

echo  Python found: %PYEXE%
echo.

cd /d "%~dp0"

REM ── Install dependencies ─────────────────────────────────────────────────────
echo  [1/3] Installing dependencies...
echo        (pywebview, pyinstaller — first run downloads ~30 MB)
echo.
"%PYEXE%" -m pip install pywebview pyinstaller --quiet --upgrade
if errorlevel 1 (
    color 0C
    echo.
    echo  ERROR: pip install failed. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo  [2/3] Building NailPOS.exe...
echo        (this bundles Python + all dependencies into one file)
echo        (may take 2-3 minutes — please wait)
echo.

REM Clean previous build
if exist dist\NailPOS.exe del /f /q dist\NailPOS.exe
if exist build rmdir /s /q build

"%PYEXE%" -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name "NailPOS" ^
    --add-data "index.html;." ^
    --add-data "checkin.html;." ^
    --add-data "booking.html;." ^
    --collect-all webview ^
    --hidden-import "webview.platforms.winforms" ^
    --hidden-import "clr" ^
    --icon "icon.ico" ^
    app.py 2>&1

if errorlevel 1 (
    color 0C
    echo.
    echo  ERROR: Build failed. See messages above.
    pause
    exit /b 1
)

REM ── Done ─────────────────────────────────────────────────────────────────────
echo.

if exist "dist\NailPOS.exe" (
    color 0A
    echo  [3/3] Creating installer shortcut...

    REM Create a simple installer bat that copies NailPOS.exe to Program Files
    echo @echo off > "dist\Install Nail POS.bat"
    echo title Install Nail POS >> "dist\Install Nail POS.bat"
    echo echo Installing Nail POS... >> "dist\Install Nail POS.bat"
    echo if not exist "%%ProgramFiles%%\Nail POS" mkdir "%%ProgramFiles%%\Nail POS" >> "dist\Install Nail POS.bat"
    echo copy /y "%%~dp0NailPOS.exe" "%%ProgramFiles%%\Nail POS\NailPOS.exe" >> "dist\Install Nail POS.bat"
    echo powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%%PUBLIC%%\Desktop\Nail POS.lnk');$s.TargetPath='%%ProgramFiles%%\Nail POS\NailPOS.exe';$s.Save()" >> "dist\Install Nail POS.bat"
    echo powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\Nail POS.lnk');$s.TargetPath='%%ProgramFiles%%\Nail POS\NailPOS.exe';$s.Save()" >> "dist\Install Nail POS.bat"
    echo echo. >> "dist\Install Nail POS.bat"
    echo echo  Done! Nail POS shortcut created on your Desktop. >> "dist\Install Nail POS.bat"
    echo pause >> "dist\Install Nail POS.bat"

    echo.
    echo  ==========================================
    echo    SUCCESS!  App is ready.
    echo  ==========================================
    echo.
    echo  Files in the  dist\  folder:
    echo.
    echo    NailPOS.exe         ^<^<  The app itself
    echo    Install Nail POS.bat ^<^<  Run this on any PC to install
    echo.
    echo  TO INSTALL on this computer:
    echo    Just double-click:  dist\NailPOS.exe
    echo.
    echo  TO SHARE with other computers:
    echo    Copy the entire  dist\  folder to a USB drive
    echo    On the other PC: right-click "Install Nail POS.bat"
    echo                     choose "Run as administrator"
    echo.
    echo  Opening dist folder...
    explorer "%~dp0dist"
) else (
    color 0C
    echo  Build did not produce NailPOS.exe. Check output above.
)

echo.
pause
