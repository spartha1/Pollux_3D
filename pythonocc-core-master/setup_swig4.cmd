@echo off
setlocal enabledelayedexpansion

echo Setting up SWIG 4.2.1...

:: Set up paths
set "WORK_DIR=%~dp0"
set "DOWNLOADS_DIR=%WORK_DIR%\downloads"
set "INSTALL_PREFIX=%CONDA_PREFIX%\Library"
set "SWIG_URL=https://github.com/swig/swigwin/releases/download/v4.2.1/swigwin-4.2.1.zip"

:: Clean up any existing files
if exist "%DOWNLOADS_DIR%\swigwin-4.2.1.zip" del /f /q "%DOWNLOADS_DIR%\swigwin-4.2.1.zip"
if exist "%DOWNLOADS_DIR%\swigwin-4.2.1" rd /s /q "%DOWNLOADS_DIR%\swigwin-4.2.1"

:: Create directories
if not exist "%DOWNLOADS_DIR%" mkdir "%DOWNLOADS_DIR%"

:: Download pre-built SWIG
echo Downloading pre-built SWIG 4.2.1...
echo URL: %SWIG_URL%
echo Download path: %DOWNLOADS_DIR%\swigwin-4.2.1.zip
curl -L -v -o "%DOWNLOADS_DIR%\swigwin-4.2.1.zip" "%SWIG_URL%"
if errorlevel 1 goto error

:: Check if download was successful
if not exist "%DOWNLOADS_DIR%\swigwin-4.2.1.zip" (
    echo Failed to download SWIG
    goto error
)

echo Download completed. File size:
dir "%DOWNLOADS_DIR%\swigwin-4.2.1.zip"

:: Extract SWIG to downloads directory
echo.
echo Extracting SWIG...
echo Source: %DOWNLOADS_DIR%\swigwin-4.2.1.zip
echo Destination: %DOWNLOADS_DIR%
powershell -Command "& {$ProgressPreference='SilentlyContinue'; Expand-Archive -Path '%DOWNLOADS_DIR%\swigwin-4.2.1.zip' -DestinationPath '%DOWNLOADS_DIR%' -Force -Verbose}"
if errorlevel 1 goto error

:: Check if extraction was successful
echo.
echo Checking extracted files...
dir "%DOWNLOADS_DIR%\swigwin-4.2.1"
if not exist "%DOWNLOADS_DIR%\swigwin-4.2.1\swig.exe" (
    echo Failed to extract SWIG - swig.exe not found
    goto error
)

:: Create bin directory if needed
if not exist "%INSTALL_PREFIX%\bin" (
    echo Creating bin directory: %INSTALL_PREFIX%\bin
    mkdir "%INSTALL_PREFIX%\bin"
)

:: Copy SWIG files
echo.
echo Copying SWIG files to %INSTALL_PREFIX%\bin...
copy /Y "%DOWNLOADS_DIR%\swigwin-4.2.1\*.*" "%INSTALL_PREFIX%\bin\" >nul
if errorlevel 1 goto error

:: Verify installation
echo.
echo Verifying SWIG installation...
echo SWIG path: %INSTALL_PREFIX%\bin\swig.exe
"%INSTALL_PREFIX%\bin\swig.exe" -version
if errorlevel 1 goto error

:: Clean up downloads
echo.
echo Cleaning up...
del /f /q "%DOWNLOADS_DIR%\swigwin-4.2.1.zip"
rd /s /q "%DOWNLOADS_DIR%\swigwin-4.2.1"

echo.
echo SWIG 4.2.1 installation completed successfully!
exit /b 0

:error
echo.
echo Failed to install SWIG
if exist "%DOWNLOADS_DIR%\swigwin-4.2.1.zip" (
    echo Download exists but may be corrupt
    dir "%DOWNLOADS_DIR%\swigwin-4.2.1.zip"
)
exit /b 1
