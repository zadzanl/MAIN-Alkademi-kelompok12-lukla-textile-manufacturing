@echo off
REM QC Inspection Terminal backend launcher
echo Starting QC Inspection Terminal backend on port 8010...
cd /d "%~dp0"
uvicorn src.main:app --reload --port 8010
