@echo off
setlocal

if not exist .venv\Scripts\python.exe (
    echo Virtual environment not found. Run install_windows.bat first.
    exit /b 1
)

.venv\Scripts\python.exe src\desktop_robot.py
