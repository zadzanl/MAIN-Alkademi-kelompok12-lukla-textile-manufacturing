@echo off
REM Backend startup script untuk Portal Eksternal UHUY B2B

set "REPO_ROOT=%~dp0\..\..\.."

echo Starting Lukla AI backend on port 8000...
start "Lukla AI Backend" cmd /k "cd /d "%REPO_ROOT%" && set PYTHONPATH=. && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"
echo AI backend will be available at: http://localhost:8000/api/v1/copilot/chat
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting backend server on port 8010...
echo.
echo Backend will be available at: http://localhost:8010
echo API Docs at: http://localhost:8010/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn src.main:app --reload --port 8010

pause
