@echo off
REM Exit immediately if a command exits with a non-zero status.
REM In batch, this is typically handled by checking ERRORLEVEL after each command.

echo Starting MedAlert AI setup...

REM 1. Install Python dependencies
echo Installing Python dependencies...
cd backend
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo Error installing Python dependencies. Exiting.
    exit /b %ERRORLEVEL%
)

REM 2. Populate MongoDB with simulated data
echo Populating MongoDB with simulated data...
python -m backend.utils.data_generator
IF %ERRORLEVEL% NEQ 0 (
    echo Error populating data. Exiting.
    exit /b %ERRORLEVEL%
)

REM 3. Start the FastAPI backend
echo Starting FastAPI backend...
start /B uvicorn main:app --reload --port 8000
cd ..
IF %ERRORLEVEL% NEQ 0 (
    echo Error starting backend. Exiting.
    exit /b %ERRORLEVEL%
)

REM 4. Start the React frontend
echo Starting React frontend...
cd frontend
call npm install
IF %ERRORLEVEL% NEQ 0 (
    echo Error installing frontend dependencies. Exiting.
    exit /b %ERRORLEVEL%
)
start /B npm run dev
cd ..
IF %ERRORLEVEL% NEQ 0 (
    echo Error starting frontend. Exiting.
    exit /b %ERRORLEVEL%
)

echo MedAlert AI is running. Backend on port 8000, Frontend on port 5173 (or similar).
echo To stop the processes, you may need to manually close the terminal windows or find the PIDs and use 'taskkill'.

REM Keep the script running to keep the started processes alive in the background
pause