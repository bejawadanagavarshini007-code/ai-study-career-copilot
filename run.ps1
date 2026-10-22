Write-Host "====================================================" -ForegroundColor Cyan
Write-Host " Starting AI Study & Career Copilot..." -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

Set-Location $PSScriptRoot

Write-Host "Installing/verifying dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt --quiet

Write-Host "Launching web browser at http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8000"

Write-Host "Starting FastAPI backend server..." -ForegroundColor Green
python backend/app.py
