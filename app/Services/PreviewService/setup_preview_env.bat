@echo off
echo Setting up Preview Environment...

REM Check if conda is available
where conda >nul 2>&1
if errorlevel 1 (
    echo Error: conda not found in PATH
    exit /b 1
)

REM Remove existing environment if it exists
echo Removing old environment if it exists...
call conda remove -n preview_env --all -y >nul 2>&1

REM Create new environment
echo Creating new Python environment...
call conda create -n preview_env python=3.10 -y
if errorlevel 1 goto error

REM Activate environment
echo Activating environment...
call conda activate preview_env
if errorlevel 1 goto error

REM Configure conda channels
echo Configuring conda channels...
call conda config --add channels conda-forge
call conda config --set channel_priority strict

REM Install PythonOCC and dependencies
echo Installing PythonOCC and dependencies...
call conda install -c conda-forge ^
    pythonocc-core=7.7.0 ^
    occt=7.7.0 ^
    python=3.10 ^
    numpy=1.24.3 ^
    -y
if errorlevel 1 goto error

REM Install visualization dependencies
echo Installing visualization dependencies...
call conda install -c conda-forge ^
    pythreejs ^
    ipywidgets ^
    -y
if errorlevel 1 goto error

REM Install additional packages
echo Installing additional packages...
call pip install "fastapi==0.104.1" "uvicorn==0.24.0" "pillow==10.1.0" "numpy==1.24.3"
if errorlevel 1 goto error

echo.
echo Environment setup complete!
echo To use the preview server:
echo 1. Activate the environment: conda activate preview_env
echo 2. Run the server: python step_preview_server.py
goto end

:error
echo.
echo Error occurred during setup!
pause
exit /b 1

:end
pause
