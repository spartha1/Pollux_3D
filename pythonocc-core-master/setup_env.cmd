@echo off
setlocal enabledelayedexpansion

:: Initialize conda for this shell session
echo Initializing conda...
call "%USERPROFILE%\miniconda3\Scripts\activate.bat" base
if errorlevel 1 (
    echo Failed to initialize conda
    exit /b 1
)

:: Remove existing environment if it exists
echo Removing existing environment...
call conda env remove -n pythonocc-env -y
if errorlevel 1 (
    echo Warning: Failed to remove environment, continuing...
)

:: Create fresh environment
echo Creating new conda environment...
call conda create -y -n pythonocc-env -c conda-forge python=3.10 numpy=1.24.3
if errorlevel 1 (
    echo Failed to create environment
    exit /b 1
)

:: Activate the new environment
echo.
echo Activating new environment...
call "%USERPROFILE%\miniconda3\Scripts\activate.bat" pythonocc-env
if errorlevel 1 (
    echo Failed to activate environment
    exit /b 1
)

:: Verify environment is active
call conda info --envs
echo Current Python:
python -c "import sys; print(sys.executable)"

echo Environment setup completed successfully!
exit /b 0
