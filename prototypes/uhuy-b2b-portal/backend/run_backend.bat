@echo off
REM Backend startup script untuk Portal Eksternal UHUY B2B

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
