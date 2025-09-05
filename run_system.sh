#!/bin/bash

# LLM Assisted Claims Submission Text Extraction Program
# Unix/Linux/macOS Shell Script for Easy Execution

echo ""
echo "========================================"
echo "LLM Claims Extraction Program Launcher"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed or not in PATH"
        echo "Please install Python 3.8+ and try again"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Python found: $($PYTHON_CMD --version)"
echo "Checking system..."

# Check if test script exists
if [ ! -f "test_system.py" ]; then
    echo "ERROR: test_system.py not found"
    echo "Please ensure you're in the correct directory"
    exit 1
fi

# Run system test first
echo ""
echo "Running system test..."
$PYTHON_CMD test_system.py

if [ $? -ne 0 ]; then
    echo ""
    echo "System test failed. Please fix issues before proceeding."
    exit 1
fi

echo ""
echo "System test passed! Starting main program..."
echo ""

# Check if master script exists
if [ ! -f "LLM_Assisted_Claims_Submission_Text_Extraction_Program.py" ]; then
    echo "ERROR: Master script not found"
    exit 1
fi

# Run the master script
$PYTHON_CMD LLM_Assisted_Claims_Submission_Text_Extraction_Program.py

echo ""
echo "Program completed."
