@echo off
setlocal

:: Set conda environment paths directly
set CONDA_ROOT=C:\Users\DANIELIVANVALDEZRODR\miniconda3
set CONDA_ENV=pollux-preview-env
set CONDA_PREFIX=%CONDA_ROOT%\envs\%CONDA_ENV%

:: Set PATH to include all necessary directories
set PATH=%CONDA_PREFIX%;%CONDA_PREFIX%\Scripts;%CONDA_PREFIX%\Library\bin;%CONDA_PREFIX%\Library\usr\bin;%CONDA_PREFIX%\Library\mingw-w64\bin;%CONDA_ROOT%;%CONDA_ROOT%\Scripts;%PATH%

:: Set conda environment variables
set CONDA_DEFAULT_ENV=%CONDA_ENV%
set CONDA_PREFIX=%CONDA_PREFIX%
set PYTHONHASHSEED=0

:: Verify Python exists
if not exist "%CONDA_PREFIX%\python.exe" (
    echo ERROR: Python not found at %CONDA_PREFIX%\python.exe
    exit /b 1
)

:: Run the Python script directly
"%CONDA_PREFIX%\python.exe" %*
