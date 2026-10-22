@echo off
title AI Study & Career Copilot
echo ====================================================
echo Starting AI Study & Career Copilot...
echo ====================================================

cd /d "%~dp0"

echo Checking dependencies...
python -m pip install -r requirements.txt --quiet

echo Starting backend server on http://127.0.0.1:8000
start "" http://127.0.0.1:8000
python backend/app.py

pause
