@echo off
setlocal enabledelayedexpansion

echo Setting up SWIG 4.2.1...

:: Set up paths
set "WORK_DIR=%~dp0"
set "DOWNLOADS_DIR=%WORK_DIR%\downloads"
set "INSTALL_PREFIX=%CONDA_PREFIX%\Library"

:: Create directories
if not exist "%DOWNLOADS_DIR%" mkdir "%DOWNLOADS_DIR%"

:: Clean up any existing files
if exist "%DOWNLOADS_DIR%\swigwin-4.2.1.zip" del /f /q "%DOWNLOADS_DIR%\swigwin-4.2.1.zip"
if exist "%DOWNLOADS_DIR%\swigwin-4.2.1" rd /s /q "%DOWNLOADS_DIR%\swigwin-4.2.1"

:: Download SWIG using curl with multiple attempts
echo Downloading SWIG 4.2.1...
set "URLS=https://swig.org/download/swigwin/swigwin-4.2.1.zip https://prdownloads.sourceforge.net/swig/swigwin-4.2.1.zip?download https://fossies.org/windows/misc/swigwin-4.2.1.zip"

set SUCCESS=0
for %%u in (%URLS%) do (
    if !SUCCESS!==0 (
        echo Trying %%u...
        curl --location --fail --progress-bar --output "%DOWNLOADS_DIR%\swigwin-4.2.1.zip" "%%u"
        if !errorlevel!==0 (
            :: Check file size (should be around 1.5MB)
            for %%F in ("%DOWNLOADS_DIR%\swigwin-4.2.1.zip") do (
                if %%~zF GTR 1000000 (
                    set SUCCESS=1
                )
            )
        )
    )
)

if !SUCCESS!==0 (
    echo Failed to download SWIG from any mirror
    goto error
)

:: Create bin directory if it doesn't exist
if not exist "%INSTALL_PREFIX%\bin" mkdir "%INSTALL_PREFIX%\bin"

:: Extract using tar (more reliable than PowerShell's Expand-Archive)
echo Extracting SWIG...
cd /d "%DOWNLOADS_DIR%"
tar -xf swigwin-4.2.1.zip
if errorlevel 1 goto error

:: Verify extraction
if not exist "%DOWNLOADS_DIR%\swigwin-4.2.1\swig.exe" (
    echo Failed to extract SWIG - swig.exe not found
    goto error
)

:: Copy files to conda environment
echo Installing SWIG...
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
