# Stop on first error
$ErrorActionPreference = "Stop"

Write-Host "Starting build process..."

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $scriptDir "build"
$sourceDir = $scriptDir

Write-Host "Directories:"
Write-Host "Script dir: $scriptDir"
Write-Host "Build dir: $buildDir"

# Create build directory
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir | Out-Null
    Write-Host "Created build directory"
}

# Clean any existing CMake cache
if (Test-Path "$buildDir\CMakeCache.txt") {
    Remove-Item -Force "$buildDir\CMakeCache.txt"
    Write-Host "Cleaned CMake cache"
}

# Install required packages
Write-Host "`nInstalling required packages..."
& conda install -y -c conda-forge cmake ninja "swig=4.2.1"
if ($LASTEXITCODE -ne 0) { throw "Failed to install packages" }

# Verify tool versions
Write-Host "`nVerifying tool versions:"
& cmake --version
& ninja --version
& swig -version

# Get SWIG paths
$swigPath = (Get-Command swig.exe).Source
$swigRoot = Split-Path $swigPath -Parent
$swigShare = Join-Path (Split-Path $swigRoot -Parent) "share" "swig" "4.2.1"

Write-Host "`nSWIG information:"
Write-Host "SWIG Path: $swigPath"
Write-Host "SWIG Root: $swigRoot"
Write-Host "SWIG Share: $swigShare"

# Set environment variables
$env:SWIG_LIB = $swigShare
$env:PATH = "$swigRoot;$env:PATH"

# Get Python executable path
$pythonPath = (Get-Command python.exe).Source
Write-Host "Python executable: $pythonPath"

# Run CMake with detailed error checking
Write-Host "`nRunning CMake..."
$cmakeOutput = & cmake `
    -G "Ninja" `
    -DSWIG_EXECUTABLE="$swigPath" `
    -DSWIG_DIR="$swigShare" `
    -DSWIG_USE_FILE="$swigShare/UseFile.cmake" `
    -DSWIG_VERSION="4.2.1" `
    -DPYTHON_EXECUTABLE="$pythonPath" `
    -DCMAKE_BUILD_TYPE=Release `
    -B "$buildDir" `
    -S "$sourceDir" 2>&1

# Output CMake results
$cmakeOutput | ForEach-Object { Write-Host $_ }

# Check for specific SWIG version issues in CMake output
if ($cmakeOutput -match "Found unsuitable version") {
    Write-Host "`nDetected SWIG version mismatch. Checking system SWIG installations..."
    Get-ChildItem -Path "C:\Program Files*\swig" -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq "swig.exe" } |
        ForEach-Object {
            Write-Host "Found system SWIG: $($_.FullName)"
            & $_.FullName -version
        }
    throw "CMake found unsuitable SWIG version. Please check the logs above."
}

if ($LASTEXITCODE -ne 0) {
    throw "CMake configuration failed"
}

# Run Ninja build
Write-Host "`nRunning Ninja build..."
& ninja -C "$buildDir"

if ($LASTEXITCODE -ne 0) {
    throw "Build failed"
}

Write-Host "`nBuild completed successfully!"
