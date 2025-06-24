@echo off
setlocal enabledelayedexpansion

echo Setting up SWIG 4.2.1...

:: Set up environment
set "WORK_DIR=%~dp0"
set "DOWNLOADS_DIR=%WORK_DIR%\downloads"
set "INSTALL_PREFIX=%CONDA_PREFIX%\Library"
set "SWIG_URL=https://github.com/tttapa/swigwin-4.2.1-bin/releases/download/v4.2.1/swigwin-4.2.1.zip"

:: Create directories
if not exist "%DOWNLOADS_DIR%" mkdir "%DOWNLOADS_DIR%"
if exist "%BUILD_DIR%" rd /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"

:: Download SWIG
echo Downloading SWIG 4.2.1...
powershell -Command "& {$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri '%SWIG_URL%' -OutFile '%DOWNLOADS_DIR%\swig-4.2.1.zip'}"
if errorlevel 1 goto error

:: Extract SWIG
echo Extracting SWIG...
powershell -Command "& {$ProgressPreference='SilentlyContinue'; Expand-Archive -Path '%DOWNLOADS_DIR%\swig-4.2.1.zip' -DestinationPath '%BUILD_DIR%' -Force}"
if errorlevel 1 goto error

:: Configure SWIG
echo Configuring SWIG...
cd /d "%BUILD_DIR%\swig-4.2.1"

echo Environment:
echo CONDA_PREFIX: %CONDA_PREFIX%
echo INSTALL_PREFIX: %INSTALL_PREFIX%
echo PCRE2_PREFIX: %PCRE2_PREFIX%

echo.
echo Checking PCRE2 files:
if exist "%PCRE2_PREFIX%\include\pcre2.h" (
    echo Found pcre2.h
) else (
    echo ERROR: pcre2.h not found
    goto error
)
if exist "%PCRE2_PREFIX%\lib\pcre2-8.lib" (
    echo Found pcre2-8.lib
) else (
    echo ERROR: pcre2-8.lib not found
    goto error
)

:: Run CMake with all necessary options
cmake -G "Ninja" ^
    -DCMAKE_INSTALL_PREFIX="%INSTALL_PREFIX%" ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DPCRE2_INCLUDE_DIR="%PCRE2_PREFIX%\include" ^
    -DPCRE2_LIBRARY="%PCRE2_PREFIX%\lib\pcre2-8.lib" ^
    -DBISON_EXECUTABLE="%CONDA_PREFIX%\Library\bin\bison.exe" ^
    -DCMAKE_VERBOSE_MAKEFILE=ON ^
    -DBUILD_SHARED_LIBS=ON ^
    -DSWIG_USE_PCRE2=ON ^
    -B build -S .

if errorlevel 1 (
    echo CMake configuration failed
    goto error
)

:: Build SWIG
echo Building SWIG...
ninja -C build
if errorlevel 1 goto error

:: Install SWIG
echo Installing SWIG...
ninja -C build install
if errorlevel 1 goto error

:: Verify installation
echo Verifying SWIG installation...
"%INSTALL_PREFIX%\bin\swig.exe" -version
if errorlevel 1 goto error

:: Clean up
cd /d "%WORK_DIR%"
rd /s /q "%BUILD_DIR%"

echo SWIG 4.2.1 installation completed successfully!
exit /b 0

:error
echo Failed to install SWIG
cd /d "%WORK_DIR%"
exit /b 1
