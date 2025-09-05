@echo off
echo ========================================
echo Claims Data Embeddings Pipeline (Local)
echo ========================================
echo.
echo This will run the embeddings pipeline using local FAISS database
echo (No API keys required)
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Run the local pipeline
echo.
echo Starting embeddings pipeline...
python run_local_pipeline.py

echo.
echo Pipeline completed!
echo.
echo To start the web interface, run:
echo   python web_app.py
echo.
pause
