@echo off
setlocal enabledelayedexpansion

echo Setting up build environment...

:: Clean up any locked files and remove existing environment
echo Cleaning up existing environment...
call conda deactivate
timeout /t 2 /nobreak >nul

:: Kill any processes that might be locking files
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
taskkill /F /IM conda.exe 2>nul
timeout /t 2 /nobreak >nul

:: Force remove the environment directory
if exist "%USERPROFILE%\miniconda3\envs\pythonocc-env" (
    rd /s /q "%USERPROFILE%\miniconda3\envs\pythonocc-env" 2>nul
    timeout /t 2 /nobreak >nul
)

:: Clean conda cache
echo Cleaning conda cache...
conda clean -a -y
timeout /t 2 /nobreak >nul

:: Verify conda is working
echo Verifying conda installation...
conda --version
if errorlevel 1 (
    echo ERROR: Conda is not working properly.
    echo Please try reinstalling Miniconda3.
    goto error
)

:: Initialize conda for this shell session
echo Initializing conda...
call "%USERPROFILE%\miniconda3\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Failed to initialize conda.
    echo Please check if Miniconda3 is installed correctly.
    goto error
)

:: Verify conda environment
echo Listing available conda environments...
conda env list
if errorlevel 1 (
    echo ERROR: Could not list conda environments.
    goto error
)

:: Create base environment with VC runtime first
echo.
echo Creating base conda environment...
call conda create -y -n pythonocc-env ^
    -c conda-forge ^
    python=3.10 ^
    vs2015_runtime ^
    vc=14 ^
    --no-deps

:: Activate the environment
call conda activate pythonocc-env

:: Test environment activation and write permissions
echo Testing environment access...
python -c "import sys; print('Python location:', sys.executable)"
if errorlevel 1 (
    echo Failed to access Python in new environment
    goto error
)

:: Install VC runtime packages first
echo Installing Visual C++ Runtime...
call conda install -y -c conda-forge vs2015_runtime vc=14
if errorlevel 1 goto error

:: Wait a moment for any file operations to complete
timeout /t 5 /nobreak >nul

:: Install packages one by one to ensure proper installation
echo Installing required packages...
call conda install -y -c conda-forge numpy=1.24.3
if errorlevel 1 goto error

call conda install -y -c conda-forge cmake=3.26.4 ninja=1.11.1
if errorlevel 1 goto error

call conda install -y -c conda-forge occt=7.7.2
if errorlevel 1 goto error

call conda install -y -c conda-forge pybind11=2.10.4 eigen=3.4.0 pcre2=10.42
if errorlevel 1 goto error

:: Verify critical packages
echo Verifying installations...
python -c "import numpy; print('NumPy version:', numpy.__version__)"
if errorlevel 1 goto error

:: Set up SWIG 4.2.1
echo.
echo Setting up SWIG 4.2.1...
call setup_swig5.cmd
if errorlevel 1 goto error

echo SWIG installation completed

:: Verify SWIG version
"%CONDA_PREFIX%\Library\bin\swig.exe" -version

:: Initialize Visual Studio environment
echo.
echo Initializing Visual Studio environment...
set "VS2022_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
call "%VS2022_PATH%\Common7\Tools\VsDevCmd.bat" -arch=x64
call "%VS2022_PATH%\VC\Auxiliary\Build\vcvars64.bat"

:: Set up build directory
set "BUILD_DIR=%~dp0build"
if exist "%BUILD_DIR%" rd /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"

:: Run CMake with all necessary options
echo.
echo Running CMake...
cmake -G "Ninja" ^
    -DCMAKE_C_COMPILER=cl ^
    -DCMAKE_CXX_COMPILER=cl ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DPYTHON_EXECUTABLE="%CONDA_PREFIX%\python.exe" ^
    -DPython3_ROOT_DIR="%CONDA_PREFIX%" ^
    -DPYTHON_INCLUDE_DIR="%CONDA_PREFIX%\include" ^
    -DNUMPY_INCLUDE_DIR="%CONDA_PREFIX%\Lib\site-packages\numpy\core\include" ^
    -DOCCT_INCLUDE_DIR="%CONDA_PREFIX%\Library\include\opencascade" ^
    -DOCCT_LIBRARY_DIR="%CONDA_PREFIX%\Library\lib" ^
    -DSWIG_EXECUTABLE="%CONDA_PREFIX%\Library\bin\swig.exe" ^
    -B "%BUILD_DIR%" ^
    -S "%~dp0"

if errorlevel 1 (
    echo CMake configuration failed
    exit /b 1
)

:: Build with Ninja
echo.
echo Building with Ninja...
ninja -C "%BUILD_DIR%"

if errorlevel 1 (
    echo Build failed
    exit /b 1
)

echo.
echo Build completed successfully!

:error
echo An error occurred during the installation. Please check the logs for more details.
exit /b 1
