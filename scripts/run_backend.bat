@echo off
REM Start FailureFoundry FastAPI Backend Server
echo Starting FailureFoundry Backend on http://127.0.0.1:8000 ...

if exist "%~dp0..\.venv\Scripts\python.exe" (
    "%~dp0..\.venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir "%~dp0..\backend" --host 127.0.0.1 --port 8000 --reload
) else (
    echo Virtual environment not found. Run: python -m venv .venv ^&^& .\.venv\Scripts\pip install -r backend\requirements.txt
    exit /b 1
)
