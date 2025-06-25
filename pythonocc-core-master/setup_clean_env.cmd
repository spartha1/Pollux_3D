@echo off
setlocal enabledelayedexpansion

echo ======================================
echo Cleaning up and creating fresh environment
echo ======================================

:: First, deactivate any active environment
call conda deactivate
timeout /t 2 /nobreak >nul

:: Kill any Python processes
echo Killing any Python processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
taskkill /F /IM conda.exe 2>nul
timeout /t 2 /nobreak >nul

:: Remove existing environment if it exists
echo Removing existing environment...
call conda env remove -n pythonocc-env -y
timeout /t 2 /nobreak >nul

:: Clean conda completely
echo Cleaning conda cache and packages...
call conda clean --all --yes
timeout /t 2 /nobreak >nul

:: Create new environment with specific versions
echo Creating new environment with Python 3.10...
call conda create -y -n pythonocc-env -c conda-forge ^
    python=3.10 ^
    numpy=1.24.3 ^
    cmake=3.26.4 ^
    ninja=1.11.1 ^
    occt=7.7.2 ^
    pybind11=2.10.4 ^
    eigen=3.4.0 ^
    pcre2=10.42 ^
    vs2015_runtime ^
    compilers ^
    ninja ^
    make

if errorlevel 1 (
    echo Failed to create environment
    goto error
)

:: Activate environment
echo.
echo Activating new environment...
call conda activate pythonocc-env
if errorlevel 1 (
    echo Failed to activate environment
    goto error
)

:: Verify critical packages
echo.
echo Verifying installations...
python -c "import numpy; print('NumPy version:', numpy.__version__)"
if errorlevel 1 goto error

:: Set up SWIG 4.2.1
echo.
echo Setting up SWIG 4.2.1...

:: Create SWIG directory if it doesn't exist
if not exist "swig-4.2.1" (
    echo Downloading SWIG 4.2.1...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/swig/swig/archive/refs/tags/v4.2.1.zip' -OutFile 'swig-4.2.1.zip'}"
    echo Extracting SWIG...
    powershell -Command "& {Expand-Archive -Path 'swig-4.2.1.zip' -DestinationPath '.' -Force}"
    ren swig-4.2.1 swig-build
    move swig-build swig-4.2.1
)

:: Build SWIG if needed
if not exist "swig-4.2.1\swig.exe" (
    cd swig-4.2.1
    cmake -G "Ninja" ^
        -DCMAKE_BUILD_TYPE=Release ^
        -DCMAKE_INSTALL_PREFIX="%CONDA_PREFIX%" ^
        -B build -S .

    ninja -C build
    ninja -C build install
    cd ..
)

:: Add SWIG to PATH
set "PATH=%~dp0swig-4.2.1;%PATH%"
echo SWIG has been added to PATH
echo Current SWIG version:
swig -version

echo.
echo Environment setup completed!
echo.
echo Next steps:
echo 1. Verify SWIG installation: swig -version
echo 2. Run the build script: setup_and_build_new.cmd
echo.

exit /b 0

:error
echo.
echo An error occurred during setup.
echo Please check the output above for details.
exit /b 1
