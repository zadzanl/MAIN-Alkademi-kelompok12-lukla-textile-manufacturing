@echo off
REM Backend startup script untuk Sampling & Spec R&D

cd /d "%~dp0"

echo Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Starting backend server on port 8009...
echo.
echo Backend will be available at: http://localhost:8009
echo API Docs at: http://localhost:8009/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn src.main:app --reload --port 8009

pause
