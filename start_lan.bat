@echo off
cd /d "%~dp0"
set APP_HOST=0.0.0.0
set APP_PORT=5000
python app.py
pause
