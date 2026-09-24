@echo off
title Adding Services to Nail POS...
cd /d "%~dp0"
py add_services.py
if %errorlevel% neq 0 (
    python add_services.py
)
pause
