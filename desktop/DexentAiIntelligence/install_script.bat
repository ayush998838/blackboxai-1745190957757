@echo off
REM Dexent.ai Installation Script for Windows
REM This script installs all necessary components for Dexent.ai

echo ========================================
echo Dexent.ai Installation Script for Windows
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python 3.11 or later.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version (should be 3.11 or higher)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Detected Python version: %PYTHON_VERSION%

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install required packages
echo Installing required packages...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install required packages.
    pause
    exit /b 1
)

REM Check if PostgreSQL is installed
psql --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PostgreSQL is not installed. It is recommended for production use.
    echo Download from: https://www.postgresql.org/download/windows/
    echo.
    echo Using SQLite database for now.
    echo.
) else (
    echo PostgreSQL is installed.
    echo Please update the .env file with your PostgreSQL credentials.
    echo.
)

REM Check if VB-Audio Virtual Cable is installed
if not exist "%ProgramFiles%\VB\CABLE\*.*" (
    echo VB-Audio Virtual Cable is not installed.
    echo It is recommended for audio routing.
    echo Download from: https://vb-audio.com/Cable/
    echo.
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating default .env file...
    echo DATABASE_URL=sqlite:///dexent.db> .env
    echo SESSION_SECRET=dexent-ai-secure-session-secret>> .env
    echo FIREBASE_API_KEY=>> .env
    echo FIREBASE_PROJECT_ID=>> .env
    echo FIREBASE_APP_ID=>> .env
    echo OPENAI_API_KEY=>> .env
    echo.
    echo Please update the .env file with your API keys and database credentials.
    echo.
)

REM Create required directories
echo Creating required directories...
mkdir uploads 2>nul
mkdir processed 2>nul
mkdir models 2>nul
mkdir instance 2>nul

REM Create desktop shortcut
echo Creating desktop shortcut...
set SCRIPT_DIR=%~dp0
set SHORTCUT_PATH=%USERPROFILE%\Desktop\Dexent.ai.lnk
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%SCRIPT_DIR%venv\Scripts\pythonw.exe'; $Shortcut.Arguments = '%SCRIPT_DIR%windows_client.py'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Save()"

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo To start Dexent.ai:
echo 1. Double-click the Dexent.ai shortcut on your desktop
echo - OR -
echo 1. Open Command Prompt
echo 2. Navigate to the Dexent.ai directory: cd %SCRIPT_DIR%
echo 3. Activate the virtual environment: venv\Scripts\activate
echo 4. Run the application: python windows_client.py
echo.
echo For more information, see the README.md file.
echo.
pause