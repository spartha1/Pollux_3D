@echo off
setlocal enabledelayedexpansion

set CONDA_ROOT=C:\Users\DANIELIVANVALDEZRODR\miniconda3
set CONDA_ENV=pollux-preview-env
set CONDA_PYTHON=%CONDA_ROOT%\envs\%CONDA_ENV%\python.exe
set SCRIPT_DIR=%~dp0

echo [Preview Service] Starting hybrid preview server...

if not exist "%CONDA_PYTHON%" (
    echo [Preview Service] ERROR: Python not found at %CONDA_PYTHON%
    echo [Preview Service] Trying system Python...
    set CONDA_PYTHON=python
)

:: Verificar Python
echo [Preview Service] Using Python: %CONDA_PYTHON%
"%CONDA_PYTHON%" -c "import sys; print('Python version:', sys.version)" 2>nul
if errorlevel 1 (
    echo [Preview Service] ERROR: Python not working
    exit /b 1
)

:: Cambiar al directorio del script
cd /d "%SCRIPT_DIR%"

:: Matar cualquier instancia previa del puerto 8052
echo [Preview Service] Checking for existing server on port 8052...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr /r /c:":8052.*LISTENING" 2^>nul') do (
    echo [Preview Service] Stopping existing process %%a
    taskkill /F /PID %%a >nul 2>&1
)

:: Iniciar el servidor híbrido
echo [Preview Service] Starting hybrid_preview_server.py...
echo [Preview Service] Directory: %SCRIPT_DIR%
echo [Preview Service] Python: %CONDA_PYTHON%

"%CONDA_PYTHON%" hybrid_preview_server.py
