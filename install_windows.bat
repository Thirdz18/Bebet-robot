@echo off
setlocal

where python >nul 2>nul
if errorlevel 1 (
    echo Python is not installed or not added to PATH.
    echo Install Python 3.10+ from https://www.python.org/downloads/ then run this file again.
    exit /b 1
)

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Setup complete.
echo Run the robot with: .venv\Scripts\python.exe src\desktop_robot.py
