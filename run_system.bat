@echo off
REM LLM Assisted Claims Submission Text Extraction Program
REM Windows Batch File for Easy Execution

echo.
echo ========================================
echo LLM Claims Extraction Program Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python found. Checking system...

REM Check if test script exists
if not exist "test_system.py" (
    echo ERROR: test_system.py not found
    echo Please ensure you're in the correct directory
    pause
    exit /b 1
)

REM Run system test first
echo.
echo Running system test...
python test_system.py

if errorlevel 1 (
    echo.
    echo System test failed. Please fix issues before proceeding.
    pause
    exit /b 1
)

echo.
echo System test passed! Starting main program...
echo.

REM Check if master script exists
if not exist "LLM_Assisted_Claims_Submission_Text_Extraction_Program.py" (
    echo ERROR: Master script not found
    pause
    exit /b 1
)

REM Run the master script
python LLM_Assisted_Claims_Submission_Text_Extraction_Program.py

echo.
echo Program completed.
pause
