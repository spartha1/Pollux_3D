@echo off
setlocal enabledelayedexpansion

echo Setting up build environment...

:: Kill any processes that might be locking files
echo Cleaning up processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
taskkill /F /IM conda.exe 2>nul
timeout /t 2 /nobreak >nul

:: Clean up previous installation
echo Cleaning up previous installation...
call conda deactivate 2>nul
timeout /t 2 /nobreak >nul

if exist "%USERPROFILE%\miniconda3\envs\pythonocc-env" (
    rd /s /q "%USERPROFILE%\miniconda3\envs\pythonocc-env"
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

:: Create minimal environment first
echo.
echo Creating minimal environment...
call conda create -y -n pythonocc-env python=3.10
if errorlevel 1 (
    echo ERROR: Failed to create environment.
    goto error
)

:: Activate the new environment
echo.
echo Activating environment...
call conda activate pythonocc-env
if errorlevel 1 (
    echo ERROR: Failed to activate environment.
    goto error
)

:: Install packages one by one
echo.
echo Installing Visual C++ Runtime...
call conda install -y -c conda-forge vs2015_runtime
if errorlevel 1 goto error

timeout /t 2 /nobreak >nul

echo Installing NumPy...
call conda install -y -c conda-forge numpy=1.24.3
if errorlevel 1 goto error

echo Installing build tools...
call conda install -y -c conda-forge cmake=3.26.4 ninja=1.11.1
if errorlevel 1 goto error

echo Installing OpenCASCADE...
call conda install -y -c conda-forge occt=7.7.2
if errorlevel 1 goto error

echo Installing additional dependencies...
call conda install -y -c conda-forge pybind11=2.10.4 eigen=3.4.0 pcre2=10.42
if errorlevel 1 goto error

:: Verify installation
echo.
echo Verifying installation...
python -c "import numpy; print('NumPy version:', numpy.__version__)"
if errorlevel 1 goto error

:: Set up SWIG 4.2.1
echo.
echo Setting up SWIG 4.2.1...
call setup_swig5.cmd
if errorlevel 1 goto error

echo SWIG installation completed

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

:: Run CMake
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
    goto error
)

:: Build with Ninja
echo.
echo Building with Ninja...
ninja -C "%BUILD_DIR%"

if errorlevel 1 (
    echo Build failed
    goto error
)

echo.
echo Build completed successfully!
exit /b 0

:error
echo.
echo An error occurred during the installation.
echo Please check the output above for details.
exit /b 1
