@echo off
setlocal enabledelayedexpansion

echo ======================================
echo Building pythonocc-core
echo ======================================

:: Activate environment
call conda activate pythonocc-env
if errorlevel 1 (
    echo Failed to activate environment
    goto error
)

:: Find and initialize Visual Studio environment
echo Initializing Visual Studio environment...
for /f "usebackq tokens=1* delims=: " %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64`) do (
    if /i "%%i"=="installationPath" set VS_PATH=%%j
)

if not defined VS_PATH (
    echo Error: Visual Studio installation not found.
    goto error
)

call "!VS_PATH!\Common7\Tools\VsDevCmd.bat" -arch=x64
call "!VS_PATH!\VC\Auxiliary\Build\vcvars64.bat"

:: Set up build directory
set "BUILD_DIR=%~dp0build"
if exist "%BUILD_DIR%" rd /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"

:: Copy OpenCASCADE headers for SWIG
echo Copying OpenCASCADE headers...
if not exist "%~dp0swigwin-4.2.1\include" mkdir "%~dp0swigwin-4.2.1\include"
xcopy /E /I /Y "%CONDA_PREFIX%\Library\include\opencascade\*.*" "%~dp0swigwin-4.2.1\include\"

:: Configure CMake
echo.
echo Running CMake configuration...
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
    -DSWIG_EXECUTABLE="%~dp0swigwin-4.2.1\swig.exe" ^
    -DSWIG_DIR="%~dp0swigwin-4.2.1" ^
    -DSWIG_VERSION="4.2.1" ^
    -DSWIG_INCLUDE="%~dp0swigwin-4.2.1\include" ^
    -B "%BUILD_DIR%" ^
    -S "%~dp0"

if errorlevel 1 (
    echo CMake configuration failed
    goto error
)

:: Build
echo.
echo Building with Ninja...
ninja -C "%BUILD_DIR%"

if errorlevel 1 (
    echo Build failed
    goto error
)

echo.
echo Build completed successfully!

:: Test import
echo.
echo Testing Python module...
python -c "import OCC.Core.BRepPrimAPI; print('Successfully imported OCC.Core!')"

exit /b 0

:error
echo.
echo An error occurred during the build process.
echo Please check the output above for details.
exit /b 1
