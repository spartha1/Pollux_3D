@echo off
echo Starting Preview Service...
cd /d %~dp0

REM Check if preview_env exists
conda env list | find "preview_env" > nul
if errorlevel 1 (
    echo Preview environment not found. Setting up...
    call setup_preview_env.bat
    if errorlevel 1 (
        echo Failed to set up preview environment
        exit /b 1
    )
)

REM Activate preview environment
call conda activate preview_env
if errorlevel 1 (
    echo Failed to activate preview environment
    exit /b 1
)

echo Starting preview server...
python step_preview_server.py

if errorlevel 1 (
    echo Failed to start preview server
    exit /b 1
)
