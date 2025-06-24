@echo off
setlocal enabledelayedexpansion

echo Setting up SWIG 4.2.1...

:: Set up paths
set "WORK_DIR=%~dp0"
set "DOWNLOADS_DIR=%WORK_DIR%\downloads"
set "INSTALL_PREFIX=%CONDA_PREFIX%\Library"
set "SWIG_URL=https://github.com/tttapa/swigwin-4.2.1-bin/releases/download/v4.2.1/swigwin-4.2.1.zip"

:: Create directories
if not exist "%DOWNLOADS_DIR%" mkdir "%DOWNLOADS_DIR%"

:: Download pre-built SWIG
echo Downloading pre-built SWIG 4.2.1...
powershell -Command "& {$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri '%SWIG_URL%' -OutFile '%DOWNLOADS_DIR%\swigwin-4.2.1.zip'}"
if errorlevel 1 goto error

:: Extract SWIG to conda environment
echo Installing SWIG...
powershell -Command "& {$ProgressPreference='SilentlyContinue'; Expand-Archive -Path '%DOWNLOADS_DIR%\swigwin-4.2.1.zip' -DestinationPath '%DOWNLOADS_DIR%' -Force}"
if errorlevel 1 goto error

:: Copy SWIG executable and DLLs
echo Copying SWIG files...
if not exist "%INSTALL_PREFIX%\bin" mkdir "%INSTALL_PREFIX%\bin"
copy /Y "%DOWNLOADS_DIR%\swigwin-4.2.1\*.*" "%INSTALL_PREFIX%\bin\" >nul
if errorlevel 1 goto error

:: Verify installation
echo Verifying SWIG installation...
"%INSTALL_PREFIX%\bin\swig.exe" -version
if errorlevel 1 goto error

echo SWIG 4.2.1 installation completed successfully!
exit /b 0

:error
echo Failed to install SWIG
exit /b 1
