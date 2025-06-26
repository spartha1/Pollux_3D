@echo off
setlocal EnableDelayedExpansion

:: Definir rutas absolutas y variables
set CONDA_ROOT=C:\Users\Leinad\miniconda3
set CONDA_ENV=pollux-preview-env
set CONDA_PYTHON=%CONDA_ROOT%\envs\%CONDA_ENV%\python.exe
set CONDA_ACTIVATE=%CONDA_ROOT%\Scripts\activate.bat
set CONDA_DEACTIVATE=%CONDA_ROOT%\Scripts\deactivate.bat

:: Obtener el script a ejecutar
set SCRIPT_PATH=%1
if "%SCRIPT_PATH%"=="" (
    echo Error: Please provide a Python script path
    echo Usage: %0 path/to/script.py
    exit /b 1
)

:: Desactivar cualquier entorno activo (conda o venv)
echo Deactivating any active environment...
if defined VIRTUAL_ENV (
    call !VIRTUAL_ENV!\Scripts\deactivate.bat
)
if defined CONDA_DEFAULT_ENV (
    call %CONDA_DEACTIVATE%
)

:: Activar el entorno conda limpio
echo.
echo Activating conda environment %CONDA_ENV%...
call %CONDA_ACTIVATE% %CONDA_ENV%

:: Verificar la activación
echo.
echo Verifying environment:
"%CONDA_PYTHON%" -c "import os, sys; print(f'Python: {sys.executable}\nConda env: {os.environ.get(\"CONDA_DEFAULT_ENV\", \"None\")}\nConda prefix: {os.environ.get(\"CONDA_PREFIX\", \"None\")}')"

:: Ejecutar el script
echo.
echo Running script: %SCRIPT_PATH%
"%CONDA_PYTHON%" "%SCRIPT_PATH%"
