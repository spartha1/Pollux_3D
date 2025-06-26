@echo off
echo Initializing Conda environment...

:: Inicializar conda primero
call C:\Users\Leinad\miniconda3\Scripts\conda.exe init powershell
echo Conda initialized. Please close and reopen PowerShell, then run:
echo.
echo conda activate pollux-preview-env
echo python -c "import sys; print(sys.executable)"
echo python -c "import OCC; print(OCC.__version__)"
echo.
pause
