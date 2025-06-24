@echo off
setlocal

:: Initialize Visual Studio environment
echo Initializing Visual Studio environment...
set "VS2022_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
call "%VS2022_PATH%\Common7\Tools\VsDevCmd.bat" -arch=x64
call "%VS2022_PATH%\VC\Auxiliary\Build\vcvars64.bat"

:: Activate conda environment
echo.
echo Activating conda environment...
call conda activate pythonocc-env

:: Set paths
set "BUILD_DIR=%~dp0build"
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

:: Run CMake
echo.
echo Running CMake...
cmake -G "Ninja" ^
      -DCMAKE_C_COMPILER=cl ^
      -DCMAKE_CXX_COMPILER=cl ^
      -DCMAKE_BUILD_TYPE=Release ^
      -B "%BUILD_DIR%" ^
      -S "%~dp0"

if errorlevel 1 (
    echo CMake configuration failed
    exit /b 1
)
