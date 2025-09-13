#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting MedAlert AI setup..."

# 1. Populate MongoDB with simulated data
echo "Populating MongoDB with simulated data..."
python backend/utils/data_generator.py

# 2. Start the FastAPI backend
echo "Starting FastAPI backend..."
cd backend
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# 3. Start the React frontend
echo "Starting React frontend..."
cd frontend
npm install # Ensure dependencies are installed
npm run dev &
FRONTEND_PID=$!
cd ..

echo "MedAlert AI is running. Backend on port 8000, Frontend on port 5173 (or similar)."
echo "To stop the processes, run: kill $BACKEND_PID $FRONTEND_PID"

wait $BACKEND_PID
wait $FRONTEND_PID