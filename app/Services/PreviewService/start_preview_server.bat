@echo off
setlocal EnableDelayedExpansion

:: Definir rutas absolutas y variables
set CONDA_ROOT=C:\Users\Leinad\miniconda3
set CONDA_ENV=pollux-preview-env
set CONDA_PYTHON=%CONDA_ROOT%\envs\%CONDA_ENV%\python.exe
set CONDA_ACTIVATE=%CONDA_ROOT%\Scripts\activate.bat

echo Starting Preview Server with conda Python...

:: Desactivar cualquier entorno virtual activo
if defined VIRTUAL_ENV (
    echo Deactivating virtual environment...
    call !VIRTUAL_ENV!\Scripts\deactivate.bat
)

:: Activar el entorno conda
echo.
echo Activating conda environment %CONDA_ENV%...
call %CONDA_ACTIVATE% %CONDA_ENV%

:: Verificar la activación
echo.
echo Verifying environment:
"%CONDA_PYTHON%" -c "import os, sys; print(f'Python: {sys.executable}\nConda env: {os.environ.get(\"CONDA_DEFAULT_ENV\", \"None\")}\nConda prefix: {os.environ.get(\"CONDA_PREFIX\", \"None\")}')"

:: Verificar OCC
echo.
echo Checking OCC imports:
"%CONDA_PYTHON%" verify_occ_imports.py

:: Iniciar el servidor
echo.
echo Starting preview server...
"%CONDA_PYTHON%" simple_preview_server.py

pause
