@echo off
echo Cleaning up Python environments...

:: Desactivar entorno virtual si está activo
if defined VIRTUAL_ENV (
    echo Deactivating virtual environment...
    call %VIRTUAL_ENV%\Scripts\deactivate.bat
)

:: Desactivar conda si está activo
echo Deactivating conda environment...
call C:\Users\Leinad\miniconda3\Scripts\deactivate.bat

:: Activar el entorno conda limpio
echo Activating clean conda environment...
call C:\Users\Leinad\miniconda3\Scripts\activate.bat pollux-preview-env

:: Verificar que estamos usando el Python correcto
echo.
echo Verifying Python executable...
python -c "import sys; print('Using Python from:', sys.executable)"

:: Intentar importar OCC
echo.
echo Testing OCC import...
python -c "import OCC; print('OCC version:', OCC.__version__)"

echo.
echo Environment setup complete.
echo Please check above for any errors.
pause
