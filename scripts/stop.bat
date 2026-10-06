@echo off
REM stop.bat
echo Stopping Docker containers...
docker compose down
echo Containers stopped.
