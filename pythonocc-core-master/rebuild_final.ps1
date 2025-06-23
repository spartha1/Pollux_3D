# Stop on first error
$ErrorActionPreference = "Stop"

Write-Host "Starting build process..."

# Get script directory
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
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

# Install required packages (except SWIG)
Write-Host "`nInstalling required packages..."
conda config --add channels conda-forge
conda install -y cmake ninja
if ($LASTEXITCODE -ne 0) { throw "Failed to install packages" }

# Get tool paths
$cmakePath = (Get-Command cmake.exe).Source
$ninjaPath = (Get-Command ninja.exe).Source
$pythonPath = (Get-Command python.exe).Source

# Use local SWIG installation
$swigDir = Join-Path $scriptDir "swig-4.2.1"
$swigPath = Join-Path $swigDir "swig.exe"

if (-not (Test-Path $swigPath)) {
    throw "SWIG not found at $swigPath. Please ensure SWIG is properly installed."
}

Write-Host "`nTool paths:"
Write-Host "CMake: $cmakePath"
Write-Host "Ninja: $ninjaPath"
Write-Host "SWIG: $swigPath"
Write-Host "Python: $pythonPath"

# Get SWIG paths
$swigRoot = $swigDir
$swigLib = Join-Path $swigRoot "Lib"  # Windows package has a Lib subdirectory

Write-Host "`nSWIG information:"
Write-Host "SWIG Path: $swigPath"
Write-Host "SWIG Root: $swigRoot"
Write-Host "SWIG Lib: $swigLib"

# Verify tool versions
Write-Host "`nVerifying tool versions:"
& $cmakePath --version
& $ninjaPath --version
& $swigPath -version

# Set environment variables for SWIG
$env:SWIG_EXECUTABLE = $swigPath
$env:SWIG_DIR = $swigLib
$env:SWIG_LIB = $swigLib
$env:SWIG_ROOT = $swigRoot
$env:PATH = "$swigRoot;$env:PATH"

# Create SWIG use file if it doesn't exist
$swigUseFile = Join-Path $swigLib "UseSWIG.cmake"
if (-not (Test-Path $swigUseFile)) {
    @"
set(SWIG_EXECUTABLE "$($swigPath.Replace('\','/'))")
set(SWIG_DIR "$($swigLib.Replace('\','/'))")
set(SWIG_VERSION "4.2.1")
set(SWIG_FOUND TRUE)
"@ | Out-File -FilePath $swigUseFile -Encoding UTF8
}

Write-Host "`nCreated SWIG use file at: $swigUseFile"

# Get OpenCASCADE paths from conda
$condaPrefix = & conda info --json | ConvertFrom-Json | Select-Object -ExpandProperty active_prefix
$occIncludeDir = Join-Path $condaPrefix "Library\include\opencascade"
$occLibDir = Join-Path $condaPrefix "Library\lib"

Write-Host "`nOpenCASCADE paths:"
Write-Host "Include: $occIncludeDir"
Write-Host "Library: $occLibDir"

# Run CMake
Write-Host "`nRunning CMake..."
$cmakeArgs = @(
    "-G", "Ninja"
    "-DSWIG_EXECUTABLE=$swigPath"
    "-DSWIG_DIR=$swigLib"
    "-DSWIG_USE_FILE=$swigUseFile"
    "-DSWIG_VERSION=4.2.1"
    "-DSWIG_FOUND=TRUE"
    "-DPYTHON_EXECUTABLE=$pythonPath"
    "-DCMAKE_BUILD_TYPE=Release"
    "-DOCCT_INCLUDE_DIR=$occIncludeDir"
    "-DOCCT_LIBRARY_DIR=$occLibDir"
    "-B", "$buildDir"
    "-S", "$sourceDir"
)

Write-Host "CMake arguments:"
$cmakeArgs | ForEach-Object { Write-Host "  $_" }

$cmakeOutput = & $cmakePath $cmakeArgs 2>&1
$cmakeOutput | ForEach-Object { Write-Host $_ }

if ($LASTEXITCODE -ne 0) {
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
    throw "CMake configuration failed"
}

# Run Ninja build
Write-Host "`nRunning Ninja build..."
& $ninjaPath -C "$buildDir"

if ($LASTEXITCODE -ne 0) {
    throw "Build failed"
}

Write-Host "`nBuild completed successfully!"
