@echo off
echo =====================================
echo Iniciando servicio de vista previa...
echo =====================================
echo.

echo Verificando Python...
where python
if errorlevel 1 (
    echo Error: Python no encontrado en el PATH
    pause
    exit /b 1
)

echo.
echo Version de Python:
python --version
echo.

echo Instalando dependencias...
echo.
pip install fastapi uvicorn pillow
if errorlevel 1 (
    echo Error instalando dependencias
    pause
    exit /b 1
)

echo.
echo Iniciando servidor...
echo.
python -u simple_preview_server.py
if errorlevel 1 (
    echo Error iniciando el servidor
    pause
    exit /b 1
)

pause
