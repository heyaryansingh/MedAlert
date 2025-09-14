# MedAlert AI Chatbot Startup Script
Write-Host "Starting MedAlert AI Chatbot System..." -ForegroundColor Green
Write-Host ""

# Kill any existing Python processes to clear previous run history
Write-Host "Clearing previous run history..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    $pythonProcesses | Stop-Process -Force
    Write-Host "Previous Python processes terminated." -ForegroundColor Green
} else {
    Write-Host "No previous Python processes found." -ForegroundColor Green
}

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install fastapi uvicorn python-multipart | Out-Null

# Start the backend server in background
Write-Host "Starting backend server..." -ForegroundColor Yellow
Start-Process python -ArgumentList "chatbot_server.py" -WindowStyle Hidden

# Wait a moment for server to start
Start-Sleep -Seconds 3

# Open the web page
Write-Host "Opening MedAlert web page..." -ForegroundColor Yellow
Start-Process "medalert_app.html"

Write-Host ""
Write-Host "MedAlert AI Chatbot System is now running!" -ForegroundColor Green
Write-Host "- Backend server: http://localhost:8001" -ForegroundColor Cyan
Write-Host "- Web interface: Opened in your default browser" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to stop the server and exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Kill the Python process
Write-Host "Stopping server..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Server stopped." -ForegroundColor Green
