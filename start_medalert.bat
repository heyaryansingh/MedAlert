@echo off
echo Starting MedAlert AI Chatbot System...
echo.

REM Kill any existing Python processes to clear previous run history
echo Clearing previous run history...
taskkill /F /IM python.exe >nul 2>&1
if errorlevel 1 (
    echo No previous Python processes found.
) else (
    echo Previous Python processes terminated.
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install required packages
echo Installing required packages...
pip install fastapi uvicorn python-multipart >nul 2>&1

REM Start the backend server in background
echo Starting backend server...
start /B python chatbot_server.py

REM Wait a moment for server to start
timeout /t 3 /nobreak >nul

REM Open the web page
echo Opening MedAlert web page...
start medalert_app.html

echo.
echo MedAlert AI Chatbot System is now running!
echo - Backend server: http://localhost:8001
echo - Web interface: Opened in your default browser
echo.
echo Press any key to stop the server and exit...
pause >nul

REM Kill the Python process
taskkill /F /IM python.exe >nul 2>&1
echo Server stopped.
