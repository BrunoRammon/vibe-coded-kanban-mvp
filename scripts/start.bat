@echo off
REM start.bat
echo Starting Docker containers...
docker compose up --build -d
echo Server is running at http://localhost:8000
