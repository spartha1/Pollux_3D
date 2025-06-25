@echo off
setlocal enabledelayedexpansion

echo Setting up SWIG 4.2.1...

:: Set up paths
set "WORK_DIR=%~dp0"
set "DOWNLOADS_DIR=%WORK_DIR%\downloads"
set "INSTALL_PREFIX=%CONDA_PREFIX%\Library"
set "SWIG_URL=https://versaweb.dl.sourceforge.net/project/swig/swigwin/swigwin-4.2.1/swigwin-4.2.1.zip"

:: Clean up any existing files
if exist "%DOWNLOADS_DIR%\swigwin-4.2.1.zip" del /f /q "%DOWNLOADS_DIR%\swigwin-4.2.1.zip"
if exist "%DOWNLOADS_DIR%\swigwin-4.2.1" rd /s /q "%DOWNLOADS_DIR%\swigwin-4.2.1"

:: Create directories
if not exist "%DOWNLOADS_DIR%" mkdir "%DOWNLOADS_DIR%"

:: Try different mirrors for downloading SWIG
echo Downloading pre-built SWIG 4.2.1...

:: First try SourceForge mirror
powershell -Command "& {
    $ErrorActionPreference = 'Stop'
    $urls = @(
        'https://sourceforge.net/projects/swig/files/swigwin/swigwin-4.2.1/swigwin-4.2.1.zip/download',
        'https://master.dl.sourceforge.net/project/swig/swigwin/swigwin-4.2.1/swigwin-4.2.1.zip',
        'https://deac-fra.dl.sourceforge.net/project/swig/swigwin/swigwin-4.2.1/swigwin-4.2.1.zip',
        'https://deac-ams.dl.sourceforge.net/project/swig/swigwin/swigwin-4.2.1/swigwin-4.2.1.zip'
    )

    $success = $false
    foreach ($url in $urls) {
        try {
            Write-Host "Trying $url..."
            $ProgressPreference = 'SilentlyContinue'
            Start-BitsTransfer -Source $url -Destination '%DOWNLOADS_DIR%\swigwin-4.2.1.zip'

            # Check file size (should be around 1.5MB)
            $size = (Get-Item '%DOWNLOADS_DIR%\swigwin-4.2.1.zip').Length
            if ($size -gt 1000000) {
                $success = $true
                break
            } else {
                Write-Host "Downloaded file too small: $size bytes"
                Remove-Item '%DOWNLOADS_DIR%\swigwin-4.2.1.zip' -Force
            }
        } catch {
            Write-Host "Failed to download from $url"
            continue
        }
    }

    if (-not $success) { exit 1 }
}"
if errorlevel 1 goto error

:: Verify download
if not exist "%DOWNLOADS_DIR%\swigwin-4.2.1.zip" (
    echo Failed to download SWIG from any mirror
    goto error
)

:: Extract SWIG to downloads directory
echo Installing SWIG...

:: Try to use 7-Zip if available
where 7z >nul 2>&1
if not errorlevel 1 (
    echo Using 7-Zip to extract...
    7z x -y -o"%DOWNLOADS_DIR%" "%DOWNLOADS_DIR%\swigwin-4.2.1.zip"
) else (
    echo Using PowerShell to extract...
    powershell -Command "& {
        $ErrorActionPreference = 'Stop'
        try {
            $ProgressPreference='SilentlyContinue'
            Expand-Archive -Path '%DOWNLOADS_DIR%\swigwin-4.2.1.zip' -DestinationPath '%DOWNLOADS_DIR%' -Force
        } catch {
            Write-Host 'Extraction failed:'
            Write-Host $_
            exit 1
        }
    }"
)
if errorlevel 1 goto error

:: Check if extraction was successful
if not exist "%DOWNLOADS_DIR%\swigwin-4.2.1\swig.exe" (
    echo Failed to extract SWIG
    goto error
)

:: Copy SWIG executable and DLLs
echo Copying SWIG files...
if not exist "%INSTALL_PREFIX%\bin" mkdir "%INSTALL_PREFIX%\bin"
copy /Y "%DOWNLOADS_DIR%\swigwin-4.2.1\*.*" "%INSTALL_PREFIX%\bin\" >nul
if errorlevel 1 goto error

:: Verify installation
echo Verifying SWIG installation...
"%INSTALL_PREFIX%\bin\swig.exe" -version
if errorlevel 1 goto error

:: Clean up downloads
echo Cleaning up...
del /f /q "%DOWNLOADS_DIR%\swigwin-4.2.1.zip"
rd /s /q "%DOWNLOADS_DIR%\swigwin-4.2.1"

echo SWIG 4.2.1 installation completed successfully!
exit /b 0

:error
echo Failed to install SWIG
exit /b 1
