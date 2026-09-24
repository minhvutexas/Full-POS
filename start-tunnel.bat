@echo off
title Nail POS — Internet Tunnel
echo.
echo ════════════════════════════════════════════
echo   💅 Nail POS — Cloudflare Tunnel
echo ════════════════════════════════════════════
echo.
echo This exposes your local POS to the internet
echo so your website booking form can send
echo appointments directly to the POS.
echo.
echo STEP 1: Make sure server.js is running first
echo         (run start.bat in another window)
echo.
echo STEP 2: Starting tunnel to port 3000...
echo.

where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    echo Cloudflared not found. Downloading...
    echo.
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile '%~dp0cloudflared.exe'}"
    if %errorlevel% neq 0 (
        echo Download failed. Please install manually:
        echo   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
        pause
        exit /b 1
    )
    echo Downloaded cloudflared.exe
    echo.
    "%~dp0cloudflared.exe" tunnel --url http://localhost:3000
) else (
    cloudflared tunnel --url http://localhost:3000
)

echo.
echo ════════════════════════════════════════════
echo  Copy the https://xxxxx.trycloudflare.com
echo  URL above and paste it into booking.html
echo  as the POS_SERVER_URL value at the top.
echo ════════════════════════════════════════════
pause
