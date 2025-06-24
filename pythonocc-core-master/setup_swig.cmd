@echo off
setlocal enabledelayedexpansion

echo Setting up SWIG 4.2.1...

:: Set up paths
set "WORK_DIR=%~dp0"
set "DOWNLOADS_DIR=%WORK_DIR%\downloads"
set "BUILD_DIR=%WORK_DIR%\build-swig"
set "INSTALL_PREFIX=%CONDA_PREFIX%\Library"
set "SWIG_URL=https://github.com/swig/swig/archive/refs/tags/v4.2.1.zip"

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

echo CONDA_PREFIX: %CONDA_PREFIX%
echo INSTALL_PREFIX: %INSTALL_PREFIX%
dir "%CONDA_PREFIX%\Library\include"
dir "%CONDA_PREFIX%\Library\lib"

:: Run CMake with verbose output
cmake -G "Ninja" ^
    -DCMAKE_INSTALL_PREFIX="%INSTALL_PREFIX%" ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DPCRE2_INCLUDE_DIR="%CONDA_PREFIX%\Library\include" ^
    -DPCRE2_LIBRARY="%CONDA_PREFIX%\Library\lib\pcre2-8.lib" ^
    -DBISON_EXECUTABLE="%CONDA_PREFIX%\Library\bin\bison.exe" ^
    -DCMAKE_VERBOSE_MAKEFILE=ON ^
    -B build -S .
if errorlevel 1 goto error

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
