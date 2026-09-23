@echo off
title Space Debris Monitoring System - Prototype Launcher
color 0A
echo =========================================================================
echo               SPACE DEBRIS ORBITAL MONITORING SYSTEM
echo                    [ Operational Monitoring Environment ]
echo =========================================================================
echo.
echo Starting Python HTTP Backend Server on port 8000...
echo.

start "" /B python app.py

echo Waiting for server initialization...
timeout /t 2 /nobreak >nul

echo Launching browser interface at http://127.0.0.1:8000 ...
start http://127.0.0.1:8000

echo.
echo =========================================================================
echo Server is running live at: http://127.0.0.1:8000
echo Press Ctrl+C in this window or close it to stop the server.
echo =========================================================================
echo.
pause
