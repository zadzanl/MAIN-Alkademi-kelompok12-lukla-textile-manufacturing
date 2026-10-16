@echo off
REM Backend startup script untuk Sampling & Spec R&D

cd /d "%~dp0"
set "REPO_ROOT=%~dp0..\..\.."

echo Checking virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment in .venv...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

echo Ensuring backend dependencies are installed...
python -m pip install --disable-pip-version-check -q -r requirements.txt

echo Starting Lukla AI backend on port 8000...
start "Lukla AI Backend" cmd /k "cd /d "%REPO_ROOT%" && set PYTHONPATH=. && "%VIRTUAL_ENV%\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

echo Starting backend server on port 8009...
echo.
echo Backend will be available at: http://localhost:8009
echo Lukla Assistant API at:       http://localhost:8009/api/v1/copilot/chat
echo API Docs at:                  http://localhost:8009/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8009

pause
