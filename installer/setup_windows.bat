@echo off
setlocal EnableExtensions

set "APP_NAME=Pullan Dental Clinic"
set "APP_DIR=%LOCALAPPDATA%\PullanDentalClinic"
set "SOURCE_DIR=%~dp0.."
set "PYTHON_CMD="

echo.
echo ==========================================
echo  Pullan Dental Clinic Installer
echo ==========================================
echo.

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL%==0 (
        set "PYTHON_CMD=python"
    )
)

if "%PYTHON_CMD%"=="" (
    echo Python was not found.
    echo.
    echo The installer will try to install Python using winget.
    echo If this fails, install Python 3.11 or newer from https://www.python.org/downloads/windows/
    echo and run this installer again.
    echo.
    where winget >nul 2>nul
    if %ERRORLEVEL%==0 (
        winget install --id Python.Python.3.13 -e --source winget
    )

    where py >nul 2>nul
    if %ERRORLEVEL%==0 (
        set "PYTHON_CMD=py -3"
    ) else (
        where python >nul 2>nul
        if %ERRORLEVEL%==0 (
            set "PYTHON_CMD=python"
        )
    )
)

if "%PYTHON_CMD%"=="" (
    echo.
    echo Python is still not available. Please install Python and re-run this installer.
    pause
    exit /b 1
)

where curl >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo curl was not found.
    echo.
    echo InfiniReach SMS uses curl as a fallback when Cloudflare blocks Python requests.
    echo Please install curl or update Windows, then run this installer again.
    pause
    exit /b 1
)

echo Installing to:
echo   %APP_DIR%
echo.

if not exist "%APP_DIR%" mkdir "%APP_DIR%"
robocopy "%SOURCE_DIR%" "%APP_DIR%" /E /XD ".git" "__pycache__" "instance" "backups" "dist" /XF "*.pyc" >nul
if %ERRORLEVEL% GEQ 8 (
    echo Failed to copy application files.
    pause
    exit /b 1
)

cd /d "%APP_DIR%"

if not exist ".env" (
    copy ".env.example" ".env" >nul
)

powershell -NoProfile -ExecutionPolicy Bypass -File "installer\ensure_sms_env.ps1" -EnvPath ".env"

if not exist "instance" mkdir "instance"
if not exist "backups" mkdir "backups"

echo Creating Python virtual environment...
%PYTHON_CMD% -m venv ".venv"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)

echo Installing required packages...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
call ".venv\Scripts\pip.exe" install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies. Check your internet connection and try again.
    pause
    exit /b 1
)

echo Creating launchers...
(
    echo @echo off
    echo cd /d "%%~dp0"
    echo powershell -NoProfile -ExecutionPolicy Bypass -File "%%~dp0installer\launch_local.ps1"
) > "Run Pullan Dental Clinic.bat"

(
    echo @echo off
    echo cd /d "%%~dp0"
    echo powershell -NoProfile -ExecutionPolicy Bypass -File "%%~dp0installer\launch_lan.ps1"
) > "Run Pullan Dental Clinic LAN.bat"

powershell -NoProfile -ExecutionPolicy Bypass -File "installer\create_shortcuts.ps1" -AppDir "%APP_DIR%"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create shortcuts.
    pause
    exit /b 1
)

echo.
echo Installation complete.
echo.
echo Desktop shortcut:
echo   Pullan Dental Clinic ^(LAN^)
echo.
echo Installed folder:
echo   %APP_DIR%
echo.
echo Run locally:
echo   %APP_DIR%\Run Pullan Dental Clinic.bat
echo.
echo Run on LAN:
echo   %APP_DIR%\Run Pullan Dental Clinic LAN.bat
echo.
pause
