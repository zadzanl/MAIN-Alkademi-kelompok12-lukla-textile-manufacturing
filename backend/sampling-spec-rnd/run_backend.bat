@echo off
REM Backend startup script untuk Sampling & Spec R&D

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting backend server on port 8007...
echo.
echo Backend will be available at: http://localhost:8007
echo API Docs at: http://localhost:8007/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn src.main:app --reload --port 8007

pause
