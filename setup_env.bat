@echo off
setlocal enabledelayedexpansion

REM Check if conda is available
where conda >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: conda command not found
    echo Please install Miniconda or Anaconda and ensure it's in your PATH
    exit /b 1
)

REM Remove existing pollux environment if it exists
conda env list | findstr /C:"pollux" >nul
if %ERRORLEVEL% equ 0 (
    echo Removing existing pollux environment...
    call conda env remove -n pollux -y
    if %ERRORLEVEL% neq 0 (
        echo Warning: Failed to remove existing environment
    )
)

echo Creating fresh pollux environment...
call conda create -n pollux python=3.10 -y
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to create pollux environment
    exit /b 1
)

REM Install required packages using conda-forge
echo Installing required packages...

REM First install numpy as it's a dependency
echo Installing numpy...
call conda install -n pollux -c conda-forge numpy=1.24 -y
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install numpy
    echo Please try running: conda install -n pollux -c conda-forge numpy=1.24 -y
    exit /b 1
)

REM Add conda-forge as a channel and install pythonocc-core
echo Adding conda-forge channel...
call conda config --add channels conda-forge
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to add conda-forge channel
    exit /b 1
)

echo Installing pythonocc-core...
call conda install -n pollux -c dlr-sc -c conda-forge pythonocc-core=7.7.0 smesh=8.3.0.1 -y
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install pythonocc-core
    echo Trying alternative installation method...

    REM Try alternative installation method
    call conda install -n pollux -c conda-forge -c dlr-sc pythonocc-core=7.7.0 -y
    if %ERRORLEVEL% neq 0 (
        echo Error: Both installation methods failed for pythonocc-core
        echo Please try manually:
        echo conda activate pollux
        echo conda install -c conda-forge -c dlr-sc pythonocc-core=7.7.0
        exit /b 1
    )
)

REM Install remaining packages with pip
echo Installing additional Python packages...
call conda run -n pollux pip install ezdxf numpy-stl
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install ezdxf and numpy-stl
    echo Please try running: pip install ezdxf numpy-stl
    exit /b 1
)

echo Environment setup complete!
echo You can now use the file analysis features.
