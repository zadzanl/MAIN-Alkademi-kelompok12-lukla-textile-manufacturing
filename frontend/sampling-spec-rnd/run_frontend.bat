@echo off
REM Frontend startup script untuk Sampling & Spec R&D

echo Installing dependencies...
call npm install

echo.
echo Starting frontend server on port 3007...
echo.
echo Frontend will be available at: http://localhost:3007
echo Backend should be running on: http://localhost:8007
echo.
echo Press Ctrl+C to stop the server
echo.

call npm run dev

pause
