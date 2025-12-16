@echo off
title Pharma Agentic AI
echo.
echo ============================================================
echo   PHARMA AGENTIC AI - Multi-Agent Pharmaceutical Intelligence
echo ============================================================
echo.
echo Starting application...
echo.

REM Try Python from PATH first, then common locations
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python run.py %*
) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" run.py %*
) else if exist "C:\Python311\python.exe" (
    "C:\Python311\python.exe" run.py %*
) else if exist "C:\Python310\python.exe" (
    "C:\Python310\python.exe" run.py %*
) else (
    echo ERROR: Python not found. Please install Python 3.10+ or add it to PATH.
    pause
    exit /b 1
)

pause
