@echo off
title Rebuilding Nail POS...
cd /d "%~dp0"

echo.
echo ========================================
echo   Nail POS - Rebuilding App
echo ========================================
echo.

echo [1/3] Installing packages (first time may take 2-3 min)...
call npm install
if %errorlevel% neq 0 (
    echo ERROR: npm install failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Building new installer...
call npm run build
if %errorlevel% neq 0 (
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo [3/3] Done! Running new installer...
echo.
start "" "dist\Nail POS Setup 1.0.0.exe"

echo.
echo ========================================
echo   Install complete - reopen Nail POS!
echo ========================================
pause
