@echo off
setlocal enabledelayedexpansion

echo Initializing build environment...

:: Initialize Visual Studio environment
set "VS2022_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
set "VS2019_PATH=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community"

if exist "%VS2022_PATH%\Common7\Tools\VsDevCmd.bat" (
    echo Found Visual Studio 2022
    call "%VS2022_PATH%\Common7\Tools\VsDevCmd.bat" -arch=x64
    call "%VS2022_PATH%\VC\Auxiliary\Build\vcvars64.bat"
) else if exist "%VS2019_PATH%\Common7\Tools\VsDevCmd.bat" (
    echo Found Visual Studio 2019
    call "%VS2019_PATH%\Common7\Tools\VsDevCmd.bat" -arch=x64
    call "%VS2019_PATH%\VC\Auxiliary\Build\vcvars64.bat"
) else (
    echo Error: Visual Studio 2019 or 2022 not found
    exit /b 1
)

:: Activate conda environment
echo.
echo Activating conda environment...
call conda activate pythonocc-env
if errorlevel 1 (
    echo Error: Failed to activate conda environment
    exit /b 1
)

:: Set additional environment variables
set "PYTHONPATH=%CONDA_PREFIX%\Lib\site-packages"
set "PATH=%CONDA_PREFIX%\Library\bin;%PATH%"

:: Verify cl.exe is available
where cl.exe >nul 2>nul
if errorlevel 1 (
    echo Error: cl.exe not found in PATH
    exit /b 1
)

:: Run the PowerShell script
echo.
echo Running build script...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0rebuild_final_conda_new2.ps1"
if errorlevel 1 (
    echo Error: Build failed
    exit /b 1
)

echo.
echo Build process completed
