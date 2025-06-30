@echo off
setlocal

set CONDA_ROOT=C:\Users\Leinad\miniconda3
set CONDA_ENV=pollux-preview-env
set CONDA_PYTHON=%CONDA_ROOT%\envs\%CONDA_ENV%\python.exe
set SCRIPT_DIR=%~dp0

echo [Preview Service] Starting with conda Python...

if not exist "%CONDA_PYTHON%" (
    echo [Preview Service] ERROR: Python not found at %CONDA_PYTHON%
    exit /b 1
)

:: Verificar Python
echo [Preview Service] Using Python: %CONDA_PYTHON%
"%CONDA_PYTHON%" -c "import sys; print('Python version:', sys.version)"

:: Cambiar al directorio del script
cd /d "%SCRIPT_DIR%"

:: Matar cualquier instancia previa
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8050.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: Iniciar el servidor
echo [Preview Service] Starting server...
"%CONDA_PYTHON%" simple_preview_server.py
