@echo off
REM Template para wrapper de conda multiplataforma
REM ESTE ES UN TEMPLATE - usar generate_scripts.php para crear la versión final
setlocal

:: Set conda environment paths from configuration
set CONDA_ROOT={{CONDA_ROOT}}
set CONDA_ENV={{CONDA_ENV}}
set CONDA_PREFIX=%CONDA_ROOT%\envs\%CONDA_ENV%

:: Set PATH to include all necessary directories
set PATH=%CONDA_PREFIX%;%CONDA_PREFIX%\Scripts;%CONDA_PREFIX%\Library\bin;%CONDA_PREFIX%\Library\usr\bin;%CONDA_PREFIX%\Library\mingw-w64\bin;%CONDA_ROOT%;%CONDA_ROOT%\Scripts;%PATH%

:: Set conda environment variables
set CONDA_DEFAULT_ENV=%CONDA_ENV%
set CONDA_PREFIX=%CONDA_PREFIX%
set PYTHONHASHSEED=0

:: Verify Python exists
if not exist "{{PYTHON_EXECUTABLE}}" (
    echo ERROR: Python not found at {{PYTHON_EXECUTABLE}}
    exit /b 1
)

:: Run the Python script directly
"{{PYTHON_EXECUTABLE}}" %*
