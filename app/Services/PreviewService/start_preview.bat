@echo off
REM Ensure we use the correct Python from conda
set PYTHONPATH=
set PYTHONHOME=
set CONDA_PYTHON=C:\Users\Leinad\miniconda3\envs\pollux-preview-env\python.exe

REM Start the preview server
"%CONDA_PYTHON%" "%~dp0simple_preview_server.py"
