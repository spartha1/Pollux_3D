@echo off
setlocal enabledelayedexpansion

echo Setting up build environment...

:: Remove existing environment if it exists
call conda env remove -n pythonocc-env -y

:: Create new environment with all required packages
echo Creating conda environment with required packages...
call conda create -y -n pythonocc-env -c conda-forge python=3.10 numpy=1.24.3 cmake=3.26.4 ninja=1.11.1 occt=7.7.2 pybind11=2.10.4 eigen=3.4.0 pcre2=10.42

if errorlevel 1 (
    echo Failed to create conda environment
    exit /b 1
)

:: Activate the environment
call conda activate pythonocc-env

:: Set up SWIG 4.2.1
echo.
echo Setting up SWIG 4.2.1...
call setup_swig3.cmd
if errorlevel 1 (
    echo SWIG setup failed
    goto error
)

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
