@echo off
echo Starting Preview Server with conda Python...

:: Definir rutas absolutas
set CONDA_PYTHON=C:\Users\Leinad\miniconda3\envs\pollux-preview-env\python.exe
set CONDA_ACTIVATE=C:\Users\Leinad\miniconda3\Scripts\activate.bat

:: Desactivar cualquier entorno virtual activo
if defined VIRTUAL_ENV (
    echo Deactivating virtual environment...
    call %VIRTUAL_ENV%\Scripts\deactivate.bat
)

:: Activar el entorno conda
echo Activating conda environment...
call %CONDA_ACTIVATE% pollux-preview-env

:: Mostrar información del entorno
echo.
echo Using Python from:
"%CONDA_PYTHON%" -c "import sys; print(sys.executable)"

:: Verificar OCC
echo.
echo Checking OCC installation:
"%CONDA_PYTHON%" -c "import OCC; from OCC.Core.STEPControl import STEPControl_Reader; print('OCC imports OK')"

:: Iniciar el servidor
echo.
echo Starting preview server...
"%CONDA_PYTHON%" app/Services/PreviewService/preview_server.py
