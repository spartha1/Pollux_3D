@echo off
echo =====================================
echo Starting preview service...
echo =====================================
echo.

REM Activate conda environment
call conda activate preview_env
if errorlevel 1 (
    echo Error: Could not activate preview_env
    echo Please run setup_preview_env.bat first
    pause
    exit /b 1
)

REM Find available port
powershell -Command "$port = 8088; while ((Test-NetConnection localhost -Port $port -WarningAction SilentlyContinue).TcpTestSucceeded) { $port++ }; echo $port" > temp_port.txt
set /p PORT=<temp_port.txt
del temp_port.txt

echo Selected port: %PORT%
echo.

echo Checking Python in preview_env...
where python
if errorlevel 1 (
    echo Error: Python not found in PATH
    pause
    exit /b 1
)

echo.
echo Version de Python:
python --version
echo.

echo Instalando dependencias...
echo.
pip install fastapi "uvicorn[standard]" pillow
if errorlevel 1 (
    echo Error instalando dependencias
    pause
    exit /b 1
)

echo.
echo Iniciando servidor...
echo.
set PYTHONUNBUFFERED=1
python -u simple_preview_server.py %PORT%
if errorlevel 1 (
    echo Error iniciando el servidor
    pause
    exit /b 1
)

pause
