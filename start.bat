@echo off
title Nail POS Server
echo.
echo Starting Nail POS Server...
echo.

REM Try py launcher first (Windows Python Launcher)
where py >nul 2>&1
if %errorlevel% equ 0 (
    py "%~dp0server.py"
    pause
    exit /b 0
)

REM Try python
where python >nul 2>&1
if %errorlevel% equ 0 (
    python "%~dp0server.py"
    pause
    exit /b 0
)

REM Try python3
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    python3 "%~dp0server.py"
    pause
    exit /b 0
)

REM Try common install locations
set PYEXE=
if exist "C:\Users\minhv\AppData\Local\Programs\Python\Python314\python.exe" set PYEXE=C:\Users\minhv\AppData\Local\Programs\Python\Python314\python.exe
if exist "C:\Users\minhv\AppData\Local\Programs\Python\Python313\python.exe" set PYEXE=C:\Users\minhv\AppData\Local\Programs\Python\Python313\python.exe
if exist "C:\Users\minhv\AppData\Local\Programs\Python\Python312\python.exe" set PYEXE=C:\Users\minhv\AppData\Local\Programs\Python\Python312\python.exe
if exist "C:\Users\minhv\AppData\Local\Programs\Python\Python311\python.exe" set PYEXE=C:\Users\minhv\AppData\Local\Programs\Python\Python311\python.exe
if exist "C:\Program Files\Python314\python.exe" set PYEXE=C:\Program Files\Python314\python.exe
if exist "C:\Python314\python.exe" set PYEXE=C:\Python314\python.exe

if not "%PYEXE%"=="" (
    "%PYEXE%" "%~dp0server.py"
    pause
    exit /b 0
)

echo ERROR: Python not found.
echo.
echo Please add Python to your PATH:
echo   1. Open Start menu, search "Environment Variables"
echo   2. Edit PATH and add your Python folder
echo.
echo Or download Python from: https://www.python.org
pause
exit /b 1
