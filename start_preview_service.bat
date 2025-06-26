@echo off
setlocal enabledelayedexpansion

REM Detectar el entorno
if "%APP_ENV%"=="production" (
    set PYTHON_PATH=/usr/bin/python3
) else (
    set PYTHON_PATH=C:\Users\Leinad\miniconda3\envs\pollux-preview-env\python.exe
)

REM Iniciar el servidor
echo Starting Preview Service...
"%PYTHON_PATH%" app/Services/PreviewService/preview_server.py

if errorlevel 1 (
    echo Error starting server
    pause
    exit /b 1
)

endlocal
