# Stop on first error
$ErrorActionPreference = "Stop"

Write-Host "Setting up build environment..."

# Initialize Visual Studio environment
Write-Host "`nInitializing Visual Studio environment..."
$vsPath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
if (Test-Path $vsPath) {
    Write-Host "Found Visual Studio at: $vsPath"
    & "${env:COMSPEC}" /c "`"$vsPath`" x64 && set" | foreach-object {
        if ($_ -match "=") {
            $v = $_.split("=")
            Set-Item -Force -Path "ENV:\$($v[0])" -Value "$($v[1])"
        }
    }
    Write-Host "Visual Studio environment initialized"
} else {
    Write-Host "Visual Studio BuildTools not found at expected location."
    Write-Host "Please install Visual Studio BuildTools 2022 with C++ workload."
    exit 1
}

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

# Run CMake with verbose output
Write-Host "`nRunning CMake..."
$cmakeArgs = @(
    "-G", "Ninja"
    "--log-level=verbose"
    "--debug-output"
    "-DCMAKE_VERBOSE_MAKEFILE=ON"
    "-DSWIG_EXECUTABLE=$swigPath"
    "-DSWIG_DIR=$swigRoot"
    "-DSWIG_USE_FILE=$swigUseFile"
    "-DSWIG_VERSION=4.2.1"
    "-DSWIG_FOUND=TRUE"
    "-DPYTHON_EXECUTABLE=$pythonPath",
    "-DPython3_ROOT_DIR=$env:CONDA_PREFIX",
    "-DPython3_EXECUTABLE=$pythonPath""
    "-DOCCT_INCLUDE_DIR=$occIncludeDir"
    "-DOCCT_LIBRARY_DIR=$occLibDir"
    "-DCMAKE_BUILD_TYPE=Release"
    "-B", $buildDir
    "-S", $sourceDir
)

Write-Host "CMake arguments:"
$cmakeArgs | ForEach-Object { Write-Host "  $_" }

Write-Host "`nRunning CMake configuration..."

# Run CMake and capture output to a log file
$logFile = Join-Path $scriptDir "cmake_output.log"
& $cmakePath $cmakeArgs *>&1 | Tee-Object -FilePath $logFile

Write-Host "`nChecking CMake output for errors..."
Get-Content $logFile | ForEach-Object {
    Write-Host $_
    if ($_ -match "CMake Error:|CMake Warning:") {
        Write-Host "Found error/warning: $_" -ForegroundColor Red
    }
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "CMake configuration failed. See output above for details."
    exit 1
}

# Run Ninja build
Write-Host "`nRunning Ninja build..."
& $ninjaPath -C "$buildDir"

if ($LASTEXITCODE -ne 0) {
    throw "Build failed"
}

Write-Host "`nBuild completed successfully!"
