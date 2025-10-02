@echo off
echo Starting A.R.I.E.S. - Autonomous Reasoning & Interaction Executive System
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run A.R.I.E.S.
python main.py

REM Keep window open if there's an error
pause
