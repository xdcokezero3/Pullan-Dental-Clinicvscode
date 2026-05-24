@echo off
cd /d "%~dp0"
set APP_HOST=0.0.0.0
set APP_PORT=5000
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    python app.py
)
pause
