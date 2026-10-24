@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 backend\local_server.py
) else (
  python backend\local_server.py
)
pause
